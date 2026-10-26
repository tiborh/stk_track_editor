"""Check the saved pickup scene and re-export it separately in background Blender."""

import argparse
from pathlib import Path
import sys

import addon_utils
import bpy


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_modular_track import validate_export
from track_layout import load_layout
from track_licenses import read_notice, write_notice

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--exporter-root", type=Path, default=ROOT / "vendor/stk-blender")
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
sys.path.insert(0, str(args.exporter_root.resolve()))
for module in ("io_scene_spm", "io_antarctica_scene"):
    addon_utils.enable(module, default_set=True)

circuit = load_layout(ROOT / "track/layouts/pickup_oval.json")
source = ROOT / "track/modular" / circuit.track_id
bpy.ops.wm.open_mainfile(filepath=str(source / f"{circuit.track_id}.blend"))
assert bpy.context.scene["layout_version"] == 2
assert bpy.context.scene["layout_source"] == "//layout.json"
objects = [obj for obj in bpy.data.objects if "pickup_id" in obj]
assert len(objects) == len(circuit.pickups)
for placed in circuit.pickups:
    pickup = placed.pickup
    obj = bpy.data.objects[f"Pickup {pickup.id}"]
    assert obj.type == "EMPTY"
    assert obj["type"] == pickup.kind
    assert obj["dropitem"] == "true"
    assert obj["module_id"] == pickup.tile
    assert obj["along"] == pickup.along
    assert obj["lateral"] == pickup.lateral
    x, y, z = placed.position
    assert all(abs(a - b) < 0.0001 for a, b in zip(obj.location, (x, y, z + 1)))
    assert obj.name in bpy.data.collections["Gameplay"].objects
for image in bpy.data.images:
    if image.filepath:
        assert image.filepath.startswith("//textures/"), image.filepath
        assert Path(bpy.path.abspath(image.filepath)).is_file(), image.filepath

assets = ROOT / "build/pickup-playtest/refinement"
output = assets / "tracks" / circuit.track_id
output.mkdir(parents=True, exist_ok=True)
prefs = bpy.context.preferences.addons["io_antarctica_scene"].preferences
prefs.stk_assets_path = str(assets)
prefs.stk_export_images = True
prefs.stk_delete_old_files_on_export = False
prefs.stk_check_tex_analyse = False
assert bpy.ops.screen.stk_track_export(filepath=str(output / circuit.track_id)) == {"FINISHED"}
write_notice(read_notice(source / "licenses.txt"), output)
assert (output / "licenses.txt").read_bytes() == (source / "licenses.txt").read_bytes()
validate_export(output, circuit)
print("PICKUP_HANDOFF_OK: saved editable empties re-export with matching kinds and positions")
