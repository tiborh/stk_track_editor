"""Generate an editable Blender scene and STK export from a modular JSON circuit."""

import argparse
from datetime import datetime, timezone
import html
import math
from pathlib import Path
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET

import addon_utils
import bpy
from mathutils import Quaternion


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from build_track import material, mesh_object
from track_layout import load_layout
from track_licenses import read_notice, write_notice


def ribbon(name, samples, lower, upper, height, mat):
    vertices = [s.offset(offset, height) for s in samples for offset in (lower, upper)]
    faces = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2)
             for i in range(len(samples) - 1)]
    return mesh_object(name, vertices, faces, mat)


def collection(name):
    group = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(group)
    bpy.context.view_layer.active_layer_collection = (
        bpy.context.view_layer.layer_collection.children[group.name])


def barriers(circuit, red, white):
    samples = circuit.route + circuit.route[:1]
    for side in (-1, 1):
        centre = side * (circuit.road_width / 2 + 0.25)
        vertices = [s.offset(offset, z) for s in samples
                    for offset, z in ((centre - 0.25, 0), (centre + 0.25, 0),
                                      (centre - 0.25, 1), (centre + 0.25, 1))]
        faces, distances = [], []
        distance = 0
        for i, (a, b) in enumerate(zip(samples, samples[1:])):
            first, next_first = 4 * i, 4 * (i + 1)
            faces.extend(((first, next_first, next_first + 2, first + 2),
                          (first + 1, first + 3, next_first + 3, next_first + 1),
                          (first + 2, next_first + 2, next_first + 3, first + 3)))
            distances.extend([int(distance / 8) % 2] * 3)
            distance += math.hypot(b.x - a.x, b.y - a.y)
        obj = mesh_object("Left barrier" if side < 0 else "Right barrier",
                          vertices, faces, red)
        obj.data.materials.append(white)
        for face, index in zip(obj.data.polygons, distances):
            face.material_index = index


def markings(circuit, white, red, asphalt):
    distance, next_post = 0, 0
    samples = circuit.route + circuit.route[:1]
    for i, (a, b) in enumerate(zip(samples, samples[1:])):
        if int(distance / 4.5) % 2 == 0:
            ribbon(f"Centre dash {i:03}", (a, b), -0.12, 0.12, 0.015, white)
        if distance >= next_post:
            for side in (-1, 1):
                x, y, _ = a.offset(side * (circuit.road_width / 2 + 2.5))
                vertices = [(x + dx, y + dy, z) for z in (0, 2, 2.7)
                            for dx, dy in ((-0.2, -0.2), (0.2, -0.2),
                                           (0.2, 0.2), (-0.2, 0.2))]
                faces = [(8, 9, 10, 11)]
                for level in range(2):
                    for edge in range(4):
                        p, q = level * 4 + edge, level * 4 + (edge + 1) % 4
                        faces.append((p, q, q + 4, p + 4))
                post = mesh_object(f"Roadside post {i:03} {side}", vertices, faces, white)
                post.data.materials.append(red)
                for face in post.data.polygons:
                    face.material_index = int(face.index == 0 or face.index >= 5)
            next_post += 20
        distance += math.hypot(b.x - a.x, b.y - a.y)
    half = circuit.road_width / 2
    count = math.ceil(circuit.road_width)
    for i in range(count):
        x, end = -half + i * circuit.road_width / count, -half + (i + 1) * circuit.road_width / count
        for row in range(2):
            y = (row - 1) * 0.6
            mesh_object(f"Finish tile {i}-{row}",
                        [(x, y, 0.02), (end, y, 0.02),
                         (end, y + 0.6, 0.02), (x, y + 0.6, 0.02)],
                        [(0, 1, 2, 3)], white if (i + row) % 2 else asphalt)


def gameplay(circuit):
    samples = circuit.route
    half = circuit.road_width / 2
    vertices = [s.offset(offset) for s in samples for offset in (-half, half)]
    count = len(samples)
    vertices.extend([(-half, -1, 0), (half, -1, 0)])
    route = mesh_object("Main driveline", vertices,
                        [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2)
                         for i in range(count - 1)],
                        edges=[(2 * count, 0), (2 * count + 1, 1)])
    route["type"] = "MAIN-DRIVELINE"
    route["activate"] = "quarter"
    route["strict_lapline"] = "false"
    route.display_type = "WIRE"
    distance, index = 0, 1
    length = circuit.length
    names = ("quarter", "half", "three_quarters", "lap")
    for a, b in zip(samples, samples[1:] + samples[:1]):
        distance += math.hypot(b.x - a.x, b.y - a.y)
        if index <= 3 and distance >= length * index / 4:
            check = mesh_object(names[index - 1],
                                [b.offset(-half - 1), b.offset(half + 1)], [],
                                edges=[(0, 1)])
            check["type"] = "check"
            check["name"] = names[index - 1]
            check["activate"] = names[index]
            index += 1
    for placed in circuit.pickups:
        pickup = placed.pickup
        obj = bpy.data.objects.new(f"Pickup {pickup.id}", None)
        bpy.context.collection.objects.link(obj)
        obj.location = placed.position
        obj.location.z += 1
        obj.empty_display_type = "CUBE" if pickup.kind == "item" else "CONE"
        obj.empty_display_size = 0.7
        obj["type"] = pickup.kind
        obj["dropitem"] = "true"
        obj["pickup_id"] = pickup.id
        obj["module_id"] = pickup.tile
        obj["along"] = pickup.along
        obj["lateral"] = pickup.lateral


def preview(circuit, path):
    size = 256
    samples = circuit.route + circuit.route[:1]
    margin = circuit.road_width
    xmin = min(s.x for s in samples) - margin
    ymin = min(s.y for s in samples) - margin
    xmax = max(s.x for s in samples) + margin
    ymax = max(s.y for s in samples) + margin
    scale = (size - 12) / max(xmax - xmin, ymax - ymin)
    cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
    pixels = [0.20, 0.42, 0.12, 1] * (size * size)
    for extra, color in ((0.7, (0.95, 0.95, 0.95, 1)),
                         (0, (0.22, 0.24, 0.27, 1))):
        radius = (circuit.road_width / 2 + extra) * scale
        for a, b in zip(samples, samples[1:]):
            steps = max(1, math.ceil(math.hypot(b.x - a.x, b.y - a.y) * scale))
            for i in range(steps + 1):
                t = i / steps
                x = (a.x + t * (b.x - a.x) - cx) * scale + size / 2
                y = (a.y + t * (b.y - a.y) - cy) * scale + size / 2
                for py in range(max(0, int(y - radius)), min(size, math.ceil(y + radius))):
                    for px in range(max(0, int(x - radius)), min(size, math.ceil(x + radius))):
                        if (px - x) ** 2 + (py - y) ** 2 <= radius ** 2:
                            offset = 4 * (py * size + px)
                            pixels[offset:offset + 4] = color
    image = bpy.data.images.new("Track preview", width=size, height=size)
    image.use_fake_user = True
    image.pixels[:] = pixels
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()


def validate_export(output, circuit):
    for name in ("track.xml", "scene.xml", "quads.xml", "graph.xml", "materials.xml",
                 f"{circuit.track_id}_track.spm", "screenshot.png",
                 "modular_asphalt.png", "modular_grass.png",
                 "modular_white.png", "modular_red.png"):
        path = output / name
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"Missing or empty export: {path}")
        if path.suffix == ".xml":
            ET.parse(path)
    quads = ET.parse(output / "quads.xml").getroot().findall("quad")
    if len(quads) != len(circuit.route):
        raise RuntimeError(f"Expected {len(circuit.route)} route quads, got {len(quads)}")
    checks = ET.parse(output / "scene.xml").getroot().find("checks")
    if checks is None or len(checks) != 4:
        raise RuntimeError("Expected a lap line and three linked checkpoints")
    for index, check in enumerate(checks):
        if check.get("other-ids") != str((index + 1) % 4):
            raise RuntimeError(f"Broken checkpoint chain at {index}")
    scene = ET.parse(output / "scene.xml").getroot()
    tags = {"item": "item", "nitro_small": "small-nitro", "nitro_big": "big-nitro"}
    exported = [node for node in scene if node.tag in tags.values()]
    if len(exported) != len(circuit.pickups):
        raise RuntimeError(f"Expected {len(circuit.pickups)} exported pickups, got {len(exported)}")
    for placed in circuit.pickups:
        matches = [node for node in exported if node.get("id") == f"Pickup {placed.pickup.id}"]
        if len(matches) != 1 or matches[0].tag != tags[placed.pickup.kind]:
            raise RuntimeError(f"Missing or wrong pickup: {placed.pickup.id}")
        node = matches[0]
        x, y, z = placed.position
        expected = (x, z + 1, y)
        if node.get("drop", "true") != "true" or any(
                abs(float(node.get(axis, "nan")) - value) > 0.011
                or not math.isfinite(float(node.get(axis, "nan")))
                for axis, value in zip(("x", "y", "z"), expected)):
            raise RuntimeError(f"Incorrect pickup position/drop: {placed.pickup.id}")
    materials = ET.parse(output / "materials.xml").getroot()
    for entry in materials.findall("material"):
        name = entry.get("name")
        if name is None or not (output / name).is_file():
            raise RuntimeError(f"Missing material texture: {name}")


def build(circuit, source, assets, exporter_root, license_notice=None):
    for module in ("io_scene_spm", "io_antarctica_scene"):
        if not (exporter_root / module / "__init__.py").is_file():
            raise FileNotFoundError(f"Exporter module not found: {exporter_root / module}")
    sys.path.insert(0, str(exporter_root.resolve()))
    for module in ("io_scene_spm", "io_antarctica_scene"):
        addon_utils.enable(module, default_set=True)
        if not addon_utils.check(module)[1]:
            raise RuntimeError(f"Cannot enable Blender add-on {module}")
    textures = source / "textures"
    textures.mkdir()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    for key, value in {
        "is_stk_track": "true", "track_version": 7, "code": circuit.track_id,
        "name": html.escape(circuit.name, quote=True), "designer": "Modular track prototype",
        "groups": "standard", "default_num_laps": 3, "reverse": "false",
        "music": "kart_grand_prix.music", "screenshot": "screenshot.png",
        "sky_color": "145 195 235", "start_karts_per_row": 2,
        "start_forwards_distance": 2.5, "start_sidewards_distance": 3.0,
        "start_upwards_distance": 0.2,
    }.items():
        scene[key] = value
    scene["layout_version"] = circuit.version
    scene["layout_source"] = "//layout.json"
    prefs = bpy.context.preferences.addons["io_antarctica_scene"].preferences
    prefs.stk_assets_path = str(assets)
    prefs.stk_export_images = True
    prefs.stk_delete_old_files_on_export = False
    prefs.stk_check_tex_analyse = False
    asphalt = material("modular_asphalt", (0.22, 0.24, 0.27, 1), textures, grain=0.08)
    grass = material("modular_grass", (0.20, 0.42, 0.12, 1), textures, grain=0.06)
    white = material("modular_white", (0.95, 0.95, 0.95, 1), textures)
    red = material("modular_red", (0.75, 0.06, 0.03, 1), textures)
    half = circuit.road_width / 2
    collection("Road and markings")
    for module in circuit.modules:
        obj = ribbon(f"Road {module[0].tile_id}", module, -half, half, 0, asphalt)
        obj["module_id"] = module[0].tile_id
        for side in (-1, 1):
            offset = side * (half - 0.4)
            ribbon(f"Edge stripe {module[0].tile_id} {side}", module,
                   offset - 0.12, offset + 0.12, 0.015, white)
    xs, ys = [s.x for s in circuit.route], [s.y for s in circuit.route]
    xmin, xmax, ymin, ymax = min(xs) - 25, max(xs) + 25, min(ys) - 25, max(ys) + 25
    markings(circuit, white, red, asphalt)
    collection("Landscape and barriers")
    mesh_object("Grass", [(xmin, ymin, -0.08), (xmax, ymin, -0.08),
                          (xmax, ymax, -0.08), (xmin, ymax, -0.08)],
                [(0, 1, 2, 3)], grass)
    barriers(circuit, red, white)
    collection("Gameplay")
    gameplay(circuit)
    collection("Lighting")
    light = bpy.data.lights.new("Sun", "SUN")
    sun = bpy.data.objects.new("Sun", light)
    scene.collection.objects.link(sun)
    sun.location = (40, -30, 80)
    sun["type"], sun["ambient"], sun["color"] = "SUN", "150 150 150", "255 245 225"
    light.energy = 2
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.region_3d.view_location = ((xmin + xmax) / 2, (ymin + ymax) / 2, 0)
                area.spaces.active.region_3d.view_distance = max(xmax - xmin, ymax - ymin)
                area.spaces.active.region_3d.view_rotation = Quaternion((1, 0, 0, 0))
                area.spaces.active.region_3d.view_perspective = "ORTHO"
                area.spaces.active.shading.color_type = "MATERIAL"
    preview(circuit, textures / "screenshot.png")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(source / f"{circuit.track_id}.blend"))
    output = assets / "tracks" / circuit.track_id
    output.mkdir(parents=True)
    result = bpy.ops.screen.stk_track_export(filepath=str(output / circuit.track_id))
    if result != {"FINISHED"}:
        raise RuntimeError(f"Track export failed: {result}")
    write_notice(license_notice, source, output)
    validate_export(output, circuit)
    for image in bpy.data.images:
        if image.filepath:
            image.filepath = "//textures/" + Path(image.filepath).name
    bpy.ops.wm.save_as_mainfile(filepath=str(source / f"{circuit.track_id}.blend"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout", type=Path)
    parser.add_argument("--exporter-root", type=Path,
                        default=ROOT / "vendor/stk-blender")
    parser.add_argument("--license-file", type=Path,
                        help="Track attribution notice; defaults to <layout>.licenses.txt.")
    parser.add_argument("--replace-generated", action="store_true",
                        help="Back up existing source/export folders before replacing them.")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    circuit = load_layout(args.layout)
    notice = read_notice(args.layout.with_suffix(".licenses.txt"), args.license_file)
    source = ROOT / "track/modular" / circuit.track_id
    output = ROOT / "build/tracks" / circuit.track_id
    if (source.exists() or output.exists()) and not args.replace_generated:
        parser.error("Generated output already exists. Preserve manual edits separately; "
                     "use --replace-generated to back up and rebuild.")
    source.parent.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".modular-", dir=source.parent) as source_temp:
        with tempfile.TemporaryDirectory(prefix=".modular-", dir=ROOT / "build") as export_temp:
            staged_source, staged_assets = Path(source_temp), Path(export_temp)
            # Build inside a child so the temporary-directory owner remains in place.
            staged_source = staged_source / circuit.track_id
            staged_source.mkdir()
            shutil.copyfile(args.layout, staged_source / "layout.json")
            build(circuit, staged_source, staged_assets, args.exporter_root, notice)
            if source.exists() or output.exists():
                stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
                backup = ROOT / "build/modular-backups" / circuit.track_id / stamp
                backup.mkdir(parents=True)
                for old, name in ((source, "source"), (output, "export")):
                    if old.exists():
                        old.rename(backup / name)
                print(f"PREVIOUS_BUILD: {backup}")
            staged_source.rename(source)
            (staged_assets / "tracks" / circuit.track_id).rename(output)
    print(f"TRACK_READY: {output}")
    print(f"BLENDER_SOURCE: {source / (circuit.track_id + '.blend')}")
    print(f"LAYOUT: {len(circuit.modules)} modules, {circuit.length:.1f} m")


if __name__ == "__main__":
    main()
