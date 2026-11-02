# Current handoff

Updated 2026-11-02. Start with [README](README.md) for setup and
[ROADMAP](ROADMAP.md) for scope; this file is the current development state,
not a replacement for the guides or dated evidence in [CHANGELOG](CHANGELOG.md).

## Confirmed

- The visual editor supports flat straights/corners, start selection, shared
  Python diagnostics, undo/redo and versioned JSON save/load.
- Roadmap item 2's practical kart-choice target is accepted. The suggested
  Konqi launch and normal in-game selection work on the player's desktop.
- The player completed a full three-lap, four-kart race on UI-authored Double
  Clover. First Circle, Modular Oval and Modular Bends remain references.
- Item boxes, small nitro and big nitro support road-relative placement,
  selection/update/deletion, history, save/load and native Blender export.
  The player reports: **"I have also tested the item box and nitro placement.
  they look good."** This confirms placement appearance; a complete human
  pickup collection/use/respawn acceptance run was not explicitly reported.
- Automated rendered Pickup Oval racing completed three laps with four
  finishers, zero rescues and repeated item/nitro collection. Exact historical
  results and limitations are in the changelog.

## Repository transition

The working checkout is now `~/repos/github/tiborh/stk_track_editor`, intended
for the public `tiborh/stk_track_editor` repository. It is a source-only copy.
The original study workspace, its generated scenes/exports, local logs and
installed game links were left untouched. Those artifacts are not in a clone.
Do not redirect existing add-on links or overwrite their targets implicitly.
On this machine, an ignored `vendor/stk-blender` link reuses the established
external exporter checkout. Fresh clones should follow the installation guide.
Generated validation builds in this new checkout are also ignored and not
installed into the game.

Code/documentation are GPL-3.0-or-later. Original example layouts and generated
artwork are CC-BY-SA-4.0, credited to tiborh. Matching attribution notices now
travel with generated tracks. See [LICENSING](LICENSING.md).

## Next development step

Start the approved Pyodide/GitHub Pages trial, now roadmap item 1. Read the
[implementation brief](docs/PYODIDE.md) for the architecture, inspected code,
scalability tradeoffs, implementation sequence and acceptance checks. Reuse
the Python core in a browser worker while preserving the local workflow.
This is a recorded decision, not an implemented or verified deployment.

The focused human pickup checklist remains outstanding in
[Authoring](docs/AUTHORING.md#generate-and-play), including a saved/reopened
variation, item use, both nitro sizes, respawning and a full race. Record only
what was actually observed. The browser-delivery trial may proceed first,
but complete that checklist before roadmap item 4, per-module road surfaces.

The historical X11 `BadWindow` root cause is still unknown. Mei's missing
exhaust-particle asset warning did not prevent isolated races; it is not an
established explanation for that exit. Preserve the Tux/add-ons-disabled
fallback and do not change packages, game settings or installed assets without
reviewing the proposed change with the player.

## Documentation maintenance

Keep this handoff current rather than appending history here. Put dated results
in the changelog, future scope/status in the roadmap and reusable instructions
in the guides. Keep the README a short entry point.
