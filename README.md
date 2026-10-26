# STK Track Editor

An **unofficial, independent track editor for SuperTuxKart**. This project is
not affiliated with or endorsed by the SuperTuxKart team.

A local, top-down modular sketcher with a repeatable pipeline:

```text
visual editor -> versioned JSON -> Blender scene -> STK export -> local race
```

Flat circuits support straights, corners, item boxes and both nitro sizes.
JSON is the repeatable authoring source; Blender refinement is an explicit
one-way handoff, not automatic round-tripping.

## Quick start

The editor needs **Python 3.10+** and a modern browser, with no Python packages
to install. Run from the checkout root:

```bash
git clone https://github.com/tiborh/stk_track_editor.git
cd stk_track_editor
python3 tools/diagnose.py --editor-only
python3 tools/track_editor.py
```

Open **http://127.0.0.1:8765**. Load an example, edit it, and **Save JSON**.
The server binds only to loopback; stop it with Ctrl+C. The editor does not
write workspace files, run Blender or launch the game.
Choose a new track ID for variations to preserve the examples.

## Generate and drive

Generation also needs Blender, SuperTuxKart and the two `stk-blender` exporter
modules. Follow [installation and configuration](docs/INSTALLATION.md), then
the [authoring guide](docs/AUTHORING.md) for generation, local installation
and racing. Use `python3 tools/diagnose.py --probe-blender` to inspect that setup.

This repository contains source and example layouts, **not** preinstalled
tracks, generated Blender scenes, game assets or local playtest logs.
The initially verified platform is Linux; other platforms are not yet verified.

## Documentation

| Document | Purpose |
|---|---|
| [Installation](docs/INSTALLATION.md) | Prerequisites, exporter configuration and first build |
| [Authoring guide](docs/AUTHORING.md) | Current edit/save/build/install/play workflow and layout format |
| [Development guide](docs/DEVELOPMENT.md) | Diagnostics, implementation map, checks, exporter constraints and troubleshooting |
| [Handoff](HANDOFF.md) | Current status, player feedback and next development step |
| [Roadmap](ROADMAP.md) | Ordered future increments, status and acceptance gates |
| [Changelog](CHANGELOG.md) | Dated changes, investigations, exact results and player feedback |
| [Licensing](LICENSING.md) | Code, example artwork, attribution and external dependencies |
| [Contributing](CONTRIBUTING.md) | Change scope, checks and contribution licensing |

## License

Code and documentation: [GPL-3.0-or-later](LICENSE).
Included example layouts and their original generated artwork:
[CC-BY-SA-4.0](LICENSES/CC-BY-SA-4.0.txt), credited to **tiborh**, with per-track
notices. Third-party components retain their own licenses.
