"""Add source-verified thread callouts to the existing native cell half-body view.

This is a deterministic annotation update, not a new CAD render.  The saved
native view, its hole circles, leaders and hidden-hole dashes are preserved.
Both the native raster and its STEP are pinned; a geometry revision must supply
a newly verified view instead of silently reusing these annotation locations.
Run with the project environment; only Pillow is required.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import operator
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


REPO = Path(__file__).resolve().parents[1]
SOURCE_IMAGE = REPO / "tools/drawing_sources/cell_halfbody_v9_16_native_single_view.png"
STEP = REPO / "Production/CellEnclosure/Rb_Cell_Enclosure_HalfBody_V9_16.step"
OUTPUT = REPO / "Production/CellEnclosure/Rb_Cell_Enclosure_HalfBody_V9_16_3D_TAP_single_view.png"
EVIDENCE = REPO / "Production/CellEnclosure/Rb_Cell_Enclosure_HalfBody_V9_16_thread_drawing_validation.json"
SOURCE_IMAGE_SHA256 = "2b0f66cc4b667fdedc2fe2bb3b9258d14775cfcb3b0fa83d07d05177814500b1"
STEP_SHA256 = "8436c88c6188a60b2cf1e37683d6647cae19f3200ab0693e92192f42de188591"
CELL_FUNCTION_AST_SHA256 = {
    "_sliding_cell_slot": "30710f8987f3af58196e44c6ae6c97a712f51c63b128984822caaeaaff7bb0cb",
    "_sliding_cell_block": "b7e88b2e3f83f3b79dee8edfc317a03db75d547015c778576674f4f046eca36f",
    "_sliding_cell_common_cuts": "63abe7ba2969e1a8835bfba3741de8458a0cafe73920ed6c45a86728eba47924",
    "_sliding_cell_half": "6b53f50e55ee6638a7bb821fc4ff4e2ada0169930887376460fa6ec44531127d",
    "sliding_cell_half_shape": "5123d43134ddecd60529a2b585da9a46cf608f745e2d6acbbb0ad6c61322c26d",
}
RED = (189, 21, 48)
BLUE = (6, 91, 181)
GRAY = (75, 85, 99)
WHITE = (255, 255, 255)

# Pixel coordinates in the pinned 2880 x 2160 native drawing.  The region
# borders stop short of every existing leader; no hole or model pixels lie in
# these white-background annotation regions.  Bottom/right bounds are exclusive.
CALLOUTS = [
    {"name": "clearance_slot_near", "region": (530, 350, 964, 543),
     "box": (540, 360, 954, 539), "lines": ("NO TAP", "8-32 CLEARANCE"), "color": BLUE},
    {"name": "clearance_slot_far", "region": (1490, 330, 1930, 521),
     "box": (1500, 340, 1920, 517), "lines": ("NO TAP", "8-32 CLEARANCE"), "color": BLUE},
    {"name": "hidden_end_tap_left", "region": (1048, 490, 1385, 644),
     "box": (1053, 495, 1381, 640), "lines": ("8-32 UNC", "TAP"), "color": RED},
    {"name": "hidden_end_tap_right", "region": (2226, 1043, 2575, 1204),
     "box": (2229, 1046, 2570, 1199), "lines": ("8-32 UNC", "TAP"), "color": RED},
    {"name": "visible_end_tap_left", "region": (397, 1341, 745, 1494),
     "box": (402, 1344, 741, 1489), "lines": ("8-32 UNC", "TAP"), "color": RED},
    {"name": "visible_end_tap_right", "region": (768, 1439, 1114, 1595),
     "box": (773, 1442, 1110, 1590), "lines": ("8-32 UNC", "TAP"), "color": RED},
]
FOOTER_REGION = (400, 1940, 2480, 2130)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def constant_value(node):
    """Read the cell's literal design dictionary without importing FreeCAD."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple)):
        return [constant_value(v) for v in node.elts]
    if isinstance(node, ast.Dict):
        return {constant_value(k): constant_value(v) for k, v in zip(node.keys, node.values)}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -constant_value(node.operand)
    operations = {ast.Add: operator.add, ast.Sub: operator.sub,
                  ast.Mult: operator.mul, ast.Div: operator.truediv}
    if isinstance(node, ast.BinOp) and type(node.op) in operations:
        return operations[type(node.op)](constant_value(node.left), constant_value(node.right))
    raise ValueError(f"Unsupported nonliteral cell parameter: {ast.dump(node)}")


def source_evidence():
    path = REPO / "optomech.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assignments = [n for n in tree.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "SLIDING_CELL" for t in n.targets)]
    if len(assignments) != 1:
        raise ValueError("Expected exactly one literal SLIDING_CELL definition")
    p = constant_value(assignments[0].value)
    expected = {
        "x_range_mm": [-44.0, 44.0], "half_height_mm": 24.0,
        "cover_hole_yz_mm": [[17.0, 17.0], [-14.5, 17.0], [17.0, -17.0], [-14.5, -17.0]],
        "slot_x_mm": [-39.9, 39.9], "slot_y_mm": [0.5, 11.0],
        "slot_width_mm": 0.172 * 25.4, "seat_tap_diameter_mm": 0.136 * 25.4,
    }
    for key, value in expected.items():
        if p.get(key) != value:
            raise ValueError(f"Cell feature changed: {key}")
    # The thread name is supported by the explicit screw specification, rather
    # than guessed from the tap-drill diameter.
    if not p["cover_screw"].startswith("8-32 ") or not p["seat_screw"].startswith("8-32 "):
        raise ValueError("The explicit cover/seat screw specification is no longer 8-32")
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    actual_hashes = {}
    for name, expected_hash in CELL_FUNCTION_AST_SHA256.items():
        actual_hash = hashlib.sha256(ast.dump(functions[name], include_attributes=False).encode()).hexdigest()
        if actual_hash != expected_hash:
            raise ValueError(f"Cell construction function changed: {name}; recheck drawing against STEP")
        actual_hashes[name] = actual_hash
    return {
        "path": "optomech.py", "sha256": sha256(path),
        "parameter_definition_line": assignments[0].lineno,
        "construction_function_ast_sha256": actual_hashes,
        "thread_evidence": "SLIDING_CELL.cover_screw explicitly specifies 8-32; _sliding_cell_common_cuts creates the four end taps. No thread designation is inferred solely from bore diameter.",
        "slot_evidence": "SLIDING_CELL.seat_screw explicitly specifies 8-32; slot_width_mm is documented as 8-32 close clearance. _sliding_cell_slot cuts through each half.",
        "tap_thread": "8-32 UNC", "tap_count": 4,
        "tap_mouth_centres_local_mm": [[x, y, z] for x in p["x_range_mm"]
                                       for y, z in p["cover_hole_yz_mm"] if z < 0],
        "tap_axes_inward_local": [[1, 0, 0], [-1, 0, 0]],
        "slot_count": 2, "slot_type": "8-32 clearance / NO TAP",
        "slot_centreline_ends_local_mm": [[[x, y, 0] for y in p["slot_y_mm"]]
                                          for x in p["slot_x_mm"]],
        "slot_width_mm": p["slot_width_mm"], "tap_length_in_drawing": False,
    }


def font(size: int, bold: bool = False):
    filename = "arialbd.ttf" if bold else "arial.ttf"
    candidates = [Path("C:/Windows/Fonts") / filename]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    raise FileNotFoundError("The reproducible drawing requires Windows Arial/Arial Bold")


def is_antialias_of(pixel, color, tolerance=4):
    direction = [c - 255 for c in color]
    length2 = sum(d * d for d in direction)
    t = sum((p - 255) * d for p, d in zip(pixel, direction)) / length2
    if not -0.02 <= t <= 1.02:
        return False
    return max(abs(p - (255 + t * d)) for p, d in zip(pixel, direction)) <= tolerance


def verify_blank_annotation_regions(image):
    for item in CALLOUTS:
        for pixel in image.crop(item["region"]).get_flattened_data():
            if pixel != WHITE and not is_antialias_of(pixel, item["color"]):
                raise ValueError(f"Annotation region contains non-label pixels: {item['name']}, {pixel}")


def centered(draw, center, text, selected_font, color):
    draw.text(center, text, font=selected_font, fill=color, anchor="mm")


def render(output: Path = OUTPUT, evidence: Path = EVIDENCE):
    if sha256(SOURCE_IMAGE) != SOURCE_IMAGE_SHA256 or sha256(STEP) != STEP_SHA256:
        raise ValueError("Pinned native image or STEP changed; do not reuse the old callout coordinates")
    facts = source_evidence()
    original = Image.open(SOURCE_IMAGE).convert("RGB")
    if original.size != (2880, 2160):
        raise ValueError("Unexpected native image size")
    verify_blank_annotation_regions(original)
    image = original.copy()
    draw = ImageDraw.Draw(image)
    for item in CALLOUTS:
        left, top, right, bottom = item["region"]
        draw.rectangle((left, top, right - 1, bottom - 1), fill=WHITE)
        x0, y0, x1, y1 = item["box"]
        draw.rounded_rectangle((x0, y0, x1, y1), radius=14, fill=WHITE, outline=item["color"], width=5)
        xc, yc = (x0 + x1) / 2, (y0 + y1) / 2
        if item["color"] == RED:
            centered(draw, (xc, yc - 31), item["lines"][0], font(46, True), RED)
            centered(draw, (xc, yc + 30), item["lines"][1], font(57, True), RED)
        else:
            centered(draw, (xc, yc - 34), item["lines"][0], font(66, True), BLUE)
            centered(draw, (xc, yc + 35), item["lines"][1], font(38, True), BLUE)
    x0, y0, x1, y1 = FOOTER_REGION
    draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=WHITE)
    centered(draw, (1440, 2005), "DASHED = HIDDEN HOLES", font(50, True), RED)
    footer = "4 x 8-32 UNC TAP  |  2 x 8-32 clearance slots - NO TAP"
    centered(draw, (1440, 2076), footer, font(42), GRAY)
    mask = Image.new("1", image.size)
    maskdraw = ImageDraw.Draw(mask)
    for region in [item["region"] for item in CALLOUTS] + [FOOTER_REGION]:
        x0, y0, x1, y1 = region
        maskdraw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=1)
    changed_outside = sum(a != b and not allowed for a, b, allowed in
                          zip(original.get_flattened_data(), image.get_flattened_data(), mask.get_flattened_data()))
    if changed_outside:
        raise ValueError("Native geometry/leader pixels changed outside annotation regions")
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=False)
    record = {
        "schema": "cell_halfbody_thread_drawing/1", "passed": True,
        "scope": "Text-only annotation update of an existing verified native engineering view; no geometry regeneration or alteration.",
        "step": {"path": STEP.relative_to(REPO).as_posix(), "sha256": sha256(STEP)},
        "native_image": {"path": SOURCE_IMAGE.relative_to(REPO).as_posix(), "sha256": sha256(SOURCE_IMAGE)},
        "output": {"path": output.relative_to(REPO).as_posix() if output.is_relative_to(REPO) else str(output), "sha256": sha256(output)},
        "renderer": {"path": Path(__file__).resolve().relative_to(REPO).as_posix(), "sha256": sha256(Path(__file__))},
        "source_evidence": facts,
        "callouts": [{"name": a["name"], "text": list(a["lines"]), "annotation_region_xyxy_px": list(a["region"])} for a in CALLOUTS],
        "pixel_checks": {"size_px": list(image.size), "changed_pixels_outside_annotation_regions": changed_outside,
                         "native_geometry_hole_circles_leaders_and_hidden_dashes_preserved": True,
                         "annotation_regions_were_white_background_and_old_label_only": True},
        "manufacturing_geometry_changed": False,
        "tap_length_in_drawing": False,
    }
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"passed": True, "output": str(output), "evidence": str(evidence), "sha256": sha256(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--evidence", type=Path, default=EVIDENCE)
    args = parser.parse_args()
    render(args.output.resolve(), args.evidence.resolve())
