"""Run with blender --background --factory-startup --python-exit-code 1 --python tools/build_track.py."""

import argparse
import math
from pathlib import Path
import random
import sys
import xml.etree.ElementTree as ET

import addon_utils
import bpy
from mathutils import Quaternion


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from track_licenses import read_notice, write_notice


TRACK_ID = "llm_loop"
SEGMENTS = 128
RADIUS = 45.0
HALF_WIDTH = 7.0


def point(radius, angle, height=0.0):
    return (radius * math.cos(angle) - RADIUS, radius * math.sin(angle), height)


def mesh_object(name, vertices, faces, material=None, edges=()):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, edges, faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if material is not None:
        mesh.materials.append(material)
        uv = mesh.uv_layers.new(name="UVMap")
        for loop in mesh.loops:
            co = mesh.vertices[loop.vertex_index].co
            uv.data[loop.index].uv = (co.x / 8.0, co.y / 8.0)
    return obj


def material(name, color, texture_dir, grain=0.0):
    image = bpy.data.images.new(name + ".png", width=64, height=64)
    rng = random.Random(0)
    pixels = []
    for _ in range(64 * 64):
        shade = rng.uniform(-grain, grain)
        pixels.extend([max(0, min(1, channel + shade)) for channel in color[:3]])
        pixels.append(color[3])
    image.pixels[:] = pixels
    image.filepath_raw = str(texture_dir / (name + ".png"))
    image.file_format = "PNG"
    image.save()
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = color
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = 0.9
    texture = mat.node_tree.nodes.new("ShaderNodeTexImage")
    texture.image = image
    mat.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    return mat


def ring(name, inner, outer, height, mat):
    vertices = [
        point(radius, math.tau * i / SEGMENTS, height)
        for i in range(SEGMENTS)
        for radius in (inner, outer)
    ]
    faces = [
        (2 * i, 2 * i + 1, 2 * ((i + 1) % SEGMENTS) + 1,
         2 * ((i + 1) % SEGMENTS))
        for i in range(SEGMENTS)
    ]
    return mesh_object(name, vertices, faces, mat)


def wall(name, radius, mat, stripe_mat):
    inner, outer = radius - 0.25, radius + 0.25
    vertices = [
        point(r, math.tau * i / SEGMENTS, z)
        for i in range(SEGMENTS)
        for r, z in ((inner, 0), (outer, 0), (inner, 1), (outer, 1))
    ]
    faces = []
    for i in range(SEGMENTS):
        a, b = 4 * i, 4 * ((i + 1) % SEGMENTS)
        faces.extend(((a, b, b + 2, a + 2),
                      (a + 1, a + 3, b + 3, b + 1),
                      (a + 2, b + 2, b + 3, a + 3)))
    obj = mesh_object(name, vertices, faces, mat)
    obj.data.materials.append(stripe_mat)
    for face in obj.data.polygons:
        face.material_index = (face.index // 6) % 2
    return obj


def motion_markers(white, red):
    vertices, faces = [], []
    for i in range(0, SEGMENTS, 4):
        start = len(vertices)
        for j in range(3):
            angle = math.tau * (i + j) / SEGMENTS
            vertices.extend(point(radius, angle, 0.015)
                            for radius in (RADIUS - 0.12, RADIUS + 0.12))
        faces.extend((start + 2 * j, start + 2 * j + 1,
                      start + 2 * j + 3, start + 2 * j + 2) for j in range(2))
    mesh_object("Dashed centre line", vertices, faces, white)
    for i in range(24):
        x, y, _ = point(RADIUS + HALF_WIDTH + 2.5, math.tau * i / 24)
        vertices = [(x + dx, y + dy, z)
                    for z in (0, 2.0, 2.7)
                    for dx, dy in ((-0.2, -0.2), (0.2, -0.2),
                                   (0.2, 0.2), (-0.2, 0.2))]
        faces = [(8, 9, 10, 11)]
        for level in range(2):
            for side in range(4):
                a, b = level * 4 + side, level * 4 + (side + 1) % 4
                faces.append((a, b, b + 4, a + 4))
        post = mesh_object(f"Roadside post {i + 1:02}", vertices, faces, white)
        post.data.materials.append(red)
        for face in post.data.polygons:
            face.material_index = int(face.index == 0 or face.index >= 5)


def preview(path):
    size = 256
    image = bpy.data.images.new("Track preview", width=size, height=size)
    pixels = []
    for y in range(size):
        for x in range(size):
            dx, dy = (x - size / 2) / 2, (y - size / 2) / 2
            radius = math.hypot(dx, dy)
            angle = math.atan2(dy, dx) % math.tau
            color = (0.20, 0.42, 0.12, 1)
            if RADIUS - HALF_WIDTH <= radius <= RADIUS + HALF_WIDTH:
                color = (0.22, 0.24, 0.27, 1)
                if abs(radius - RADIUS) < 0.4 and int(angle / math.tau * SEGMENTS) % 4 < 2:
                    color = (0.95, 0.95, 0.95, 1)
                if abs(dy) < 0.8 and dx > 0:
                    color = (0.95, 0.95, 0.95, 1)
            if abs(abs(radius - RADIUS) - HALF_WIDTH) < 0.6:
                color = ((0.75, 0.06, 0.03, 1) if int(angle / math.tau * SEGMENTS) % 4 < 2
                         else (0.95, 0.95, 0.95, 1))
            pixels.extend(color)
    image.pixels[:] = pixels
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()


def validate_export(output):
    for filename in ("track.xml", "scene.xml", "quads.xml", "graph.xml",
                     "materials.xml", f"{TRACK_ID}_track.spm", "screenshot.png"):
        path = output / filename
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"Missing or empty export: {path}")
        if path.suffix == ".xml":
            ET.parse(path)
    quads = ET.parse(output / "quads.xml").getroot().findall("quad")
    if len(quads) != SEGMENTS:
        raise RuntimeError(f"Expected {SEGMENTS} route quads, got {len(quads)}")
    checks = ET.parse(output / "scene.xml").getroot().find("checks")
    if checks is None or len(checks) != 4:
        raise RuntimeError("Expected a lap line and three linked checkpoints")
    for index, check in enumerate(checks):
        if check.get("other-ids") != str((index + 1) % 4):
            raise RuntimeError(f"Broken checkpoint chain at index {index}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exporter-root", type=Path,
                        default=ROOT / "vendor/stk-blender")
    parser.add_argument("--license-file", type=Path,
                        help="Override track/llm_loop.licenses.txt attribution notice.")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    notice = read_notice(ROOT / "track/llm_loop.licenses.txt", args.license_file)
    for module in ("io_scene_spm", "io_antarctica_scene"):
        if not (args.exporter_root / module / "__init__.py").is_file():
            raise FileNotFoundError(f"Exporter module not found: {args.exporter_root / module}")
    sys.path.insert(0, str(args.exporter_root.resolve()))
    for module in ("io_scene_spm", "io_antarctica_scene"):
        addon_utils.enable(module, default_set=True)
        if not addon_utils.check(module)[1]:
            raise RuntimeError(f"Cannot enable Blender add-on {module}")

    source = ROOT / "track"
    output = ROOT / "build/tracks" / TRACK_ID
    textures = source / "textures"
    textures.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    for key, value in {
        "is_stk_track": "true", "track_version": 7, "code": TRACK_ID,
        "name": "First Circle", "designer": "Procedural test track",
        "groups": "standard", "default_num_laps": 3, "reverse": "false",
        "music": "kart_grand_prix.music", "screenshot": "screenshot.png",
        "sky_color": "145 195 235", "start_karts_per_row": 2,
        "start_forwards_distance": 2.5, "start_sidewards_distance": 3.0,
        "start_upwards_distance": 0.2,
    }.items():
        scene[key] = value
    prefs = bpy.context.preferences.addons["io_antarctica_scene"].preferences
    prefs.stk_assets_path = str(ROOT / "build")
    prefs.stk_export_images = True
    prefs.stk_delete_old_files_on_export = False
    prefs.stk_check_tex_analyse = False

    asphalt = material("circle_asphalt", (0.22, 0.24, 0.27, 1), textures, grain=0.08)
    grass = material("circle_grass", (0.20, 0.42, 0.12, 1), textures, grain=0.06)
    white = material("circle_white", (0.95, 0.95, 0.95, 1), textures)
    red = material("circle_red", (0.75, 0.06, 0.03, 1), textures)
    mesh_object("Grass", [(-115, -70, -0.08), (25, -70, -0.08),
                          (25, 70, -0.08), (-115, 70, -0.08)],
                [(0, 1, 2, 3)], grass)
    ring("Road", RADIUS - HALF_WIDTH, RADIUS + HALF_WIDTH, 0, asphalt)
    for radius in (RADIUS - HALF_WIDTH + 0.4, RADIUS + HALF_WIDTH - 0.4):
        ring("Edge stripe", radius - 0.12, radius + 0.12, 0.015, white)
    wall("Inner barrier", RADIUS - HALF_WIDTH - 0.25, red, white)
    wall("Outer barrier", RADIUS + HALF_WIDTH + 0.25, red, white)
    motion_markers(white, red)
    for i in range(14):
        for j in range(2):
            x, y = i - HALF_WIDTH, (j - 1) * 0.6
            mesh_object(f"Finish tile {i}-{j}",
                        [(x, y, 0.02), (x + 1, y, 0.02),
                         (x + 1, y + 0.6, 0.02), (x, y + 0.6, 0.02)],
                        [(0, 1, 2, 3)], white if (i + j) % 2 else asphalt)

    route_vertices = [
        point(radius, math.tau * i / SEGMENTS, 0)
        for i in range(SEGMENTS)
        for radius in (RADIUS - HALF_WIDTH, RADIUS + HALF_WIDTH)
    ]
    # Leave the final quad open; the exporter closes the route automatically.
    route_faces = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2)
                   for i in range(SEGMENTS - 1)]
    route_vertices.extend([(-HALF_WIDTH, -1, 0), (HALF_WIDTH, -1, 0)])
    route = mesh_object("Main driveline", route_vertices, route_faces,
                        edges=[(2 * SEGMENTS, 0), (2 * SEGMENTS + 1, 1)])
    route["type"] = "MAIN-DRIVELINE"
    route["activate"] = "quarter"
    route["strict_lapline"] = "false"
    route.display_type = "WIRE"
    for index, name in enumerate(("quarter", "half", "three_quarters"), 1):
        angle = math.tau * index / 4
        check = mesh_object(name, [point(RADIUS - HALF_WIDTH, angle),
                                  point(RADIUS + HALF_WIDTH, angle)],
                            [], edges=[(0, 1)])
        check["type"] = "check"
        check["name"] = name
        check["activate"] = ("half", "three_quarters", "lap")[index - 1]

    light = bpy.data.lights.new("Sun", "SUN")
    sun = bpy.data.objects.new("Sun", light)
    scene.collection.objects.link(sun)
    sun.location = (40, -30, 80)
    sun["type"] = "SUN"
    sun["ambient"] = "150 150 150"
    sun["color"] = "255 245 225"
    light.energy = 2
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.region_3d.view_location = (-RADIUS, 0, 0)
                area.spaces.active.region_3d.view_distance = 150
                area.spaces.active.region_3d.view_rotation = Quaternion((1, 0, 0, 0))
                area.spaces.active.region_3d.view_perspective = "ORTHO"
                area.spaces.active.shading.color_type = "MATERIAL"
    preview(textures / "screenshot.png")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(source / "loop.blend"))
    result = bpy.ops.screen.stk_track_export(filepath=str(output / TRACK_ID))
    if result != {"FINISHED"}:
        raise RuntimeError(f"Track export failed: {result}")
    write_notice(notice, output)
    validate_export(output)
    print(f"TRACK_READY: {output}")
    print(f"BLENDER_SOURCE: {source / 'loop.blend'}")


if __name__ == "__main__":
    main()
