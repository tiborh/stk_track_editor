# Track authoring

[README](../README.md) | [Roadmap](../ROADMAP.md) | [Changelog](../CHANGELOG.md)

This is the current edit/save/build/play guide. Run all commands from the
workspace root, even when the layout file lives under `track/layouts/`.
The editor and layout validator use only Python's standard library.
Generation requires the established Blender/exporter setup described in the
[installation guide](INSTALLATION.md). A fresh clone contains source/layouts,
not generated tracks or game installations.

## Visual editor

Run from this workspace:

```bash
python3 tools/track_editor.py
```

Open **http://127.0.0.1:8765** in a browser. The server binds only to the loopback
interface; stop it with Ctrl+C. Use `--port 8766` if the default port is occupied.
There are no new runtime dependencies, build steps, external web resources,
Blender subprocesses, game launches or server-side file writes.

### Controls and workflow

- Click a grid cell to place a straight or corner. Use **R / Rotate brush**
  to rotate the next piece clockwise; **Rotate existing** rotates a placed tile.
  Occupied cells are not silently replaced. **Erase** removes a tile.
- **Set start** selects a straight; the yellow arrow shows the heading.
  Selecting a new start aligns the heading automatically if necessary.
  Use **Start heading** to reverse direction. A later incompatible heading or
  tile rotation is reported as invalid rather than silently corrected.
- **Undo/Redo** includes placement, rotation, erasure, start and metadata edits.
  History retains up to 100 edits. Keyboard shortcuts: **1-6** select tools,
  **R** rotates the brush, **Ctrl/Cmd+Z** undoes, **Ctrl/Cmd+Shift+Z** or
  **Ctrl/Cmd+Y** redoes (outside text fields).
- Pan, zoom and **Fit track** navigate the grid. North is up; hovered cells
  show their coordinates. The existing coordinate range (-100 to 100 on each
  axis) and maximum of 900 modules are enforced.
- **Load oval example / Load bends example / Load pickup example** reads the
  supplied layout inputs without modifying them. **Open JSON** loads a layout or draft.
  Loading/new clears history and asks before discarding unsaved edits.
- **Save JSON** requests a browser download; choose the destination or move the
  downloaded file into `track/layouts/`. The browser controls download completion
  and destination: the editor cannot verify that the file reached disk.
  There is no autosave; save before stopping the server or closing the browser.
  The title marks unsaved changes, and closing a dirty page prompts for confirmation.

The Python validator remains authoritative. Red dots show **all disconnected
ports**, using the generator's own `Tile.ports` definitions. The status panel
shows the first validation problem, or the length/module count of a valid
single closed circuit. Invalid metadata/unsupported structures are rejected on
open/save with an explicit message; the current layout survives a failed open.
Duplicate JSON keys are rejected before browser decoding can hide them.
If the local server stops, validation/save failures are displayed explicitly.

**Incomplete drafts use the same versioned JSON structure as complete layouts.**
They may have 0-900 modules, disconnected ends, separate loops, or a missing/invalid start
reference (`start.tile` is an empty string until selected). Shared structural
validation still checks field names, IDs, dimensions, tile coordinates, types,
rotations and unique cells. Draft allowance is editor-only: the generator
continues to require at least four modules, an aligned start, connected ports
and exactly one closed circuit. There is no second browser-side circuit validator.

### Generate a saved circuit

Use a **new track ID**, such as `modular_my_circuit`, to preserve the reference
tracks. Set a printable name, cell size 60-120 m and road width 10-18 m.
When the editor says **Ready to generate**, save the JSON, then use the existing
pipeline from the workspace directory:

```bash
python3 tools/track_layout.py track/layouts/my_circuit.json
blender --background --factory-startup --disable-autoexec \
  --python-exit-code 1 --python tools/build_modular_track.py -- \
  track/layouts/my_circuit.json
```

Generation/export, rebuild backups and Blender refinement are described in
the [export reference](#modular-layout-and-export-reference); see also
[installation](#install-a-new-generated-circuit). Browser build/play controls,
3D preview, elevation and Blender round-tripping remain out of scope.

## Road-relative pickups

Run `python3 tools/track_editor.py` and open **http://127.0.0.1:8765**.
Restart an older editor server and reload the browser to get the new controls.
**Load pickup example** opens `track/layouts/pickup_oval.json`. As with the other
examples, change its track ID before generating your own variation.

### Authoring

Choose **6 Place pickup**, select **Item box**, **Small nitro** or **Big nitro**,
set **Along path** and **Lateral offset**, then click the road module.
The click chooses the module, not an arbitrary world position. Orange squares
are item boxes; cyan and purple circles are small and big nitro respectively.
Markers are drawn from Python's shared road sampler, not a second browser
geometry implementation.

Click a marker or use **Selected pickup** to select it. Adjust the position/kind
fields and click **Update selected**; **Delete selected** removes it.
Those fields also set subsequent new placements. Placement and updates are
validated by Python before committing, with explicit errors for invalid values.
All pickup changes participate in the existing undo/redo and JSON save/open
workflow. Selection alone is not a layout edit.

Pickups stay attached when their module rotates. Erasing an occupied module
asks for confirmation and removes its pickups in the same undoable edit;
Undo restores both. Replacing a piece still requires erasing it first.
Changing road width can invalidate existing lateral offsets: the error is
reported, and save/build stays blocked until the offsets or width are corrected.
Draft circuits may contain pickups on existing modules, but dangling module
references and invalid positions are not valid drafts.

### Version 2 format and positioning

Version-1 layouts retain their original meaning and remain version 1 when
opened/saved without pickups. The first successful pickup placement upgrades
the layout to version 2 and adds a required `pickups` array. Version 2 with an
empty array is supported; deleting the last pickup does not downgrade it.
Unknown fields, unsupported versions and duplicate JSON keys are still rejected.

Each entry has exactly these fields:

```json
{"id": "box_left", "kind": "item", "tile": "start", "along": 0.8, "lateral": -3}
```

`id` is a unique lowercase identifier (same syntax/length as module IDs).
`kind` is `item`, `nitro_small` or `nitro_big`; `tile` is an existing module ID.
At most 2,000 pickups are allowed. `along` is a finite number from 0 to 1,
measured along the module's **canonical** path. Before clockwise tile rotation,
a straight runs south to north, and a corner runs south to east.
`lateral` is metres to the right of that canonical tangent, with negative
values to the left. It must stay within `road_width / 2 - 2` metres of the
centreline, leaving a 2 m edge margin for either nitro size.
Spacing between pickups is not automatically enforced; avoid overlapping them.

The road mesh and pickup positions share `road_sample`. Tile rotation and the
existing race-start transform are applied once; tile JSON order, start choice
and traversal reversal do not change a pickup's physical position relative to
its road. Saved placements have no independent world height to migrate when
elevation is introduced.

The Blender source contains editable cube/cone empties in **Gameplay**, with
pickup and module IDs plus their saved along/lateral properties. They export
using native STK `item`, `small-nitro` and `big-nitro` scene entries, 1 m above
the sampled road with normal drop-to-road behavior. Collection, item use,
respawn timing and AI item behavior are provided by SuperTuxKart, not custom
scripts. Blender refinement remains a one-way handoff: changing an empty's
location does not update the layout JSON or its authoring properties.

### Generate and play

After [generating and installing the example](INSTALLATION.md#first-generated-example),
restart the game, then:

```bash
supertuxkart --track=addon_modular_pickup_oval \
  --kart=konqi --disable-addon-karts \
  --numkarts=4 --laps=3 --no-start-screen
```

For reproducible generation from the workspace root:

```bash
python3 tools/track_layout.py track/layouts/pickup_oval.json
blender --background --factory-startup --disable-autoexec \
  --python-exit-code 1 --python tools/build_modular_track.py -- \
  track/layouts/pickup_oval.json
```

If you have already generated this ID in this checkout, rebuilding requires
`--replace-generated` after the standalone `--`, with normal backup behavior.
The generated source is
`track/modular/modular_pickup_oval/modular_pickup_oval.blend`; export is
`build/tracks/modular_pickup_oval/`. Keep accepted reference tracks intact
when generating variations.

**Human acceptance still required:** complete three laps, collect an item box
and use the granted item, collect both nitro sizes and use nitro, revisit pickup
locations after respawning, and check that the AI can race and collect sensibly.
Also save/reopen a pickup-equipped variation in the editor and generate it.
Report any misplaced, buried, unreachable or non-respawning pickup. Do not mark
roadmap item 2 accepted solely because generation or automated racing succeeded.

## Modular layout and export reference

### Layout data and validation

`tools/track_layout.py` uses only the Python standard library. It validates the
input before any Blender construction and derives a driving order from module
connections; JSON array order is not driving order.

```bash
python3 tools/track_layout.py track/layouts/oval.json
python3 tools/track_layout.py track/layouts/bends.json
python3 -m unittest discover -s tools -p 'test_*.py' -v
```

Version 1 has exactly these top-level fields:

```json
{
  "version": 1,
  "id": "modular_oval",
  "name": "Modular Oval",
  "cell_size": 90,
  "road_width": 14,
  "start": {"tile": "start", "heading": "north"},
  "tiles": [
    {"id": "start", "kind": "straight", "x": 0, "y": 0, "rotation": 0}
  ]
}
```

This fragment demonstrates the fields; it is **not** a complete circuit. Use one
of the supplied files for a connected example.

- Cell coordinates are integers: east is +X, north is +Y. Each module occupies
  one square cell. Coordinates must be in [-100, 100], with 4-900 modules.
- At rotation 0, a `straight` connects south to north, and a `corner` connects
  south to east. Rotations are **clockwise** 0, 90, 180, or 270 degrees.
  Connections can be traversed in either direction, so one corner type supports
  both left and right turns.
- `cell_size` is 60-120 metres; corner centreline radius is half that value.
  `road_width` is 10-18 metres. These intentionally conservative limits keep
  geometry and barriers inside each module's footprint.
- The start must name a straight tile and an aligned heading (`north`, `east`,
  `south`, or `west`). The generator puts the finish at that tile's centre and
  transforms the scene so the race starts at the origin facing Blender +Y.
- Track IDs must start with `modular_`, followed by 1-40 lowercase letters,
  digits, or underscores. This keeps their output separate from `llm_loop`.

Duplicate IDs/cells/JSON keys, unsupported fields/types, unconnected or
misaligned ports, and separate closed loops are generator errors. The editor
can save incomplete drafts, but only a valid single closed circuit can build.
Version 2 adds the required `pickups` array described in
[pickup positioning](#version-2-format-and-positioning).

### Generate or rebuild

For a layout with no existing generated outputs:

```bash
blender --background --factory-startup --disable-autoexec \
  --python-exit-code 1 --python tools/build_modular_track.py -- \
  track/layouts/oval.json
```

If an example already has output in this checkout, explicitly authorize
replacing its generator-owned output:

```bash
blender --background --factory-startup --disable-autoexec \
  --python-exit-code 1 --python tools/build_modular_track.py -- \
  track/layouts/oval.json --replace-generated
```

Substitute `track/layouts/bends.json` for the second circuit. The builder accepts
`--exporter-root /path/to/stk-blender` after `--`, with the same default exporter
checkout as the circle builder.

Each successful build produces:

```text
track/modular/<id>/layout.json       # snapshot of the input
track/modular/<id>/licenses.txt      # attribution notice, when supplied
track/modular/<id>/<id>.blend        # editable scene
track/modular/<id>/textures/         # source images, including preview
build/tracks/<id>/                  # complete game export
```

Generation and export happen in temporary, track-specific directories; XML,
route/checkpoint structure, required meshes, and textures are checked before
publishing. Existing outputs are refused unless `--replace-generated` is used.
That option first moves the previous source and export to
`build/modular-backups/<id>/<UTC timestamp>/`, then publishes the new build.
These backups are retained, not automatically pruned.

The implementation reuses mesh/material helpers from `tools/build_track.py`,
but does not run or modify the circle generator.

The default exporter checkout is `vendor/stk-blender`, configured as in
[Installation](INSTALLATION.md#configure-the-exporters). The builder copies
`<layout-name>.licenses.txt` into generated source and export as `licenses.txt`;
`--license-file` after Blender's `--` selects an explicit notice.
Missing notices warn: private builds are possible, but attribution/licensing
must be settled before redistribution. See [Licensing](../LICENSING.md).

### Blender handoff

Open `track/modular/modular_oval/modular_oval.blend` or the corresponding bends
scene. Roads are separate named meshes with a `module_id` property. Collections
separate roads/markings, landscape/barriers, gameplay, and lighting. Texture
paths are relative to the source scene, and the preview has a persistent Blender
user so it survives reopening and subsequent exports.

**Save a separate working copy before refining anything.** This is a one-way
handoff: regeneration does not merge arbitrary Blender edits back into JSON.
Keep access to the source `textures/` folder when moving or saving the working
file; Blender's Save As path remapping can retain those references. When
exporting manually, enable both exporter add-ons and set **Assets (data) path**
to this workspace's `build/`, or to a separate assets root for experiments.
Do not point it at a temporary staging path from an old build log.

Road geometry edits can require corresponding driveline/checkline edits.
Adding scenery or adjusting materials is a safer first Blender exercise.
Carry `licenses.txt` into manual exports and update it for any new assets or
modifications; the Blender exporter does not handle this automatically.

After generating the oval and bends sources in this checkout, the repeatable
integration check opens both sources, checks road normals and
relative textures, adds a roadside cube to separate working copies, and
re-exports without rerunning the generator:

```bash
blender --background --factory-startup --disable-autoexec \
  --python-exit-code 1 --python tools/check_modular_handoff.py
```

This uses the default exporter checkout and writes only test refinements under
`build/modular-playtest/refinement/`. It does not install those refinements.

## Install a new generated circuit

Generation does not install a new track ID. After a successful build, create
one local add-on link, substituting your layout's ID for `modular_my_circuit`:

```bash
ln -s "$PWD/build/tracks/modular_my_circuit" \
  "$HOME/.local/share/supertuxkart/addons/tracks/modular_my_circuit"
```

Use this only for a new destination; inspect existing files/links rather than
overwriting them. The link automatically targets later builds with the same ID.
Restart the game after building, and use the `addon_` prefix at launch:

```bash
supertuxkart --track=addon_modular_my_circuit \
  --kart=konqi --disable-addon-karts \
  --numkarts=4 --laps=3 --no-start-screen
```

The printable track name is not its launch ID. The accepted Double Clover
workaround uses `--kart=tux --disable-addon-karts`; Konqi is also human-checked.
Normal menu selection works too: run `supertuxkart --disable-addon-karts`.
See the [kart investigation](../CHANGELOG.md#2026-10-26---kart-choice)
for the distinction between asset warnings and the unresolved historical X11 exit.
