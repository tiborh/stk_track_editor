# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

from track_licenses import read_notice, write_notice


ROOT = Path(__file__).resolve().parents[1]


class TrackLicenseTests(unittest.TestCase):
    def test_examples_have_explicit_notices(self):
        for layout in (ROOT / "track/layouts").glob("*.json"):
            with self.subTest(layout=layout.name):
                notice = read_notice(layout.with_suffix(".licenses.txt"))
                self.assertIn("Copyright: 2026 tiborh", notice)
                self.assertIn("License: CC-BY-SA-4.0", notice)
                self.assertIn(f"track/layouts/{layout.name}", notice)
        self.assertIn("CC-BY-SA-4.0", read_notice(ROOT / "track/llm_loop.licenses.txt"))

    def test_notice_copied_verbatim_to_source_and_export(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = root / "example.licenses.txt"
            original.write_text("Copyright: Example author\nLicense: CC-BY-4.0\n")
            source, export = root / "source", root / "export"
            source.mkdir()
            export.mkdir()
            write_notice(read_notice(original), source, export)
            self.assertEqual((source / "licenses.txt").read_bytes(), original.read_bytes())
            self.assertEqual((export / "licenses.txt").read_bytes(), original.read_bytes())

    def test_override_is_explicit_and_missing_or_empty_override_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            default, override = root / "default.txt", root / "override.txt"
            override.write_text("Different author and license")
            self.assertEqual(read_notice(default, override), "Different author and license")
            with self.assertRaises(FileNotFoundError):
                read_notice(default, root / "missing.txt")
            override.write_text(" \n")
            with self.assertRaisesRegex(ValueError, "empty"):
                read_notice(default, override)

    def test_missing_default_warns_without_inventing_attribution(self):
        with tempfile.TemporaryDirectory() as temporary:
            stream = io.StringIO()
            with contextlib.redirect_stderr(stream):
                notice = read_notice(Path(temporary) / "missing.txt")
            self.assertIsNone(notice)
            self.assertIn("before redistributing", stream.getvalue())
            write_notice(notice, temporary)
            self.assertFalse((Path(temporary) / "licenses.txt").exists())

    def test_unlicensed_build_cannot_retain_stale_notice(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "licenses.txt"
            path.write_text("Attribution from a different build")
            with self.assertRaisesRegex(ValueError, "stale attribution"):
                write_notice(None, temporary)
            self.assertEqual(path.read_text(), "Attribution from a different build")


if __name__ == "__main__":
    unittest.main()
