"""Tests für den Drive-Weg (iPad). Drive und YouTube sind Attrappen."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import drive_inbox
import upload
from drive_inbox import DOC_MIME, Job, plan_jobs, process
from upload import MetadataError, parse_text_meta


class ParseTextTests(unittest.TestCase):
    def test_title_and_description(self):
        data = parse_text_meta("﻿\n  Mein Titel  \n\nZeile 1\nZeile 2\n")
        self.assertEqual(data, {"title": "Mein Titel", "description": "Zeile 1\nZeile 2"})

    def test_settings_block(self):
        data = parse_text_meta(
            "Titel\n\nText\n---\ntags: a, b c ,\nSichtbarkeit: Öffentlich\nKinder: nein\nsprache: de\n")
        self.assertEqual(data["tags"], ["a", "b c"])
        self.assertEqual(data["privacy"], "public")
        self.assertFalse(data["made_for_kids"])
        self.assertEqual(data["language"], "de")
        self.assertEqual(data["description"], "Text")

    def test_termin_forces_private(self):
        data = parse_text_meta("T\n---\ntermin: 2026-12-01T17:00:00Z")
        self.assertEqual(data["privacy"], "private")
        upload.VideoMeta.from_dict(data)  # gültig

    def test_dashes_in_description_are_kept(self):
        text = "T\n\nTeil 1\n---\nTeil 2 ist kein Einstellungsblock"
        self.assertEqual(parse_text_meta(text)["description"], "Teil 1\n---\nTeil 2 ist kein Einstellungsblock")

    def test_bad_privacy(self):
        with self.assertRaisesRegex(MetadataError, "Sichtbarkeit"):
            parse_text_meta("T\n---\nsichtbarkeit: geheim")

    def test_empty(self):
        with self.assertRaises(MetadataError):
            parse_text_meta("\n\n")


def f(name, mime="", id_=None):
    return {"id": id_ or name, "name": name, "mimeType": mime}


class PlanTests(unittest.TestCase):
    def test_pairs_and_notes(self):
        files = [
            f("a.mp4", "video/mp4"), f("a", DOC_MIME), f("a.jpg", "image/jpeg"),
            f("b.MOV", "video/quicktime"), f("b.txt", "text/plain"), f("b.json", "application/json"),
            f("c.mp4", "video/mp4"),                                   # noch kein Text
            f("d.mp4", "video/mp4"), f("d.txt"), f("d.FEHLER.txt"),     # Fehler-Sperre
            f("e.mp4", "video/mp4"), f("e.txt", DOC_MIME),              # Doc namens "e.txt"
            f("hochgeladen", drive_inbox.FOLDER_MIME),
        ]
        jobs, notes = plan_jobs(files)
        by_base = {j.base: j for j in jobs}
        self.assertEqual(sorted(by_base), ["a", "b", "e"])
        self.assertEqual(by_base["a"].meta["name"], "a")
        self.assertEqual(by_base["a"].thumbnail["name"], "a.jpg")
        self.assertEqual(by_base["b"].meta["name"], "b.json")  # JSON hat Vorrang
        self.assertTrue(any("c.mp4" in n for n in notes))
        self.assertTrue(any("d.FEHLER.txt" in n for n in notes))


class FakeInbox:
    folder_id, done_id = "INBOX", "DONE"

    def __init__(self, files, texts):
        self.files, self.texts = files, texts
        self.moved, self.written, self.downloaded = [], {}, []

    def list_files(self):
        return self.files

    def read_text(self, file):
        return self.texts[file["name"]]

    def download(self, file, target: Path):
        self.downloaded.append(file["name"])
        target.write_bytes(b"data")

    def move_to_done(self, file):
        self.moved.append(file["name"])

    def write_text(self, name, text, parent):
        self.written[(parent, name)] = text


class ProcessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.work = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_success_moves_and_writes_link(self):
        inbox = FakeInbox([f("a.mp4", "video/mp4"), f("a", DOC_MIME), f("a.png", "image/png")],
                          {"a": "Titel A\n\nBeschreibung\n---\nsichtbarkeit: nicht gelistet"})
        factory = mock.Mock(return_value="YT")
        with mock.patch.object(upload, "upload_video", return_value="VID") as up:
            self.assertEqual(process(inbox, factory, self.work), 0)
        _, path, meta = up.call_args.args
        self.assertEqual(path.name, "a.mp4")
        self.assertEqual((meta.title, meta.privacy), ("Titel A", "unlisted"))
        self.assertTrue(meta.thumbnail.endswith("a.png"))
        self.assertEqual(sorted(inbox.moved), ["a", "a.mp4", "a.png"])
        self.assertIn("https://youtu.be/VID", inbox.written[("DONE", "a – Link.txt")])
        self.assertEqual(list(self.work.iterdir()), [])  # temporäre Dateien weg

    def test_bad_text_writes_error_file_and_keeps_files(self):
        inbox = FakeInbox([f("a.mp4", "video/mp4"), f("a.txt")], {"a.txt": "x" * 120})
        with mock.patch.object(upload, "upload_video") as up:
            self.assertEqual(process(inbox, mock.Mock(), self.work), 1)
        up.assert_not_called()
        self.assertEqual(inbox.downloaded, [])  # kein unnötiger Download
        self.assertEqual(inbox.moved, [])
        self.assertIn("100", inbox.written[("INBOX", "a.FEHLER.txt")])

    def test_move_failure_after_upload_blocks_retry(self):
        inbox = FakeInbox([f("a.mp4", "video/mp4"), f("a.txt")], {"a.txt": "T"})
        inbox.move_to_done = mock.Mock(side_effect=OSError("Drive weg"))
        with mock.patch.object(upload, "upload_video", return_value="VID"):
            self.assertEqual(process(inbox, mock.Mock(), self.work), 1)
        note = inbox.written[("INBOX", "a.FEHLER.txt")]
        self.assertIn("BEREITS HOCHGELADEN", note)
        self.assertIn("youtu.be/VID", note)
        # Nächster Lauf: Fehlerdatei sperrt das Video → kein Doppel-Upload
        jobs, _ = plan_jobs(inbox.files + [f("a.FEHLER.txt")])
        self.assertEqual(jobs, [])

    def test_nothing_to_do_does_not_log_in_to_youtube(self):
        factory = mock.Mock()
        self.assertEqual(process(FakeInbox([], {}), factory, self.work), 0)
        factory.assert_not_called()


class DriveInboxTests(unittest.TestCase):
    """Prüft die echten Drive-API-Aufrufe gegen eine Attrappe des Clients."""

    def test_finds_or_creates_folders(self):
        drive = mock.Mock()
        files = drive.files.return_value
        files.list.return_value.execute.side_effect = [{"files": [{"id": "F1"}]}, {"files": []}]
        files.create.return_value.execute.return_value = {"id": "DONE1"}
        inbox = drive_inbox.DriveInbox(drive, "YouTube-Upload")
        self.assertEqual((inbox.folder_id, inbox.done_id), ("F1", "DONE1"))
        body = files.create.call_args.kwargs["body"]
        self.assertEqual(body, {"name": "hochgeladen", "mimeType": drive_inbox.FOLDER_MIME, "parents": ["F1"]})
        self.assertIn("name='YouTube-Upload'", files.list.call_args_list[0].kwargs["q"])

    def test_read_doc_exports_text(self):
        inbox = drive_inbox.DriveInbox.__new__(drive_inbox.DriveInbox)
        inbox.drive = mock.Mock()
        inbox.drive.files().export_media().execute.return_value = "Titel".encode()
        self.assertEqual(inbox.read_text({"id": "x", "mimeType": DOC_MIME}), "Titel")
        inbox.drive.files().export_media.assert_called_with(fileId="x", mimeType="text/plain")


if __name__ == "__main__":
    unittest.main()
