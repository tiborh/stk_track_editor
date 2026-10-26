const $ = (id) => document.getElementById(id);
const svgNS = "http://www.w3.org/2000/svg";
const fresh = () => ({
  version: 1, id: "modular_my_circuit", name: "My Circuit",
  cell_size: 90, road_width: 14, start: {tile: "", heading: "north"}, tiles: [],
});
let layout = fresh();
let tool = "straight";
let rotation = 0;
let undo = [];
let redo = [];
let saved = JSON.stringify(layout);
let revision = 0;
let validationTimer;
let fileOperation = 0;
let selectedPickup = "";
let view = {x: -5.5, y: -4.5, width: 12, height: 9};

function element(tag, attributes) {
  const node = document.createElementNS(svgNS, tag);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
  return node;
}

function notice(message = "") { $("notice").textContent = message; }
function dirty() { return JSON.stringify(layout) !== saved; }
function confirmDiscard() { return !dirty() || window.confirm("Discard unsaved layout changes?"); }

async function inspect(data) {
  const response = await fetch("/api/inspect", {
    method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || `Validation failed (${response.status}).`);
  }
  return response.json();
}

function drawDiagnostics(result) {
  $("status").textContent = result.message;
  $("status").dataset.valid = String(result.valid);
  $("ports").replaceChildren(...result.ports.map((port) => element("circle", {
    cx: port.x + port.dx * 0.5, cy: -port.y - port.dy * 0.5,
    r: 0.075, class: "port", "data-tile": port.tile,
  })));
  $("pickups").replaceChildren(...result.pickups.map((pickup) => {
    const marker = element(pickup.kind === "item" ? "rect" : "circle",
      pickup.kind === "item" ?
        {x: pickup.x - 0.07, y: -pickup.y - 0.07, width: 0.14, height: 0.14} :
        {cx: pickup.x, cy: -pickup.y, r: pickup.kind === "nitro_big" ? 0.09 : 0.065});
    marker.setAttribute("class", `pickup ${pickup.kind}`);
    marker.dataset.id = pickup.id;
    marker.dataset.selected = String(pickup.id === selectedPickup);
    const title = element("title", {});
    title.textContent = `${pickup.id}: ${pickup.kind}`;
    marker.append(title);
    marker.addEventListener("click", (event) => {
      event.stopPropagation();
      selectPickup(pickup.id);
    });
    return marker;
  }));
}

function scheduleValidation() {
  clearTimeout(validationTimer);
  const expected = ++revision;
  $("ports").replaceChildren();
  $("pickups").replaceChildren();
  $("status").textContent = "Checking layout...";
  $("status").dataset.valid = "false";
  const snapshot = structuredClone(layout);
  validationTimer = setTimeout(async () => {
    try {
      const result = await inspect(snapshot);
      if (revision === expected) drawDiagnostics(result);
    } catch (error) {
      if (revision === expected) {
        $("status").textContent = `Validation unavailable: ${error.message}. Keep the server running.`;
        $("status").dataset.valid = "false";
      }
    }
  }, 120);
}

function drawTile(tile, ghost = false) {
  const group = element("g", {
    transform: `translate(${tile.x} ${-tile.y}) rotate(${tile.rotation})`,
    "data-id": tile.id,
  });
  const d = tile.kind === "straight" ? "M 0 .5 L 0 -.5" : "M 0 .5 A .5 .5 0 0 1 .5 0";
  group.append(element("path", {d, class: "road", "stroke-width": layout.road_width / layout.cell_size}));
  group.append(element("path", {d, class: "centerline"}));
  if (!ghost && layout.start.tile === tile.id) {
    const marker = element("g", {
      transform: `rotate(${["north", "east", "south", "west"].indexOf(layout.start.heading) * 90 - tile.rotation})`,
    });
    marker.append(element("path", {d: "M 0 -.25 L .12 .12 L 0 .06 L -.12 .12 Z", class: "start"}));
    group.append(marker);
  }
  return group;
}

function render() {
  $("tiles").replaceChildren(...layout.tiles.map((tile) => drawTile(tile)));
  $("ghost").replaceChildren();
  $("name").value = layout.name;
  $("track-id").value = layout.id;
  $("cell-size").value = layout.cell_size;
  $("road-width").value = layout.road_width;
  $("heading").value = layout.start.heading;
  $("start-label").textContent = `Start: ${layout.start.tile || "not set"}`;
  $("undo").disabled = undo.length === 0;
  $("redo").disabled = redo.length === 0;
  renderPickupSelection();
  document.title = `${dirty() ? "* " : ""}${layout.name} - Track Sketcher`;
  scheduleValidation();
}

function renderPickupSelection() {
  const pickups = layout.pickups || [];
  const selected = pickups.find((pickup) => pickup.id === selectedPickup);
  if (!selected) selectedPickup = "";
  $("pickup-selection").replaceChildren(new Option("None (place a new pickup)", ""),
    ...pickups.map((pickup) => new Option(`${pickup.id} (${pickup.kind}, ${pickup.tile})`, pickup.id)));
  $("pickup-selection").value = selectedPickup;
  $("pickup-update").disabled = !selected;
  $("pickup-delete").disabled = !selected;
  if (selected) {
    $("pickup-kind").value = selected.kind;
    $("pickup-along").value = selected.along;
    $("pickup-lateral").value = selected.lateral;
  }
  for (const marker of $("pickups").children) {
    marker.dataset.selected = String(marker.dataset.id === selectedPickup);
  }
}

function selectPickup(id) {
  selectedPickup = id;
  renderPickupSelection();
}

async function putPickup(tile, id = "") {
  const candidate = structuredClone(layout);
  if (candidate.version === 1) {
    candidate.version = 2;
    candidate.pickups = [];
  }
  if (!id) {
    id = "pickup_1";
    for (let i = 1; candidate.pickups.some((item) => item.id === id); i++) id = `pickup_${i + 1}`;
  }
  const pickup = {
    id, kind: $("pickup-kind").value, tile,
    along: Number($("pickup-along").value), lateral: Number($("pickup-lateral").value),
  };
  if (!$("pickup-along").value.trim() || !$("pickup-lateral").value.trim()) {
    return notice("Pickup position fields must contain numbers.");
  }
  const index = candidate.pickups.findIndex((item) => item.id === id);
  if (index < 0) candidate.pickups.push(pickup);
  else candidate.pickups[index] = pickup;
  const expectedRevision = revision;
  try {
    const result = await inspect(candidate);
    if (revision !== expectedRevision) return notice("Placement cancelled because the layout changed. Try again.");
    if (!result.draft_ok) return notice(`Cannot place pickup: ${result.message}`);
    selectedPickup = id;
    edit(() => { layout = candidate; });
  } catch (error) { notice(`Pickup validation failed: ${error.message}`); }
}

function edit(change) {
  const before = structuredClone(layout);
  change();
  if (JSON.stringify(before) === JSON.stringify(layout)) return;
  undo.push(before);
  if (undo.length > 100) undo.shift();
  redo = [];
  notice();
  render();
}

function selectTool(value) {
  tool = value;
  for (const button of document.querySelectorAll("[data-tool]")) {
    button.setAttribute("aria-pressed", String(button.dataset.tool === tool));
  }
  $("ghost").replaceChildren();
}

function rotateBrush() {
  rotation = (rotation + 90) % 360;
  $("rotation").textContent = `${rotation} degrees clockwise`;
  $("ghost").replaceChildren();
}

function cellAt(event) {
  const point = new DOMPoint(event.clientX, event.clientY).matrixTransform($("grid").getScreenCTM().inverse());
  return {x: Math.floor(point.x + 0.5), y: -Math.floor(point.y + 0.5)};
}

function inBounds({x, y}) { return Math.abs(x) <= 100 && Math.abs(y) <= 100; }

function useCell(cell) {
  if (!inBounds(cell)) return notice("Coordinates must be within -100 to 100.");
  const tile = layout.tiles.find((item) => item.x === cell.x && item.y === cell.y);
  if (tool === "erase") {
    const count = (layout.pickups || []).filter((pickup) => pickup.tile === tile?.id).length;
    if (count && !window.confirm(`Erase this module and its ${count} pickup(s)? Undo restores both.`)) return;
    if (tile) edit(() => {
      layout.tiles = layout.tiles.filter((item) => item !== tile);
      if (layout.version === 2) layout.pickups = layout.pickups.filter((pickup) => pickup.tile !== tile.id);
      if (layout.start.tile === tile.id) layout.start.tile = "";
    });
  } else if (tool === "pickup") {
    if (!tile) return notice("Choose an existing road module for the pickup.");
    void putPickup(tile.id);
  } else if (tool === "rotate") {
    if (tile) edit(() => { tile.rotation = (tile.rotation + 90) % 360; });
    else notice("Choose an existing tile to rotate.");
  } else if (tool === "start") {
    if (tile?.kind !== "straight") return notice("The start must be placed on a straight.");
    const vertical = tile.rotation % 180 === 0;
    edit(() => {
      layout.start.tile = tile.id;
      const aligned = vertical ? ["north", "south"] : ["east", "west"];
      if (!aligned.includes(layout.start.heading)) layout.start.heading = aligned[0];
    });
  } else {
    if (tile) return notice("Cell occupied. Use Rotate existing or Erase first.");
    if (layout.tiles.length >= 900) return notice("A layout supports at most 900 tiles.");
    let id = "tile_1";
    for (let i = 1; layout.tiles.some((item) => item.id === id); i++) id = `tile_${i + 1}`;
    edit(() => { layout.tiles.push({id, kind: tool, ...cell, rotation}); });
  }
}

function updateView() {
  $("grid").setAttribute("viewBox", `${view.x} ${view.y} ${view.width} ${view.height}`);
  $("ghost").replaceChildren();
}

function fit() {
  if (layout.tiles.length === 0) view = {x: -5.5, y: -4.5, width: 12, height: 9};
  else {
    const xs = layout.tiles.map((tile) => tile.x);
    const ys = layout.tiles.map((tile) => -tile.y);
    view = {
      x: Math.min(...xs) - 1.5, y: Math.min(...ys) - 1.5,
      width: Math.max(4, Math.max(...xs) - Math.min(...xs) + 3),
      height: Math.max(4, Math.max(...ys) - Math.min(...ys) + 3),
    };
  }
  updateView();
}

function zoom(factor) {
  const width = Math.max(3, Math.min(220, view.width * factor));
  const height = Math.max(3, Math.min(220, view.height * factor));
  view.x -= (width - view.width) / 2;
  view.y -= (height - view.height) / 2;
  view.width = width;
  view.height = height;
  updateView();
}

function replace(data, isSaved) {
  layout = data;
  selectedPickup = "";
  undo = [];
  redo = [];
  saved = isSaved ? JSON.stringify(data) : "";
  notice();
  fit();
  render();
}

async function loadText(text, expectedOperation, expectedRevision) {
  if (text.length > 1_000_000) throw new Error("Layout exceeds 1,000,000 bytes.");
  // Let Python decode the original text too, so duplicate keys cannot be lost by JSON.parse.
  const response = await fetch("/api/inspect", {
    method: "POST", headers: {"Content-Type": "application/json"}, body: text,
  });
  const result = await response.json();
  if (!response.ok || !result.draft_ok) throw new Error(result.message);
  if (fileOperation !== expectedOperation || revision !== expectedRevision) {
    return notice("Load cancelled because the layout changed while reading. Try opening again.");
  }
  replace(JSON.parse(text), true);
}

async function loadExample(name) {
  if (!confirmDiscard()) return;
  const operation = ++fileOperation;
  const expectedRevision = revision;
  try {
    const response = await fetch(`/examples/${name}.json`);
    if (!response.ok) throw new Error(`Cannot load example (${response.status}).`);
    await loadText(await response.text(), operation, expectedRevision);
    if (fileOperation === operation && revision === expectedRevision + 1) {
      notice("Example loaded. Change its track ID before generating to preserve the reference track.");
    }
  } catch (error) { notice(`Open failed: ${error.message}`); }
}

$("grid").addEventListener("click", (event) => useCell(cellAt(event)));
$("grid").addEventListener("pointermove", (event) => {
  const cell = cellAt(event);
  $("position").textContent = `Cell (${cell.x}, ${cell.y}); north is up.`;
  $("ghost").replaceChildren();
  if (inBounds(cell) && ["straight", "corner"].includes(tool)) {
    $("ghost").append(drawTile({id: "preview", kind: tool, ...cell, rotation}, true));
  }
});
$("grid").addEventListener("pointerleave", () => $("ghost").replaceChildren());
for (const button of document.querySelectorAll("[data-tool]")) {
  button.addEventListener("click", () => selectTool(button.dataset.tool));
}
$("rotate").addEventListener("click", rotateBrush);
$("pickup-selection").addEventListener("change", () => selectPickup($("pickup-selection").value));
$("pickup-update").addEventListener("click", () => {
  const pickup = (layout.pickups || []).find((item) => item.id === selectedPickup);
  if (pickup) void putPickup(pickup.tile, pickup.id);
});
$("pickup-delete").addEventListener("click", () => {
  if (selectedPickup) edit(() => {
    layout.pickups = layout.pickups.filter((pickup) => pickup.id !== selectedPickup);
  });
});
$("undo").addEventListener("click", () => {
  if (!undo.length) return;
  redo.push(structuredClone(layout));
  layout = undo.pop();
  notice();
  render();
});
$("redo").addEventListener("click", () => {
  if (!redo.length) return;
  undo.push(structuredClone(layout));
  layout = redo.pop();
  notice();
  render();
});
for (const [id, key, numeric] of [
  ["name", "name", false], ["track-id", "id", false],
  ["cell-size", "cell_size", true], ["road-width", "road_width", true],
]) {
  $(id).addEventListener("change", () => {
    const value = numeric ? Number($(id).value) : $(id).value;
    edit(() => { layout[key] = value; });
  });
}
$("heading").addEventListener("change", () => {
  const value = $("heading").value;
  edit(() => { layout.start.heading = value; });
});
for (const [id, dx, dy] of [["left", -1, 0], ["right", 1, 0], ["up", 0, -1], ["down", 0, 1]]) {
  $(id).addEventListener("click", () => {
    view.x = Math.max(-105, Math.min(105, view.x + dx * view.width / 4));
    view.y = Math.max(-105, Math.min(105, view.y + dy * view.height / 4));
    updateView();
  });
}
$("zoom-in").addEventListener("click", () => zoom(0.8));
$("zoom-out").addEventListener("click", () => zoom(1.25));
$("fit").addEventListener("click", fit);
$("new").addEventListener("click", () => {
  if (!confirmDiscard()) return;
  fileOperation++;
  replace(fresh(), false);
});
$("oval").addEventListener("click", () => loadExample("oval"));
$("bends").addEventListener("click", () => loadExample("bends"));
$("pickup-oval").addEventListener("click", () => loadExample("pickup_oval"));
$("open").addEventListener("click", () => {
  if (confirmDiscard()) $("file").click();
});
$("file").addEventListener("change", async () => {
  const file = $("file").files[0];
  if (!file) return;
  const operation = ++fileOperation;
  const expectedRevision = revision;
  try {
    if (file.size > 1_000_000) throw new Error("Layout exceeds 1,000,000 bytes.");
    await loadText(await file.text(), operation, expectedRevision);
  } catch (error) { notice(`Open failed: ${error.message}`); }
  finally { $("file").value = ""; }
});
$("save").addEventListener("click", async () => {
  const snapshot = structuredClone(layout);
  const expectedRevision = revision;
  try {
    const result = await inspect(snapshot);
    if (!result.draft_ok) return notice(`Cannot save: ${result.message}`);
    const blob = new Blob([`${JSON.stringify(snapshot, null, 2)}\n`], {type: "application/json"});
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${snapshot.id}.json`;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    if (revision === expectedRevision) {
      saved = JSON.stringify(snapshot);
      document.title = `${layout.name} - Track Sketcher`;
      notice(result.valid ? "JSON download requested. Generate it with the existing command." :
        "Draft JSON download requested. Finish the circuit before generating.");
    }
  } catch (error) { notice(`Save failed: ${error.message}`); }
});
document.addEventListener("keydown", (event) => {
  if (["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement.tagName)) return;
  const key = event.key.toLowerCase();
  if ((event.ctrlKey || event.metaKey) && ["z", "y"].includes(key)) {
    event.preventDefault();
    $(key === "y" || event.shiftKey ? "redo" : "undo").click();
  } else if (!event.ctrlKey && !event.metaKey && !event.altKey) {
    if (key === "r") rotateBrush();
    const tools = {1: "straight", 2: "corner", 3: "rotate", 4: "erase", 5: "start", 6: "pickup"};
    if (tools[key]) selectTool(tools[key]);
  }
});
window.addEventListener("beforeunload", (event) => {
  if (dirty()) { event.preventDefault(); event.returnValue = ""; }
});
render();
