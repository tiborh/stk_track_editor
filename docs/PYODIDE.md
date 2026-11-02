# Pyodide and GitHub Pages implementation brief

[Roadmap](../ROADMAP.md) | [Handoff](../HANDOFF.md) | [Development](DEVELOPMENT.md)

## Decision and status

On 2026-11-02 the player approved trying Pyodide as the next roadmap priority:
a browser-only sketcher hosted on GitHub Pages, reusing the Python validation
and geometry rather than implementing a second validator in JavaScript.
This is an approved experiment, not an implemented or verified deployment.
No Pyodide version, supported-browser matrix or performance targets have been
selected or measured.

The intended project URL is `https://tiborh.github.io/stk_track_editor/`.
GitHub Pages serves static files; it cannot run the current Python HTTP
server. Visitors should be able to edit, validate and download layout JSON
without installing Python. Blender generation, STK exports and racing remain
local, separate operations.

## Findings in the current code

- `editor/index.html` loads `/editor.css` and `/editor.js`; these root-relative
  paths do not point into the GitHub Pages project subdirectory.
- `editor/editor.js` calls `POST /api/inspect` both from `inspect()` for layout
  diagnostics and from `loadText()` for raw imported JSON. `loadExample()` uses
  `/examples/<name>.json`. Publishing the assets unchanged would break these
  operations, not just optional diagnostics.
- `tools/track_editor.py` serves an explicit asset/example map. Its
  `inspect_layout()` returns `draft_ok`, `valid`, diagnostic text, disconnected
  ports and pickup marker coordinates. JSON decoding and request-size checks
  currently live in the HTTP handler.
- `tools/track_layout.py` uses standard-library Python, including `dataclasses`,
  `json`, `math`, `pathlib` and `re`, without Blender. It is the candidate shared
  core; compatibility with the chosen Pyodide runtime still needs testing.
- The frontend already debounces validation and uses revision/file-operation
  guards. Preserve these, layout mutations through `edit()`, undo/redo and dirty
  tracking. Ignoring stale responses does not cancel their underlying work.
- `tools/test_track_editor.py` covers inspector results, drafts, examples,
  malformed JSON and HTTP boundaries. `tools/check_track_editor_browser.py`
  exercises real interactions but currently starts its own Python server;
  passing that check alone cannot establish static-site compatibility.

## Runtime and architecture

Pyodide is CPython compiled to WebAssembly through Emscripten. The browser
loads that interpreter, its standard library and application Python modules;
the `.py` application is still executed by Python, not translated into
JavaScript. Optional native Python extensions require compatible WebAssembly
builds; desktop packages and executables cannot simply be reused.

Keep the responsibility split:

```text
JavaScript UI and SVG renderer
  -> asynchronous validation adapter
     -> local HTTP adapter -> shared Python inspection/geometry
     -> module Web Worker -> Pyodide -> same Python inspection/geometry

Saved layout JSON -> local Blender/STK generation and gameplay
```

Extract inspection and strict JSON decoding into a browser-independent Python
module. It must not depend on the DOM, Pyodide APIs, HTTP server or `bpy`.
Keep `track_layout.py` authoritative for circuit and pickup geometry; do not
port or duplicate its rules in JavaScript. Retain the dependency-free local
server and its loopback Host/Origin checks rather than exposing it publicly.

Initialize one Python runtime in a module-type Web Worker and import the
shared modules once. The UI sends requests with IDs and original JSON text;
the worker returns serializable results or explicit errors. A worker cannot
directly manipulate the DOM. Keep Python execution off the UI thread, but
do not assume that a worker makes computation faster or requests parallel.

Pass user input as data to a fixed Python entry point, never interpolate it
into executable Python source. Decode original JSON with `unique_fields`
before JavaScript parsing can erase duplicate keys. Preserve version-1/2
semantics, draft-versus-complete-circuit behavior, strict field/type/finite-number
checks and the existing input-size boundary, accounting for UTF-8 bytes versus
JavaScript string length. Keep malformed input, invalid layouts and runtime
failures distinguishable.

Prefer a simple JSON message boundary over long-lived cross-language object
graphs. If using Pyodide Python-object proxies, explicitly release them when
finished. Ensure pending requests fail visibly on initialization errors, worker
failure or incompatible runtime loads; do not substitute successful-looking
validation or silently fall back to a public/local backend. Adapt the current
"Keep the server running" error text for hosted operation.

## Hosting, files and trust boundaries

Pin an exact Pyodide release and verify its supported Python/browser behavior
when implementing. Decide between self-hosted runtime assets and a pinned CDN:
self-hosting improves control over availability and deployment contents; a CDN
adds an external runtime supply/availability dependency. Do not use a moving
`stable` or `latest` runtime URL.

Stage a dedicated Pages artifact, not the entire checkout: UI assets, required
Python modules, example JSON and matching attribution/license notices, and any
self-hosted runtime assets. Keep generated tracks, Blender files, exporter
checkouts and local logs out. Use project-base-aware URLs for modules, workers,
runtime files and examples, tested under `/stk_track_editor/`, not only `/`.
Preserve required licensing notices for the application, examples and runtime.

Keep the local server's CSP/security behavior intact. Plan the hosted page's
worker/WebAssembly loading policy separately; Python-server response headers
do not automatically accompany static files on Pages. Verify actual Pages
constraints before relying on custom headers, cross-origin isolation,
SharedArrayBuffer or execution-interruption features.

Pyodide's default filesystem is virtual and in memory; loading application
modules there does not grant access to the visitor's disk. State is not
persistent across reloads unless explicitly implemented. Preserve existing
file-picker/download behavior rather than adding directory permissions,
automatic workspace writes or browser-profile access.

Validation can happen entirely on the visitor's device without uploading
layouts. Pyodide can nevertheless use browser APIs through JavaScript; it is
not an extra sandbox for arbitrary untrusted Python. Only trusted application
code runs; imported layouts remain JSON data. Offline operation requires a
deliberate caching design and is not part of the initial promise.

## Scalability assessment

More visitors do not share one validation server: each device runs its own
Python runtime. Pages/CDN hosting still has limits. Feature growth such as
surfaces, terrain data, more road pieces and elevation calculations fits the
shared-core approach in principle, not as a measured performance guarantee.

The costs are a megabyte-scale runtime download, initialization and memory,
JSON/message conversion, Python computation and frontend rendering. Browser
caching can help repeat visits. Large SVG scenes may become a bottleneck
independently of Pyodide, especially on lower-powered devices. A future 3D
renderer is a separate concern; Blender, native exports and large asset
processing stay outside this browser runtime.

Measure cold/warm startup, edit-to-diagnostic latency, responsiveness and memory
where available using existing examples and larger valid layouts within current
format limits. Record runtime/browser/device versions and fixture sizes.
Agree acceptance targets from those observations; no track-size, mobile
performance or latency guarantees have been established.

Start with full validation and existing debounce. If measurements justify it,
coalesce rapid edits, avoid accumulating obsolete work, cache derived results
or introduce incremental diagnostics while retaining full validation at
important boundaries. Do not start with interpreter pools, a second validator
or speculative optimization. Clean adapters preserve the option to replace
Pyodide or add a separately designed backend if future requirements demand it.

## Suggested implementation sequence and acceptance

1. Extract shared inspection/JSON handling without changing local behavior.
   Run existing Python tests and local browser scenarios.
2. Select/pin a runtime and make a worker proof of concept inspect existing
   examples and invalid raw JSON using the same Python modules.
3. Add the asynchronous frontend adapter and project-base-aware asset/example
   paths. Exercise editing, pickups, drafts, history, file operations and error
   states with no `/api/inspect` backend available.
4. Compare desktop Python and Pyodide results on valid v1/v2 layouts, incomplete
   drafts, invalid schema/numbers/references and duplicate-key JSON. Confirm
   route/pickup geometry equivalence with explicit numerical tolerances where
   necessary. Test rapid edits and overlapping file operations for stale results.
5. Run real-browser tests against both local HTTP and a staged static site
   served under the Pages project prefix. Measure larger-layout behavior and
   cold/warm initialization. Test runtime-load failures and worker failures.
6. Add a dedicated Pages Actions deployment and verify the actual HTTPS site,
   including worker/runtime loads and JSON save/reopen, before declaring it
   delivered. Stage only intended files; preserve existing required checks.

Acceptance requires observed parity, usable measured performance, working
project-subpath deployment and an unchanged local workflow. Record failures,
versions and limits in the changelog. Do not claim universal browser support,
offline capability, Blender/export validation or human gameplay acceptance
from this trial. The outstanding pickup gameplay checklist remains a gate for
later track/gameplay increments.

## References

Authoritative material consulted 2026-11-02; recheck APIs for the pinned release:

- [GitHub Pages static hosting and project URLs](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
- [Pyodide overview and CPython/WebAssembly model](https://pyodide.org/en/stable/)
- [Module Web Workers and message passing](https://pyodide.org/en/stable/usage/webworker.html)
- [Virtual filesystem and optional persistence](https://pyodide.org/en/stable/usage/file-system.html)
- [Python/WebAssembly compatibility constraints](https://pyodide.org/en/stable/usage/wasm-constraints.html)
