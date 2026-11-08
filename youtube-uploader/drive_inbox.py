"""Google-Drive-Eingangsordner: holt Videos + Texte aus Drive und lädt sie auf YouTube.

Gedacht für Uploads vom iPad: Video und Text in den Drive-Ordner legen,
GitHub Actions ruft `python upload.py drive` auf und erledigt den Rest.

Pro Video im Ordner (gleicher Name, andere Endung):
    folge-12.mp4                 das Video
    folge-12  (Google Doc)       ODER folge-12.txt ODER folge-12.json  – Titel/Beschreibung
    folge-12.jpg                 optional: Thumbnail

Danach liegt alles im Unterordner "hochgeladen", plus "folge-12 – Link.txt".
Schlägt etwas fehl, entsteht "folge-12.FEHLER.txt" mit der Ursache. Solange diese
Datei existiert, wird das Video übersprungen – nach dem Korrigieren einfach löschen.
"""
from __future__ import annotations

import io
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import upload
from upload import MetadataError, VideoMeta, parse_text_meta

FOLDER_MIME = "application/vnd.google-apps.folder"
DOC_MIME = "application/vnd.google-apps.document"
DONE_FOLDER = "hochgeladen"
ERROR_SUFFIX = ".FEHLER.txt"
LINK_SUFFIX = " – Link.txt"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

def _split(name: str) -> tuple[str, str]:
    p = Path(name)
    return (p.stem, p.suffix.lower()) if p.suffix else (name, "")


@dataclass
class Job:
    base: str
    video: dict
    meta: dict
    thumbnail: dict | None = None


def plan_jobs(files: list[dict]) -> tuple[list[Job], list[str]]:
    """Ordnet Drive-Dateien zu Jobs. Gibt (Jobs, Hinweise) zurück."""
    videos, metas, images, errors = {}, {}, {}, set()
    for f in files:
        name, mime = f["name"], f.get("mimeType", "")
        if mime == FOLDER_MIME or name.endswith(LINK_SUFFIX):
            continue
        if name.endswith(ERROR_SUFFIX):
            errors.add(name[: -len(ERROR_SUFFIX)])
            continue
        base, ext = _split(name)
        if mime.startswith("video/") or ext in upload.VIDEO_EXTENSIONS:
            videos[base] = f
        elif mime == DOC_MIME:
            # Docs haben keine echte Endung; "folge-12.txt" als Doc soll trotzdem passen.
            doc_base = base if ext in (".txt", ".json") else name
            metas.setdefault(doc_base, {})["doc"] = f
        elif ext in (".json", ".txt"):
            metas.setdefault(base, {})[ext] = f
        elif ext in IMAGE_EXTENSIONS or mime in ("image/jpeg", "image/png"):
            images[base] = f

    jobs, notes = [], []
    for base, video in sorted(videos.items()):
        if base in errors:
            notes.append(f"Übersprungen (erst {base}{ERROR_SUFFIX} löschen): {video['name']}")
            continue
        options = metas.get(base, {})
        meta = options.get(".json") or options.get(".txt") or options.get("doc")
        if not meta:
            notes.append(f"Wartet auf Text (Doc/.txt/.json namens '{base}'): {video['name']}")
            continue
        jobs.append(Job(base, video, meta, images.get(base)))
    return jobs, notes


class DriveInbox:
    def __init__(self, drive, folder_name: str):
        self.drive = drive
        self.folder_id = self._folder(folder_name, "root")
        self.done_id = self._folder(DONE_FOLDER, self.folder_id)

    def _folder(self, name: str, parent: str) -> str:
        q = (f"mimeType='{FOLDER_MIME}' and name='{name.replace(chr(39), chr(92) + chr(39))}' "
             f"and '{parent}' in parents and trashed=false")
        found = self.drive.files().list(q=q, fields="files(id)", pageSize=1).execute().get("files", [])
        if found:
            return found[0]["id"]
        created = self.drive.files().create(
            body={"name": name, "mimeType": FOLDER_MIME, "parents": [parent]}, fields="id").execute()
        print(f"Drive-Ordner angelegt: {name}")
        return created["id"]

    def list_files(self) -> list[dict]:
        files, token = [], None
        while True:
            resp = self.drive.files().list(
                q=f"'{self.folder_id}' in parents and trashed=false",
                fields="nextPageToken, files(id, name, mimeType)",
                pageSize=1000, pageToken=token).execute()
            files += resp.get("files", [])
            token = resp.get("nextPageToken")
            if not token:
                return files

    def read_text(self, f: dict) -> str:
        if f.get("mimeType") == DOC_MIME:
            data = self.drive.files().export_media(fileId=f["id"], mimeType="text/plain").execute()
        else:
            data = self.drive.files().get_media(fileId=f["id"]).execute()
        return data.decode("utf-8") if isinstance(data, bytes) else data

    def download(self, f: dict, target: Path) -> None:
        from googleapiclient.http import MediaIoBaseDownload

        with io.FileIO(target, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, self.drive.files().get_media(fileId=f["id"]),
                                             chunksize=32 * 1024 * 1024)
            done = False
            while not done:
                _, done = downloader.next_chunk(num_retries=5)

    def move_to_done(self, f: dict) -> None:
        self.drive.files().update(fileId=f["id"], addParents=self.done_id,
                                  removeParents=self.folder_id, fields="id").execute()

    def write_text(self, name: str, text: str, parent: str) -> None:
        from googleapiclient.http import MediaInMemoryUpload

        self.drive.files().create(
            body={"name": name, "parents": [parent]},
            media_body=MediaInMemoryUpload(text.encode("utf-8"), mimetype="text/plain"),
            fields="id").execute()


def load_job_meta(inbox: DriveInbox, job: Job) -> VideoMeta:
    text = inbox.read_text(job.meta)
    if job.meta["name"].lower().endswith(".json"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise MetadataError(f"JSON fehlerhaft: {exc}") from None
    else:
        data = parse_text_meta(text)
    data.pop("thumbnail", None)  # Thumbnail kommt im Drive-Modus aus dem Ordner
    return VideoMeta.from_dict(data)


def process(inbox: DriveInbox, youtube_factory, workdir: Path) -> int:
    """Arbeitet den Ordner ab. Gibt die Zahl der Fehler zurück."""
    jobs, notes = plan_jobs(inbox.list_files())
    for note in notes:
        print(note)
    if not jobs:
        print("Nichts hochzuladen.")
        return 0

    youtube, failed = None, 0
    for job in jobs:
        print(f"Bearbeite: {job.video['name']}")
        try:
            meta = load_job_meta(inbox, job)
            video_path = workdir / job.video["name"]
            print("  Lade aus Drive …")
            inbox.download(job.video, video_path)
            if job.thumbnail:
                thumb_path = workdir / job.thumbnail["name"]
                inbox.download(job.thumbnail, thumb_path)
                meta.thumbnail = str(thumb_path)
            youtube = youtube or youtube_factory()
            video_id = upload.upload_video(youtube, video_path, meta)
        except Exception as exc:
            failed += 1
            print(f"  FEHLGESCHLAGEN: {exc}")
            try:
                inbox.write_text(job.base + ERROR_SUFFIX,
                                 f"Upload von {job.video['name']} fehlgeschlagen:\n\n{exc}\n\n"
                                 "Korrigiere das Problem und lösche dann diese Datei – "
                                 "beim nächsten Lauf wird es erneut versucht.\n",
                                 inbox.folder_id)
            except Exception as note_exc:
                print(f"  Konnte Fehlerdatei nicht anlegen: {note_exc}")
            continue
        finally:
            for p in workdir.iterdir():
                p.unlink()

        try:
            for f in (job.video, job.meta, job.thumbnail):
                if f:
                    inbox.move_to_done(f)
            stamp = datetime.now().astimezone().strftime("%d.%m.%Y %H:%M")
            inbox.write_text(job.base + LINK_SUFFIX,
                             f"{meta.title}\nhttps://youtu.be/{video_id}\n"
                             f"Studio: https://studio.youtube.com/video/{video_id}/edit\n"
                             f"Sichtbarkeit: {meta.privacy}\nHochgeladen: {stamp}\n",
                             inbox.done_id)
        except Exception as exc:
            # Das Video ist schon auf YouTube – auf keinen Fall noch mal hochladen.
            failed += 1
            print(f"  Aufräumen in Drive fehlgeschlagen: {exc}")
            inbox.write_text(job.base + ERROR_SUFFIX,
                             f"{job.video['name']} ist BEREITS HOCHGELADEN: https://youtu.be/{video_id}\n\n"
                             f"Nur das Verschieben in '{DONE_FOLDER}' ist gescheitert ({exc}).\n"
                             f"Verschiebe die Dateien selbst und lösche diese Datei.\n",
                             inbox.folder_id)
    return failed


def run(token_path: Path, folder_name: str | None = None) -> int:
    from googleapiclient.discovery import build

    creds = upload.load_credentials(token_path)
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)
    inbox = DriveInbox(drive, folder_name or os.environ.get("YT_DRIVE_FOLDER", "YouTube-Upload"))
    with tempfile.TemporaryDirectory() as tmp:
        return process(inbox, lambda: build("youtube", "v3", credentials=creds, cache_discovery=False),
                       Path(tmp))
