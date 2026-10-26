#!/usr/bin/env python3
"""Read-only inventory for the LLM-assisted SuperTuxKart track workflow."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


MODULES = ("io_scene_spm", "io_antarctica_scene")
FLATPAK_APPS = {
    "Blender": "org.blender.Blender",
    "SuperTuxKart": "net.supertuxkart.SuperTuxKart",
}
PROBE_MARKER = "STK_DIAGNOSTIC_JSON="
PROBE_CODE = """
import bpy, addon_utils, json
mesh = bpy.data.meshes.new("stk_diagnostic")
mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
assert len(mesh.polygons) == 1, "Mesh creation failed"
bpy.data.meshes.remove(mesh)
print("STK_DIAGNOSTIC_JSON=" + json.dumps({
    "version": bpy.app.version_string,
    "addon_paths": list(addon_utils.paths()),
}))
"""


class Report:
    def __init__(self):
        self.failed = False

    def emit(self, status, name, detail):
        print(f"[{status}] {name}: {detail}")
        if status in ("MISSING", "ERROR"):
            self.failed = True


def absolute_path(value):
    return Path(value).expanduser().absolute()


def xdg_path(variable, fallback):
    value = os.environ.get(variable)
    if value and Path(value).is_absolute():
        return Path(value)
    return Path.home() / fallback


def run_command(command, timeout):
    return subprocess.run(
        command, capture_output=True, text=True, errors="replace",
        timeout=timeout, check=False,
    )


def get_flatpak_apps(report):
    if not shutil.which("flatpak"):
        return set()
    try:
        result = run_command(
            ["flatpak", "list", "--app", "--columns=application"], 20
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        report.emit("ERROR", "Flatpak inventory", str(error))
        return set()
    if result.returncode:
        report.emit(
            "ERROR", "Flatpak inventory",
            result.stderr.strip() or f"exit {result.returncode}",
        )
        return set()
    return set(result.stdout.splitlines())


def probe_blender(binary, timeout, report):
    try:
        result = run_command(
            [binary, "--background", "--factory-startup", "--disable-autoexec",
             "--python-exit-code", "1", "--python-expr", PROBE_CODE],
            timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        report.emit("ERROR", "Blender probe", str(error))
        return None
    if result.returncode:
        output = (result.stdout + "\n" + result.stderr).strip()
        report.emit(
            "ERROR", "Blender probe",
            f"exit {result.returncode}\n{output[-6000:]}",
        )
        return None
    for line in result.stdout.splitlines():
        if line.startswith(PROBE_MARKER):
            try:
                data = json.loads(line[len(PROBE_MARKER):])
                if (
                    not isinstance(data, dict)
                    or not isinstance(data.get("version"), str)
                    or not isinstance(data.get("addon_paths"), list)
                    or not all(isinstance(p, str) for p in data["addon_paths"])
                ):
                    raise ValueError("unexpected probe data shape")
            except (ValueError, TypeError) as error:
                report.emit("ERROR", "Blender probe", str(error))
                return None
            report.emit("OK", "Headless Blender", f'{data["version"]}; mesh API works')
            if result.stderr.strip():
                report.emit("WARN", "Blender stderr", result.stderr.strip()[-3000:])
            return [Path(path) for path in data["addon_paths"]]
    report.emit(
        "ERROR", "Blender probe",
        "No structured result returned.\n" + result.stdout[-3000:],
    )
    return None


def addon_candidates(config_home, binary):
    roots = [
        config_home / "blender",
        Path.home() / ".var/app/org.blender.Blender/config/blender",
        Path("/usr/share/blender"),
        Path("/usr/local/share/blender"),
    ]
    if binary:
        roots.append(Path(binary).resolve().parent)
    candidates = []
    for root in roots:
        if root.is_dir():
            for version in sorted(root.iterdir()):
                if version.is_dir() and re.fullmatch(r"\d+\.\d+", version.name):
                    candidates.extend([
                        version / "scripts/addons",
                        version / "scripts/addons_core",
                    ])
    for variable in ("BLENDER_USER_SCRIPTS", "BLENDER_SYSTEM_SCRIPTS"):
        if os.environ.get(variable):
            candidates.append(absolute_path(os.environ[variable]) / "addons")
    return list(dict.fromkeys(candidates))


def inspect_exporters(paths, source_root, probed, report):
    for module in MODULES:
        installed = [path / module for path in paths
                     if (path / module / "__init__.py").is_file()]
        source = source_root / module if source_root else None
        if installed:
            label = "probe search path" if probed else "candidate path; may be another version"
            report.emit("OK", module, f"{label}: " + ", ".join(map(str, installed)))
        elif source and (source / "__init__.py").is_file():
            report.emit(
                "WARN", module,
                f"source found at {source}; installation/explicit loading still needed",
            )
        else:
            report.emit(
                "MISSING", module,
                "not found in checked locations; obtain stk-blender or pass --exporter-root",
            )
    report.emit(
        "WARN", "Exporter compatibility",
        "files are not an activation/export test; verify both modules with the chosen Blender",
    )


def inspect_paths(paths, label, report, data=False):
    for path in dict.fromkeys(paths):
        if data:
            usable = (path / "tracks").is_dir() and (path / "textures").is_dir()
            detail = "tracks/ and textures/ found" if usable else "expected tracks/ and textures/ not found"
        else:
            usable = path.is_dir()
            detail = "directory exists" if usable else "directory absent; create only when installing"
        report.emit("OK" if usable else "WARN", label, f"{path} ({detail})")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blender", default="blender", help="Blender executable name or path")
    parser.add_argument("--stk-command", default="supertuxkart", help="Native game executable name or path")
    parser.add_argument("--exporter-root", type=absolute_path, help="stk-blender source checkout")
    parser.add_argument("--stk-data-dir", type=absolute_path, help="Game data root to inspect")
    parser.add_argument("--addons-dir", type=absolute_path, help="Destination containing custom track folders")
    parser.add_argument("--probe-blender", action="store_true", help="Run a background mesh/API probe (does not enable exporters)")
    parser.add_argument("--editor-only", action="store_true",
                        help="Check only prerequisites for the browser editor (no Blender/game needed)")
    parser.add_argument("--timeout", type=int, default=60, help="Blender probe timeout in seconds (default: 60)")
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if args.editor_only and args.probe_blender:
        parser.error("--editor-only and --probe-blender cannot be combined")

    report = Report()
    print("SuperTuxKart track development inventory (no installation or game launch)")
    print(f"Platform: {sys.platform}; Python: {sys.version.split()[0]}")
    report.emit("OK" if sys.version_info >= (3, 10) else "MISSING",
                "Python interpreter", f"{sys.executable} (Python 3.10+ required)")
    root = Path(__file__).resolve().parents[1]
    for name in ("tools/track_editor.py", "tools/track_layout.py", "editor/index.html",
                 "editor/editor.js", "editor/editor.css",
                 "track/layouts/oval.json", "track/layouts/bends.json",
                 "track/layouts/pickup_oval.json"):
        report.emit("OK" if (root / name).is_file() else "MISSING", "Editor file", name)
    if args.editor_only:
        print("\nResult: " + ("required gaps/errors found" if report.failed
                              else "editor prerequisites available; Blender/game checked separately"))
        return 1 if report.failed else 0
    config_home = xdg_path("XDG_CONFIG_HOME", ".config")
    data_home = xdg_path("XDG_DATA_HOME", ".local/share")
    for variable in ("XDG_CONFIG_HOME", "XDG_DATA_HOME"):
        if os.environ.get(variable) and not Path(os.environ[variable]).is_absolute():
            report.emit("WARN", variable, "relative value ignored per XDG specification")

    flatpaks = get_flatpak_apps(report)
    blender = shutil.which(args.blender)
    stk = shutil.which(args.stk_command)
    for name, executable, requested, default in (
        ("Blender", blender, args.blender, "blender"),
        ("SuperTuxKart", stk, args.stk_command, "supertuxkart"),
    ):
        if executable:
            report.emit("OK", name, executable)
        elif requested == default and FLATPAK_APPS[name] in flatpaks:
            report.emit("OK", name, f"Flatpak {FLATPAK_APPS[name]} (native command absent)")
        else:
            report.emit("MISSING", name, f"executable not found: {requested}")
    for command in ("git", "curl", "gimp", "krita", "inkscape"):
        location = shutil.which(command)
        report.emit("OK" if location else "WARN", f"Optional {command}", location or "not on PATH")

    paths = addon_candidates(config_home, blender)
    probed = False
    if args.probe_blender:
        if not blender:
            report.emit(
                "ERROR", "Blender probe",
                "requires a native/portable executable; use --blender (Flatpak wrapper not supported)",
            )
        else:
            discovered = probe_blender(blender, args.timeout, report)
            if discovered is not None:
                paths = discovered
                probed = True
    for path in paths:
        report.emit("OK" if path.is_dir() else "WARN", "Add-on search candidate", str(path))
    if not paths:
        report.emit("WARN", "Add-on search", "no versioned directory found; try --probe-blender")
    local_checkout = Path(__file__).resolve().parent.parent / "vendor/stk-blender"
    source_root = args.exporter_root or local_checkout
    if args.exporter_root and not args.exporter_root.is_dir():
        report.emit("ERROR", "Exporter source override", f"not a directory: {args.exporter_root}")
    inspect_exporters(paths, source_root, probed, report)

    data_paths = [args.stk_data_dir] if args.stk_data_dir else [
        Path("/usr/share/supertuxkart/data"),
        Path("/usr/share/games/supertuxkart/data"),
        Path("/usr/local/share/supertuxkart/data"),
    ]
    inspect_paths(data_paths, "Game data candidate", report, data=True)
    track_paths = [args.addons_dir] if args.addons_dir else [
        data_home / "supertuxkart/addons/tracks",
        Path.home() / ".var/app/net.supertuxkart.SuperTuxKart/data/supertuxkart/addons/tracks",
    ]
    inspect_paths(track_paths, "Local track destination candidate", report)
    report.emit(
        "WARN", "Manual checks",
        "confirm the active game data/user path, graphics, exporter activation, export, and a full race; "
        "Snap/custom sandbox layouts are not auto-detected",
    )
    print("\nResult: " + ("required gaps/errors found" if report.failed else "inventory complete; review warnings"))
    return 1 if report.failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except OSError as error:
        print(f"[ERROR] Filesystem inspection: {error}", file=sys.stderr)
        sys.exit(1)
