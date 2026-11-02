# Roadmap

[README](README.md) | [Authoring](docs/AUTHORING.md) | [Changelog](CHANGELOG.md)

Proposed 2026-10-25; priorities and status updated 2026-11-02.

The following is the recommended implementation order, not an agreed commitment
to every feature. **Item 1 is approved for the next implementation trial;
item 2 is accepted; item 3 is implemented with human acceptance pending;
items 4-9 remain planning only.** The Pyodide trial is not yet implemented or
verified on GitHub Pages. Iteration 2 remains the
human-accepted authoring baseline. Keep each increment independently playable
and retain the accepted reference layouts and exports.
The player's subsequent **"they look good"** feedback accepts item/nitro
placement appearance. Full human collection/use/respawn acceptance was not
explicitly reported; see [HANDOFF](HANDOFF.md) for the current next step.

The next priority is browser-only delivery using the shared Python core.
The subsequent track progression preserves the pickup acceptance gate, then
adds richer racing, separates road and terrain, and introduces height/crossings.
Complexity is relative to this workspace, not an implementation-time estimate.

| Order | Recommended increment | Relative complexity | Builds on |
|---|---|---|---|
| 1 | Trial Pyodide and GitHub Pages delivery | Medium; compatibility/performance unmeasured | Shared Python inspection/geometry and existing browser checks |
| 2 | Diagnose and restore kart choice | Uncertain; potentially small | Known-working race command |
| 3 | Place item boxes and nitro | Low-medium | Existing road sampling and editor |
| 4 | Per-module road surfaces | Medium | Versioned layout extensions from step 3 |
| 5 | Separate flat terrain layer | Medium | Surface/material handling from step 4 |
| 6 | Additional flat road pieces | Medium-high | Established placement and surface semantics |
| 7 | Elevation-aware roads and terrain | High | Separate terrain layer and explicit piece connections |
| 8 | Grade-separated crossings and bridges | High-very high | Elevation, clearance and multi-passage connectivity |
| 9 | Optional at-grade crossings or branching routes | Very high | Explicit route identity through shared locations |

## 1. Trial a browser-only editor with Pyodide

**Approved 2026-11-02 as the next priority; not implemented or deployed.**
Read the [implementation brief](docs/PYODIDE.md) before starting; it records
the inspected code, runtime model, deployment constraints, scalability
assessment, proposed sequence, references and acceptance checks.

Target `https://tiborh.github.io/stk_track_editor/`: visitors edit, validate and
download layout JSON without installing Python or using a hosted Python API.
GitHub Pages is static hosting; the current `/api/inspect` dependency prevents
an unchanged deployment. Blender generation, exports and gameplay remain local.

Extract shared inspection/strict JSON decoding from the HTTP server and run
the same Python core through a pinned Pyodide runtime in a module Web Worker.
Keep JavaScript responsible for UI/rendering, preserve the local server and
its security boundaries, and do not duplicate validation or geometry rules.
Make asset/example/worker paths work under the Pages project prefix.

Prove local-versus-browser validation parity, run interaction checks on both
delivery modes, measure cold/warm startup and larger-layout responsiveness,
then verify the actual Pages deployment. Handle runtime/worker errors visibly;
do not promise offline support, arbitrary native Python packages or unmeasured
track-size/mobile performance. Keep the adapters replaceable if future
requirements outgrow browser execution.

This delivery experiment may proceed before pickup gameplay acceptance, but
does not complete or waive that checklist before later track/gameplay changes.

## 2. Diagnose kart selection independently

**Practical target accepted 2026-10-26:** broader bundled and selected add-on
choices completed isolated rendered races, and the player confirmed both the
suggested Konqi launch and normal in-game kart/track selection work. See the
[kart-choice investigation](CHANGELOG.md#2026-10-26---kart-choice).
The earlier `BadWindow` root cause remains unknown; no global add-on failure was
reproduced. Proceed to item boxes and nitro without blocking on that historical error.

Determine whether other bundled karts work with add-on karts disabled, then
isolate whether enabling add-ons fails generally or only for particular assets.
Investigate missing exhaust-particle warnings and the earlier X11 `BadWindow`
failure separately; neither is an established root cause.

Target: broaden the known-working kart choice and document any remaining
restriction. Preserve the Tux workaround. Review any proposed package, asset or
game-setting changes with the player before applying them.

This is a bounded maintenance investigation, not a prerequisite for changing
the track format. If unresolved, continue feature work using the working command.

## 3. Add road-relative pickup placement

**Implemented 2026-10-26; human acceptance pending.**
See [Road-relative pickups](docs/AUTHORING.md#road-relative-pickups) for editor
controls, version-2 semantics, export, launch command and the remaining
acceptance checklist. Do not start road surfaces until this increment's focused
gameplay acceptance is complete.

Start with item boxes and nitro, not hazards or arbitrary scenery. Add editor
placement, selection, deletion, undo/redo, validation and save/load, followed by
generator/export support. Use the game's existing pickup behavior.

Store positions relative to a module's canonical road path: position along the
path and lateral offset. Resolve world position through shared road sampling,
including tile rotation and the start-frame transformation. Placement must not
depend on JSON tile order or the race's traversal direction. Reject invalid
placements explicitly; define what happens when their module is deleted or
replaced. Later elevation should supply road height through the same sampling
interface rather than require rewriting saved pickup positions.

Introduce an explicit new layout version because version 1 rejects extra fields.
Continue loading existing version-1 layouts with their original meaning. Keep
Python validation authoritative and share it with editor diagnostics.

Target: save/reopen a pickup-equipped circuit, generate it, and complete a race
confirming collection, item use, respawning and sensible AI interaction.

## 4. Add per-module road surfaces

Begin with a small supported surface palette and a default matching the current
asphalt. Keep material appearance and gameplay effects explicit: a dirt-looking
texture must not silently imply altered grip. Introduce handling changes only
with verified exporter/runtime properties and driving feedback.

Keep surface identity separate from piece shape and rotation. A surface should
remain applicable to future road pieces without creating separate piece types
for every shape/material combination.

Target: a mixed-surface circuit with reliable joins, visible transitions, working
pickups and acceptable human/AI handling. Defer arbitrary painted road patches.

## 5. Add a separate flat terrain layer

Allow painting a small terrain palette around the road, initially at a constant
height. Keep terrain cells independent of road occupancy: replacing a road must
not erase the underlying terrain definition. Reuse supported material identities
where appropriate, but distinguish terrain behavior from road behavior.

Define road/terrain overlap, collision and off-road recovery explicitly. Preserve
the road's visual motion cues and avoid introducing terrain seams or coplanar
surfaces that flicker.

Target: save/reopen and drive a circuit with varied surroundings, including an
intentional off-road and rescue check. Hills, water mechanics and freeform
sculpting remain out of scope for this increment.

## 6. Expand flat road construction

Add a small set of useful pieces, chosen from driving feedback: for example,
broader bends or chicanes. Establish explicit piece footprints and connection
definitions before adding multi-cell pieces. Validate occupied cells, matching
ports, road-edge joins and curvature rather than relying on visual adjacency.

Keep shape sampling, surface selection and pickup placement separate. Preserve
stable module identity where possible, and explicitly reject or request
repositioning of pickups that no longer fit a replacement piece.

Target: a circuit using the new pieces that preserves lap counting, AI routing
and rescue behavior. Continue requiring a single route; do not introduce branches
merely to support more shapes.

## 7. Introduce elevation-aware roads and terrain

Extend shared road sampling with height and orientation so road meshes, pickups,
markings, barriers, drivelines and checklines derive from the same geometry.
Require compatible endpoint elevations and smooth transitions between pieces.
Evolve terrain from the separate flat layer rather than attaching landscape
height implicitly to road tiles.

Start with gentle ramps and hills, not jumps, banking or loops. Check grade
limits, road/terrain intersections, item height, AI behavior and rescue placement.
Retain flat layouts as unchanged defaults.

Target: a complete race over a modest hill, including manual rescue and seam
checks. This establishes the vertical geometry needed for bridges.

## 8. Add bridges and grade-separated crossings

Start with one controlled over/under crossing and its approach pieces, retaining
one unambiguous race route. Represent the two passages explicitly: sharing a
horizontal location must not automatically connect them. Connection validation
must include elevation and passage identity.

Validate overhead clearance, approach grades, barriers, collisions, checkpoint
progress and rescue placement on each level. Ensure pickups and surface settings
refer to the intended passage, not merely its grid cell.

Target: a figure-eight-style circuit with correct human/AI routing, lap counting
and recovery above and below the crossing.

## 9. Consider at-grade crossings and branches separately

These are optional later extensions, not automatic consequences of bridge
support. An at-grade crossing with fixed straight-through passages differs from
a junction where the driver may choose a route.

First consider a fixed-route crossing with explicit passage pairing and progress
checks. Add branching routes only if desired, with a separate design for AI
choices, route rejoining, checkpoint activation, shortcut prevention and rescue.
Do not force these semantics into the current single-circuit validator early.

## Rules across the roadmap

- Evolve the format only when an increment needs it; keep old layouts loadable
  and reject unsupported data explicitly rather than discarding it.
- Reuse shared geometry and validation; do not create independent browser rules
  or separate coordinate transforms for each feature.
- Preserve JSON as the repeatable authoring source and Blender refinement as an
  explicit one-way handoff. None of these increments requires round-tripping.
- Keep build/play automation, 3D preview and decorative-object libraries separate
  from this sequence. They can be reconsidered when workflow friction justifies
  them, without blocking the track capabilities above.
- For track/gameplay increments, complete focused export and gameplay acceptance
  before the next dependent increment; the browser-delivery trial does not waive
  the pickup gate. Successful generation alone does not establish correct racing.
