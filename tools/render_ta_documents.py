"""Make a production-board BOM and TAP_or_NOT sheet from one CAD export.

Run with the project-local Python environment (Python >= 3.10, matplotlib).
The BOM uses the bundled Codex Node.js runtime and @oai/artifact-tool. Override
their locations with --node and --node-modules when using another installation.

Example::

    python tools/render_ta_documents.py --report TA_validation.json \
        --holes TA_holes.json --edges TA_plate_edges.json \
        --output-dir Production/TABoardV9 --stem TA_Board_V9 \
        --step-name TA_Board_V9_baseplate_11p625x11in.step --title "TA board V9.13"

Inputs follow board_tools.inspect_board and the run_split2.py hole/edge dumps.
Dimensions, hole positions, thread types and quantities are read from those
inputs. No plate dimensions or mounting-hole positions are assumed.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile


ADAPTERS = {
    "surface_adapter_rotation_stage_lip": "Surface_Adapter_rsp05_lip.step",
    "surface_adapter_isolator_lip": "Surface_Adapter_isolator_lip.step",
    "surface_adapter_fiberport_lip": "Surface_Adapter_fiberport_lip.step",
    "TA_adapter": "TA_adapter_board_model.step",
    "aom_adapter": "AOM_Adapter.step (upper adapter; lower seat is integral)",
    "shutter_adapter": "Shutter_Adapter.step",
    "cube_mount_halfinch": "Cube_Mount_Halfinch.step",
    "slide_mount": "Iris_Mount.step (IDA12 slide mount)",
    # V9.16: the lower and the upper half of the cell enclosure are one part, ordered twice
    "SlidingCellEnclosure": "Rb_Cell_Enclosure_HalfBody_V9_16.step",
    "SlidingCellLid": "Rb_Cell_Enclosure_HalfBody_V9_16.step",
    "SlidingCellCover": "Rb_Cell_Enclosure_Cover_V9_16.step",
}
ELEMENTS = {
    "mirror_mount_M05": "Newport M05 mirror mount",
    "circular_mirror_union_optic": "1/2 in mirror (BB05-E03 or equivalent)",
    "rotation_stage_rsp05": "RSP05 rotation mount",
    "rotation_stage_rsp05_bonded_cube": "RSP05 rotation mount",
    "cube_splitter": "PBS cube 12.7 mm",
    "fiberport_mount_KA05T_holes": "KA05T fiber port mount",
    "fiberport_mount_km05T": "KM05T fiber port mount",
    "fiber_adapter_sm05fca2": "SM05FCA2 fiber adapter",
    "lens_tube_sm05l05": "SM05L05 lens tube",
    "lens_adapter_s05tm09": "S05TM09 lens adapter",
    "mounted_lens_c220tmda": "C220TMD-A fiber lens",
    "isolator_850": "IOT-5-850-VLP isolator",
    "isolator_850_long_pocket": "IOT-5-850-VLP isolator",
    "AOMO_3100_125": "G&H AOMO 3100-125",
    "prism_mount_km100pm_bridged": "KM100PM (bridged)",
    "shutter_sr475": "SRS SR475 shutter",
    "pinhole_ida12": "IDA12-P5 iris",
    "lens_holder_l05g": "POLARIS-L05G lens holder",
    "lens_holder_l05g_no_pin_slots": "POLARIS-L05G lens holder (no pin slots)",
    "TA_butterfly": "TA butterfly package (TAboard)",
    "TA_butterfly_on_adapter": "TA butterfly package (TAboard), on TA adapter",
    "baseplate_mount": "1/4-20 table bolt (baseplate fixing)",
    "thumbscrew_hkts_5_64": "HKTS-5/64 thumbscrew adjuster",
    "SlidingCellGlass": "GC25075-RB rubidium vapour cell (CAD envelope)",
}
# Already counted as an assembly, or machining/nominal-axis geometry, not a part.
NON_BOM_CLASSES = {
    "baseplate", "IntegralAOMBaseplate", "IntegralAOMSeat", "BareTappedHole",
    "CellPocketMachining", "SlidingCellSeat", "mirror_mount_KA05T", "mirror_mount_km05T",
    "RSP05CubeAdhesive",  # modelled bond layer, not a separately purchased part
    "beam_path", "beam_path_manual",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def finite(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def validate_inputs(report, holes, edges):
    """Reject stale/mismatched geometry and holes that cannot be classified."""
    plates = [o for o in report["objects"]
              if o.get("class") in {"baseplate", "IntegralAOMBaseplate"}]
    if len(plates) != 1:
        raise ValueError(f"Expected one baseplate in validation report, got {len(plates)}")
    plate = plates[0]
    if not report.get("plate_valid") or report.get("plate_solid_count") != 1:
        raise ValueError("The report must confirm one valid baseplate solid")
    box = plate["bbox"]
    edge_box = edges["bbox"]
    if len(box) != 6 or len(edge_box) != 4 or not all(map(finite, box + edge_box)):
        raise ValueError("Invalid plate bounds")
    if any(abs(a - b) > 0.06 for a, b in zip([box[0], box[1], box[3], box[4]], edge_box)):
        raise ValueError("Plate edges and validation report have different bounds")
    if holes.get("plate", plate["label"]) != plate["label"]:
        raise ValueError("Hole inventory and validation report name different plates")
    if edges.get("plate", plate["label"]) != plate["label"]:
        raise ValueError("Plate edges and validation report name different plates")
    if not edges.get("levels") or not finite(edges.get("top_z")):
        raise ValueError("Edge dump must contain levels and top_z")
    if abs(edges["top_z"]-box[5]) > .06:
        raise ValueError("Plate top height differs between edge dump and validation report")
    if not holes.get("features"):
        raise ValueError("Hole inventory is empty")
    seen = set()
    for hole in holes["features"]:
        if hole["kind"] not in {"TAP", "PLAIN"}:
            raise ValueError(f"Unclassified hole: {hole}")
        xy = (hole["x"], hole["y"])
        if not all(map(finite, xy)) or xy in seen:
            raise ValueError(f"Invalid or duplicate hole axis: {xy}")
        seen.add(xy)
        if not (box[0] <= xy[0] <= box[3] and box[1] <= xy[1] <= box[4]):
            raise ValueError(f"Hole axis outside the plate: {xy}")
        if not re.search(r"(?:8-32|1/4-20)", hole["spec"]):
            raise ValueError(f"Unsupported hole specification: {hole['spec']}")
    plain = [h for h in holes["features"] if h["kind"] == "PLAIN"]
    for xy in report.get("mount_holes_mm", []):
        if not any(math.hypot(h["x"]-xy[0], h["y"]-xy[1]) < .03 for h in plain):
            raise ValueError(f"Reported table mount is absent from the clearance-hole inventory: {xy}")
    return plate


def thread_name(hole):
    """Use the thread callout belonging to the smallest (functional) cylinder."""
    spec = hole["spec"].split(" + ")[-1]
    match = re.search(r"(8-32|1/4-20)", spec)
    if not match:
        raise ValueError(f"Missing thread size in {spec}")
    return ("#" if match[1] == "8-32" else "") + match[1]


def build_bom(report, holes, title, step_name, source_name, sheet_name):
    adapters, elements, unknown = Counter(), Counter(), Counter()
    objects = report["objects"]
    for obj in objects:
        cls, label = obj.get("class"), obj.get("label", obj.get("name", ""))
        if not cls or cls in NON_BOM_CLASSES:
            continue
        if cls in ADAPTERS:
            adapters[ADAPTERS[cls]] += 1
        elif cls == "waveplate":
            kind = "quarter-wave (QWP)" if "QWP" in label.upper() else "half-wave (HWP)"
            elements[f"1/2 in {kind} waveplate"] += 1
        elif cls == "circular_lens":
            parts = [p for p in obj.get("part_numbers", []) if p]
            elements["Lens " + (parts[0] if parts else label)] += 1
        elif cls == "mounted_lens_c220tmda" and report.get("mode") == "splitting":
            elements["Fiber collimation lens, f ~4.5 mm (CAD envelope: C220TMD-A)"] += 1
        elif cls in ELEMENTS:
            elements[ELEMENTS[cls]] += 1
        else:
            unknown[cls] += 1
    if unknown:
        raise ValueError(f"Unmapped physical classes in BOM; review before publishing: {dict(unknown)}")
    # Only the legacy bare RSP05 needs an unmodelled cube allowance. The bonded
    # subclass has a real cube_splitter child, counted in the object inventory.
    empty_pbs = sum(o.get("class") == "rotation_stage_rsp05" and
                    any(word in o.get("label", "").lower() for word in ("empty", "rotating")) and
                    "pbs" in o.get("label", "").lower() for o in objects)
    if empty_pbs:
        elements["PBS cube bonded to empty output RSP05 (not modelled)"] += empty_pbs
    cell_count = sum(o.get("class") == "SlidingCellEnclosure" for o in objects)
    if cell_count:
        elements["8-32 x 2-1/4 in socket head screw (cell through-slot; not modelled)"] += 2*cell_count
        elements["#8 flat washer (under the cell through-slot screw heads; not modelled)"] += 2*cell_count
        elements["8-32 x 5/8 in socket head screw (cell end covers; not modelled)"] += 8*cell_count
    selected_stations = report.get('conditioning_station_audit', {})
    if selected_stations.get('declaration', {}).get('holder_selection_confirmed') is True:
        if selected_stations.get('actual_selected_holder_fit', {}).get('passed') is not True:
            raise ValueError('Selected conditioning holders require actual native fit evidence')
        elements['POLARIS-L05G lens holder (four planned conditioning positions)'] += 4
    adapters[step_name] += 1
    rows, headers = [[title, None], [None, None]], []
    for heading, counts in [("Adaptors", adapters), ("Elements", elements)]:
        headers.append(len(rows) + 1)
        rows.append([heading, "#"])
        rows.extend([name, count] for name, count in sorted(counts.items()))
        rows.append([None, None])
    headers.append(len(rows) + 1)
    rows.append(["Notes", None])
    notes = [f"Modelled component quantities: {source_name}. Adapter filenames follow Production/Adapters.",
             f"Tapping classification: {sheet_name}. Hole locations and counts come from the exported plate solid."]
    taps = Counter(thread_name(h) for h in holes["features"] if h["kind"] == "TAP")
    plains = Counter(thread_name(h) for h in holes["features"] if h["kind"] == "PLAIN")
    notes.append("Plate holes: " + "; ".join(
        [f"{n} x {s} tapped" for s, n in sorted(taps.items())] +
        [f"{n} x {s} clearance (do not tap)" for s, n in sorted(plains.items())]) + ".")
    classes = Counter(o.get("class") for o in objects)
    if classes["IntegralAOMSeat"]:
        notes.append("AOM lower seats are integral with the baseplate. Only the upper AOM adapter is a separate part.")
        relief = report.get('aom_machining_relief_audit')
        if relief is not None:
            parameters = relief.get('parameters', {})
            clearance = relief.get('single_axis_adapter_clearance', {})
            floor_gap = clearance.get('minimum_floor_gap_mm')
            side_gap = clearance.get('minimum_sidewall_gap_mm')
            if (relief.get('schema') not in ('aom_machining_relief_audit/1', 'aom_machining_relief_audit/2')
                    or relief.get('passed') is not True
                    or relief.get('seat_count') != classes['IntegralAOMSeat']
                    or parameters.get('side_clearance_mm') != 6
                    or parameters.get('front_relief_depth_mm') != 4
                    or parameters.get('front_corner_radius_mm') != 3
                    or clearance.get('pitch_down_interval_deg') != [0, 4]
                    or not finite(floor_gap) or floor_gap <= 0
                    or not finite(side_gap) or side_gap <= 0):
                raise ValueError('AOM machining notes require matching passed native relief evidence')
            if relief.get('schema') == 'aom_machining_relief_audit/2':
                seats = relief.get('seats', [])
                if (parameters.get('side_clearance_datum') != 'locating lip outer face'
                        or len(seats) != classes['IntegralAOMSeat']
                        or not all(s.get('side_channel', {}).get('passed') is True for s in seats)):
                    raise ValueError('AOM BOM notes require actual flush-wall evidence for every seat')
                notes.append(f"The {classes['IntegralAOMSeat']} integral AOM seats have 6 mm side clearance measured from the locating lip outer face, a flush side-wall transition and a 4 mm-deep front relief with R3 corners. The bearing faces and installation height remain unchanged.")
            else:
                notes.append(f"The {classes['IntegralAOMSeat']} integral AOM seats have 6 mm side clearance and a 4 mm-deep front relief with R3 corners. The bearing faces and installation height remain unchanged.")
            notes.append(f"The machining audit checks single-axis pitch-down from 0 to 4 degrees: minimum floor gap {floor_gap:.5f} mm and minimum sidewall gap {side_gap:g} mm. Combined-axis travel is not certified.")
    if classes["TA_butterfly_on_adapter"]:
        notes.append("The TA butterfly package mounts to the TA adapter. Its small adapter threads are not baseplate taps.")
    if classes["BareTappedHole"]:
        tail_holes = sum(o.get("class") == "BareTappedHole" and
                         "rear clamp tap" in o.get("label", "").lower() for o in objects)
        if tail_holes:
            notes.append(f"{tail_holes} bare 8-32 taps retain the fiber tail-clamp hole pairs. They are baseplate machining; the tail clamps are not modelled parts.")
        other_bare = classes["BareTappedHole"] - tail_holes
        if other_bare:
            conditioning = (report.get("conditioning_station_audit") or {}).get("declaration") or {}
            counts = conditioning.get("expected_counts") or {}
            if counts.get("total") == other_bare and counts.get("cylindrical") and counts.get("spherical"):
                if conditioning.get('holder_selection_confirmed') is True:
                    notes.append(f"{other_bare} bare conditioning stations provide {counts['cylindrical']} cylindrical-lens and {counts['spherical']} spherical-lens positions. Four selected POLARIS-L05G holders are listed as planned parts; actual native holder/cutter fit is verified, while optics remain unselected.")
                else:
                    notes.append(f"{other_bare} bare conditioning stations provide {counts['cylindrical']} cylindrical-lens and {counts['spherical']} spherical-lens mounting positions. Holders and optics remain unselected and are not installed or counted in this BOM.")
            else:
                notes.append(f"{other_bare} bare conditioning stations are drilled provisions. No holder or optic is installed there.")
    if classes["fiberport_mount_km05T"]:
        notes.append("KM05T mounts are counted once at each fiber assembly root; their mirror-mount child is not counted again. The lip adapters and optical subparts are listed separately.")
    if report.get("mode") == "splitting":
        notes.append("The splitting-board optical model assumes an f ~4.5 mm fiber collimation lens in each head. C220TMD-A is the retained CAD envelope, not the specified optical prescription. Confirm the actual lens and beam size before operation.")
        entrance_hwps = report.get("pre_aom_waveplates") or (report.get("pre_aom_waveplate_audit") or {}).get("declaration") or []
        if entrance_hwps:
            hwp_count = sum(o.get("class") == "waveplate" and "QWP" not in o.get("label", "").upper() for o in objects)
            stage_count = classes["rotation_stage_rsp05"] + classes["rotation_stage_rsp05_bonded_cube"]
            bonded_count = classes["rotation_stage_rsp05_bonded_cube"]
            notes.append(f"Each of the {len(entrance_hwps)} AOM entrances has a dedicated HWP, RSP05 and lip adapter. The {hwp_count-len(entrance_hwps)} downstream HWPs remain installed, giving {hwp_count} HWPs in total. The {stage_count} RSP05 mounts include {bonded_count} bonded-PBS stages that hold cubes, not additional waveplates.")
        if report.get("pre_aom_waveplate_audit", {}).get("input_order", {}).get("passed") is True:
            notes.append("The single input QWP has its own RSP05 and lip adapter. Input order is fiber port -> steering mirror -> QWP -> entrance HWP -> AOM; the QWP is counted separately from the fourteen HWPs.")
        motion = report.get('aom_adjustment_audit', {})
        if motion.get('passed') is True and report.get('aom_machining_relief_audit') is None:
            notes.append('External AOM hardware clears an ideal-pivot net rotation cone of 4 degrees with 1 mm added margin. This external-hardware check does not certify adapter-to-plate clearance or combined-axis travel.')
    reference = report.get("optical_reference_model") or {}
    if (reference.get("kind") == "zero_order_reference_model" and
            reference.get("aom_rf_state") == "off" and
            type(reference.get("modeled_order")) is int and reference["modeled_order"] == 0 and
            finite(reference.get("diffraction_angle_deg")) and
            abs(reference["diffraction_angle_deg"]) <= 1.e-10):
        notes.append("Optical reference: AOM RF off, straight-through zero order. RF-on first-order propagation, order rejection and fiber-coupling performance are not evaluated for this layout.")
    if classes["RSP05CubeAdhesive"]:
        notes.append("The bonded PBS cubes are modelled and counted once above. Their modelled corner adhesive pads describe the assumed bond geometry and are not separate procurement items. Adhesive selection, bond strength and coating compatibility require assembly engineering.")
    if report.get("single_output_design") or reference.get("kind") == "single_output_no_aom":
        notes.append("The TA has one direct fiber output after the rubidium cell: mirror, first lens, mirror, second lens, HWP, bonded rotating PBS and KA05T fiber port. The folded distance between the two lenses is 45.319348 mm.")
        if (report.get("conditioning_station_audit") or {}).get("declaration", {}).get("schema") == "conditioning_stations/1":
            notes.append("The upstream HWP is on the first horizontal TA output leg, before the first steering mirror. The QWP is on the left vertical leg, after the isolator and before the conditioning stations.")
        if report.get('upstream_order_audit', {}).get('passed') is True:
            notes.append('Original upstream order restored: TA -> two steering mirrors -> HWP -> isolator -> QWP -> common folding mirrors and conditioning. Actual native optical centres, axes and mirror normals are independently checked.')
        if report.get('mount_support_audit', {}).get('passed') is True:
            notes.append('All six M05 mirror bases are checked against the actual machined plate, excluding only their own mounting bores. The TA adapter pocket must not remove a mirror support footprint; vertical separation alone is insufficient.')
    if classes["CellPocketMachining"]:
        notes.append("The reserved cell pocket is machining only. No cell enclosure is included in the installed component counts.")
    if classes["SlidingCellEnclosure"]:
        notes.append("The V9.16 cell enclosure is two identical half bodies (the upper one is the lower one turned over) and two identical end covers; their STEP files and the TAP / NO TAP picture are in Production/CellEnclosure. The seat pocket and mounting taps are baseplate machining, not separate parts.")
    if classes["SlidingCellCover"]:
        notes.append("The supplied V9.16 front and rear cell covers are opaque and have no beam apertures. Machine the beam apertures before optical operation; their present geometry blocks the beam.")
    if empty_pbs:
        notes.append(f"The {empty_pbs} empty output RSP05 mounts each require one bonded PBS cube, listed separately because it is not modelled.")
    if classes["thumbscrew_hkts_5_64"]:
        notes.append("HKTS-5/64 adjusters are modelled separately. If supplied with the selected M05 or fiber-mount kit, do not order them twice.")
    note_rows = []
    for i, note in enumerate(notes, 1):
        note_rows.append(len(rows) + 1)
        rows.append([f"{i}. {note}", None])
    return {"rows": rows, "headers": headers, "noteRows": note_rows,
            "adapters": dict(adapters), "elements": dict(elements)}


BOM_JS = r'''
import fs from "node:fs/promises";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";
const [input, output, previewDir] = process.argv.slice(2);
const data = JSON.parse(await fs.readFile(input, "utf8"));
const wb = Workbook.create();
const ws = wb.worksheets.add("Sheet1");
const count = data.rows.length;
ws.showGridLines = false;
ws.getRange(`A1:B${count}`).values = data.rows;
ws.getRange(`A1:B${count}`).format.font = {name: "Arial", size: 11, color: "#111111"};
ws.getRange(`A1:B${count}`).format.verticalAlignment = "center";
ws.getRange(`A1:B${count}`).format.rowHeight = 24;
ws.getRange(`A1:A${count}`).format.columnWidth = 100;
ws.getRange(`B1:B${count}`).format.columnWidth = 8;
ws.getRange(`B1:B${count}`).setNumberFormat("0");
ws.getRange(`B1:B${count}`).format.horizontalAlignment = "right";
ws.getRange("A1").format.font.bold = true;
ws.getRange("A1").format.font.size = 14;
ws.getRange("A1:B1").format.rowHeight = 30;
for (const n of data.headers) {
  ws.getRange(`A${n}:B${n}`).format.font.bold = true;
  ws.getRange(`A${n}:B${n}`).format.borders = {bottom: {style: "thin", color: "#999999"}};
}
for (let n = 1; n <= count; n++) {
  const label = data.rows[n-1][0];
  if (typeof label === "string" && label.length > 92) {
    ws.getRange(`A${n}`).format.wrapText = true;
    ws.getRange(`A${n}:B${n}`).format.rowHeight = 18 * Math.ceil(label.length/92) + 8;
  }
}
wb.recalculate();
const checked = ws.getRange(`A1:B${count}`).values;
if (JSON.stringify(checked) !== JSON.stringify(data.rows)) throw new Error("BOM values changed during authoring");
console.log((await wb.inspect({kind:"table", range:"Sheet1!A1:B12", include:"values,formulas", tableMaxRows:12, tableMaxCols:2})).ndjson);
console.log((await wb.inspect({kind:"match", searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!", options:{useRegex:true,maxResults:20}, summary:"BOM formula error scan"})).ndjson);
if (previewDir) {
  await fs.mkdir(previewDir, {recursive:true});
  for (let start = 1; start <= count; start += 27) {
    const end = Math.min(start + 26, count);
    const picture = await wb.render({sheetName:"Sheet1", range:`A${start}:B${end}`, scale:1.5, format:"png"});
    await fs.writeFile(`${previewDir}/bom_rows_${start}_${end}.png`, new Uint8Array(await picture.arrayBuffer()));
  }
}
const xlsx = await SpreadsheetFile.exportXlsx(wb);
await xlsx.save(output);
'''


def render_bom(data, target, node, node_modules, work_dir, preview_dir):
    if not node.is_file() or not node_modules.is_dir():
        raise FileNotFoundError("Supply the bundled Node executable and node_modules with --node and --node-modules")
    work_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="board-bom-", dir=work_dir) as scratch_name:
        scratch = Path(scratch_name).resolve()
        if not scratch.is_relative_to(work_dir.resolve()):
            raise ValueError("Temporary directory escaped the chosen work directory")
        link = scratch / "node_modules"
        try:
            if os.name == "nt":
                # Native PowerShell creates the junction; no string-built shell command.
                linker = scratch / "link.ps1"
                linker.write_text('param([string]$LinkPath, [string]$PackagePath)\n'
                                  'New-Item -ItemType Junction -Path $LinkPath -Target $PackagePath | Out-Null\n',
                                  encoding="utf-8")
                subprocess.run(["powershell", "-NoProfile", "-File", str(linker),
                    str(link), str(node_modules.resolve())], check=True)
            else:
                link.symlink_to(node_modules.resolve(), target_is_directory=True)
            (scratch / "bom.mjs").write_text(BOM_JS, encoding="utf-8")
            (scratch / "bom.json").write_text(json.dumps(data), encoding="utf-8")
            subprocess.run([str(node), str(scratch / "bom.mjs"), str(scratch / "bom.json"),
                            str(scratch / "bom.xlsx"), str(preview_dir.resolve()) if preview_dir else ""],
                           cwd=scratch, check=True)
            # Move only the deliverable; artifact-tool diagnostic sidecars stay temporary.
            (scratch / "bom.xlsx").replace(target.resolve())
        finally:
            # Remove only the link itself before TemporaryDirectory removes our files.
            if link.is_symlink():
                link.unlink()
            elif link.exists() and os.name == "nt":
                os.rmdir(link)


def render_tapping(report, holes, edges, plate, args):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    from matplotlib.patches import Circle, Rectangle

    pw, ph, frame = 594.0, 420.0, 8.0  # A2 landscape, matching the branch sheets.
    ink, grey, red, blue = "#101010", "#909090", "#d0021b", "#0047b3"
    box = edges["bbox"]
    x0, y0, x1, y1 = box
    width, height = x1-x0, y1-y0
    thickness = plate["bbox"][5]-plate["bbox"][2]
    fig = plt.figure(figsize=(pw/25.4, ph/25.4))

    def text_mm(x, y, text, **kwargs):
        return fig.text(x/pw, y/ph, text, **kwargs)

    fig.patches.append(Rectangle((frame/pw, frame/ph), (pw-2*frame)/pw,
                                (ph-2*frame)/ph, transform=fig.transFigure,
                                fill=False, lw=1.1, ec=ink))
    fig.patches.append(Rectangle((frame/pw, 371/ph), (pw-2*frame)/pw, 41/ph,
                                transform=fig.transFigure, fill=False, lw=.9, ec=ink))
    text_mm(14, 400, args.title.upper() + " - WHICH HOLES ARE TAPPED",
            fontsize=14, weight="bold", va="center")
    text_mm(14, 388, f"Geometry: {args.step_name}\nThis sheet identifies threaded and clearance holes. Drill sizes, tolerances, material and finish: shop standard.",
            fontsize=8, va="center", linespacing=1.5)
    relief = report.get('aom_machining_relief_audit') or {}
    if relief.get('passed') is True:
        parameters = relief.get('parameters', {})
        if (relief.get('schema') not in ('aom_machining_relief_audit/1', 'aom_machining_relief_audit/2')
                or parameters.get('side_clearance_mm') != 6
                or parameters.get('front_relief_depth_mm') != 4
                or parameters.get('front_corner_radius_mm') != 3):
            raise ValueError('Tapping-sheet AOM note requires matching machining relief evidence')
        if relief.get('schema') == 'aom_machining_relief_audit/2':
            seats = relief.get('seats', [])
            if (parameters.get('side_clearance_datum') != 'locating lip outer face'
                    or parameters.get('side_corner_radius_mm') != 3
                    or len(seats) != relief.get('seat_count') or not seats
                    or not all(s.get('side_channel', {}).get('passed') is True for s in seats)):
                raise ValueError('Flush AOM wall note requires actual lip-face clearance evidence for every seat')
            note = 'AOM: 6 mm from locating-lip outer face; flush side wall; R3 corners; front relief 4 mm deep. Bearing faces and height unchanged.'
        else:
            note = 'AOM MACHINING: 6 mm side clearance; front relief 4 mm deep, R3 corners. Bearing faces and installation height unchanged.'
        text_mm(14, 382, note,
                fontsize=8, va='center')
    text_mm(580, 378, f"PLATE  {width:.2f} x {height:.2f} x {thickness:.2f} mm    UNITS mm    COORDINATES = STEP FILE",
            fontsize=8, ha="right", va="center", family="DejaVu Sans Mono")
    left, bottom, avail_w, avail_h = 31, 71, 539, 286
    scale = min(avail_w/width, avail_h/height, 1.0)
    left += (avail_w-width*scale)/2
    bottom += (avail_h-height*scale)/2
    ax = fig.add_axes([left/pw, bottom/ph, width*scale/pw, height*scale/ph])
    ax.set(xlim=(x0, x1), ylim=(y0, y1), aspect="equal")
    ax.axis("off")
    for z, polylines in sorted(edges["levels"].items(), key=lambda kv: float(kv[0])):
        top = abs(float(z)-edges["top_z"]) < .05
        ax.add_collection(LineCollection(polylines, colors=ink if top else grey,
                          linewidths=.75 if top else .4, zorder=3 if top else 2))
    taps = [h for h in holes["features"] if h["kind"] == "TAP"]
    plain = [h for h in holes["features"] if h["kind"] == "PLAIN"]
    ring = 3.1/scale
    for hole in taps:
        ax.add_patch(Circle((hole["x"], hole["y"]), ring, fill=False, ec=red, lw=1.05, zorder=5, clip_on=False))
    bolt_centres = report.get("mount_holes_mm", [])
    callouts = []
    for hole in plain:
        x, y = hole["x"], hole["y"]
        if bolt_centres:
            near = min(bolt_centres, key=lambda p: math.hypot(p[0]-x, p[1]-y))
            if math.hypot(near[0]-x, near[1]-y) < .03:
                x, y = near[:2]
        radius = 7.0/scale
        ax.add_patch(Circle((x,y), radius, fill=False, ec=blue, lw=2, zorder=7, clip_on=False))
        d = radius/math.sqrt(2)
        ax.plot([x-d, x+d], [y-d, y+d], color=blue, lw=1.8, zorder=8, clip_on=False)
        ax.plot([x-d, x+d], [y+d, y-d], color=blue, lw=1.8, zorder=8, clip_on=False)
        sx, sy = (1 if x < (x0+x1)/2 else -1), (1 if y < (y0+y1)/2 else -1)
        row = [other for other in plain if abs(other['y']-y)<.03]
        if len(row)>1 and y>(y0+y1)/2:
            # Labels outside a shared upper row keep leaders from crossing.
            row_midpoint = sum(other['x'] for other in row)/len(row)
            sx = -1 if x<row_midpoint else 1
        annotation = ax.annotate(f"DO NOT TAP\nX {x:.2f}  Y {y:.2f}", xy=(x,y),
                    xytext=(x+sx*.12*width, y+sy*.09*height), color=blue,
                    fontsize=8.5, weight="bold", ha="left" if sx>0 else "right",
                    va="bottom" if sy>0 else "top", zorder=10,
                    arrowprops={"arrowstyle":"-|>", "color":blue, "lw":1.3,
                                "shrinkA":0, "shrinkB":12},
                    bbox={"boxstyle":"round,pad=0.3", "fc":"white", "ec":blue, "lw":1})
        callouts.append(annotation)
    # Nearby top bolts can send both labels into the same central space.
    # Stagger text boxes using their rendered bounds, leaving hole positions
    # and leader endpoints unchanged.
    placed_boxes = []
    for annotation in callouts:
        for _ in range(len(callouts)+1):
            fig.canvas.draw()
            box = annotation.get_bbox_patch().get_window_extent(fig.canvas.get_renderer()).expanded(1.08, 1.15)
            if not any(box.overlaps(previous) for previous in placed_boxes):
                placed_boxes.append(box)
                break
            tx, ty = annotation.get_position()
            annotation.set_position((tx, ty-12./scale))
        else:
            raise ValueError("Could not separate platform-hole coordinate callouts")
    for value in range(math.ceil(x0/50)*50, math.floor(x1/50)*50+1, 50):
        ax.plot([value,value], [y0,y0-4/scale], color=ink, lw=.5, clip_on=False)
        ax.text(value,y0-6/scale,str(value),fontsize=7,ha="center",va="top",clip_on=False)
    for value in range(math.ceil(y0/50)*50, math.floor(y1/50)*50+1, 50):
        ax.plot([x0,x0-4/scale], [value,value], color=ink, lw=.5, clip_on=False)
        ax.text(x0-6/scale,value,str(value),fontsize=7,ha="right",va="center",clip_on=False)
    text_mm(left, 56, f"DATUM  X {x0:.3f}  Y {y0:.3f}  (lower-left outline corner)", fontsize=8)
    footer = fig.add_axes([12/pw, 12/ph, 570/pw, 35/ph])
    footer.set(xlim=(0,570), ylim=(0,35)); footer.axis("off")
    footer.add_patch(Rectangle((0,0),570,35,fill=False,ec=ink,lw=1.1,clip_on=False))
    tap_sizes = Counter(thread_name(h) for h in taps)
    plain_sizes = Counter(thread_name(h) for h in plain)
    tap_text = ", ".join(f"{n} x {name} UNC" for name,n in sorted(tap_sizes.items()))
    plain_text = ", ".join(f"{n} x {name} clearance" for name,n in sorted(plain_sizes.items()))
    footer.add_patch(Circle((10,24),3.3,fill=False,ec=red,lw=1.3))
    footer.text(20,24,"TAP - "+tap_text,fontsize=12,weight="bold",color=red,va="center")
    footer.add_patch(Circle((10,10),3.3,fill=False,ec=blue,lw=1.8))
    footer.plot([7.7,12.3],[7.7,12.3],color=blue,lw=1.5)
    footer.plot([7.7,12.3],[12.3,7.7],color=blue,lw=1.5)
    footer.text(20,10,"DO NOT TAP - "+plain_text,fontsize=12,weight="bold",color=blue,va="center")
    footer.plot([355,355],[3,32],color=ink,lw=.8)
    footer.text(366,25,f"{len(holes['features'])} holes. Every hole is marked.",fontsize=9,va="center")
    footer.text(366,14,"Pocket corner radii are end-mill fillets, not holes.",fontsize=8.2,va="center")
    footer.text(562,4,f"SCALE 1 : {1/scale:.2f}",fontsize=8,ha="right",weight="bold")
    target = args.output_dir / (args.stem + "_baseplate_TAP_or_NOT")
    fig.savefig(target.with_suffix(".pdf"))
    fig.savefig(target.with_suffix(".png"), dpi=args.dpi)
    plt.close(fig)
    return {"tap":len(taps), "plain":len(plain), "total":len(holes["features"]),
            "size_mm":[width,height,thickness]}


def main():
    runtime = Path.home()/".cache/codex-runtimes/codex-primary-runtime/dependencies/node"
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("report", "holes", "edges", "output-dir"):
        parser.add_argument("--"+name, type=Path, required=True)
    parser.add_argument("--stem", default="TA_Board_V9")
    parser.add_argument("--title", default="TA board V9")
    parser.add_argument("--step-name", required=True, help="Filename of this export's baseplate STEP")
    parser.add_argument("--node", type=Path, default=runtime/"bin/node.exe")
    parser.add_argument("--node-modules", type=Path, default=runtime/"node_modules")
    parser.add_argument("--work-dir", type=Path, default=Path("work/document-build"))
    parser.add_argument("--preview-dir", type=Path, help="Write BOM QA images here for visual inspection")
    parser.add_argument("--dpi", type=int, default=230)
    parser.add_argument("--skip-bom", action="store_true", help="Render only the tapping sheet")
    args = parser.parse_args()
    if Path(args.stem).name != args.stem or Path(args.step_name).name != args.step_name:
        parser.error("--stem and --step-name must be filenames without directory components")
    report, holes, edges = (read_json(p) for p in [args.report,args.holes,args.edges])
    plate = validate_inputs(report,holes,edges)
    bom = build_bom(report,holes,args.title,args.step_name,args.report.name,
                    args.stem+"_baseplate_TAP_or_NOT.pdf")
    args.output_dir.mkdir(parents=True,exist_ok=True)
    if not args.skip_bom:
        render_bom(bom,args.output_dir/(args.stem+".xlsx"),args.node,args.node_modules,
                   args.work_dir,args.preview_dir)
    summary = render_tapping(report,holes,edges,plate,args)
    print(json.dumps({"outputs":str(args.output_dir.resolve()), "holes":summary,
                      "adapters":bom["adapters"], "elements":bom["elements"]},indent=2))


if __name__ == "__main__":
    main()
