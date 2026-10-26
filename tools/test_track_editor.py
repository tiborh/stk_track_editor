import copy
import http.client
import json
from pathlib import Path
import threading
import unittest
from http.server import ThreadingHTTPServer

from track_editor import EditorHandler, inspect_layout
from track_layout import parse_layout


ROOT = Path(__file__).resolve().parents[1]


class EditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), EditorHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.data = json.loads((ROOT / "track/layouts/oval.json").read_text())

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            connection.request(method, path, body, headers or {})
            response = connection.getresponse()
            return response.status, response.read(), dict(response.getheaders())
        finally:
            connection.close()

    def test_examples_match_generator(self):
        for name in ("oval", "bends", "pickup_oval"):
            data = json.loads((ROOT / f"track/layouts/{name}.json").read_text())
            result = inspect_layout(data)
            self.assertTrue(result["valid"])
            self.assertEqual(result["ports"], [])
            self.assertIn(f"{parse_layout(data).length:.1f} m", result["message"])

    def test_empty_and_incomplete_drafts(self):
        self.data["tiles"] = []
        self.data["start"]["tile"] = ""
        result = inspect_layout(self.data)
        self.assertTrue(result["draft_ok"])
        self.assertFalse(result["valid"])
        self.data["tiles"] = [{"id": "a", "kind": "straight", "x": 0, "y": 0, "rotation": 90}]
        result = inspect_layout(self.data)
        self.assertTrue(result["draft_ok"])
        self.assertEqual({(p["dx"], p["dy"]) for p in result["ports"]}, {(-1, 0), (1, 0)})
        with self.assertRaises(ValueError):
            parse_layout(self.data)

    def test_diagnostics_all_rotations(self):
        for turns in range(4):
            data = copy.deepcopy(self.data)
            for tile in data["tiles"]:
                for _ in range(turns):
                    tile["x"], tile["y"] = tile["y"], -tile["x"]
                tile["rotation"] = (tile["rotation"] + turns * 90) % 360
            data["start"]["heading"] = ("north", "east", "south", "west")[turns]
            self.assertTrue(inspect_layout(data)["valid"])
            data["tiles"].pop()
            result = inspect_layout(data)
            self.assertTrue(result["draft_ok"])
            self.assertFalse(result["valid"])
            self.assertEqual(len(result["ports"]), 2)

    def test_draft_structure_still_checked(self):
        for key, value in (("version", 2), ("id", "../bad"), ("tiles", [{}]),
                           ("cell_size", 10), ("start", {"tile": "", "heading": "up"})):
            with self.subTest(key=key):
                result = inspect_layout({**self.data, key: value})
                self.assertFalse(result["draft_ok"])
                self.assertFalse(result["valid"])
        self.data["tiles"].append(copy.deepcopy(self.data["tiles"][0]))
        self.assertFalse(inspect_layout(self.data)["draft_ok"])

    def test_assets_and_not_found(self):
        for path in ("/", "/editor.js", "/editor.css", "/examples/oval.json", "/examples/bends.json",
                     "/examples/pickup_oval.json"):
            status, body, headers = self.request("GET", path)
            self.assertEqual(status, 200)
            self.assertTrue(body)
            self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        for path in ("/../README.md", "/tools/build_track.py", "/api/build"):
            self.assertEqual(self.request("GET", path)[0], 404)

    def test_inspection_http(self):
        status, body, _ = self.request("POST", "/api/inspect", json.dumps(self.data),
                                       {"Content-Type": "application/json"})
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["valid"])
        status, body, _ = self.request("POST", "/api/inspect", '{"version":1,"version":1}',
                                       {"Content-Type": "application/json"})
        self.assertEqual(status, 400)
        self.assertIn("duplicate key", json.loads(body)["message"])
        self.assertEqual(self.request("POST", "/api/inspect", "invalid",
                                     {"Content-Type": "application/json"})[0], 400)
        self.assertEqual(self.request("POST", "/api/inspect", "[" * 2000,
                                     {"Content-Type": "application/json"})[0], 400)
        self.assertEqual(self.request("POST", "/api/inspect", "{}")[0], 415)
        self.assertEqual(self.request("POST", "/api/inspect", "",
                                     {"Content-Type": "application/json"})[0], 413)
        self.assertEqual(self.request("POST", "/api/build", "{}")[0], 404)

    def test_cross_origin_and_host_rejected(self):
        self.assertEqual(self.request("GET", "/", headers={"Host": "example.com"})[0], 403)
        self.assertEqual(self.request("POST", "/api/inspect", "{}",
                                     {"Origin": "https://example.com",
                                      "Content-Type": "application/json"})[0], 403)


if __name__ == "__main__":
    unittest.main()
