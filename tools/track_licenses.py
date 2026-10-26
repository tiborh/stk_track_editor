# SPDX-License-Identifier: GPL-3.0-or-later
"""Carry explicit track attribution into generated source and export folders."""

from pathlib import Path
import sys


def read_notice(default, override=None):
    path = Path(override) if override is not None else Path(default)
    if override is None and not path.exists():
        print(f"WARNING: No track license notice at {path}. "
              "Private generation is allowed; add attribution and licensing "
              "before redistributing this track.", file=sys.stderr)
        return None
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"Track license notice is empty: {path}")
    return text


def write_notice(text, *directories):
    if text is None:
        for directory in directories:
            path = Path(directory) / "licenses.txt"
            if path.exists() or path.is_symlink():
                raise ValueError(f"Refusing to retain stale attribution without a notice: {path}")
        return
    for directory in directories:
        (Path(directory) / "licenses.txt").write_text(text, encoding="utf-8")
