# Development and environment

[README](../README.md) | [Authoring](AUTHORING.md) | [Roadmap](../ROADMAP.md) | [Changelog](../CHANGELOG.md)

See [Installation](INSTALLATION.md) for a fresh checkout and
[HANDOFF](../HANDOFF.md) for current development state.

Run commands from the workspace root. Do not install packages, replace the
system Blender, change game settings or overwrite accepted tracks without
reviewing the proposed change with the player. Re-investigate compatibility
when the environment changes or an actual failure occurs, not every session.

## Implementation map

| File | Responsibility |
|---|---|
| `tools/track_layout.py` | Versioned structure validation, tile ports, circuit traversal, canonical sampling and pickup positioning |
| `tools/track_editor.py` | Loopback-only server, shared draft inspection and explicit asset/example routes |
| `editor/` | Browser drawing, history, file interchange and pickup controls |
| `tools/build_modular_track.py` | Blender scene, native pickups, validated export and rebuild backups |
| `tools/build_track.py` | Preserved First Circle generator and shared mesh/material helpers |
| `tools/track_licenses.py` | Explicit per-track notice loading and export/source propagation |
| `track/layouts/` | Repeatable JSON authoring sources |
| `track/modular/<id>/` | Generated editable scenes, texture sources and input snapshots |
| `build/tracks/<id>/` | Generated game-ready exports |
| `build/*playtest/` | Isolated race settings, logs and Blender refinements |

## Focused checks

```bash
python3 -m unittest discover -s tools -p 'test_*.py'
node --check editor/editor.js
python3 tools/check_track_editor_browser.py
```

The real-browser check optionally uses already-installed Python Playwright and
system Chromium; neither is an editor runtime dependency.
Its optional Python dependency is pinned in `tools/requirements-browser.txt`;
ordinary source checks and editor startup do not require it. Dependabot checks
this file and GitHub Actions versions weekly.

Copilot's agent browser tools are configured separately in
[`.github/mcp.json`](../.github/mcp.json), using the shared `browser-tools-mcp`
launcher. Follow the [browser-tools README](https://github.com/tiborh/browser-tools#readme)
for machine setup, keep the launcher on Copilot's inherited `PATH`, and verify
selection with `browser-tools-mcp --check`. Restart Copilot CLI in the trusted
project and inspect `/mcp` to load it. The launcher uses a headless, isolated
browser session and preserves this project's working directory. It does not
provide Python Playwright for `check_track_editor_browser.py`.

For generated Blender scenes:

```bash
blender --background --factory-startup --disable-autoexec \
  --python-exit-code 1 --python tools/check_pickup_handoff.py
blender --background --factory-startup --disable-autoexec \
  --python-exit-code 1 --python tools/check_modular_handoff.py
```

These re-export into separate `build/` test folders rather than regenerating
accepted tracks. Automated export/race checks do not substitute for human
gameplay acceptance. Record dated results and their limits in the
[changelog](../CHANGELOG.md).
Generate the referenced example sources first; they are not shipped in a clone.
Pass `-- --exporter-root /path/to/stk-blender` to use a non-default checkout.

## Exporter constraints to preserve

The default checkout is `vendor/stk-blender`; both `io_scene_spm` and
`io_antarctica_scene` are required. An existing checkout elsewhere can be
selected with `--exporter-root`. Blender 5.2.1 exported successfully with
revision `992ab8aad3e9a4850e1ec25145940dd10da509c4` plus a local graph-XML fix:
`stk_track_utils.py` must write `<?xml version="1.0" encoding="utf-8"?>`.
Apply the included compatibility patch only to a matching unpatched checkout,
as described in [Installation](INSTALLATION.md#configure-the-exporters).
Preserve the fix when updating the exporter; see the
[First Circle record](../CHANGELOG.md#2026-10-16---first-circle).

The export operator takes a file stem inside an existing track folder, not just
the folder. The main driveline needs connected quad topology and start antennae;
checklines must form the full activation chain back to `lap`. Keep previews'
`use_fake_user` setting and relative texture paths so later Blender exports
retain the thumbnail/textures. See the
[iteration-1 implementation record](../CHANGELOG.md#implementation-files-and-issues-resolved)
for the original failures and fixes.

## Diagnostic script

```bash
python3 tools/diagnose.py
python3 tools/diagnose.py --editor-only
python3 tools/diagnose.py --probe-blender
python3 tools/diagnose.py --help
```

The script uses only Python's standard library. By default it checks executables,
Python/editor prerequisites, known add-on locations, game data, and user track
locations. `--editor-only` does not require Blender or the game or launch any
external program. It does not install,
download, create directories, launch the game, or modify Blender preferences.
It queries Flatpak's installed-app list if Flatpak is available.

`--probe-blender` launches a temporary background Blender process with factory
settings and automatic script execution disabled. It creates a tiny mesh in
memory and reports version and add-on search paths; it does not save a file or
enable exporters. Blender itself may create runtime/cache files. The subprocess
has a timeout. **This is not a sandbox for untrusted Blender binaries.**

Useful overrides:

```bash
python3 tools/diagnose.py \
  --blender /absolute/path/to/portable-blender/blender \
  --exporter-root /absolute/path/to/stk-blender \
  --stk-data-dir /absolute/path/to/supertuxkart/data \
  --addons-dir /absolute/path/to/supertuxkart/addons/tracks \
  --probe-blender
```

`--exporter-root` points to a checkout containing both exporter module directories;
finding that checkout does not mean the modules are installed. `--addons-dir` is
the directory containing track folders, not one particular track folder.

Output statuses:

| Status | Meaning |
|---|---|
| `OK` | The specific check succeeded; not proof of end-to-end track readiness |
| `WARN` | Optional tool missing, path uncertain, or manual verification needed |
| `MISSING` | Required executable or exporter files not found |
| `ERROR` | A requested operation failed; the error needs investigation |

Exit status is `0` for no detected required gaps/errors, `1` for required gaps or
probe/query errors, and `2` for invalid command-line arguments. Warnings alone do
not make it fail. Finding exporter files does **not** establish that they can be
enabled or used with this Blender version. Snap and unusual portable/sandboxed
layouts require manual inspection; absence from the report is not proof of
absence from the machine. Output includes local paths; review before sharing.

## Necessary and useful tools

| Tool | Purpose | Needed for first loop? |
|---|---|---|
| SuperTuxKart and its game data | Actual local race and gameplay feedback | Yes |
| Blender | Geometry, materials, scene metadata, export host | Yes |
| STK `io_scene_spm` add-on | STK mesh format import/export | Yes |
| STK `io_antarctica_scene` add-on | Track, driveline, checkline, material export | Yes |
| Python 3 | Diagnostics and orchestration outside Blender | Yes for these scripts |
| Blender's bundled Python / `bpy` | Procedural scene creation inside Blender | Included with Blender |
| Git | Fetch exporter and version source/scripts | Recommended |
| curl or browser | Read documentation/download tools | Useful |
| GIMP, Krita, or Inkscape | Texture and preview editing | Optional |
| Recording/screenshot tool | Capture driving issues and compare revisions | Optional |

Do not `pip install bpy` for this workflow. Run scene-building scripts using
Blender's own Python, not the system interpreter. No external Python packages
are currently required. Headless scene creation does not prove that graphical
Blender or the game can run; gameplay needs a working display and graphics stack.

On this Manjaro system, inspect packages with:

```bash
pacman -Q blender supertuxkart python git
```

If those packages are actually missing, review a normal Manjaro installation
transaction such as `sudo pacman -Syu --needed blender supertuxkart python git`.
This can upgrade the whole system; it is not a diagnostic command. Do not use
Arch partial-upgrade shortcuts. On another distribution use its package manager.
The STK exporter add-ons are a separate setup step.

## Resources and authority

Consulted 2026-10-15. Tutorials include older Blender UI screenshots and
instructions; use current exporter code as the authority for API details.

| Resource | What to use it for |
|---|---|
| [Official track-making guide](https://supertuxkart.net/Making_Tracks) | Overall process and links to individual topics |
| [Official exporter repository and README](https://github.com/supertuxkart/stk-blender) | Installation, requirements, materials, exporter code |
| [Tool installation](https://supertuxkart.net/Installing_Tools) | Add-on directories and enabling both modules |
| [Track properties](https://supertuxkart.net/Making_Tracks:_Properties) | Asset output root, track identity, race setup |
| [Drivelines and checklines](https://supertuxkart.net/Making_Tracks:_Drivelines_and_Checklines) | AI route, start topology, lap validation |
| [Local testing](https://supertuxkart.net/Making_Tracks:_Testing) | Export, local installation, track selection |
| [Materials](https://supertuxkart.net/Materials) | Supported game material properties |
| [Artist debug mode](https://supertuxkart.net/Artist_Debug_Mode) | Visualize gameplay data when diagnosing problems |
| [Licensing](https://supertuxkart.net/Licensing) | Asset attribution and redistribution constraints |
| [Blender command-line arguments](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html) | Background execution and error exit codes |
| [Blender Python API](https://docs.blender.org/api/current/) | `bpy` scene and mesh operations |
| [STK source](https://github.com/supertuxkart/stk-code) | Runtime interpretation and diagnostic options |
| [STK community forum](https://forum.supertuxkart.net/) | Compatibility reports and track-making help |

At the initial consultation, the exporter README stated Blender 3.0+ and
STK 1.0+ minimums. A minimum version does not guarantee compatibility with
every newer release. The working local combination is recorded above; if
an update breaks it, investigate the exact error before considering a
side-by-side supported Blender release. Do not silently downgrade the system.

## Design rationale and research references

The target is **SuperTuxKart**, not the separate downhill game Tux Racer.
The intended progression is:

```text
simple visual editor -> versioned layout data -> Blender generator
                     -> editable .blend -> existing STK exporter -> local race
```

The Stunts (1990, also known as 4D Sports Driving) reference is its construction
experience: a top-down grid, recognizable pieces, rotations, separate terrain,
and a short build/drive/adjust cycle. Its standard 30x30 layout and compact
1,802-byte track format illustrate storing module choices rather than meshes.
Original Stunts also has multi-cell pieces; our first implementation deliberately
uses only one-cell modules. Do not confuse later community-editor conveniences
with features of the original DOS editor.

References consulted during brainstorming:

| Reference | Relevance |
|---|---|
| [Stunts overview](https://en.wikipedia.org/wiki/Stunts_(video_game)) | Historical context and original editor screenshot |
| [Stunts Wiki: track file](https://wiki.stunts.hu/wiki/Track_file) | Grid, separate track/terrain encoding, and multi-cell piece documentation |
| [Stunts Wiki: in-game editor](https://wiki.stunts.hu/wiki/In-game_editor) | Original editor reference; exact controls were not fully verified |
| [Bliss](https://www.raceforkicks.com/bliss/) | Later community editor: block transformations, analysis, and automatic scenery |
| [Stunts HD Track Editor](https://github.com/slayerofmadness/stunts-hd-track-editor) | Modern grid UI, footprints, rotation, connection diagnostics, and file interchange |
| [STK drivelines/checklines](https://supertuxkart.net/Making_Tracks:_Drivelines_and_Checklines) | Gameplay metadata required beyond visible road geometry |
| [STK gameplay fundamentals](https://supertuxkart.net/Making_Tracks:_Gameplay_Fundamentals) | Visibility, width, turns, and meaningful playtesting |

The Stunts Wiki intermittently returned server errors/timeouts during research;
some details were available through indexed documentation and community-editor
documentation. A byte-compatible Stunts importer, copied game assets, or a
faithful recreation of every original control is not part of the current scope.
No Stunts game assets or community-editor code were incorporated.

## Iterate from player experience

Change one major variable at a time, retain the last playable build, and record
the same game settings so comparisons are meaningful. Fix route/collision/lap
bugs before expanding features or adding art.

For each revision record:

| Field | Example / purpose |
|---|---|
| Revision and build identity | `r001`, source commit if available, exporter commit |
| Build environment | Exact Blender and STK versions |
| Parameters changed | Width 14 -> 16 m; everything else unchanged |
| Test setup | Kart, difficulty, speed class, AI count, laps, input device |
| Observations | Which corner/landmark, what happened, frequency |
| Measurements | Lap times, rescues, AI failures; FPS if performance is an issue |
| Player assessment | Too tight, too wide, boring, confusing direction, etc. |
| Next hypothesis | Broaden turn 2 rather than increasing width everywhere |

Lap-time and frame-rate targets should be agreed after driving the baseline,
not invented as requirements now.

## Troubleshooting

| Symptom | First investigation |
|---|---|
| `import bpy` fails in system Python | Execute the script through Blender |
| Add-on found but cannot enable | Capture traceback; compare Blender API and exporter revision |
| Add-on exists but background export cannot find it | Check the selected binary's paths and explicit activation under factory startup |
| Headless Blender crashes | Preserve stderr; check dependencies/driver compatibility; try a side-by-side Blender before changing system packages |
| Track missing from selection | Actual user directory, folder nesting, `track.xml`, group, duplicate ID, game restart, runtime logs |
| Track loads black/white or misses textures | Supported material nodes, exported filenames, texture packaging, case-sensitive paths |
| AI stops or takes the wrong route | Main driveline connectivity, direction, start markers, seam, corner smoothness |
| Laps never count or count early | Lap line and full checkline activation chain |
| Karts fall through or hit invisible edges | Collision settings, normals, seam gaps, non-road objects |
| Rescue is wrong or puts karts out of bounds | Driveline position/orientation and nearby road/collision geometry |
| Start crashes or grid overlaps | Starting road width, karts per row, and spacing properties |
| Older build still seems to load | Duplicate IDs, wrong installation directory, stale overlay files |

Read exact errors before changing tools. Do not hide exceptions or silently
substitute a different exporter/track.

## Recording a result

Append entries after meaningful attempts, including failures:

```text
Date / revision:
Goal:
Environment / exporter commit:
Exact command:
Result (observed, not assumed):
Error and resolution:
Player feedback:
Files / parameters changed:
Last known playable build:
Next concrete step:
```
