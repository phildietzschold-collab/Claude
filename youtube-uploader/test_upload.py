"""Tests ohne echten YouTube-Zugang: die API wird durch Attrappen ersetzt."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import upload
from upload import MetadataError, VideoMeta


class ValidateTests(unittest.TestCase):
    def test_minimal_ok(self):
        VideoMeta(title="Hallo").validate()

    def test_title_too_long(self):
        with self.assertRaisesRegex(MetadataError, "100"):
            VideoMeta(title="x" * 101).validate()

    def test_empty_title(self):
        with self.assertRaises(MetadataError):
            VideoMeta(title="   ").validate()

    def test_angle_brackets_rejected(self):
        with self.assertRaisesRegex(MetadataError, "<"):
            VideoMeta(title="ok", description="a <b> c").validate()

    def test_description_bytes(self):
        # 2600 Umlaute = 5200 Bytes in UTF-8, obwohl nur 2600 Zeichen
        with self.assertRaises(MetadataError):
            VideoMeta(title="ok", description="ä" * 2600).validate()

    def test_tags_too_long(self):
        with self.assertRaisesRegex(MetadataError, "500"):
            VideoMeta(title="ok", tags=["a" * 50] * 10).validate()

    def test_publish_at_requires_private(self):
        with self.assertRaisesRegex(MetadataError, "private"):
            VideoMeta(title="ok", privacy="public", publish_at="2026-12-01T10:00:00Z").validate()

    def test_publish_at_needs_timezone(self):
        with self.assertRaisesRegex(MetadataError, "Zeitzone"):
            VideoMeta(title="ok", publish_at="2026-12-01T10:00:00").validate()

    def test_unknown_field(self):
        with self.assertRaisesRegex(MetadataError, "titel"):
            VideoMeta.from_dict({"title": "ok", "titel": "Tippfehler"})

    def test_body(self):
        body = VideoMeta(title=" Mein Video ", tags=["a"], language="de",
                         publish_at="2026-12-01T10:00:00Z").to_body()
        self.assertEqual(body["snippet"]["title"], "Mein Video")
        self.assertEqual(body["snippet"]["defaultLanguage"], "de")
        self.assertEqual(body["status"], {"privacyStatus": "private",
                                          "selfDeclaredMadeForKids": False,
                                          "publishAt": "2026-12-01T10:00:00Z"})


class ResumableTests(unittest.TestCase):
    def _http_error(self, status):
        from googleapiclient.errors import HttpError
        return HttpError(mock.Mock(status=status), b"{}")

    def test_retries_on_server_error(self):
        req = mock.Mock()
        req.next_chunk.side_effect = [self._http_error(503), ConnectionError("weg"), (None, {"id": "abc"})]
        sleeps = []
        self.assertEqual(upload._resumable_upload(req, "v", sleep=sleeps.append), {"id": "abc"})
        self.assertEqual(len(sleeps), 2)

    def test_client_error_not_retried(self):
        req = mock.Mock()
        req.next_chunk.side_effect = [self._http_error(400)]
        from googleapiclient.errors import HttpError
        with self.assertRaises(HttpError):
            upload._resumable_upload(req, "v", sleep=lambda s: None)

    def test_gives_up(self):
        req = mock.Mock()
        req.next_chunk.side_effect = ConnectionError("weg")
        with self.assertRaisesRegex(RuntimeError, "abgebrochen"):
            upload._resumable_upload(req, "v", sleep=lambda s: None)


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _add(self, name, meta):
        (self.dir / f"{name}.mp4").write_bytes(b"fake video")
        if meta is not None:
            (self.dir / f"{name}.json").write_text(json.dumps(meta), encoding="utf-8")

    def test_uploads_and_moves(self):
        self._add("clip", {"title": "Clip eins", "description": "Text"})
        self._add("ohne_json", None)
        (self.dir / "clip.jpg").write_bytes(b"thumb")

        fake_service = mock.Mock()
        with mock.patch.object(upload, "build_service", return_value=fake_service), \
             mock.patch.object(upload, "upload_video", return_value="VID123") as up:
            with self.assertRaises(SystemExit) as cm:
                upload.main(["batch", str(self.dir)])
        self.assertEqual(cm.exception.code, 0)
        meta = up.call_args.args[2]
        self.assertEqual(meta.title, "Clip eins")
        self.assertEqual(meta.thumbnail, "clip.jpg")  # automatisch gefunden

        done = self.dir / "uploaded"
        self.assertTrue((done / "clip.mp4").exists())
        self.assertTrue((done / "clip.jpg").exists())
        result = json.loads((done / "clip.json").read_text(encoding="utf-8"))
        self.assertEqual(result["url"], "https://youtu.be/VID123")
        self.assertFalse((self.dir / "clip.mp4").exists())
        self.assertTrue((self.dir / "ohne_json.mp4").exists())  # unangetastet

    def test_dry_run_uploads_nothing(self):
        self._add("clip", {"title": "Clip"})
        with mock.patch.object(upload, "build_service") as bs:
            with self.assertRaises(SystemExit) as cm:
                upload.main(["batch", str(self.dir), "--dry-run"])
        self.assertEqual(cm.exception.code, 0)
        bs.assert_not_called()
        self.assertTrue((self.dir / "clip.mp4").exists())

    def test_bad_metadata_reported_others_continue(self):
        self._add("gut", {"title": "Gut"})
        self._add("schlecht", {"title": "x" * 150})
        with mock.patch.object(upload, "build_service"), \
             mock.patch.object(upload, "upload_video", return_value="V") as up:
            with self.assertRaises(SystemExit) as cm:
                upload.main(["batch", str(self.dir)])
        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(up.call_count, 1)
        self.assertTrue((self.dir / "schlecht.mp4").exists())

    def test_failed_upload_stays_in_inbox(self):
        self._add("clip", {"title": "Clip"})
        with mock.patch.object(upload, "build_service"), \
             mock.patch.object(upload, "upload_video", side_effect=RuntimeError("quota")):
            with self.assertRaises(SystemExit) as cm:
                upload.main(["batch", str(self.dir)])
        self.assertEqual(cm.exception.code, 1)
        self.assertTrue((self.dir / "clip.mp4").exists())
        self.assertTrue((self.dir / "clip.json").exists())


class UploadVideoTests(unittest.TestCase):
    def test_calls_insert_with_body(self):
        with tempfile.NamedTemporaryFile(suffix=".mp4") as f:
            f.write(b"x")
            f.flush()
            yt = mock.Mock()
            with mock.patch.object(upload, "_resumable_upload", return_value={"id": "ID1"}):
                vid = upload.upload_video(yt, Path(f.name), VideoMeta(title="T", description="D"))
        self.assertEqual(vid, "ID1")
        kwargs = yt.videos().insert.call_args.kwargs
        self.assertEqual(kwargs["part"], "snippet,status")
        self.assertEqual(kwargs["body"]["snippet"]["description"], "D")
        yt.thumbnails().set.assert_not_called()


if __name__ == "__main__":
    unittest.main()
