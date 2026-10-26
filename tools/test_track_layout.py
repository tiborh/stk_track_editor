import copy
import json
import math
from pathlib import Path
import tempfile
import unittest

from track_layout import DIRECTIONS, load_layout, parse_layout


ROOT = Path(__file__).resolve().parents[1]


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "track/layouts/oval.json").read_text())

    def assert_continuous(self, circuit):
        for a, b in zip(circuit.modules, circuit.modules[1:] + circuit.modules[:1]):
            for lateral in (-circuit.road_width / 2, 0, circuit.road_width / 2):
                for left, right in zip(a[-1].offset(lateral), b[0].offset(lateral)):
                    self.assertAlmostEqual(left, right, places=10)
            self.assertAlmostEqual(a[-1].tx, b[0].tx, places=10)
            self.assertAlmostEqual(a[-1].ty, b[0].ty, places=10)
        for a, b in zip(circuit.route, circuit.route[1:] + circuit.route[:1]):
            self.assertGreater(math.hypot(b.x - a.x, b.y - a.y), 0.1)
            self.assertLessEqual(math.hypot(b.x - a.x, b.y - a.y), 3.001)
            vertices = [a.offset(-7), a.offset(7), b.offset(7), b.offset(-7)]
            area = sum(p[0] * q[1] - p[1] * q[0]
                       for p, q in zip(vertices, vertices[1:] + vertices[:1]))
            self.assertGreater(area, 0)
        first = circuit.route[0]
        self.assertAlmostEqual(first.x, 0)
        self.assertAlmostEqual(first.y, 0)
        self.assertAlmostEqual(first.tx, 0)
        self.assertAlmostEqual(first.ty, 1)

    def test_examples_and_lengths(self):
        for name, straights, corners in (("oval", 2, 4), ("bends", 4, 6)):
            with self.subTest(name=name):
                circuit = load_layout(ROOT / f"track/layouts/{name}.json")
                self.assert_continuous(circuit)
                expected = straights * 90 + corners * math.pi * 45 / 2
                self.assertAlmostEqual(circuit.length, expected, delta=0.1)

    def test_unordered_tiles_are_equivalent(self):
        original = parse_layout(self.data)
        self.data["tiles"].reverse()
        self.assertEqual(original, parse_layout(self.data))

    def test_reverse_direction(self):
        self.data["start"]["heading"] = "south"
        self.assert_continuous(parse_layout(self.data))

    def test_all_rotations_and_headings(self):
        for turns in range(4):
            with self.subTest(turns=turns):
                data = copy.deepcopy(self.data)
                for tile in data["tiles"]:
                    for _ in range(turns):
                        tile["x"], tile["y"] = tile["y"], -tile["x"]
                    tile["rotation"] = (tile["rotation"] + turns * 90) % 360
                data["start"]["heading"] = list(DIRECTIONS)[turns]
                self.assert_continuous(parse_layout(data))

    def test_bad_values(self):
        for key, value in (("version", True), ("version", 2), ("id", "../llm_loop"),
                           ("id", "llm_loop"), ("name", ""), ("name", "bad\nname"),
                           ("cell_size", float("nan")), ("cell_size", 30),
                           ("cell_size", 10 ** 1000),
                           ("road_width", True), ("road_width", 50), ("tiles", [])):
            with self.subTest(key=key, value=value):
                data = copy.deepcopy(self.data)
                data[key] = value
                with self.assertRaises(ValueError):
                    parse_layout(data)

    def test_invalid_tiles_and_start(self):
        for key, value in (("id", "east"), ("kind", "bridge"), ("rotation", 45),
                           ("rotation", True), ("x", 0.5), ("y", 101)):
            with self.subTest(key=key, value=value):
                data = copy.deepcopy(self.data)
                data["tiles"][0][key] = value
                with self.assertRaises(ValueError):
                    parse_layout(data)
        for start in ({"tile": [], "heading": "north"},
                      {"tile": "missing", "heading": "north"},
                      {"tile": "north_west", "heading": "south"},
                      {"tile": "start", "heading": "east"},
                      {"tile": "start", "heading": []}):
            with self.subTest(start=start), self.assertRaises(ValueError):
                parse_layout({**self.data, "start": start})

    def test_overlapping_cells(self):
        self.data["tiles"][1]["y"] = 0
        with self.assertRaisesRegex(ValueError, "occupied cell"):
            parse_layout(self.data)

    def test_disconnected_or_misaligned_port(self):
        self.data["tiles"][1]["rotation"] = 180
        with self.assertRaisesRegex(ValueError, "unconnected port"):
            parse_layout(self.data)

    def test_two_closed_loops_rejected(self):
        second = copy.deepcopy(self.data["tiles"])
        for tile in second:
            tile["x"] += 5
            tile["id"] += "_second"
        self.data["tiles"] += second
        with self.assertRaisesRegex(ValueError, "separate loops"):
            parse_layout(self.data)

    def test_unknown_and_missing_fields_rejected(self):
        for location in ("layout", "start", "tile"):
            data = copy.deepcopy(self.data)
            target = {"layout": data, "start": data["start"],
                      "tile": data["tiles"][0]}[location]
            target["typo"] = 0
            with self.subTest(location=location), self.assertRaises(ValueError):
                parse_layout(data)
        del self.data["road_width"]
        with self.assertRaisesRegex(ValueError, "missing"):
            parse_layout(self.data)

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text('{"version": 1, "version": 2}')
            with self.assertRaisesRegex(ValueError, "duplicate key"):
                load_layout(path)


if __name__ == "__main__":
    unittest.main()
