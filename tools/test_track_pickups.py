import copy
import json
import math
from pathlib import Path
import unittest

from track_editor import inspect_layout
from track_layout import PICKUP_MARGIN, Tile, parse_layout, read_layout, road_sample


ROOT = Path(__file__).resolve().parents[1]


class PickupTests(unittest.TestCase):
    def setUp(self):
        self.original = json.loads((ROOT / "track/layouts/oval.json").read_text())
        self.data = copy.deepcopy(self.original)
        self.data.update(version=2, pickups=[
            {"id": "box", "kind": "item", "tile": "start", "along": 0.75, "lateral": -3},
            {"id": "small", "kind": "nitro_small", "tile": "north_west", "along": 0.3, "lateral": 2},
            {"id": "big", "kind": "nitro_big", "tile": "east", "along": 0.5, "lateral": 0},
        ])

    def test_v1_and_empty_v2_preserve_geometry(self):
        old = parse_layout(self.original)
        new = parse_layout({**self.original, "version": 2, "pickups": []})
        self.assertEqual(old.route, new.route)
        self.assertEqual(old.modules, new.modules)
        self.assertEqual(old.pickups, ())
        self.assertEqual(new.pickups, ())
        self.assertEqual(new.version, 2)
        with self.assertRaisesRegex(ValueError, "unknown"):
            parse_layout({**self.original, "pickups": []})
        with self.assertRaisesRegex(ValueError, "missing"):
            parse_layout({**self.original, "version": 2})

    def world_positions(self, data):
        circuit = parse_layout(data)
        _, _, size, _, tiles, _, start, heading = read_layout(data)
        origin = road_sample(tiles[start], size, 0.5)
        tx, ty = {"north": (0, 1), "east": (1, 0),
                  "south": (0, -1), "west": (-1, 0)}[heading]
        return [(x * ty + y * tx + origin.x, -x * tx + y * ty + origin.y, z)
                for x, y, z in (placed.position for placed in circuit.pickups)]

    def test_order_heading_and_start_do_not_move_pickups(self):
        expected = self.world_positions(self.data)
        self.data["tiles"].reverse()
        self.assertEqual(expected, self.world_positions(self.data))
        for start in ({"tile": "start", "heading": "south"},
                      {"tile": "east", "heading": "south"},
                      {"tile": "east", "heading": "north"}):
            self.data["start"] = start
            for a, b in zip(expected, self.world_positions(self.data)):
                for x, y in zip(a, b):
                    self.assertAlmostEqual(x, y)

    def test_canonical_geometry_all_rotations(self):
        for kind in ("straight", "corner"):
            for rotation in (0, 90, 180, 270):
                for along in (0, 0.25, 0.5, 1):
                    tile = Tile("piece", kind, 3, -2, rotation)
                    sample = road_sample(tile, 90, along)
                    if kind == "straight":
                        local = (0, 90 * (along - 0.5))
                        tangent = (0, 1)
                    else:
                        angle = along * math.pi / 2
                        local = (45 * (1 - math.cos(angle)), 45 * (math.sin(angle) - 1))
                        tangent = (math.sin(angle), math.cos(angle))
                    x, y = tile.rotate(*local)
                    tx, ty = tile.rotate(*tangent)
                    self.assertAlmostEqual(sample.x, x + 270)
                    self.assertAlmostEqual(sample.y, y - 180)
                    self.assertAlmostEqual(sample.tx, tx)
                    self.assertAlmostEqual(sample.ty, ty)
                    px, py, z = sample.offset(3)
                    self.assertAlmostEqual(px, sample.x + ty * 3)
                    self.assertAlmostEqual(py, sample.y - tx * 3)
                    self.assertEqual(z, 0)

    def test_editor_uses_same_geometry_even_in_drafts(self):
        for turns in range(4):
            data = copy.deepcopy(self.data)
            for tile in data["tiles"]:
                for _ in range(turns):
                    tile["x"], tile["y"] = tile["y"], -tile["x"]
                tile["rotation"] = (tile["rotation"] + turns * 90) % 360
            data["start"]["heading"] = ("north", "east", "south", "west")[turns]
            result = inspect_layout(data)
            self.assertTrue(result["valid"])
            expected = self.world_positions(data)
            for marker, (x, y, _) in zip(result["pickups"], expected):
                self.assertAlmostEqual(marker["x"] * data["cell_size"], x)
                self.assertAlmostEqual(marker["y"] * data["cell_size"], y)
            data["tiles"] = data["tiles"][:2]
            data["pickups"] = data["pickups"][:2]
            data["start"]["tile"] = ""
            draft = inspect_layout(data)
            self.assertTrue(draft["draft_ok"])
            self.assertFalse(draft["valid"])
            self.assertEqual(draft["pickups"], result["pickups"][:2])

    def test_invalid_pickups_rejected_by_editor_and_generator(self):
        invalid = [
            ("id", ""), ("id", []), ("id", "small"), ("kind", "banana"), ("kind", []),
            ("tile", "missing"), ("tile", []), ("along", -0.01), ("along", 1.01),
            ("along", True), ("along", "0.5"), ("along", float("nan")),
            ("lateral", float("inf")), ("lateral", True), ("lateral", 5.01),
            ("lateral", -5.01), ("extra", 0),
        ]
        for key, value in invalid:
            with self.subTest(key=key, value=value):
                data = copy.deepcopy(self.data)
                data["pickups"][0][key] = value
                with self.assertRaises(ValueError):
                    parse_layout(data)
                self.assertFalse(inspect_layout(data)["draft_ok"])
        for value in (None, {}, [{}], [self.data["pickups"][0]] * 2001):
            with self.subTest(value=type(value)):
                self.assertFalse(inspect_layout({**self.data, "pickups": value})["draft_ok"])
        del self.data["pickups"][0]["along"]
        self.assertFalse(inspect_layout(self.data)["draft_ok"])

    def test_boundaries_and_width_changes(self):
        for along in (0, 1):
            for lateral in (-5, 5):
                self.data["pickups"][0].update(along=along, lateral=lateral)
                self.assertTrue(inspect_layout(self.data)["valid"])
        self.data["road_width"] = 10
        self.assertFalse(inspect_layout(self.data)["draft_ok"])
        self.data["pickups"][0]["lateral"] = 10 / 2 - PICKUP_MARGIN
        self.assertTrue(inspect_layout(self.data)["valid"])


if __name__ == "__main__":
    unittest.main()
