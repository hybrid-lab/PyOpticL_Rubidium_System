"""Render a board validation JSON as a conservative, annotated XY plan.

Use the project-local Conda environment. Requires matplotlib; FreeCAD is not
needed. The report is the only geometry source. This is a presentation of saved
evidence, not a replacement for the 3D or projected-clearance audit.

Example::

    python tools/render_board_clearance.py --report TA_validation.json \
        --output TA_table_fit.png --title "TA board V9.9" --table

Hardware is drawn from per-object XY hulls when explicitly supplied as
``hull_xy_mm`` or ``projection_xy_mm``, otherwise from axis-aligned ``bbox``
envelopes. Bbox overlaps must not be interpreted as physical collisions.
``--table`` consumes table_envelope_audit/1 in report['table_envelope']; without
that audit it draws a labelled, centred 15 x 28 in reference frame only.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Patch, Polygon, Rectangle


PLATES = {"baseplate", "IntegralAOMBaseplate"}
MACHINING = {"IntegralAOMSeat", "CellPocketMachining", "SlidingCellSeat"}
COLORS = {
    "hardware": "#80909e", "adapter": "#2a966f", "mirror": "#4a78ac",
    "knob": "#a083bb", "cell": "#b49a65", "ta_cable": "#e69a28",
    "aom_sma": "#d65c65", "fiber_front": "#32a6ac", "clamp": "#d69a31",
    "cable_extension": "#c58414",
    "corridor": "#ceb144", "other_service": "#9c7db4",
}
BEAM_COLORS = ["#cf3d42", "#db811e", "#b49713", "#209565",
               "#287cc2", "#7656c1", "#cb4193"]


def finite(values):
    return all(isinstance(v, (int, float)) and math.isfinite(v) for v in values)


def points(value):
    if not isinstance(value, (list, tuple)) or len(value) < 3:
        return None
    if all(isinstance(p, (list, tuple)) and len(p) >= 2 and finite(p[:2]) for p in value):
        return [(float(p[0]), float(p[1])) for p in value]
    return None


def rectangle_points(bounds):
    x0, y0, x1, y1 = bounds
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def xy_bbox(obj):
    b = obj.get("bbox")
    if not isinstance(b, (list, tuple)) or len(b) != 6 or not finite(b):
        return None
    if b[3] <= b[0] or b[4] <= b[1]:
        return None
    return [b[0], b[1], b[3], b[4]]


def region_polygon(region):
    polygon = points(region.get("corners_xy_mm"))
    if polygon:
        return polygon
    origin, direction = region.get("origin_xy_mm"), region.get("direction_xy")
    length, width = region.get("length_mm"), region.get("width_mm")
    if not origin or not direction or not finite([*origin, *direction, length, width]):
        return None
    dx, dy = direction[:2]
    norm = math.hypot(dx, dy)
    if norm <= 0 or length <= 0 or width <= 0:
        return None
    dx, dy = dx/norm, dy/norm
    x, y = origin[:2]
    nx, ny = -dy*width/2, dx*width/2
    return [(x+nx, y+ny), (x+dx*length+nx, y+dy*length+ny),
            (x+dx*length-nx, y+dy*length-ny), (x-nx, y-ny)]


def category(obj):
    cls = obj.get("class", "").lower()
    if "adapter" in cls or cls in {"slide_mount", "cube_mount_halfinch"}:
        return "adapter"
    if "thumbscrew" in cls:
        return "knob"
    if "mirror" in cls and "km05" not in cls and "ka05" not in cls:
        return "mirror"
    if "slidingcell" in cls:
        return "cell"
    return "hardware"


def short_label(obj):
    cls, label = obj.get("class", ""), obj.get("label", obj["name"])
    if cls.startswith("TA_butterfly"):
        return "TA"
    if cls == "AOMO_3100_125":
        return label.replace("AOMO 3100-125", "AOM")
    if "isolator" in cls:
        return "Isolator"
    if cls == "SlidingCellEnclosure":
        return "Rb cell"
    if cls == "shutter_sr475":
        return "Shutter"
    if cls == "cube_splitter":
        return label.replace("Main power", "Main")
    if cls.startswith("fiberport_mount"):
        if label.startswith("Input"):
            return "Input"
        match = re.search(r"Output\s+(\d+)\b.*\(([^)]+)\)", label)
        if match:
            return f"Out {match[1]} ({match[2]})"
        return "AOM fiber" if "AOM branch" in label else "Direct fiber"
    return None


def beam_color(name, index):
    if name.startswith("Common") or name == "TA supply":
        return BEAM_COLORS[0]
    if name == "AOM branch":
        return BEAM_COLORS[4]
    if name == "Reflected branch":
        return BEAM_COLORS[3]
    return BEAM_COLORS[index % len(BEAM_COLORS)]


def render(report, output, title=None, table=False):
    objects = report.get("objects", [])
    plates = [o for o in objects if o.get("class") in PLATES]
    if len(plates) != 1 or not xy_bbox(plates[0]):
        raise ValueError("Report must contain one baseplate with a finite bbox")
    plate_bounds = xy_bbox(plates[0])
    plate_size = report.get("plate_size_mm", [])
    regions = report.get("service_clearance", {}).get("regions")
    if regions is None:
        regions = report.get("service_regions", [])
    fibers = report.get("fiber_clearance", {}).get("fibers", [])
    audit = report.get("table_envelope", {}) if table else {}
    extension = audit.get("conservative_cable_beyond_edge", {})
    table_bounds = audit.get("table_bounds_in_board_frame_xy_mm")
    occupied = audit.get("occupied_bounds_xy_mm")
    if not table_bounds and audit.get("table_bounds_xy_mm"):
        tx, ty = audit.get("translation_xy_mm", [0., 0.])
        b = audit["table_bounds_xy_mm"]
        table_bounds = [b[0]-tx, b[1]-ty, b[2]-tx, b[3]-ty]

    hardware = []
    extent_points = rectangle_points(plate_bounds)
    for obj in objects:
        cls = obj.get("class", "")
        if not cls or cls in PLATES | MACHINING | {"baseplate_mount", "BareTappedHole"}:
            continue
        poly = points(obj.get("projection_xy_mm")) or points(obj.get("hull_xy_mm"))
        b = xy_bbox(obj)
        if poly or b:
            poly = poly or rectangle_points(b)
            hardware.append((obj, poly))
            extent_points.extend(poly)
    for region in regions:
        extent_points.extend(region_polygon(region) or [])
    extent_points.extend(region_polygon(extension) or [])
    for fiber in fibers:
        extent_points.extend(points(fiber.get("corridor_xy_mm")) or [])
        extent_points.extend(points(fiber.get("clamp_reserved_span_xy_mm")) or [])
    xvals, yvals = zip(*extent_points)
    visible_bounds = [min(xvals), min(yvals), max(xvals), max(yvals)]
    if table and not table_bounds:
        # This fallback illustrates possible placement; it is not an audit.
        width, height = (381., 711.2) if plate_bounds[3]-plate_bounds[1] >= plate_bounds[2]-plate_bounds[0] else (711.2, 381.)
        cx, cy = (min(xvals)+max(xvals))/2, (min(yvals)+max(yvals))/2
        table_bounds = [cx-width/2, cy-height/2, cx+width/2, cy+height/2]
    if table_bounds:
        visible_bounds = [min(visible_bounds[0], table_bounds[0]), min(visible_bounds[1], table_bounds[1]),
                          max(visible_bounds[2], table_bounds[2]), max(visible_bounds[3], table_bounds[3])]
    portrait = visible_bounds[3]-visible_bounds[1] > visible_bounds[2]-visible_bounds[0]
    fig = plt.figure(figsize=(11.5, 12.8) if portrait else (16., 10.2), facecolor="white")
    grid = fig.add_gridspec(1, 2, width_ratios=(3.4, 1.25) if portrait else (4.5, 1.25),
                           left=.07, right=.985, bottom=.09, top=.90, wspace=.06)
    ax, notes = fig.add_subplot(grid[0]), fig.add_subplot(grid[1])
    notes.axis("off")
    legend, used = [], set()

    def polygon(poly, key, label, alpha=.18, hatch=None, linestyle="-", zorder=2):
        if not poly:
            return
        color = COLORS.get(key, key)
        ax.add_patch(Polygon(poly, closed=True, facecolor=color, edgecolor=color,
                             alpha=alpha, linewidth=.8, hatch=hatch, linestyle=linestyle, zorder=zorder))
        if label and key not in used:
            legend.append(Patch(facecolor=color, edgecolor=color, alpha=.4, hatch=hatch, label=label))
            used.add(key)

    if table_bounds:
        tb = table_bounds
        ax.add_patch(Rectangle((tb[0], tb[1]), tb[2]-tb[0], tb[3]-tb[1], facecolor="#f5f7fa",
                               edgecolor="#52647b", linewidth=2., zorder=0))
        ax.text((tb[0]+tb[2])/2, tb[3]+7., "15 × 28 in table", ha="center", va="bottom", fontsize=10, color="#52647b")
    b = plate_bounds
    ax.add_patch(Rectangle((b[0], b[1]), b[2]-b[0], b[3]-b[1], facecolor="#fafbfb",
                           edgecolor="#303b47", linewidth=1.7, zorder=1))
    if len(plate_size) >= 2:
        ax.add_patch(Rectangle((0., 0.), plate_size[0], plate_size[1], fill=False,
                               edgecolor="#aab5bf", linestyle=":", linewidth=.7, zorder=1))
    labels = {"adapter": "Adapters / seats (green)", "mirror": "Mirrors / mirror mounts",
              "knob": "Adjustment knobs", "cell": "Cell enclosure", "hardware": "Other component envelopes"}
    # Recessed adapters remain visible on this installation plan.
    hardware.sort(key=lambda item: category(item[0]) != "adapter")
    for obj, poly in hardware:
        key = category(obj)
        polygon(poly, key, labels[key], alpha=.28 if key == "adapter" else .36, zorder=2)

    for region in regions:
        key = region.get("kind", "other_service")
        if key not in COLORS:
            key = "other_service"
        length, width = region.get("length_mm", 0), region.get("width_mm", 0)
        label = {"ta_cable": f"TA cable {length:g} × {width:g} mm",
                 "aom_sma": f"RF elbow {length:g} × {width:g} mm",
                 "fiber_front": "Fiber front access (saved sizes)"}.get(key, "Other service region")
        polygon(region_polygon(region), key, label, alpha=.22, linestyle="--", zorder=3)
    if extension:
        polygon(region_polygon(extension), "cable_extension", "Extra 4 in beyond plate edge",
                alpha=.16, hatch="..", linestyle="--", zorder=3)
    for fiber in fibers:
        polygon(points(fiber.get("corridor_xy_mm")), "corridor", "Fiber tail corridor", alpha=.16, linestyle=":", zorder=3)
        poly = points(fiber.get("clamp_reserved_span_xy_mm"))
        bands = [poly] if poly else [points(p) for p in fiber.get("clamp_bands_xy_mm", [])]
        for band in bands:
            polygon(band, "clamp", "Tail clamp + required margins", alpha=.25, hatch="///", zorder=3)
        for pair in fiber.get("hole_pairs_xy_mm", []):
            for x, y in pair:
                ax.plot(x, y, "o", ms=2.6, color="#a85322", zorder=7)

    # Every saved segment is drawn, including any real AOM diffraction kink.
    path_legend = []
    for index, path in enumerate(report.get("paths", [])):
        pts = path.get("points", [])
        if len(pts) < 2:
            continue
        color = beam_color(path["name"], index)
        radii = path.get("envelope", [])
        if isinstance(radii, (int, float)):
            radii = [radii]*len(pts)
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            dx, dy = b[0]-a[0], b[1]-a[1]
            norm = math.hypot(dx, dy)
            if norm > 0 and len(radii) > i+1:
                nx, ny = -dy/norm, dx/norm
                r0, r1 = radii[i], radii[i+1]
                envelope = [(a[0]+nx*r0, a[1]+ny*r0), (b[0]+nx*r1, b[1]+ny*r1),
                            (b[0]-nx*r1, b[1]-ny*r1), (a[0]-nx*r0, a[1]-ny*r0)]
                ax.add_patch(Polygon(envelope, facecolor=color, edgecolor="none", alpha=.15, zorder=4))
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color, linewidth=1.25, zorder=5)
        name = path["name"].replace("Common cylindrical conditioning provision", "Common conditioning").replace("Common spherical telescope", "Common telescope / cell")
        path_legend.append(Line2D([0], [0], color=color, lw=1.7, label=name))

    for obj in objects:
        if obj.get("class") == "baseplate_mount":
            x, y = obj["position"][:2]
            ax.add_patch(Circle((x, y), 4.9, facecolor="#435361", edgecolor="white", linewidth=.9, zorder=6))
            ax.add_patch(Circle((x, y), 2.8, facecolor="white", edgecolor="none", zorder=7))
        elif obj.get("class") == "BareTappedHole" and "station" in obj.get("label", "").lower():
            x, y = obj["position"][:2]
            ax.plot(x, y, "+", color="#59636b", ms=5, mew=.8, zorder=7)
        label = short_label(obj)
        if label and obj.get("position"):
            x, y = obj["position"][:2]
            ax.annotate(label, (x, y), xytext=(0, 6), textcoords="offset points", ha="center", va="bottom",
                        fontsize=7.4, color="#283746", zorder=8,
                        bbox=dict(facecolor="white", edgecolor="none", alpha=.85, pad=1.1))

    if occupied and table:
        b = occupied
        ax.add_patch(Rectangle((b[0], b[1]), b[2]-b[0], b[3]-b[1], fill=False,
                               edgecolor="#6c586d", linewidth=.9, linestyle=(0, (4, 3)), zorder=6))
        legend.append(Line2D([0], [0], color="#6c586d", linestyle="--", label="Audited occupied envelope"))
    ax.set_aspect("equal", adjustable="box")
    margin = max(12., .035*max(visible_bounds[2]-visible_bounds[0], visible_bounds[3]-visible_bounds[1]))
    ax.set_xlim(visible_bounds[0]-margin, visible_bounds[2]+margin)
    ax.set_ylim(visible_bounds[1]-margin, visible_bounds[3]+margin+8.)
    ax.set_xlabel("Board x (mm)", fontsize=9)
    ax.set_ylabel("Board y (mm)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(color="#a0a9b4", alpha=.17, linewidth=.5)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#cbd1d8")
    notes.legend(handles=legend+path_legend, loc="upper left", frameon=False, fontsize=8.1,
                 handlelength=2., labelspacing=.68, borderaxespad=0.)

    audit_text = []
    if len(plate_size) >= 2:
        audit_text.append(f"Nominal plate: {plate_size[0]/25.4:g} × {plate_size[1]/25.4:g} in")
    pb = plate_bounds
    audit_text.append(f"Machined plate: {pb[2]-pb[0]:.2f} × {pb[3]-pb[1]:.2f} mm")
    if table:
        if audit and occupied:
            width, height = occupied[2]-occupied[0], occupied[3]-occupied[1]
            audit_text.append(f"Audited total extent: {width:.2f} × {height:.2f} mm\n({width/25.4:.2f} × {height/25.4:.2f} in)")
            result = "PASS" if audit.get("passed") is True else "NOT PASSED / NOT RECORDED"
            audit_text.append(f"Saved table-envelope check: {result}")
            audit_text.append("Table fit permits translation; table-hole grid alignment is not verified.")
        else:
            audit_text.append("Table placement is a centred reference only; no saved table-envelope audit.")
    audit_text.extend(["Conservative XY envelopes, not exact CAD silhouettes. Rectangle overlaps do not establish a collision.",
                       "Service widths and connector bend radii retain the assumptions in the source report."])
    if report.get("projection_audit", {}).get("optical_path_readiness") == "blocked_by_unmachined_cell_covers":
        audit_text.append("Cell covers have no beam apertures. The optical path is not ready for operation.")
    if not any(r.get("kind") == "fiber_front" for r in regions):
        audit_text.append("No separate fiber-front service regions are recorded in this report.")
    note = "\n\n".join(textwrap.fill(t, 37) for t in audit_text)
    notes.text(0., .03, note, va="bottom", ha="left", fontsize=8., color="#4f5965", transform=notes.transAxes)
    fig.suptitle(title or report.get("document", "Board clearance plan"), fontsize=15, fontweight="semibold", y=.963)
    fig.text(.07, .925, "XY installation plan · geometry and service reservations from the validation report", fontsize=10, color="#536273")
    fig.text(.07, .028, "Beam lines are nominal axes; translucent ribbons show the reported beam envelope. Dimensions are millimetres unless labelled.", fontsize=8, color="#596673")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, facecolor="white")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--title")
    parser.add_argument("--table", action="store_true", help="Show the 15 x 28 in table envelope")
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8-sig"))
    render(report, args.output, args.title, args.table)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
