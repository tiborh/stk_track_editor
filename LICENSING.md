# Licensing and attribution

## Project code and documentation

Unless explicitly identified otherwise, the editor, Python scripts, tests and
documentation are copyright 2026 tiborh and contributors, licensed under
**GNU GPL version 3 or any later version** (`GPL-3.0-or-later`).
See [LICENSE](LICENSE) for the full terms.

The project was developed with AI assistance. Contributions must have clear
provenance and be distributable under the applicable project license.

## Example layouts and generated artwork

The included example layouts and their original procedurally generated
geometry, textures and previews are copyright 2026 **tiborh**, licensed under
**Creative Commons Attribution-ShareAlike 4.0 International**
(`CC-BY-SA-4.0`). See [the full license](LICENSES/CC-BY-SA-4.0.txt).

Each `track/layouts/<name>.json` has a matching `<name>.licenses.txt`.
The preserved First Circle generator uses `track/llm_loop.licenses.txt`.
The modular builder copies notices into generated source and export as
`licenses.txt`; the circle builder copies its notice into the export.
The notice includes the attribution, source and license link needed when
sharing the original examples.

This artwork license does not relicense the generator's source code. Nor does
it automatically apply to every track made with the editor: authors choose
licenses for their own work and must retain the terms of reused components.
When modifying an example, retain its attribution, identify your changes and
follow its ShareAlike terms where applicable.

For a new layout, create its matching `.licenses.txt` or pass
`--license-file /path/to/licenses.txt` to the builder after Blender's `--`.
Without a notice, private generation remains possible but prints an explicit
warning that the export is not ready for redistribution. Do not copy an
example's notice onto unrelated artwork.

When adding external textures, models, audio or other assets, record their
authors, copyright years, source URLs, exact licenses and modifications.
A track-wide notice does not replace individual component credits.
After a one-way Blender refinement, maintain `licenses.txt` yourself and copy
it into any separately exported package; the Blender exporter does not manage it.

## External projects

This is an **unofficial, independent tool for SuperTuxKart**, not affiliated
with or endorsed by the SuperTuxKart team. No project logos, game binaries,
game asset files or exporter add-on modules are bundled.

- [SuperTuxKart](https://github.com/supertuxkart/stk-code): game code is
  GPL-3.0-or-later; artwork has component-specific licenses. Runtime references
  to installed music or pickup types do not include those assets in our export.
- [stk-blender](https://github.com/supertuxkart/stk-blender): MIT-licensed
  exporter installed separately. The small compatibility patch in `patches/`
  contains upstream context and retains its
  [MIT copyright and permission notice](LICENSES/MIT-stk-blender.txt).
- [Blender](https://www.blender.org/about/license/): installed separately.
  Its published Python-API licensing guidance applies to our GPL scripts;
  generated artwork is separately licensed.

An independent GitHub repository is distinct from submitting an official STK
add-on. For submission, follow the project's
[licensing guidance](https://supertuxkart.net/Licensing) and
[service terms](https://supertuxkart.net/Terms), including distribution rights,
an exported license file and content approval.
