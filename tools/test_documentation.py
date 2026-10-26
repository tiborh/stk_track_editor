# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import re
import unittest
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]


def heading_ids(path):
    result, seen = set(), {}
    fenced = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            fenced = not fenced
        if fenced or not re.match(r"^#{1,6} ", line):
            continue
        text = re.sub(r"[`*_]", "", re.sub(r"^#+ ", "", line)).lower()
        slug = re.sub(r"[^\w\- ]", "", text).replace(" ", "-")
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        result.add(slug if not count else f"{slug}-{count}")
    return result


class DocumentationTests(unittest.TestCase):
    def test_local_document_links_and_fences(self):
        paths = list(ROOT.glob("*.md")) + list((ROOT / "docs").glob("*.md"))
        for path in paths:
            content = path.read_text(encoding="utf-8")
            with self.subTest(document=path.name):
                self.assertEqual(content.count("```") % 2, 0, "Unbalanced code fences")
            for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
                if "://" in link or link.startswith("mailto:"):
                    continue
                with self.subTest(document=path.name, link=link):
                    name, _, anchor = unquote(link).partition("#")
                    target = (path.parent / name).resolve() if name else path
                    self.assertTrue(target.is_file(), target)
                    if anchor:
                        self.assertIn(anchor, heading_ids(target))


if __name__ == "__main__":
    unittest.main()
