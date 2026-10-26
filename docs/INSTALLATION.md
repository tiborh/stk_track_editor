# Installation and configuration

[README](../README.md) | [Authoring](AUTHORING.md) | [Development](DEVELOPMENT.md)

## Editor only

Install Python 3.10+ and use a modern browser. No `pip install`, build step,
Node.js runtime, Blender or game installation is needed to edit/save layouts.

```bash
git clone https://github.com/tiborh/stk_track_editor.git
cd stk_track_editor
python3 tools/diagnose.py --editor-only
python3 tools/track_editor.py
```

Open **http://127.0.0.1:8765**. Stop with Ctrl+C or use `--port 8766` if occupied.
Save JSON through the browser; it controls the destination and download.

## Generation and play prerequisites

Install Blender, SuperTuxKart with its game data, and Git through your platform's
normal package/install process. **Do not `pip install bpy`**: generation runs
inside Blender's bundled Python.

The established combination is Linux, Blender 5.2.1, SuperTuxKart 1.5 and the
exporter revision below with the included graph-XML correction. This is a
verified combination, not a promise that every newer/older version works.
Windows/macOS, Flatpak and Snap workflows are not end-to-end verified here.
Do not change system packages or graphics/game settings as a diagnostic shortcut.

### Configure the exporters

For a fresh, separate exporter checkout, run from this project's root:

```bash
git clone https://github.com/supertuxkart/stk-blender.git vendor/stk-blender
git -C vendor/stk-blender checkout --detach 992ab8aad3e9a4850e1ec25145940dd10da509c4
git -C vendor/stk-blender apply --check ../../patches/stk-blender-graph-xml.patch
git -C vendor/stk-blender apply ../../patches/stk-blender-graph-xml.patch
```

The patch fixes a malformed `graph.xml` declaration in that exact revision.
It retains the [upstream MIT notice](../LICENSES/MIT-stk-blender.txt).
Do not reapply it to an existing fixed checkout or reset somebody's exporter
changes. Inspect an existing checkout before using or updating it.
`vendor/` is ignored and is not included in this project's source distribution.

All Blender scripts and the prerequisite checker default to
`vendor/stk-blender`. To use an existing checkout elsewhere, pass
`--exporter-root /absolute/path/to/stk-blender`. For Blender scripts, this
argument goes **after the standalone `--`**.

The generator explicitly enables `io_scene_spm` and `io_antarctica_scene` for
that background process and sets the export assets path. It does not save
normal Blender preferences, so manual add-on installation is unnecessary for
command-line generation. To refine in Blender's GUI, follow the exporter's
[installation instructions](https://github.com/supertuxkart/stk-blender#installation)
and the [one-way handoff guide](AUTHORING.md#blender-handoff).

### Check prerequisites

```bash
python3 tools/diagnose.py
python3 tools/diagnose.py --probe-blender
```

The checker reports missing executables, editor files, exporter candidates,
game data and local track directories. The optional probe tests headless mesh
creation and actual Blender add-on search paths. Neither mode installs
anything, launches the game or changes normal settings.

Use `--blender`, `--stk-command`, `--exporter-root`, `--stk-data-dir` and
`--addons-dir` to inspect nonstandard installations; see `--help`.
Exit 0 means no required gap was found, not that a track is game-ready.
Exit 1 means a missing prerequisite or failed probe; exit 2 is invalid arguments.
Read warnings: inventory does not prove exporter activation, working graphics
or successful gameplay.

## First generated example

Run from the project root after configuring the exporters:

```bash
python3 tools/track_layout.py track/layouts/pickup_oval.json
blender --background --factory-startup --disable-autoexec \
  --python-exit-code 1 --python tools/build_modular_track.py -- \
  track/layouts/pickup_oval.json
```

Outputs are `track/modular/modular_pickup_oval/` and
`build/tracks/modular_pickup_oval/`, including `licenses.txt`.
They are generated locally and ignored by Git. Existing output is refused;
use `--replace-generated` only when deliberately rebuilding, which retains a
backup of the previous generated source/export.

### Install locally (native Linux default)

Only if the destination does not already exist:

```bash
mkdir -p "$HOME/.local/share/supertuxkart/addons/tracks"
ln -s "$PWD/build/tracks/modular_pickup_oval" \
  "$HOME/.local/share/supertuxkart/addons/tracks/modular_pickup_oval"
```

Inspect existing files/links instead of replacing them. In particular, a
previous study-workspace installation may already use this track ID; leave it
intact and author a new ID if you need an independent installation.
XDG overrides and sandboxed installations can use different add-on directories;
confirm the actual game log/path rather than assuming this native default.

Restart the game:

```bash
supertuxkart --track=addon_modular_pickup_oval \
  --kart=konqi --disable-addon-karts \
  --numkarts=4 --laps=3 --no-start-screen
```

The runtime `addon_` prefix is required. These interactive launches use normal
game settings; isolated automated comparisons are described in the changelog.
Keep the checkout/export available while an installed symlink points to it.

## Before sharing a track

Read [Licensing](../LICENSING.md). Supplied examples carry their own notices;
for a new layout, create `<layout-name>.licenses.txt` beside its JSON or pass
`--license-file /path/to/licenses.txt` to the builder. Record all reused assets,
their sources, authors and licenses, and your modifications.
Private builds without a notice warn explicitly and are not ready to share.
