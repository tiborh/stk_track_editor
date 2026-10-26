# Changelog

[README](README.md) | [Roadmap](ROADMAP.md) | [Authoring](docs/AUTHORING.md) | [Development](docs/DEVELOPMENT.md)

Reverse-chronological implementation, investigation and acceptance records.
These entries describe what was known **at that date**; older next-step notes
and initial plans are historical, not current instructions. Use the README for
the current handoff, the roadmap for future work and the guides for commands.
Retain failures and distinguish automated checks from human acceptance.

## 2026-10-26 - Public repository preparation and placement feedback

The player tested item-box and nitro placement and reported **"they look good"**,
and approved the documentation. This accepts placement appearance without
inferring unreported item-use, respawn or full-race checks.

Prepared `tiborh/stk_track_editor` as a public, unofficial editor repository
with a source-only checkout under `~/repos/github/tiborh/`. The original study
workspace, generated scenes/exports, logs and installed links were preserved,
not migrated into Git. Historical local build/log paths below therefore do
not describe files included in a fresh clone.

The player selected GPL-3.0-or-later for code/documentation and CC-BY-SA-4.0
for original example layouts/artwork, credited to tiborh. Added per-track
notices and propagation to generated exports, installation/configuration
guidance, an editor-only prerequisite check, contributor guidance, source CI
and separate `HANDOFF.md`. No logos or game asset files are bundled.
Builders now default to `vendor/stk-blender`, with explicit override support.

From the new checkout, 34 standard-library tests, JavaScript syntax checking,
real-Chromium interaction checks, editor-only inventory and the Blender probe
passed. Fresh Pickup Oval, Oval, Bends and First Circle exports carried their
matching attribution notices. Saved modular scenes re-exported separately with
matching notices. The compatibility patch was checked against the established
upstream revision without modifying the external checkout. This repository
preparation did not add another gameplay acceptance run.

## 2026-10-26 - Documentation organization

Replaced the growing all-in-one README with a short current handoff and quick
start. Moved future scope/status into `ROADMAP.md`, current instructions into
`docs/AUTHORING.md` and `docs/DEVELOPMENT.md`, and dated evidence into this
changelog. Historical setup plans remain explicitly marked as superseded.
No game code, tracks or settings changed during this documentation reorganization.

## 2026-10-26 - Road-relative pickups

Implemented editor placement/selection/update/deletion for item boxes and both
nitro sizes, version-2 layout validation and canonical positioning, native
Blender pickup empties, and the new locally installed Pickup Oval example.
Version-1 layouts and accepted reference exports are preserved.
Human pickup acceptance is pending; see the
[checklist](docs/AUTHORING.md#generate-and-play).

### Implementation checks (2026-10-26)

```bash
python3 -m unittest discover -s tools -p 'test_*.py'
node --check editor/editor.js
python3 tools/check_track_editor_browser.py
blender --background --factory-startup --disable-autoexec \
  --python-exit-code 1 --python tools/check_pickup_handoff.py
```

The 24 standard-library tests passed. They cover version compatibility,
canonical straight/corner sampling at all rotations, start changes and reversal,
unordered modules, draft diagnostics, invalid pickup structures/numbers/references,
and road-width boundaries. Real Chromium checks exercised all three pickup kinds,
version upgrade, selection/update, rejected placement, deletion, undo/redo,
save/reopen, rotation, heading reversal, module deletion/confirmation and examples.
The saved Blender empties re-exported separately with matching kinds/positions;
export validation checks every pickup as well as the existing route/checkpoints.
No dependencies were added.

`build/pickup-export.log` and `build/pickup-handoff.log` record Blender runs.
`build/pickup-playtest/race.log` records a rendered Xvfb/llvmpipe smoke check
using isolated XDG settings, Intermediate difficulty, seed 42, three laps and
Tux/Konqi/Suzanne/Sara the Racer. All four finished with zero rescues.
Profiling totals were **17 item boxes, 5 small nitro and 15 big nitro**
collections (six boxes and two of each nitro size are placed). This supports
repeated collection/respawning in automated play, not human driving acceptance.
Existing stereo-audio and kart material/shader warnings remain in the log;
the run is not error-free. No packages, existing installed assets or normal
game settings were changed.

## 2026-10-26 - Kart choice

**Outcome:** there is no demonstrated Tux-only restriction. Konqi, Suzanne and
Sara the Racer completed rendered automated races alongside Tux with add-on
karts disabled. Enabling the installed add-ons did not generally prevent racing.
The earlier desktop `BadWindow` exit remains unexplained, not fixed.

### Observed results

SuperTuxKart 1.5 was run under Xvfb with fresh, isolated XDG config/cache
directories and symlinks to the existing tracks and installed add-on karts;
the linked assets were not edited. Rendering used Mesa llvmpipe, not the desktop
GPU driver. Audio output used `ALSOFT_DRIVERS=null`. Each run used four AI-driven
karts, one profiling lap, Intermediate difficulty and seed 42. All five runs
exited normally, reported all four finishers and zero rescues:

| Run/log in `build/kart-playtest/` | Track | Kart roster | Result |
|---|---|---|---|
| `bundled-only.log` | Modular Oval | `tux`, `konqi`, `suzanne`, `sara_the_racer` | Finished; add-on karts disabled |
| `addons-enabled-bundled-roster.log` | Modular Oval | Same bundled roster | Finished; installed add-on karts enabled |
| `addons-enabled-mei.log` | Modular Oval | `tux`, `addon_mei`, `addon_python`, `addon_among-us` | Finished; Mei exhaust errors reproduced |
| `clover-konqi.log` | Double Clover | `konqi` selected via `--kart`; Tux, Suzanne and Sara as opponents | Finished; add-on karts disabled |
| `mei-default-renderer.log` | Modular Oval | `addon_mei` selected via `--kart`; Tux, Suzanne and Sara as opponents | Finished; default advanced renderer, exhaust errors reproduced |

The first four runs disabled dynamic lights; the last retained the fresh
configuration's default renderer. All used a 640x480 window and disabled texture
compression. These are rendered **automated smoke checks**, not human driving
acceptance, exhaustive add-on coverage or reproduction of the player's desktop
graphics/settings. `results.json` records the commands, exit codes, finishing
rows and logged errors.

### Exhaust warning versus X11 failure

The installed Mei kart's `kart.xml` requests `kart_heart_exhaust.xml`, but that
file is nested under `mei/textures-files-system/`, not alongside `kart.xml`.
Explicitly racing Mei reproduces the two `Failed to load particles` messages;
the bundled-only roster does not, even when add-ons are enabled. This isolates
the observed exhaust warning to Mei's asset lookup/packaging. It does **not**
establish why the earlier game exited: Mei finished both rendered checks despite
those messages, including with the default advanced renderer.

No run reproduced `BadWindow`. Xvfb does not reproduce the real desktop window
manager, graphics driver or window-close interaction, so the original
`X_TranslateCoords` failure remains a separate, unresolved investigation.
Existing stereo positional-audio errors appeared even with bundled-only karts;
enabling add-ons also logged a missing Wumpus texture and other asset warnings.
Those messages did not prevent these races from completing. Do not treat these
logs as error-free or all installed add-ons as verified.

No package, asset or permanent game-setting repair was needed to broaden kart
choice. Any future Mei asset repair or desktop configuration change still needs
the player's approval.

### Broader kart choice for the next human race

Keep the [original Tux workaround](#human-acceptance-edited-track-and-full-race). To try another checked bundled kart on
the accepted circuit, run from the workspace:

```bash
supertuxkart --track=addon_modular_double_clover \
  --kart=konqi --disable-addon-karts \
  --numkarts=4 --laps=3 --no-start-screen
```

`--kart=suzanne` and `--kart=sara_the_racer` are the other checked alternatives.
For the normal interactive kart-selection screen instead of an immediate race,
launch `supertuxkart --disable-addon-karts`, then choose the circuit in the game.
These interactive launches use the player's normal settings, unlike the isolated
checks.

### Human acceptance (2026-10-26)

After receiving the Konqi command above, the player reported **"it works well"**
and confirmed that opening the track through SuperTuxKart's normal in-game kart
and track selection **"also works."** This accepts the practical kart-choice
target on the real desktop, not just under Xvfb.

The menu-selected kart, add-on enablement, lap completion and finishing results
were not specified; do not infer exhaustive kart coverage or another full
three-lap acceptance. The original `BadWindow` root cause remains unknown, but
the reported workflows now work without an asset or configuration repair.

### Reproduce an isolated comparison

The investigation created `build/kart-playtest/data/supertuxkart/addons/` with
track symlinks for `modular_oval` and `modular_double_clover` and a `karts` symlink
to the player's installed add-on directory. With those existing links, this
repeats the bundled baseline without using the player's normal configuration:

```bash
XDG_CONFIG_HOME="$PWD/build/kart-playtest/bundled-only/config" \
XDG_DATA_HOME="$PWD/build/kart-playtest/data" \
XDG_CACHE_HOME="$PWD/build/kart-playtest/bundled-only/cache" \
ALSOFT_DRIVERS=null \
timeout 150 xvfb-run -a -s '-screen 0 800x600x24' supertuxkart \
  --track=addon_modular_oval --numkarts=4 \
  --aiNP=tux,konqi,suzanne,sara_the_racer \
  --profile-laps=1 --difficulty=1 --seed=42 --no-start-screen \
  --screensize=640x480 --windowed --disable-dynamic-lights \
  --disable-texture-compression --disable-polling --disable-addon-karts
```

To isolate add-on loading, use separate config/cache directories and omit only
`--disable-addon-karts`. To reproduce the Mei warning, also change the roster
to `--aiNP=tux,addon_mei,addon_python,addon_among-us`.

## 2026-10-24 - Visual sketcher

### Implementation and acceptance

| File | Responsibility |
|---|---|
| `tools/track_editor.py` | Standard-library local server, explicit asset/example routes, shared draft/circuit inspection |
| `editor/index.html`, `editor/editor.css`, `editor/editor.js` | Grid drawing, editing/history, navigation, JSON import/download, diagnostics |
| `tools/track_layout.py` | Shared structure reader; strict generator validation and sampling remain authoritative |
| `tools/test_track_editor.py` | Draft, generator agreement, rotated connection diagnostics and HTTP tests |
| `tools/check_track_editor_browser.py` | Optional real-Chromium interaction check using Python Playwright |

Commands run on 2026-10-24:

```bash
python3 tools/diagnose.py
python3 tools/diagnose.py --probe-blender
python3 -m unittest discover -s tools -p 'test_*.py'
node --check editor/editor.js
python3 tools/check_track_editor_browser.py
```

Inventory and Blender mesh probe succeeded without environment changes.
The 18 standard-library tests passed. The browser check used already-installed
Python Playwright and system Chromium (neither is an editor runtime dependency).
It assembled an oval entirely through the UI, downloaded its JSON and verified
that its sampled route exactly matches the reference oval. It also exercised
occupied-cell handling, rotation, all disconnected-end markers, undo/redo,
start erasure/restoration, invalid metadata, draft save/load, both examples,
duplicate-key rejection without losing the current layout, and view controls.

The implementation checks did not regenerate or change the three iteration-1
reference tracks. Subsequent human acceptance on 2026-10-24 completed the
UI-authoring milestone, as recorded below.

### Human acceptance: edited track and full race

The player used the editor to save `track/layouts/modular_first_circuit_01.json`,
generated it, drove it, modified the layout and rebuilt it. The later circuit
is saved as `track/layouts/modular_double_clover.json`, with layout/export ID
`modular_double_clover`, display name `double_clover`, and installed game ID
`addon_modular_double_clover`.

At 19:58 on 2026-10-24, the player reported **"full race completed now"** using:

```bash
supertuxkart --track=addon_modular_double_clover \
  --kart=tux --disable-addon-karts \
  --numkarts=4 --laps=3 --no-start-screen
```

This is the recorded human three-lap acceptance of a UI-authored circuit.
The supplied log confirms the track loaded with Tux, four karts and three laps;
race completion is confirmed by the player's report, not inferred from startup
messages. The log ends without the earlier `BadWindow` error. It still contains
nonfatal warnings about other track music, kart materials/shaders and UI layout.
Individual AI finishing results, rescue counts and intentional shortcut/backward
crossing tests were not reported; do not infer those additional checks.

Workflow pitfalls resolved during the playtest:

- Run generation from the workspace root, not `track/layouts/`, because
  `tools/build_modular_track.py` is a relative path.
- Keep the standalone `--` after the Blender script path. Layout paths and
  `--replace-generated` belong after it, in either order. Rebuilding requires
  `--replace-generated`, which retains previous outputs in the existing backups.
- Saving/exporting a new ID does not install it. Create its local add-on link
  once, from the workspace root, after generating the export:

```bash
ln -s "$PWD/build/tracks/modular_double_clover" \
  "$HOME/.local/share/supertuxkart/addons/tracks/modular_double_clover"
```

The installation link automatically targets later builds with the same ID.
Restart the game after rebuilding. Use `addon_modular_double_clover` at launch,
not the display name `double_clover`; that name produced a track-not-found error.

An earlier launch closed before driving, with missing add-on kart exhaust
particles and an X11 `BadWindow` error. Running with Tux and
`--disable-addon-karts` succeeded; retain that known-working command for track
playtests. This isolates add-on karts but does not establish the crash's root
cause. No permanent game-setting change or kart removal was needed.

### Session summary

- Resumed the deferred visual-editor milestone. The player chose visual editing
  and JSON save/load first, with generation/play remaining existing commands.
- Added a dependency-free loopback browser UI, shared Python draft inspection,
  connection diagnostics, history, start selection and JSON file interchange.
- Reproduced the accepted oval via UI clicks and verified downloaded JSON yields
  the exact reference route. Checked incomplete-draft round-trip and failure UX.
- Kept all reference layouts, Blender sources, exports, installations and
  generator/build commands intact; no package or system changes were needed.
- The player generated, drove, edited and rebuilt `modular_first_circuit_01`,
  then generated/installed `modular_double_clover`. Resolved working-directory,
  Blender argument-separator and installation/game-ID confusion.
- The player confirmed a full three-lap, four-kart race on Double Clover using
  Tux with add-on karts disabled. The visual-authoring acceptance milestone is
  complete; detailed AI/rescue/shortcut checks remain unreported.
- The earlier pre-drive X11 crash was absent in the successful run, but its root
  cause is not established. Preserve the known-working launch command above.
- No further feature iteration has been agreed.

### Original iteration-2 plan (resumed 2026-10-24)

This scope was deferred at the end of iteration 1 and resumed on 2026-10-24.
The implementation and human acceptance are recorded in this dated entry.
The player selected visual editing/save-load first, keeping build/play as commands.

The agreed direction was a small **top-down visual track sketcher**, using
the current version-1 layout format and Python generator. Initial features:
grid placement of straights/corners, rotation, erasure, undo/redo, start tile and
heading selection, JSON save/load, and visible connection/validation diagnostics.
Drafts should be saveable even when incomplete; only valid circuits can build.

Reuse the Python connection rules as the authority rather than letting UI and
generator semantics drift. If browser-side validation is added, share fixtures
or otherwise check that it agrees with the Python validator. A local build/play
action is desirable, but its browser-to-process bridge has not been designed
or implemented. The editor server now runs only when explicitly launched.

Suggested next-session milestone: reproduce an existing example through the
visual UI, save it, generate it through the current pipeline, and drive it.
Preserve the accepted oval, bends, and circle as reference tracks. Do not expand
into elevation, intersections, branches, jumps, loops/corkscrews, a 3D preview,
or automatic Blender-to-layout round-tripping yet. Blender refinement remains
an explicit one-way handoff, with separate working copies.

## 2026-10-17 - Modular tracks


The first Stunts-inspired increment is a **JSON-to-Blender-to-SuperTuxKart
generator**, not yet a visual editor. The original First Circle builder, Blender
scene, and game export are unchanged. No new dependencies were needed.

Two flat, single-route example circuits are available:

| Layout | Game ID | Modules | Approximate lap length |
|---|---|---|---|
| `track/layouts/oval.json` | `addon_modular_oval` | 6 | 463 m |
| `track/layouts/bends.json` | `addon_modular_bends` | 10 | 784 m |

Both use a 14 m road and 45 m corner radius. The second includes an inward bend,
exercising left and right turns. They have road markings, striped barriers,
roadside posts, a finish marking, a main AI driveline, and three linked
checkpoints. There are no pickups, elevation changes, branches, or crossings.

The tracks are installed as local add-on symlinks, alongside First Circle.
Restart SuperTuxKart to discover them, or launch one directly:

```bash
supertuxkart --track=addon_modular_oval --numkarts=4 --laps=3 --no-start-screen
supertuxkart --track=addon_modular_bends --numkarts=4 --laps=3 --no-start-screen
```


### Observed results and remaining acceptance

The layout suite passed, including seams, corner tangents, forward-facing
road quads, all grid rotations, reverse traversal, tile-order independence,
and invalid layouts. Both examples exported with the existing Blender/exporter
combination. Separate Blender refinements also exported successfully.

Each circuit completed a four-kart, three-lap headless race at Intermediate
difficulty with seed 42 and zero rescues. Observed total race times were
63-75 seconds for the oval and 110-115 seconds for bends. Both also completed
rendered one-lap, four-kart smoke checks under Xvfb with zero rescues and no
logged errors. These are automated AI runs, **not human driving feedback**.

Logs are in `build/modular-playtest/`: `export-oval.log`, `export-bends.log`,
`race-oval.log`, `race-bends.log`, `graphics-oval.log`, `graphics-bends.log`,
and `handoff.log`. Tests used isolated XDG config/data/cache directories, not
the player's normal settings. The first headless launch reported stereo
positional-audio errors for two bundled game sounds; no track-specific error
was reported. An initial advanced-renderer Xvfb attempt timed out while using
software rendering; the completed smoke checks used `--disable-dynamic-lights`
and `--disable-texture-compression` at 640x480.

**Player feedback, 2026-10-17, after the first iteration:** "it looks good and
playable." This confirms basic human playability and a positive initial visual
impression. The player did not specify which circuit(s), lap count, or detailed
handling observations, so do not infer a full acceptance run from this feedback.
No road changes were requested.

Remaining targeted acceptance: a specifically recorded human three-lap drive,
detailed handling/visibility feedback if needed, intentional shortcut/backward
crossings, and manual rescue checks. These checks are not known failures and do
not negate the positive basic-playability feedback.

### Implementation files and issues resolved

| File | Responsibility |
|---|---|
| `tools/track_layout.py` | Strict version-1 JSON loading, tile ports, closed-route traversal, analytic road sampling, and start-frame transformation; no Blender dependency |
| `tools/build_modular_track.py` | Module meshes, markings/barriers/scenery, gameplay data, preview, validated export, source preservation, and rebuild backups |
| `tools/test_track_layout.py` | 11 standard-library test methods, with additional parameterized cases |
| `tools/check_modular_handoff.py` | Reopen generated sources and export separate Blender-refined copies |
| `track/layouts/oval.json`, `track/layouts/bends.json` | Editable authoring inputs, not generated output |

Important details to preserve:

- The exporter operator takes a **file stem inside an existing output folder**:
  for track ID `<id>`, use `filepath=<assets>/tracks/<id>/<id>`. Passing only
  `<assets>/tracks/<id>` was an initial failed attempt because the exporter
  interprets the parent as the output directory. This is fixed in the builder.
- The driveline uses connected quad topology, an open final segment that the
  exporter closes, and start antennae. It is not just a generic Blender curve.
- The three extra checklines are linked in order back to `lap`. They are placed
  by accumulated route distance and extend slightly beyond the road edges.
- The preview image needs `use_fake_user = True`. Without it, reopening the
  scene discards the unused image datablock and a later export omits the
  thumbnail. The handoff check exposed this; the fix and regression check are
  present.
- Blender image loading is lazy. After `image.reload()`, inspect pixels/size
  before relying on `has_data`; a false value alone was not a missing-file bug.
- The existing exporter checkout's graph-XML declaration fix described in the
  First Circle section is still required. No exporter update, dependency
  installation, or system setting change was made in this iteration.
- The original circle builder, `track/loop.blend`, and original `track.xml`
  retained their pre-iteration hashes. Neither modular track replaces them.

### Reproducing the automated races

The isolated test installation is under
`build/modular-playtest/data/supertuxkart/addons/tracks/`, with symlinks named
`modular_oval` and `modular_bends` pointing to this workspace's exported tracks.
Those are separate from the player's normal local add-on symlinks under
`~/.local/share/supertuxkart/addons/tracks/`.

From the workspace, with these existing test directories and symlinks:

```bash
XDG_CONFIG_HOME="$PWD/build/modular-playtest/config" \
XDG_DATA_HOME="$PWD/build/modular-playtest/data" \
XDG_CACHE_HOME="$PWD/build/modular-playtest/cache" \
timeout 120 supertuxkart --no-graphics --track=addon_modular_oval \
  --numkarts=4 --profile-laps=3 --difficulty=1 --seed=42 --no-start-screen
```

Use `addon_modular_bends` for the second circuit. For the completed graphical
smoke-check configuration, keep the same XDG overrides, replace the command
after them with the following, and again substitute the track ID as needed:

```bash
timeout 120 xvfb-run -a -s '-screen 0 800x600x24' supertuxkart \
  --track=addon_modular_oval --numkarts=4 --profile-laps=1 \
  --difficulty=1 --seed=42 --no-start-screen --screensize=640x480 \
  --windowed --disable-dynamic-lights --disable-texture-compression
```

### Session summary

- Researched the Stunts editor as a modular-authoring reference and agreed on
  JSON layout -> Blender -> SuperTuxKart, with an explicit one-way Blender handoff.
- Implemented the validator/sampler, generator, two example layouts, layout
  tests, and repeatable Blender handoff check documented above.
- Generated and installed Modular Oval and Modular Bends alongside First Circle.
  Confirmed automated race completion and separate Blender refinement exports;
  corrected exporter filepath usage and preview persistence during development.
- Player feedback after delivery: "it looks good and playable." No additional
  handling change or detailed acceptance result was specified.
- At the player's request, recorded this handoff and paused development. No
  visual editor has been implemented and no new iteration has started.
- Next session: start with the deferred visual track sketcher scope above,
  keeping the three accepted/playable reference tracks intact.

## 2026-10-16 - First Circle

The first circular track is now generated by `tools/build_track.py`. It has a
45 m centreline radius (about 283 m per lap), a 14 m wide road, barriers, a
chequered finish line, a closed AI driveline, and three sequential checkpoints.
All track geometry and textures are generated locally; no asset download is
required. It intentionally has no pickups.

After the first player feedback (motion was hard to perceive on uniform
surfaces), the track gained a dashed centre line (about 4.4 m paint / 4.4 m gap),
alternating red-and-white barrier sections, 24 tall roadside posts, and seeded
asphalt/grass grain. These fixed reference points provide visible motion and
parallax even when driving alone. The road layout, AI route, checkpoints, and
barrier positions are unchanged; posts are outside the outer barrier.
The updated export completed a four-kart, three-lap headless race with no
rescues or logged errors. The previous Blender scene is preserved as
`track/loop-before-motion-markers.blend`. The motion-cue build and race logs are
`build/playtest/export-motion.log` and `build/playtest/race-motion.log`.

**Player feedback, 2026-10-16:** The motion-cue version gives "a much better
driving experience". Keep these visual references in future iterations.
This is the preserved circle baseline; no further changes to it have been
requested. The [README](README.md) contains the current development handoff;
do not repeat the initial setup.

From this workspace, regenerate the editable source and game-ready export:

```bash
blender --background --factory-startup --python-exit-code 1 \
  --python tools/build_track.py
```

The script uses `~/repos/github/stk-blender` by default. Override it with
`-- --exporter-root /path/to/stk-blender` after the script argument. It overwrites
the generated `track/loop.blend`, source textures, and `build/tracks/llm_loop/`;
save manual edits to a different Blender file before regenerating.

Open `track/loop.blend` in Blender to inspect or edit it. The source scene's track
code is `llm_loop`; configure the exporter's **Assets (data) path** to this
workspace's `build/` directory to re-export manually. Preferences set by the
background builder are not saved into your normal Blender preferences.

The local add-on installation links
`~/.local/share/supertuxkart/addons/tracks/llm_loop` to the generated export.
Restart SuperTuxKart and select **First Circle**, or launch directly:

```bash
supertuxkart --track=addon_llm_loop --numkarts=4 --laps=3 --no-start-screen
```

The game prefixes locally installed add-on track IDs with `addon_`.
Keep the workspace in place while using this symlink installation.

Blender 5.2.1 successfully enabled both add-ons and exported the scene, mesh,
materials, route graph, and checks using exporter revision
`992ab8aad3e9a4850e1ec25145940dd10da509c4` **with one local fix**:
`io_antarctica_scene/stk_track_utils.py` wrote a malformed XML declaration in
`graph.xml` (`<?xml version="1.0"?> encoding="utf-8"?>`). Its graph writer was
corrected to `<?xml version="1.0" encoding="utf-8"?>`. This change is in the
exporter checkout, not in this workspace; preserve it when updating the add-on.

The final three-lap headless race finished with all four AI karts and zero
rescues (54-61 seconds). A graphical one-lap race also finished with all four
karts and zero rescues (18-20 seconds). The graphical profiling run logged
`InputManager::dispatchInput` errors about an unknown player while processing
input; it still completed. Subsequent human playtesting confirmed improved
driving feel with the motion cues, but was not a comprehensive visual/handling review.
Logs are in `build/playtest/`; these runs used isolated XDG config/data/cache
directories there rather than changing the normal game configuration.

The first export attempt used a strict lap checkline, which caused a ranking
warning; the final scene uses the exporter's normal check-lap structure and no
longer triggers that warning. Attempts to load the export using `--trackdir`
did not find the track in this game build; installing it as a local add-on and
using `addon_llm_loop` worked.

## 2026-10-15 - Initial preparation


- Created this guide and `tools/diagnose.py`.
- Observed the package/tool inventory recorded below.
- Consulted official exporter README and track creation/property/checkline guides.
- Ran the default diagnostic and `--probe-blender`: both returned exit `1`
  because `io_scene_spm` and `io_antarctica_scene` were not found. Blender's
  background mesh/API probe succeeded on `5.2.1 LTS`; it reported
  `/usr/share/blender/5.2/scripts/addons_core` as an add-on search path.
- GIMP and Inkscape are available; Krita is not on PATH and is not required.
- No track, exporter activation, export, local installation, or race is yet verified.
- Next: run diagnostics, establish a compatible exporter, then implement the
  parameterized loop builder and perform the first full race.

### Initial brief and inventory (historical)


Build a simple, locally playable race loop, then improve it from player feedback.
The first deliverable is a complete race, not attractive scenery. No game engine
changes, compilation, online upload, or full asset-repository download should be
necessary.

The original README was a working handoff, mixing commands, failures, version
constraints, plans and playtest findings. The following inventory and plan
are preserved as historical context, not as the current environment status.

Initial inspection on 2026-10-15:

| Item | Observed state |
|---|---|
| OS | Manjaro Linux (Arch family) |
| Blender | Native `/usr/bin/blender`; package version `17:5.2.1-2` |
| SuperTuxKart | Native `/usr/bin/supertuxkart`; package version `1.5-1` |
| Python | Native Python 3; package version `3.14.7-1` |
| Supporting commands | Git, curl, Flatpak, Snap, GIMP, and Inkscape commands found |
| Headless Blender | Blender `5.2.1 LTS` successfully created a mesh in memory |
| Game data | `/usr/share/supertuxkart/data` contains `tracks/` and `textures/` |
| Native user track directory | `~/.local/share/supertuxkart/addons/tracks` exists |
| Workspace | Initially empty; not a Git repository |
| Track generation and export | Not implemented or verified |
| Blender exporter | Both modules missing from checked paths; compatibility unverified |

These are historical observations, not guarantees about the current environment.
The current diagnostic instructions are in the
[development guide](docs/DEVELOPMENT.md#diagnostic-script).

### Original restart checklist (superseded)


1. Read this document, especially the current state and experience log (now split into README and changelog).
2. Run `python3 tools/diagnose.py`; address required missing tools.
3. Run `python3 tools/diagnose.py --probe-blender` to test headless Blender and
   inspect the add-on search paths of that actual Blender executable.
4. Preserve the established exporter/version combination and its local graph-XML
   fix. Re-investigate compatibility only if the environment changed or an actual
   failure occurs; the circle and two modular tracks already work.
5. Run the layout/editor tests if changing their implementation. Start with
   visual-editor human acceptance above rather than unnecessarily regenerating
   accepted tracks.
6. Record changes, exact commands, results, and player feedback here. Distinguish
   implemented features from proposed next steps.

Do not install packages, replace the system Blender, change game settings, or
overwrite existing tracks without reviewing the proposed change with the player.

### Original workspace and implementation plan (superseded)

#### Planned workspace layout

Only this README and the diagnostic script exist initially. Create other files
as needed, not as empty scaffolding.

```text
README.md
tools/
  diagnose.py
  build_track.py          # planned: deterministic bpy generation/export
track/
  loop.json               # planned: layout and gameplay parameters
  loop.blend              # generated editable source scene
  textures/               # original or properly licensed images
build/
  tracks/llm_loop/         # staged game-ready export
playtests/
  ...                     # optional screenshots and measurements
vendor/
  stk-blender/            # optional pinned exporter checkout
```

Keep a stable internal track ID such as `llm_loop`. Keep source outside the game's
installed track folder. Treat `build/` as generated output. If Git is initialized,
ignore generated output, caches, and bulky recordings; decide explicitly whether
to version `.blend` files or regenerate them. Pin the exporter commit once working
and record it with `git -C vendor/stk-blender rev-parse HEAD`.

#### Step-by-step workflow with an LLM

##### 1. Confirm tools and exporter compatibility

Inspect diagnostic results. If needed, obtain the exporter:

```bash
git clone https://github.com/supertuxkart/stk-blender.git vendor/stk-blender
```

Skip cloning if a checkout already exists; inspect its state before changing it.
Read its README and command-line export helper under `extras/`. Copy or symlink
`io_scene_spm` and `io_antarctica_scene` into the add-on directory for the chosen
Blender version, then enable both. Prefer user-local installation over writing to
system directories. The two modules are needed together for track export.

For headless automation, explicitly add the checkout to Python's module search
path and enable the modules in the build process, or use a verified installation.
Factory startup does not preserve your saved add-on activation. The build script
must set exporter preferences, including its assets/output root, explicitly.
Do not guess operator names, custom-property keys, or a CLI for the exporter:
inspect the pinned code and its helper first.

First export a tiny test scene with a supported material. Resolve API failures
before investing time in track geometry. A mesh-only SPM export is a useful first
check but is **not** the track-export acceptance gate.

##### 2. Specify the smallest playable loop

Proposed starting values, not established design requirements:

| Parameter | Initial idea |
|---|---|
| Layout | Flat oval / rounded rectangle, one route, no intersections |
| Scale | Approximately 160 m by 100 m overall; adjust after driving |
| Road width | Approximately 14 m; constant width, broad corners |
| Surface | Simple contrasting road and surroundings |
| Edge behavior | Simple barriers; a deliberate place to test rescue |
| Race | Normal forward race, 3 laps, initially 1 player then 3 AI |
| Gameplay data | Main driveline, lap line, at least 3 chained checklines |
| Excluded initially | Jumps, shortcuts, reverse mode, elaborate scenery, custom music |

Keep measurements and curve resolution parameterized. Model in meter-scale units
and verify the exporter's coordinate conversion; do not introduce a second
hand-written axis conversion without checking exporter behavior.

Ask the LLM to produce a repeatable Blender Python script rather than a long
sequence of UI clicks. Keep geometry, gameplay metadata, and export stages clear
enough to diagnose individually. The script should fail explicitly on bad
parameters, missing modules, or missing output, not produce success-shaped output.

##### 3. Generate geometry and materials

Create a smooth sampled centerline and two road edges, a connected road surface,
and basic boundaries. Check that the road joins cleanly at the seam, has consistent
face orientation, and has no unintended gaps, self-intersections, or sharp steps.
Avoid making the initial layout so tight that offset road edges intersect.

Use the exporter-supported node material setup: the current README describes
Principled BSDF with an image or vertex-color node feeding Base Color. Do not
assume a Blender viewport's flat color will export correctly. Original tiny
textures are enough for the prototype and avoid external asset dependencies.
Pack/save source assets as appropriate, but also verify required textures exist
in the exported track package; a packed `.blend` alone is not a deployable track.

##### 4. Add STK-specific gameplay data

Set the scene as an STK track, track name, unique folder ID, designer, and Add-Ons
group. Set the assets root to `build/` so export goes under `build/tracks/`.
Configure a start grid that fits the road.

Generate the main driveline from the same layout as the road so they stay aligned.
It is not simply a generic Blender curve: the official guide describes connected
quad topology, a start gap, and start-marking "antennae" edges. Implement the exact
representation expected by the chosen exporter revision. It should follow the
route, point the right way, and remain usable by AI through the seam.

Add at least three checklines beyond the lap line. Chain them in driving order:
main driveline activates first checkline, each activates the next, and the last
activates `lap`. Make them wide enough to catch legitimate driving. Verify this
against exporter properties, not only the visual placement of lines.

Ensure the road has intended collision behavior and the driveline supports sensible
rescue placement. A decorative finish stripe alone does not implement lap counting.

##### 5. Run the build and inspect the exported package

Once `tools/build_track.py` has actually been implemented, the intended pattern is:

```bash
blender --background --factory-startup --disable-autoexec \
  --python-exit-code 1 --python tools/build_track.py
```

This command is a **planned interface**, not something that works in this initial
workspace. Blender arguments are order-sensitive. `--python-exit-code 1` makes
uncaught script errors fail automation. Log the Blender version, exporter commit,
input parameters, and resolved output directory for each build.

Inspect output before copying it to the game. A typical modern race-track export
contains `track.xml`, `scene.xml`, `materials.xml`, `quads.xml`, `graph.xml`, one or
more `.spm` models, and referenced textures. Exact filenames and whether a file
is needed depend on the exporter/content; compare with a working race track and
the actual exporter output rather than enforcing this list blindly.

Parse XML, confirm referenced assets exist, and reject stale/partial builds.
Use a fresh track-specific staging directory, not leftover output from an older
successful build. Keep the source `.blend` so the player can inspect it in the GUI.

##### 6. Install locally and run

For a native Linux install, the documented default is:

```text
~/.local/share/supertuxkart/addons/tracks/llm_loop/
```

An XDG override, portable setup, Flatpak, or Snap can change this. Flatpak commonly
uses `~/.var/app/net.supertuxkart.SuperTuxKart/data/supertuxkart/addons/tracks/`.
Confirm the directory used by the actual game process/configuration/log before
deploying. The diagnostic prints candidates, not a guaranteed active path.

Copy the **contents of the exported track folder** into that track folder, preserving
textures and subdirectories. Avoid an extra `llm_loop/llm_loop/` nesting level.
For a first install to the native default, after inspecting the staged export:

```bash
mkdir -p "$HOME/.local/share/supertuxkart/addons/tracks"
cp -R build/tracks/llm_loop "$HOME/.local/share/supertuxkart/addons/tracks/"
```

Only use that first-install command when the destination `llm_loop` does not
already exist. For revisions, close the game, preserve the last working version
outside the scanned tracks directory, and replace only this project's folder
after reviewing the exact path. Simple overlay copies can leave stale files.
Never overwrite a bundled track or clear the entire add-ons directory.

Restart STK and look in the Add-Ons track group on the race-selection screen
(not just the online add-on download manager). Start with one kart, then test
with AI. Inspect `supertuxkart --help` before using version-specific race/debug
flags. To capture a native game's terminal output during a test:

```bash
supertuxkart 2>&1 | tee /tmp/stk-loop-playtest.log
```

This launches the GUI and the game may update its normal settings. The log path
is temporary; copy relevant findings into the experience log. Avoid running a
second instance if one is already open.

##### 7. Accept the first prototype

The milestone is complete only when all these are observed in the game:

- The custom track appears and loads with no missing-asset errors.
- The start grid fits, karts face the correct direction, and the road is solid.
- A player can finish three laps; crossing the finish after a full valid loop
  increments the lap exactly once.
- Crossing the finish without completing the required checkpoint sequence does
  not award a lap; backward/partial crossings do not produce spurious progress.
- AI can complete three laps without consistently stopping, driving backward,
  cutting across the infield, or getting stuck at the seam.
- Manual rescue and at least one off-road/fall recovery return a kart to a sensible
  location and orientation, without breaking subsequent lap counting.
- Barriers/corners do not trap karts; textures remain visible in-game.
- The player records whether width, speed, corner radii, and lap length feel good.

Do not mark these done based only on Blender rendering or successful XML export.
