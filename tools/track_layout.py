"""Validate flat modular circuits and sample their roads without Blender."""

import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re


DIRECTIONS = {"north": (0, 1), "east": (1, 0),
              "south": (0, -1), "west": (-1, 0)}
PICKUP_KINDS = ("item", "nitro_small", "nitro_big")
MAX_PICKUPS = 2000
PICKUP_MARGIN = 2.0


@dataclass(frozen=True)
class Tile:
    id: str
    kind: str
    x: int
    y: int
    rotation: int

    def rotate(self, x, y):
        for _ in range(self.rotation // 90):
            x, y = y, -x
        return x, y

    @property
    def ports(self):
        end = (0, 1) if self.kind == "straight" else (1, 0)
        return (self.rotate(0, -1), self.rotate(*end))


@dataclass(frozen=True)
class Sample:
    x: float
    y: float
    tx: float
    ty: float
    tile_id: str

    def offset(self, lateral, height=0.0):
        return (self.x + self.ty * lateral, self.y - self.tx * lateral, height)


@dataclass(frozen=True)
class Pickup:
    id: str
    kind: str
    tile: str
    along: float
    lateral: float


@dataclass(frozen=True)
class PlacedPickup:
    pickup: Pickup
    position: tuple[float, float, float]


@dataclass(frozen=True)
class Circuit:
    track_id: str
    name: str
    cell_size: float
    road_width: float
    modules: tuple[tuple[Sample, ...], ...]
    route: tuple[Sample, ...]
    version: int = 1
    pickups: tuple[PlacedPickup, ...] = ()

    @property
    def length(self):
        return sum(math.hypot(b.x - a.x, b.y - a.y)
                   for a, b in zip(self.route, self.route[1:] + self.route[:1]))


def fields(value, required, location):
    if not isinstance(value, dict):
        raise ValueError(f"{location}: expected an object")
    missing, extra = set(required) - value.keys(), value.keys() - set(required)
    if missing or extra:
        raise ValueError(f"{location}: missing {sorted(missing)}, unknown {sorted(extra)}")


def number(value, location, minimum, maximum):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not minimum <= value <= maximum or not math.isfinite(value)):
        raise ValueError(f"{location}: expected a finite number in [{minimum}, {maximum}]")
    return float(value)


def road_sample(tile, cell_size, along):
    """Canonical port 0 -> port 1 frame, independent of race traversal."""
    if tile.kind == "straight":
        x, y, tx, ty = 0, (along - 0.5) * cell_size, 0, 1
    else:
        angle = math.pi - along * math.pi / 2
        radius = cell_size / 2
        x = radius * (1 + math.cos(angle))
        y = radius * (-1 + math.sin(angle))
        tx, ty = math.sin(angle), -math.cos(angle)
    x, y = tile.rotate(x, y)
    tx, ty = tile.rotate(tx, ty)
    return Sample(x + tile.x * cell_size, y + tile.y * cell_size, tx, ty, tile.id)


def sample_tile(tile, cell_size, forward):
    count = math.ceil(cell_size / 3)
    count += count % 2
    samples = [road_sample(tile, cell_size, i / count) for i in range(count + 1)]
    if not forward:
        samples = [Sample(s.x, s.y, -s.tx, -s.ty, s.tile_id)
                   for s in reversed(samples)]
    return tuple(samples)


def read_layout(data, *, draft=False):
    """Read shared layout structure, optionally allowing incomplete circuits."""
    if (not isinstance(data, dict) or type(data.get("version")) is not int
            or data["version"] not in (1, 2)):
        raise ValueError("version: only integer versions 1 and 2 are supported")
    required = ("version", "id", "name", "cell_size", "road_width", "start", "tiles")
    fields(data, required + (("pickups",) if data["version"] == 2 else ()), "layout")
    track_id = data["id"]
    if not isinstance(track_id, str) or not re.fullmatch(r"modular_[a-z0-9_]{1,40}", track_id):
        raise ValueError("id: use modular_ followed by 1-40 lowercase letters, digits or underscores")
    if (not isinstance(data["name"], str) or not data["name"].strip()
            or len(data["name"]) > 80
            or any(ord(c) < 32 for c in data["name"])):
        raise ValueError("name: expected 1-80 printable characters")
    cell_size = number(data["cell_size"], "cell_size", 60, 120)
    width = number(data["road_width"], "road_width", 10, 18)
    minimum = 0 if draft else 4
    if not isinstance(data["tiles"], list) or not minimum <= len(data["tiles"]) <= 900:
        raise ValueError(f"tiles: expected {minimum}-900 modules")
    tiles, positions = {}, {}
    for index, item in enumerate(data["tiles"]):
        location = f"tiles[{index}]"
        fields(item, ("id", "kind", "x", "y", "rotation"), location)
        tile_id = item["id"]
        if not isinstance(tile_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,39}", tile_id):
            raise ValueError(f"{location}.id: expected a lowercase module identifier")
        if tile_id in tiles:
            raise ValueError(f"{location}: duplicate module id {tile_id}")
        if item["kind"] not in ("straight", "corner"):
            raise ValueError(f"{location}.kind: only straight and corner are supported")
        for axis in ("x", "y"):
            if type(item[axis]) is not int or not -100 <= item[axis] <= 100:
                raise ValueError(f"{location}.{axis}: expected an integer in [-100, 100]")
        if type(item["rotation"]) is not int or item["rotation"] not in (0, 90, 180, 270):
            raise ValueError(f"{location}.rotation: use 0, 90, 180 or 270 clockwise degrees")
        tile = Tile(tile_id, item["kind"], item["x"], item["y"], item["rotation"])
        if (tile.x, tile.y) in positions:
            raise ValueError(f"{location}: occupied cell {(tile.x, tile.y)}")
        tiles[tile_id] = tile
        positions[tile.x, tile.y] = tile
    fields(data["start"], ("tile", "heading"), "start")
    start_id, heading = data["start"]["tile"], data["start"]["heading"]
    if not isinstance(start_id, str):
        raise ValueError("start.tile: expected a module identifier")
    if not isinstance(heading, str) or heading not in DIRECTIONS:
        raise ValueError("start.heading: use north, east, south or west")
    read_pickups(data, tiles, width)
    return track_id, data["name"], cell_size, width, tiles, positions, start_id, heading


def read_pickups(data, tiles, width):
    if data["version"] == 1:
        return ()
    items = data["pickups"]
    if not isinstance(items, list) or len(items) > MAX_PICKUPS:
        raise ValueError(f"pickups: expected 0-{MAX_PICKUPS} pickups")
    pickups, ids = [], set()
    for index, item in enumerate(items):
        location = f"pickups[{index}]"
        fields(item, ("id", "kind", "tile", "along", "lateral"), location)
        pickup_id = item["id"]
        if (not isinstance(pickup_id, str)
                or not re.fullmatch(r"[a-z][a-z0-9_]{0,39}", pickup_id)):
            raise ValueError(f"{location}.id: expected a lowercase pickup identifier")
        if pickup_id in ids:
            raise ValueError(f"{location}: duplicate pickup id {pickup_id}")
        ids.add(pickup_id)
        if item["kind"] not in PICKUP_KINDS:
            raise ValueError(f"{location}.kind: use item, nitro_small or nitro_big")
        if not isinstance(item["tile"], str) or item["tile"] not in tiles:
            raise ValueError(f"{location}.tile: must refer to an existing module")
        along = number(item["along"], f"{location}.along", 0, 1)
        limit = width / 2 - PICKUP_MARGIN
        lateral = number(item["lateral"], f"{location}.lateral", -limit, limit)
        pickups.append(Pickup(pickup_id, item["kind"], item["tile"], along, lateral))
    return tuple(pickups)


def parse_layout(data):
    track_id, name, cell_size, width, tiles, positions, start_id, heading = read_layout(data)
    if start_id not in tiles:
        raise ValueError("start.tile: must refer to an existing module")
    start, direction = tiles[start_id], DIRECTIONS[heading]
    if start.kind != "straight" or direction not in start.ports:
        raise ValueError("start: must be on a straight aligned with the heading")
    for tile in tiles.values():
        for dx, dy in tile.ports:
            neighbour = positions.get((tile.x + dx, tile.y + dy))
            if neighbour is None or (-dx, -dy) not in neighbour.ports:
                raise ValueError(f"{tile.id}: unconnected port {(dx, dy)}")

    ordered, visited = [], set()
    current, exit_port = start, direction
    while current.id not in visited:
        visited.add(current.id)
        ordered.append(sample_tile(current, cell_size, exit_port == current.ports[1]))
        dx, dy = exit_port
        current = positions[current.x + dx, current.y + dy]
        incoming = (-dx, -dy)
        exit_port = next(port for port in current.ports if port != incoming)
    if current != start or exit_port != direction or len(visited) != len(tiles):
        raise ValueError("tiles: expected one connected closed circuit, not separate loops")

    origin = ordered[0][len(ordered[0]) // 2]

    def transform(sample):
        dx, dy = sample.x - origin.x, sample.y - origin.y
        return Sample(dx * origin.ty - dy * origin.tx,
                      dx * origin.tx + dy * origin.ty,
                      sample.tx * origin.ty - sample.ty * origin.tx,
                      sample.tx * origin.tx + sample.ty * origin.ty,
                      sample.tile_id)

    modules = tuple(tuple(transform(s) for s in module) for module in ordered)
    route = tuple(s for module in modules for s in module[:-1])
    midpoint = len(modules[0]) // 2
    route = route[midpoint:] + route[:midpoint]
    pickups = tuple(
        PlacedPickup(pickup, transform(
            road_sample(tiles[pickup.tile], cell_size, pickup.along)).offset(pickup.lateral))
        for pickup in read_pickups(data, tiles, width))
    return Circuit(track_id, name, cell_size, width, modules, route, data["version"], pickups)


def unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"JSON: duplicate key {key!r}")
        result[key] = value
    return result


def load_layout(path):
    return parse_layout(json.loads(Path(path).read_text(encoding="utf-8"),
                                   object_pairs_hook=unique_fields))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout", type=Path)
    args = parser.parse_args()
    try:
        circuit = load_layout(args.layout)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Layout error: {error}\n")
    print(f"{circuit.track_id}: {len(circuit.modules)} modules, "
          f"{circuit.length:.1f} m, {circuit.road_width:g} m wide, "
          f"{len(circuit.route)} connected route quads, {len(circuit.pickups)} pickups")


if __name__ == "__main__":
    main()
