#!/usr/bin/env python3
"""YouTube-Uploader: lädt Videos mit Titel, Beschreibung, Tags usw. auf deinen Kanal.

Befehle:
    python upload.py auth                      # einmalig: Google-Login, speichert token.json
    python upload.py upload VIDEO.mp4 --title "..." --description "..."
    python upload.py batch videos/             # lädt jedes VIDEO.mp4 mit passender VIDEO.json hoch
    python upload.py batch videos/ --dry-run   # prüft nur, lädt nichts hoch
"""
from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
HERE = Path(__file__).resolve().parent
DEFAULT_CLIENT_SECRET = HERE / "client_secret.json"
DEFAULT_TOKEN = HERE / "token.json"

VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi"}
THUMBNAIL_EXTENSIONS = (".jpg", ".jpeg", ".png")
PRIVACY_VALUES = {"public", "unlisted", "private"}
RETRIABLE_STATUS = {500, 502, 503, 504}
MAX_RETRIES = 8
CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB pro Upload-Stück


class MetadataError(ValueError):
    """Titel/Beschreibung/etc. verstoßen gegen YouTubes Regeln."""


@dataclass
class VideoMeta:
    title: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    privacy: str = "private"
    category_id: str = "22"  # 22 = "Menschen & Blogs"
    made_for_kids: bool = False
    publish_at: str | None = None  # ISO 8601, z. B. "2026-11-10T17:00:00Z"
    language: str | None = None  # z. B. "de"
    thumbnail: str | None = None
    playlist_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "VideoMeta":
        known = {
            "title", "description", "tags", "privacy", "category_id",
            "made_for_kids", "publish_at", "language", "thumbnail", "playlist_id",
        }
        unknown = set(data) - known
        if unknown:
            raise MetadataError(f"Unbekannte Felder: {', '.join(sorted(unknown))}")
        if "title" not in data:
            raise MetadataError("Feld 'title' fehlt")
        meta = cls(**data)
        meta.validate()
        return meta

    def validate(self) -> None:
        """Prüft die Regeln, an denen YouTube einen Upload sonst ablehnt."""
        title = self.title.strip()
        if not title:
            raise MetadataError("Titel ist leer")
        if len(title) > 100:
            raise MetadataError(f"Titel hat {len(title)} Zeichen, erlaubt sind 100")
        if len(self.description.encode("utf-8")) > 5000:
            raise MetadataError("Beschreibung ist länger als 5000 Bytes")
        for name, text in (("Titel", title), ("Beschreibung", self.description)):
            if "<" in text or ">" in text:
                raise MetadataError(f"{name} enthält < oder > – das lehnt YouTube ab")
        if not isinstance(self.tags, list) or not all(isinstance(t, str) for t in self.tags):
            raise MetadataError("'tags' muss eine Liste von Texten sein")
        # YouTube zählt Tags mit Leerzeichen inkl. Anführungszeichen, plus Kommas.
        tag_len = sum(len(t) + (2 if " " in t else 0) for t in self.tags) + max(len(self.tags) - 1, 0)
        if tag_len > 500:
            raise MetadataError(f"Tags sind zusammen {tag_len} Zeichen lang, erlaubt sind 500")
        if self.privacy not in PRIVACY_VALUES:
            raise MetadataError(f"'privacy' muss eins von {sorted(PRIVACY_VALUES)} sein")
        if self.publish_at:
            if self.privacy != "private":
                raise MetadataError("Für 'publish_at' muss 'privacy' auf 'private' stehen")
            try:
                when = datetime.fromisoformat(self.publish_at.replace("Z", "+00:00"))
            except ValueError as exc:
                raise MetadataError(f"'publish_at' ist kein gültiges Datum: {exc}") from None
            if when.tzinfo is None:
                raise MetadataError("'publish_at' braucht eine Zeitzone, z. B. ...Z oder +01:00")

    def to_body(self) -> dict:
        snippet = {
            "title": self.title.strip(),
            "description": self.description,
            "tags": self.tags,
            "categoryId": str(self.category_id),
        }
        if self.language:
            snippet["defaultLanguage"] = self.language
            snippet["defaultAudioLanguage"] = self.language
        status = {
            "privacyStatus": self.privacy,
            "selfDeclaredMadeForKids": bool(self.made_for_kids),
        }
        if self.publish_at:
            status["publishAt"] = self.publish_at
        return {"snippet": snippet, "status": status}


# ---------------------------------------------------------------- Login


def load_credentials(token_path: Path = DEFAULT_TOKEN):
    """Liest token.json (oder die Umgebungsvariable YOUTUBE_TOKEN_JSON) und erneuert ihn."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    raw = os.environ.get("YOUTUBE_TOKEN_JSON")
    if raw:
        creds = Credentials.from_authorized_user_info(json.loads(raw), SCOPES)
    elif token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    else:
        sys.exit(f"Kein Login gefunden ({token_path}). Führe zuerst 'python upload.py auth' aus.")

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            if not raw:
                token_path.write_text(creds.to_json())
        else:
            sys.exit("Login ist ungültig. Führe 'python upload.py auth' erneut aus.")
    return creds


def cmd_auth(args) -> None:
    from google_auth_oauthlib.flow import InstalledAppFlow

    secret = Path(args.client_secret)
    if not secret.exists():
        sys.exit(f"{secret} fehlt. Lade die OAuth-Client-Datei aus der Google Cloud Console herunter (siehe README).")
    flow = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
    Path(args.token).write_text(creds.to_json())
    print(f"Login gespeichert in {args.token}")


def build_service(token_path: Path):
    from googleapiclient.discovery import build

    return build("youtube", "v3", credentials=load_credentials(token_path), cache_discovery=False)


# ---------------------------------------------------------------- Upload


def _resumable_upload(request, label: str, sleep=time.sleep) -> dict:
    """Lädt Stück für Stück hoch und versucht es bei Netz-/Serverfehlern erneut."""
    from googleapiclient.errors import HttpError

    response = None
    retries = 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"  {label}: {int(status.progress() * 100)} %", flush=True)
            retries = 0
        except HttpError as exc:
            if exc.resp.status not in RETRIABLE_STATUS:
                raise
            error = f"Serverfehler {exc.resp.status}"
        except (OSError, ConnectionError) as exc:
            error = f"Netzwerkfehler: {exc}"
        else:
            continue
        retries += 1
        if retries > MAX_RETRIES:
            raise RuntimeError(f"Upload abgebrochen nach {MAX_RETRIES} Versuchen ({error})")
        wait = min(2 ** retries, 64) + random.random()
        print(f"  {error} – neuer Versuch in {wait:.0f} s", flush=True)
        sleep(wait)
    return response


def upload_video(youtube, video: Path, meta: VideoMeta) -> str:
    from googleapiclient.http import MediaFileUpload

    meta.validate()
    media = MediaFileUpload(str(video), chunksize=CHUNK_SIZE, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=meta.to_body(), media_body=media)
    response = _resumable_upload(request, video.name)
    video_id = response["id"]
    print(f"  Hochgeladen: https://youtu.be/{video_id}")

    if meta.thumbnail:
        thumb = Path(meta.thumbnail)
        if not thumb.is_absolute():
            thumb = video.parent / thumb
        try:
            youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(thumb))).execute()
            print(f"  Thumbnail gesetzt: {thumb.name}")
        except Exception as exc:  # Video ist schon oben – Thumbnail-Fehler soll das nicht kaputt machen
            print(f"  Thumbnail fehlgeschlagen (Kanal verifiziert?): {exc}")

    if meta.playlist_id:
        try:
            youtube.playlistItems().insert(
                part="snippet",
                body={"snippet": {"playlistId": meta.playlist_id,
                                  "resourceId": {"kind": "youtube#video", "videoId": video_id}}},
            ).execute()
            print("  Zur Playlist hinzugefügt")
        except Exception as exc:
            print(f"  Playlist fehlgeschlagen: {exc}")
    return video_id


def cmd_upload(args) -> None:
    video = Path(args.video)
    if not video.exists():
        sys.exit(f"Datei nicht gefunden: {video}")
    meta = VideoMeta(
        title=args.title,
        description=args.description or "",
        tags=[t.strip() for t in (args.tags or "").split(",") if t.strip()],
        privacy=args.privacy,
        category_id=args.category,
        made_for_kids=args.made_for_kids,
        publish_at=args.publish_at,
        language=args.language,
        thumbnail=args.thumbnail,
        playlist_id=args.playlist,
    )
    try:
        meta.validate()
    except MetadataError as exc:
        sys.exit(f"Fehler: {exc}")
    if args.dry_run:
        print(json.dumps(meta.to_body(), indent=2, ensure_ascii=False))
        return
    upload_video(build_service(Path(args.token)), video, meta)


# ---------------------------------------------------------------- Batch (Ordner)


def find_jobs(folder: Path) -> list[tuple[Path, Path]]:
    """Paare aus Video + gleichnamiger .json, z. B. clip.mp4 + clip.json."""
    jobs = []
    for video in sorted(folder.iterdir()):
        if video.suffix.lower() in VIDEO_EXTENSIONS:
            meta_file = video.with_suffix(".json")
            if meta_file.exists():
                jobs.append((video, meta_file))
            else:
                print(f"Übersprungen (keine {meta_file.name}): {video.name}")
    return jobs


def load_meta(video: Path, meta_file: Path) -> VideoMeta:
    data = json.loads(meta_file.read_text(encoding="utf-8"))
    if "thumbnail" not in data:
        for ext in THUMBNAIL_EXTENSIONS:
            candidate = video.with_suffix(ext)
            if candidate.exists():
                data["thumbnail"] = candidate.name
                break
    return VideoMeta.from_dict(data)


def cmd_batch(args) -> None:
    folder = Path(args.folder)
    done_dir = folder / "uploaded"
    jobs = find_jobs(folder)
    if not jobs:
        print("Nichts zu tun.")
        return

    # Erst alles prüfen, damit nicht nach 3 von 5 Uploads ein Tippfehler abbricht.
    planned, failed = [], 0
    for video, meta_file in jobs:
        try:
            planned.append((video, meta_file, load_meta(video, meta_file)))
        except (MetadataError, json.JSONDecodeError, TypeError) as exc:
            print(f"FEHLER in {meta_file.name}: {exc}")
            failed += 1

    for video, _, meta in planned:
        print(f"{'[Probe] ' if args.dry_run else ''}{video.name} → \"{meta.title}\" ({meta.privacy})")
    if args.dry_run or not planned:
        sys.exit(1 if failed else 0)

    youtube = build_service(Path(args.token))
    done_dir.mkdir(exist_ok=True)
    for video, meta_file, meta in planned:
        print(f"Lade hoch: {video.name}")
        try:
            video_id = upload_video(youtube, video, meta)
        except Exception as exc:
            print(f"  FEHLGESCHLAGEN: {exc}")
            failed += 1
            continue
        # Erledigtes wegräumen, damit es beim nächsten Lauf nicht doppelt hochgeht.
        result = json.loads(meta_file.read_text(encoding="utf-8"))
        result["video_id"] = video_id
        result["url"] = f"https://youtu.be/{video_id}"
        result["uploaded_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        (done_dir / meta_file.name).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        meta_file.unlink()
        shutil.move(str(video), done_dir / video.name)
        if meta.thumbnail and (video.parent / meta.thumbnail).exists():
            shutil.move(str(video.parent / meta.thumbnail), done_dir / Path(meta.thumbnail).name)
    sys.exit(1 if failed else 0)


# ---------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Videos auf YouTube hochladen")
    parser.add_argument("--token", default=str(DEFAULT_TOKEN), help="Pfad zu token.json")
    sub = parser.add_subparsers(dest="command", required=True)

    p_auth = sub.add_parser("auth", help="Einmalig mit Google einloggen")
    p_auth.add_argument("--client-secret", default=str(DEFAULT_CLIENT_SECRET))
    p_auth.set_defaults(func=cmd_auth)

    p_up = sub.add_parser("upload", help="Ein einzelnes Video hochladen")
    p_up.add_argument("video")
    p_up.add_argument("--title", required=True)
    p_up.add_argument("--description", default="")
    p_up.add_argument("--tags", help="Kommagetrennt: tag1,tag2")
    p_up.add_argument("--privacy", default="private", choices=sorted(PRIVACY_VALUES))
    p_up.add_argument("--category", default="22")
    p_up.add_argument("--made-for-kids", action="store_true")
    p_up.add_argument("--publish-at", help="Geplante Veröffentlichung, z. B. 2026-11-10T17:00:00Z")
    p_up.add_argument("--language", help="z. B. de")
    p_up.add_argument("--thumbnail")
    p_up.add_argument("--playlist", help="Playlist-ID")
    p_up.add_argument("--dry-run", action="store_true", help="Nur prüfen, nichts hochladen")
    p_up.set_defaults(func=cmd_upload)

    p_batch = sub.add_parser("batch", help="Alle Videos in einem Ordner hochladen")
    p_batch.add_argument("folder", nargs="?", default=str(HERE / "videos"))
    p_batch.add_argument("--dry-run", action="store_true", help="Nur prüfen, nichts hochladen")
    p_batch.set_defaults(func=cmd_batch)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
