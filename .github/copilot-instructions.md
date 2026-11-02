# STK Track Editor

This is an unofficial SuperTuxKart track editor. Read [CONTRIBUTING](../CONTRIBUTING.md)
and [Development](../docs/DEVELOPMENT.md) for contributor requirements,
[HANDOFF](../HANDOFF.md) for current state, and [ROADMAP](../ROADMAP.md) before
expanding scope. Setup and authoring commands live in
[Installation](../docs/INSTALLATION.md) and [Authoring](../docs/AUTHORING.md).

## Commands

Run commands from the repository root. The editor and ordinary Python tests
require Python 3.10+ and only the standard library. The browser assets are
plain JavaScript/CSS/SVG, served directly without a frontend build.

```bash
# Start the editor at http://127.0.0.1:8765
python3 tools/track_editor.py

# Source checks used in CI
python3 -m unittest discover -s tools -p 'test_*.py'
python3 tools/diagnose.py --editor-only
node --check editor/editor.js

# One test module or one test method; tools use sibling imports
PYTHONPATH=tools python3 -m unittest test_track_layout -v
PYTHONPATH=tools python3 -m unittest test_track_layout.LayoutTests.test_unordered_tiles_are_equivalent -v

# Documentation links and Markdown fence checks
python3 -m unittest discover -s tools -p 'test_documentation.py'

# Optional real-browser interaction check: Python Playwright and system Chromium
python3 tools/check_track_editor_browser.py

# Validate a complete layout without Blender
python3 tools/track_layout.py track/layouts/pickup_oval.json

# Generate an editable scene and game-ready export
blender --background --factory-startup --disable-autoexec \
  --python-exit-code 1 --python tools/build_modular_track.py -- \
  track/layouts/pickup_oval.json
```

Agent browser tools are separately configured in `.github/mcp.json` using the
shared `browser-tools-mcp` launcher. See Development for machine setup; these
MCP tools do not supply the Python Playwright dependency of the browser check.

Generation runs inside Blender's bundled Python; do not install `bpy` with pip.
Both `io_scene_spm` and `io_antarctica_scene` must exist under the exporter
checkout, defaulting to `vendor/stk-blender`. Pass `--exporter-root PATH`
after Blender's standalone `--` to select another checkout.

For generation changes, produce a fresh export. Saved-scene handoff checks use
the same Blender flags with `--python tools/check_modular_handoff.py` or
`--python tools/check_pickup_handoff.py`; generate `oval.json` and `bends.json`
for the former and `pickup_oval.json` for the latter first. These checks export
separate refinements under `build/`. Gameplay changes also require focused
human driving feedback; successful XML or automated racing is not acceptance.

## Architecture

The pipeline is browser editor -> versioned layout JSON -> shared Python
circuit model -> Blender scene -> existing STK exporters -> local race.
JSON is the repeatable authoring source. Editing the generated `.blend` is an
explicit one-way handoff, not a way to update JSON.

`tools/track_layout.py` is the Blender-independent authority for structure,
tile ports, circuit traversal, road sampling and pickup placement.
`tools/track_editor.py` exposes this through `POST /api/inspect`, distinguishing
structurally valid drafts (`draft_ok`) from complete circuits (`valid`).
The loopback-only server serves explicit asset/example routes, enforces local
Host/Origin checks, and neither writes layouts nor runs Blender or the game.
Saving JSON is a browser download whose destination/completion is browser-owned.

`editor/editor.js` owns layout state, SVG drawing, snapshot-based undo/redo,
dirty tracking and JSON interchange. Python supplies connection diagnostics
and pickup marker coordinates; do not add another circuit validator or pickup
geometry implementation in JavaScript. Keep layout mutations within `edit()`
so history/dirty state stays consistent. Async validation and file operations
use revision/operation guards to prevent stale results from replacing newer state.

`tools/build_modular_track.py` consumes the shared circuit, reuses mesh/material
helpers from the preserved First Circle generator (`tools/build_track.py`),
and creates road, gameplay metadata, textures and previews. It stages and
validates exports before publishing source under `track/modular/<id>/` and
game-ready assets under `build/tracks/<id>/`. `tools/track_licenses.py`
propagates explicit attribution to both outputs.

## Repository conventions

- Preserve version-1 layout meaning. Version 2 requires `pickups`; the editor
  upgrades only on successful first pickup placement and never downgrades after
  deleting the last pickup. Reject unknown/missing fields, unsupported versions,
  duplicate JSON keys, booleans masquerading as numbers, and non-finite numbers.
  Use the shared validators and `unique_fields` JSON hook.
- Drafts use the same schema as complete layouts but may have no tiles, open
  ports, separate loops or an unset start. Only editor draft inspection relaxes
  circuit completeness; generation requires at least four tiles, an aligned
  straight start, and exactly one connected closed circuit.
- Grid east is +X and north is +Y; rotations are clockwise quarter-turns.
  At rotation zero, straights run south-to-north and corners south-to-east.
  Traverse connections rather than JSON tile order. The generator transforms
  the start tile's centre to the origin facing Blender +Y.
- Pickup `along` and `lateral` are in the tile's canonical port-0-to-port-1
  frame, not race traversal order. Positive lateral is right of that tangent;
  start changes and traversal reversal must not move pickups relative to roads.
  Road geometry and pickup placement share `road_sample`.
- Preserve exporter-specific invariants: connected driveline quads and start
  antennae, a full checkline activation chain back to `lap`, preview
  `use_fake_user`, and relative `//textures/` paths. The export operator takes
  a file stem inside an existing track directory. Retain the graph-XML
  declaration fix documented in Development; inspect an existing exporter
  checkout before applying the compatibility patch or updating it.
- Existing generated output is refused unless `--replace-generated` is
  explicitly passed; that path backs up prior source/export. Use new track IDs
  for variations. Do not implicitly overwrite installed references, redirect
  game add-on links, change game settings, or install/change system packages.
- Keep generated `build/`, `track/modular/`, textures, `.blend` files, exporter
  checkouts and local logs untracked. Example JSON has a sibling
  `<layout-name>.licenses.txt`; new shared tracks need explicit attribution.
  Code/docs are GPL-3.0-or-later; original examples/artwork are CC-BY-SA-4.0.
- Keep README brief, reusable procedures in the guides, current state in
  HANDOFF, future scope/status in ROADMAP, and dated commands, observations,
  failures and player feedback in CHANGELOG. Record only observed acceptance.
