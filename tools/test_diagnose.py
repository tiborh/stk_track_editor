# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
import io
import unittest
from unittest.mock import patch

import diagnose


class DiagnoseTests(unittest.TestCase):
    def test_editor_only_does_not_require_or_launch_external_tools(self):
        stream = io.StringIO()
        with patch.object(diagnose, "run_command", side_effect=AssertionError("must not launch")), \
                patch.object(diagnose, "get_flatpak_apps", side_effect=AssertionError("must not query")), \
                contextlib.redirect_stdout(stream):
            self.assertEqual(diagnose.main(["--editor-only"]), 0)
        self.assertIn("editor prerequisites available", stream.getvalue())

    def test_missing_editor_asset_is_reported(self):
        original = diagnose.Path.is_file

        def is_file(path):
            return False if path.name == "editor.js" else original(path)

        stream = io.StringIO()
        with patch.object(diagnose.Path, "is_file", is_file), contextlib.redirect_stdout(stream):
            self.assertEqual(diagnose.main(["--editor-only"]), 1)
        self.assertIn("[MISSING] Editor file: editor/editor.js", stream.getvalue())

    def test_old_python_is_reported(self):
        with patch.object(diagnose.sys, "version_info", (3, 9)), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(diagnose.main(["--editor-only"]), 1)

    def test_editor_only_and_blender_probe_are_incompatible(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as result:
            diagnose.main(["--editor-only", "--probe-blender"])
        self.assertEqual(result.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
