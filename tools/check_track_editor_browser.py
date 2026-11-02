"""Exercise the sketcher in system or managed Chromium (optional Playwright required)."""

import argparse
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
import shutil
import tempfile
import threading

from track_editor import EditorHandler
from track_layout import parse_layout


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", choices=("system", "managed"), default="system",
                        help="Chromium source (default: system); managed must be installed explicitly")
    args = parser.parse_args()
    try:
        from playwright.sync_api import sync_playwright
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    except ImportError as error:
        raise SystemExit("Browser check needs optional Python Playwright; the editor does not.") from error
    chromium = shutil.which("chromium") if args.browser == "system" else None
    if args.browser == "system" and chromium is None:
        raise SystemExit("Browser check needs system Chromium.")
    server = ThreadingHTTPServer(("127.0.0.1", 0), EditorHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix="track-editor-check-") as temporary, sync_playwright() as p:
            if args.browser == "managed":
                chromium = p.chromium.executable_path
            browser = p.chromium.launch(executable_path=chromium, headless=True)
            page = browser.new_page(accept_downloads=True)
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            def accept_dialog(dialog):
                dialog.accept()

            page.on("dialog", accept_dialog)
            page.goto(f"http://127.0.0.1:{server.server_port}")

            def wait_status(text):
                try:
                    page.wait_for_function(
                        "text => document.getElementById('status').textContent.includes(text)", arg=text,
                        timeout=5000)
                except PlaywrightTimeoutError as error:
                    raise AssertionError({
                        "expected": text, "status": page.locator("#status").inner_text(),
                        "notice": page.locator("#notice").inner_text(), "errors": errors,
                        "tiles": page.locator("#tiles").inner_html(),
                    }) from error

            def click_cell(x, y):
                page.locator("#grid").scroll_into_view_if_needed()
                point = page.locator("#grid").evaluate(
                    "(grid, cell) => { const p = new DOMPoint(cell.x, -cell.y)"
                    ".matrixTransform(grid.getScreenCTM()); return {x:p.x,y:p.y}; }",
                    {"x": x, "y": y})
                page.mouse.click(point["x"], point["y"])

            def download(filename):
                with page.expect_download() as event:
                    page.locator("#save").click()
                destination = Path(temporary) / filename
                event.value.save_as(destination)
                return destination

            wait_status("4-900")
            # Recreate the accepted oval entirely through placement controls.
            example = json.loads((ROOT / "track/layouts/oval.json").read_text())
            brush = 0
            for tile in example["tiles"]:
                page.locator(f'[data-tool="{tile["kind"]}"]').click()
                while brush != tile["rotation"]:
                    page.locator("#rotate").click()
                    brush = (brush + 90) % 360
                click_cell(tile["x"], tile["y"])
            page.locator('[data-tool="start"]').click()
            click_cell(0, 0)
            wait_status("Ready to generate")
            assert page.locator("#tiles > g").count() == 6
            assert page.locator("#ports circle").count() == 0
            rebuilt = json.loads(download("rebuilt.json").read_text())
            rebuilt["id"], rebuilt["name"] = example["id"], example["name"]
            expected = parse_layout(example)
            actual = parse_layout(rebuilt)
            assert actual.length == expected.length
            assert [(s.x, s.y, s.tx, s.ty) for s in actual.route] == [
                (s.x, s.y, s.tx, s.ty) for s in expected.route]

            # Occupied cells, rotation, disconnected ends, undo/redo and draft round-trip.
            page.locator('[data-tool="corner"]').click()
            click_cell(0, 0)
            assert "occupied" in page.locator("#notice").inner_text()
            assert page.locator("#tiles > g").count() == 6
            page.locator('[data-tool="rotate"]').click()
            click_cell(0, 1)
            wait_status("unconnected")
            assert page.locator("#ports circle").count() > 0
            page.locator("#undo").click()
            wait_status("Ready to generate")
            page.locator("#redo").click()
            wait_status("unconnected")
            draft_path = download("draft.json")
            draft = json.loads(draft_path.read_text())
            page.locator("#new").click()
            page.locator("#file").set_input_files(str(draft_path))
            wait_status("unconnected")
            assert json.loads(download("draft-again.json").read_text()) == draft
            page.locator('[data-tool="erase"]').click()
            click_cell(0, 0)
            assert page.locator("#start-label").inner_text() == "Start: not set"
            page.locator("#undo").click()
            assert page.locator("#start-label").inner_text() != "Start: not set"

            # Reference loading, heading and metadata undo, invalid input preservation.
            for name in ("oval", "bends"):
                page.locator(f"#{name}").click()
                page.wait_for_function(
                    "name => document.getElementById('name').value === name",
                    arg=f"Modular {name.title()}")
                wait_status("Ready to generate")
                assert page.locator("#tiles > g").count() == (6 if name == "oval" else 10)
            page.locator("#heading").select_option("south")
            wait_status("Ready to generate")
            page.locator("#name").fill("Renamed circuit")
            page.locator("#name").press("Tab")
            page.locator("#undo").click()
            assert page.locator("#name").input_value() == "Modular Bends"
            page.locator("#cell-size").fill("20")
            page.locator("#cell-size").press("Tab")
            wait_status("cell_size")
            page.locator("#save").click()
            page.wait_for_function("() => document.getElementById('notice').textContent.startsWith('Cannot save')")
            page.locator("#undo").click()
            wait_status("Ready to generate")
            page.locator("#file").set_input_files({
                "name": "invalid.json", "mimeType": "application/json",
                "buffer": b'{"version":1,"version":1}',
            })
            page.wait_for_function("() => document.getElementById('notice').textContent.startsWith('Open failed')")
            assert page.locator("#tiles > g").count() == 10

            # Upgrade only on pickup placement; all geometry still comes from Python.
            page.locator("#oval").click()
            wait_status("6 modules")
            assert json.loads(download("v1.json").read_text())["version"] == 1
            page.locator('[data-tool="pickup"]').click()
            for kind, x, y, along, lateral, count in (
                ("item", 0, 0, "0.75", "-3", 1),
                ("nitro_small", 0, 1, "0.4", "2", 2),
                ("nitro_big", 1, 0, "0.7", "-2", 3),
            ):
                page.locator("#pickup-kind").select_option(kind)
                page.locator("#pickup-along").fill(along)
                page.locator("#pickup-lateral").fill(lateral)
                click_cell(x, y)
                wait_status(f"{count} pickups")
                assert page.locator("#pickups > .pickup").count() == count
            pickup_path = download("pickups.json")
            pickup_data = json.loads(pickup_path.read_text())
            assert pickup_data["version"] == 2
            assert len(parse_layout(pickup_data).pickups) == 3
            page.locator("#file").set_input_files(str(pickup_path))
            wait_status("3 pickups")
            assert json.loads(download("pickups-again.json").read_text()) == pickup_data

            page.locator('#pickups [data-id="pickup_2"]').click()
            assert page.locator("#pickup-selection").input_value() == "pickup_2"
            page.locator("#pickup-along").fill("0.6")
            page.locator("#pickup-lateral").fill("-1")
            page.locator("#pickup-update").click()
            page.wait_for_function(
                "() => document.querySelector('#pickups [data-id=\"pickup_2\"]')?.getAttribute('data-selected') === 'true'")
            updated = json.loads(download("updated.json").read_text())
            assert updated["pickups"][1]["along"] == 0.6
            assert updated["pickups"][1]["lateral"] == -1
            page.locator("#pickup-lateral").fill("99")
            page.locator("#pickup-update").click()
            page.wait_for_function(
                "() => document.getElementById('notice').textContent.startsWith('Cannot place pickup')")
            assert json.loads(download("unchanged.json").read_text()) == updated
            page.locator("#pickup-delete").click()
            wait_status("2 pickups")
            page.locator("#undo").click()
            wait_status("3 pickups")
            page.locator("#redo").click()
            wait_status("2 pickups")
            page.locator("#undo").click()
            wait_status("3 pickups")

            page.locator('[data-tool="rotate"]').click()
            click_cell(0, 1)
            wait_status("unconnected")
            rotated = json.loads(download("rotated-pickups.json").read_text())
            assert rotated["pickups"] == updated["pickups"]
            page.locator("#undo").click()
            wait_status("3 pickups")
            page.locator("#heading").select_option("south")
            wait_status("3 pickups")
            assert json.loads(download("reversed-pickups.json").read_text())["pickups"] == updated["pickups"]

            page.locator('[data-tool="erase"]').click()
            page.remove_listener("dialog", accept_dialog)
            page.once("dialog", lambda dialog: dialog.dismiss())
            click_cell(0, 0)
            assert page.locator("#tiles > g").count() == 6
            assert page.locator("#pickups > .pickup").count() == 3
            page.on("dialog", accept_dialog)
            click_cell(0, 0)
            wait_status("start.tile")
            erased = json.loads(download("erased-pickups.json").read_text())
            assert len(erased["pickups"]) == 2
            assert erased["start"]["tile"] == ""
            page.locator("#undo").click()
            wait_status("3 pickups")
            assert page.locator("#tiles > g").count() == 6
            assert json.loads(download("restored-pickups.json").read_text())["pickups"] == updated["pickups"]

            malformed = json.loads(json.dumps(updated))
            malformed["pickups"][0]["tile"] = "missing"
            page.locator("#file").set_input_files({
                "name": "bad-pickup.json", "mimeType": "application/json",
                "buffer": json.dumps(malformed).encode(),
            })
            page.wait_for_function("() => document.getElementById('notice').textContent.startsWith('Open failed')")
            assert page.locator("#pickups > .pickup").count() == 3
            page.locator("#pickup-oval").click()
            wait_status("10 pickups")
            assert page.locator("#pickups > .pickup").count() == 10
            assert json.loads(download("pickup-example.json").read_text()) == json.loads(
                (ROOT / "track/layouts/pickup_oval.json").read_text())
            for control in ("zoom-in", "zoom-out", "left", "right", "up", "down", "fit"):
                page.locator(f"#{control}").click()
            page.set_viewport_size({"width": 600, "height": 900})
            assert page.locator("#grid").is_visible()
            assert not errors, errors
            browser.close()
            print("Browser checks passed: UI-built oval matches generator route; drafts, "
                  "diagnostics, pickups, history, file handling and view controls work.")
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == "__main__":
    main()
