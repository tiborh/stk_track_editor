# Contributing

This is an unofficial, independent editor for SuperTuxKart. Discuss substantial
behavior or format changes before implementation; follow the
[roadmap](ROADMAP.md) and [current handoff](HANDOFF.md).

Keep changes focused and each feature independently playable. Share Python
validation/geometry between editor diagnostics and generation rather than
duplicating rules in JavaScript. Preserve version-1 layout meaning and reject
unsupported data explicitly. Keep JSON as the repeatable source and Blender
refinement an explicit one-way handoff.

Run the smallest relevant checks, and the standard source checks before a PR:

```bash
python3 -m unittest discover -s tools -p 'test_*.py'
node --check editor/editor.js
```

For editor interactions, use the optional real-browser check documented in
[Development](docs/DEVELOPMENT.md). Changes to generation need a fresh export,
and gameplay changes need focused driving feedback, not just successful XML.
Do not regenerate or overwrite somebody's installed references implicitly.

Do not commit generated `build/` output, Blender files, caches, local logs,
exporter checkouts, credentials or machine-specific configuration. Include
small repeatable layouts/tests and record exact observations in the changelog.
Keep the README brief; update instructions in guides and current state in
`HANDOFF.md`.

Code and documentation contributions must be distributable under
GPL-3.0-or-later. Included example layout/artwork contributions use
CC-BY-SA-4.0 unless explicitly agreed otherwise; retain component-specific
notices for third-party assets. Document authorship, sources and modifications,
including AI assistance where relevant. See [Licensing](LICENSING.md).

For bug reports, include the layout (if shareable), exact command, versions,
expected/observed behavior and relevant error excerpt. Review logs for private
paths or other sensitive information before posting.
