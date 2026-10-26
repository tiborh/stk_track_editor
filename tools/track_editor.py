"""Serve the local visual track sketcher without writing tracks or running Blender."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import urlsplit

from track_layout import parse_layout, read_layout, read_pickups, road_sample, unique_fields


ROOT = Path(__file__).resolve().parents[1]
ASSETS = {
    "/": ("editor/index.html", "text/html; charset=utf-8"),
    "/editor.js": ("editor/editor.js", "text/javascript; charset=utf-8"),
    "/editor.css": ("editor/editor.css", "text/css; charset=utf-8"),
    "/examples/oval.json": ("track/layouts/oval.json", "application/json"),
    "/examples/bends.json": ("track/layouts/bends.json", "application/json"),
    "/examples/pickup_oval.json": ("track/layouts/pickup_oval.json", "application/json"),
}
MAX_BODY = 1_000_000


def inspect_layout(data):
    try:
        _, _, cell_size, width, tiles, positions, _, _ = read_layout(data, draft=True)
    except ValueError as error:
        return {"draft_ok": False, "valid": False, "message": str(error),
                "ports": [], "pickups": []}
    pickups = []
    for pickup in read_pickups(data, tiles, width):
        x, y, _ = road_sample(tiles[pickup.tile], cell_size, pickup.along).offset(pickup.lateral)
        pickups.append({"id": pickup.id, "kind": pickup.kind,
                        "x": x / cell_size, "y": y / cell_size})
    ports = []
    for tile in tiles.values():
        for dx, dy in tile.ports:
            neighbour = positions.get((tile.x + dx, tile.y + dy))
            if neighbour is None or (-dx, -dy) not in neighbour.ports:
                ports.append({"tile": tile.id, "x": tile.x, "y": tile.y,
                              "dx": dx, "dy": dy})
    try:
        circuit = parse_layout(data)
    except ValueError as error:
        return {"draft_ok": True, "valid": False, "message": str(error),
                "ports": ports, "pickups": pickups}
    return {"draft_ok": True, "valid": True, "ports": [], "pickups": pickups,
            "message": f"Ready to generate: {len(circuit.modules)} modules, "
                       f"{circuit.length:.1f} m, {circuit.road_width:g} m wide, "
                       f"{len(circuit.pickups)} pickups."}


class EditorHandler(BaseHTTPRequestHandler):
    def reply(self, status, body, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; style-src 'self'; script-src 'self'; "
                         "connect-src 'self'; img-src 'self' blob:; "
                         "object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def fail(self, status, message):
        self.reply(status, json.dumps({"message": message}).encode())

    def local_request(self):
        port = self.server.server_port
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        host = self.headers.get("Host")
        origin = self.headers.get("Origin")
        if host not in hosts or (origin is not None and origin != f"http://{host}"):
            self.fail(403, "Only same-origin localhost requests are allowed.")
            return False
        return True

    def do_GET(self):
        if not self.local_request():
            return
        asset = ASSETS.get(urlsplit(self.path).path)
        if asset is None:
            self.fail(404, "Not found.")
            return
        filename, content_type = asset
        self.reply(200, (ROOT / filename).read_bytes(), content_type)

    def do_POST(self):
        if not self.local_request():
            return
        if self.path != "/api/inspect":
            self.fail(404, "Not found.")
            return
        if self.headers.get_content_type() != "application/json":
            self.fail(415, "Send application/json.")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.fail(400, "Invalid Content-Length.")
            return
        if not 0 < length <= MAX_BODY:
            self.fail(413, "Layout must be between 1 and 1,000,000 bytes.")
            return
        try:
            data = json.loads(self.rfile.read(length), object_pairs_hook=unique_fields)
        except (ValueError, UnicodeError, RecursionError) as error:
            self.fail(400, f"Invalid JSON: {error}")
            return
        self.reply(200, json.dumps(inspect_layout(data)).encode())

    def log_message(self, format, *args):
        # Avoid logging arbitrary request data from a browser.
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("--port must be in [0, 65535]")
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), EditorHandler)
    except OSError as error:
        parser.exit(1, f"Cannot start editor: {error}\n")
    print(f"Track sketcher: http://127.0.0.1:{server.server_port}", flush=True)
    print("Save JSON from the browser; generation/play remain separate commands.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEditor stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
