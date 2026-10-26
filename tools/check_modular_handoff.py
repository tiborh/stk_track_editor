"""Run in background Blender to check both examples and export separate refinements."""

import argparse
from pathlib import Path
import sys

import addon_utils
import bpy

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "tools"))
from build_modular_track import validate_export
from track_layout import load_layout
from track_licenses import read_notice, write_notice

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--exporter-root", type=Path, default=root / "vendor/stk-blender")
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
sys.path.insert(0, str(args.exporter_root.resolve()))
for module in ("io_scene_spm", "io_antarctica_scene"):
    addon_utils.enable(module, default_set=True)

for name in ("oval", "bends"):
    circuit = load_layout(root / f"track/layouts/{name}.json")
    source = root / "track/modular" / circuit.track_id
    bpy.ops.wm.open_mainfile(filepath=str(source / f"{circuit.track_id}.blend"))
    roads = [obj for obj in bpy.data.objects if "module_id" in obj]
    assert len(roads) == len(circuit.modules)
    assert {obj["module_id"] for obj in roads} == {module[0].tile_id for module in circuit.modules}
    for obj in roads:
        assert all(face.normal.z > 0.99 for face in obj.data.polygons)
        assert all(face.area > 0 for face in obj.data.polygons)
    for image in bpy.data.images:
        if image.filepath:
            assert image.filepath.startswith("//textures/"), image.filepath
            assert Path(bpy.path.abspath(image.filepath)).is_file(), image.filepath
            image.reload()
            assert len(image.pixels) == image.size[0] * image.size[1] * 4 > 0
            assert image.has_data
    for group in ("Road and markings", "Landscape and barriers", "Gameplay", "Lighting"):
        assert group in bpy.data.collections
    assert bpy.context.scene["layout_source"] == "//layout.json"
    assert (source / "layout.json").is_file()
    assert any(image.name == "Track preview" and image.use_fake_user
               for image in bpy.data.images)
    print(f"SCENE_OK: {circuit.track_id}", flush=True)
    assets = root / "build/modular-playtest/refinement"
    output = assets / "tracks" / circuit.track_id
    output.mkdir(parents=True, exist_ok=True)
    prefs = bpy.context.preferences.addons["io_antarctica_scene"].preferences
    prefs.stk_assets_path = str(assets)
    prefs.stk_export_images = True
    prefs.stk_delete_old_files_on_export = False
    prefs.stk_check_tex_analyse = False
    bpy.ops.mesh.primitive_cube_add(size=1, location=(20, -10, 0.5))
    marker = bpy.context.object
    marker.name = "Hand-edited roadside marker"
    marker.data.materials.append(bpy.data.materials["modular_white"])
    working = assets / "source" / circuit.track_id
    working.mkdir(parents=True, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(working / f"{circuit.track_id}.blend"))
    assert bpy.ops.screen.stk_track_export(filepath=str(output / circuit.track_id)) == {"FINISHED"}
    write_notice(read_notice(source / "licenses.txt"), working, output)
    assert (output / "licenses.txt").read_bytes() == (source / "licenses.txt").read_bytes()
    validate_export(output, circuit)
    print(f"REFINEMENT_EXPORT_OK: {circuit.track_id}", flush=True)
