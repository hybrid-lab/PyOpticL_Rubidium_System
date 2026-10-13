"""Read-only evidence for the ideal KM100PM sphere/cone kinematic joint.

Call audit(vertices, facets, source_stl_path=...) with the actual native mesh
in its KM-root local frame (the frame after optomech._import_stl).  A FreeCAD
Mesh may be passed instead of vertices/facets; its Topology must already be in
that local frame.  This module does not change the mesh or access a document.

The result proves nominal sphere/cone geometry, not a collision-free sweep.
The ideal maintained-contact assumption is explicit.  No real assembly
tolerance, contact play, preload loss or deformation is included.
"""

import hashlib
import itertools
import math
from pathlib import Path

import numpy as np


SPECIFICATION_URL = (
    "https://www.thorlabs.us/newgrouppage9.cfm?objectgroup_id=1811&pn=KPY1"
)
DRAWING_MIRROR_URL = (
    "https://oxxius.ru/upload/iblock/f4c/"
    "wz2q1sq0ij0hxqk9ovbhm8jlocf8jwp2/TTN005954_E0W.pdf"
)
_IMPORT_ROTATION = np.array([[0., 0., -1.], [-1., 0., 0.], [0., 1., 0.]])
_IMPORT_TRANSLATION = np.array([-8.877, 38.1, -6.731])
_EXPECTED_BOUNDS = np.array([
    -37.278950, -13.715717, -7.365717, 15.875300, 38.728116, 45.078117
])


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _topology(vertices, facets):
    if facets is None:
        vertices, facets = vertices.Topology
    points = np.asarray([tuple(p) for p in vertices], dtype=float)
    faces = np.asarray(facets, dtype=np.int64)
    if (points.ndim != 2 or points.shape[1] != 3 or len(points) == 0
            or not np.all(np.isfinite(points)) or faces.ndim != 2
            or faces.shape[1] != 3 or len(faces) == 0
            or np.min(faces) < 0 or np.max(faces) >= len(points)):
        raise ValueError("Finite vertices and valid triangular facets are required")
    # Merge exact coordinate duplicates, as a connected-shell test must not
    # depend on whether an STL reader shares coincident vertex indices.
    points, inverse = np.unique(points, axis=0, return_inverse=True)
    faces = inverse[faces]
    if np.any((faces[:, 0] == faces[:, 1]) | (faces[:, 1] == faces[:, 2])
              | (faces[:, 0] == faces[:, 2])):
        raise ValueError("Degenerate triangle indices")
    return points, faces


def _components(points, faces):
    parent = list(range(len(points)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for face in faces:
        root = find(int(face[0]))
        for index in face[1:]:
            other = find(int(index))
            if other != root:
                parent[other] = root
    labels = np.fromiter((find(i) for i in range(len(points))), int, len(points))
    face_labels = labels[faces[:, 0]]
    # Preserve first-facet order, making indices comparable with native
    # getSeparateComponents for this source, without relying on those indices.
    ordered = list(dict.fromkeys(face_labels.tolist()))
    parts = []
    for index, label in enumerate(ordered):
        ids = np.flatnonzero(labels == label)
        face_ids = np.flatnonzero(face_labels == label)
        q = points[ids]
        parts.append({"index": index, "vertex_ids": ids,
                      "facet_ids": face_ids, "points": q})
    return parts


def _read_source(path):
    data = Path(path).read_bytes()
    count = int.from_bytes(data[80:84], 'little')
    if count < 1 or len(data) != 84+50*count:
        raise ValueError("A complete nonempty binary STL is required")
    records = np.frombuffer(data, dtype=np.dtype([
        ('normal', '<f4', (3,)), ('vertices', '<f4', (3, 3)), ('attribute', '<u2')
    ]), offset=84)
    vertices = records['vertices'].reshape(-1, 3).astype(float)
    vertices = vertices @ _IMPORT_ROTATION.T + _IMPORT_TRANSLATION
    return _topology(vertices, np.arange(len(vertices)).reshape(-1, 3))


def _source_correspondence(points, faces, source, tolerance):
    """Prove every triangle matches the supplied STL, allowing native rounding."""
    expected, expected_faces = _read_source(source)
    if len(points) != len(expected) or len(faces) != len(expected_faces):
        raise ValueError("Native vertex/facet counts differ from the supplied STL")
    buckets = {}
    cells = np.floor(expected/tolerance).astype(np.int64)
    for index, cell in enumerate(cells):
        buckets.setdefault(tuple(cell), []).append(index)
    offsets = tuple(itertools.product((-1, 0, 1), repeat=3))
    mapping, residual = [], 0.
    for point in points:
        cell = np.floor(point/tolerance).astype(np.int64)
        candidates = [index for offset in offsets
                      for index in buckets.get(tuple(cell+offset), ())]
        if not candidates:
            raise ValueError("Native vertex has no source-STL counterpart")
        distances = np.max(np.abs(expected[candidates]-point), axis=1)
        nearest = int(np.argmin(distances))
        error = float(distances[nearest])
        if error > tolerance:
            raise ValueError("Native vertex differs from supplied STL beyond tolerance")
        mapping.append(candidates[nearest])
        residual = max(residual, error)
    if len(set(mapping)) != len(expected):
        raise ValueError("Native/source correspondence is not one-to-one")
    mapped = np.sort(np.asarray(mapping)[faces], axis=1)
    expected_faces = np.sort(expected_faces, axis=1)
    canonical = lambda rows: rows[np.lexsort((rows[:, 2], rows[:, 1], rows[:, 0]))]
    if not np.array_equal(canonical(mapped), canonical(expected_faces)):
        raise ValueError("Native triangle connectivity differs from supplied STL")
    return {"passed": True, "unique_vertices": len(points), "facets": len(faces),
            "maximum_vertex_coordinate_residual_mm": residual,
            "method": "One-to-one nearby-vertex matching and exact unordered triangle multiset equality; tolerates native float rounding, not missing or substituted faces."}


def _sphere(points):
    mean = np.mean(points, axis=0)
    q = points - mean
    fitted, _, rank, _ = np.linalg.lstsq(
        np.c_[2*q, np.ones(len(q))], np.sum(q*q, axis=1), rcond=None
    )
    radius_squared = fitted[3] + fitted[:3] @ fitted[:3]
    if rank != 4 or radius_squared <= 0:
        return None
    center = fitted[:3] + mean
    radius = math.sqrt(float(radius_squared))
    residual = float(np.max(np.abs(np.linalg.norm(points-center, axis=1)-radius)))
    return {"center_km_local_mm": center.tolist(), "radius_mm": radius,
            "maximum_radial_residual_mm": residual}


def _circle_sections(points, axis, tolerance):
    """Fit complete polygonal rings on planes normal to a candidate axis."""
    transverse = [i for i in range(3) if i != axis]
    ordered = points[np.argsort(points[:, axis])]
    groups, current = [], []
    for point in ordered:
        if current and point[axis]-current[0][axis] > 2*tolerance:
            groups.append(np.asarray(current)); current = []
        current.append(point)
    if current:
        groups.append(np.asarray(current))
    result = []
    for group in groups:
        q = np.unique(group[:, transverse], axis=0)
        if len(q) < 20:
            continue
        mean = q.mean(0); v = q-mean
        fit, _, rank, _ = np.linalg.lstsq(np.c_[2*v, np.ones(len(v))],
                                         np.sum(v*v, axis=1), rcond=None)
        rsq = fit[2]+fit[:2]@fit[:2]
        if rank != 3 or rsq <= 0:
            continue
        center = fit[:2]+mean; radius = math.sqrt(float(rsq))
        residual = float(np.max(np.abs(np.linalg.norm(q-center, axis=1)-radius)))
        angles = np.sort(np.arctan2(q[:, 1]-center[1], q[:, 0]-center[0]))
        gap = float(np.max(np.diff(np.r_[angles, angles[0]+2*math.pi])))
        if residual <= tolerance and gap <= math.radians(20):
            result.append({'axis_coordinate_mm': float(group[:, axis].mean()),
                           'center_transverse_mm': center.tolist(), 'radius_mm': radius,
                           'maximum_radial_residual_mm': residual,
                           'ring_vertices': len(q), 'maximum_sector_deg': math.degrees(gap)})
    return result


def _hull2(points):
    ordered = sorted(set(map(tuple, points)))
    cross = lambda a, b, c: (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    lower, upper = [], []
    for point in ordered:
        while len(lower) > 1 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    for point in reversed(ordered):
        while len(upper) > 1 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return np.asarray(lower[:-1]+upper[:-1])


def _actuator_evidence(parts, points, faces, pivot, spheres, tolerance):
    """Nominal flat / two-rod contacts and the fixed-axis screw travel bound.

    The two equal parallel rods constrain the lower ball centre to one line
    parallel to local Y on the continuously maintained rear contact branch.
    Both that line and the upper flat contact keep the ball's front-frame X
    coordinate constant. This supplies the axial-travel equation; it is not
    inferred from the displacement of a fixed material point on the plate.
    """
    balls = {s['component']: s for s in spheres}
    if 12 not in balls or 13 not in balls:
        raise ValueError('Expected unchanged upper/lower actuator contact-ball components')
    upper, lower = (np.asarray(balls[i]['center_km_local_mm']) for i in (12, 13))
    ball_radius = balls[13]['radius_mm']
    theta = math.radians(4.)

    # Actual upper contact pad: require an entire filled planar cap, and
    # measure its inscribed polygonal radius about the sphere's contact point.
    part = parts[4]; cap_x = float(part['points'][:, 0].min())
    cap_faces = faces[part['facet_ids']]
    cap_faces = cap_faces[np.all(np.abs(points[cap_faces, 0]-cap_x) <= tolerance, axis=1)]
    if len(cap_faces) < 10 or abs(cap_x-upper[0]-balls[12]['radius_mm']) > tolerance:
        raise ValueError('Upper ball is not tangent to the complete front-pad plane')
    yz = points[np.unique(cap_faces), 1:]; hull = _hull2(yz)
    if len(hull) < 20:
        raise ValueError('Upper flat pad boundary is incomplete')
    cross2 = lambda a, b: float(a[0]*b[1]-a[1]*b[0])
    twice_area = lambda tri: cross2(tri[1]-tri[0], tri[2]-tri[0])
    cap_area = sum(abs(twice_area(points[face, 1:]))/2 for face in cap_faces)
    hull_area = abs(sum(cross2(a, b) for a, b in zip(hull, np.roll(hull, -1, axis=0))))/2
    if abs(cap_area-hull_area) > 10*tolerance:
        raise ValueError('Upper contact-plane triangles do not fill their boundary')
    cap_margin = min(cross2(b-a, upper[1:]-a)/np.linalg.norm(b-a)
                     for a, b in zip(hull, np.roll(hull, -1, axis=0)))
    if cap_margin <= 0:
        raise ValueError('Upper contact point is outside the actual filled pad')

    rods = []
    for index in (5, 6):
        rings = [r for r in _circle_sections(parts[index]['points'], 1, tolerance)
                 if abs(r['radius_mm']-.79375) <= tolerance]
        if len(rings) < 3:
            raise ValueError('Each lower contact rod needs three complete unchanged cylindrical rings')
        centers = np.asarray([r['center_transverse_mm'] for r in rings])
        center = centers.mean(0)
        if np.max(np.abs(centers-center)) > tolerance:
            raise ValueError('Lower contact-rod rings are not coaxial')
        radius = float(np.mean([r['radius_mm'] for r in rings]))
        distance = float(np.linalg.norm(lower[[0, 2]]-center))
        if abs(distance-radius-ball_radius) > tolerance:
            raise ValueError('Lower ball does not remain tangent to both original rods')
        interval = [min(r['axis_coordinate_mm'] for r in rings), max(r['axis_coordinate_mm'] for r in rings)]
        # Require actual lateral faces spanning every neighbouring section.
        vertices = points[faces[parts[index]['facet_ids']]]
        radial = np.linalg.norm(vertices[:, :, [0, 2]]-center, axis=2)
        wall = vertices[np.all(np.abs(radial-radius) <= tolerance, axis=1)]
        if len(wall) < 80 or abs(wall[:, :, 1].min()-interval[0]) > tolerance or abs(wall[:, :, 1].max()-interval[1]) > tolerance:
            raise ValueError('Actual rod cylinder wall does not span its fitted rings')
        rods.append({'component': index, 'axis_km_local': [0., 1., 0.],
                     'axis_center_xz_mm': center.tolist(), 'radius_mm': radius,
                     'effective_y_interval_mm': interval, 'rings': rings,
                     'lateral_facets': len(wall),
                     'sphere_tangency_residual_mm': abs(distance-radius-ball_radius)})
    c1, c2 = (np.asarray(r['axis_center_xz_mm']) for r in rods)
    if (abs(c1[0]-c2[0]) > tolerance or abs(c1[1]+c2[1]) > tolerance or
            abs(rods[0]['radius_mm']-rods[1]['radius_mm']) > tolerance or
            abs(lower[2]) > tolerance or not c1[1] > 0. > c2[1]):
        raise ValueError('Lower contact rods lack the original symmetric parallel arrangement')
    total_radius = ball_radius+(rods[0]['radius_mm']+rods[1]['radius_mm'])/2
    rear_x = (c1[0]+c2[0])/2-math.sqrt(total_radius**2-((c1[1]-c2[1])/2)**2)
    if abs(rear_x-lower[0]) > tolerance:
        raise ValueError('Lower ball is not on the continuous rear two-rod contact branch')

    actuators = []
    for label, ball_component, controls in [('upper', 12, [7, 9, 12]), ('lower', 13, [8, 10, 13])]:
        center = np.asarray(balls[ball_component]['center_km_local_mm']); q = center-pivot
        travel = abs(q[0])*(1/math.cos(theta)-1)+np.linalg.norm(q[1:])*math.tan(theta)
        ring_evidence = []
        for component in controls[:2]:
            matching = [ring for ring in _circle_sections(parts[component]['points'], 0, tolerance)
                        if np.max(np.abs(np.asarray(ring['center_transverse_mm'])-center[1:])) <= tolerance]
            if not matching:
                raise ValueError('Actuator shaft/knob has no complete ring coaxial with its actual ball')
            ring_evidence.append({'component': component, 'coaxial_ring_count': len(matching),
                                  'rings': matching})
        item = {'name': label, 'ball_component': ball_component, 'components': controls,
                'axis_km_local': [1., 0., 0.], 'axis_origin_km_local': center.tolist(),
                'max_axial_travel_for_net4_deg_mm': float(travel),
                'coaxial_control_geometry': ring_evidence,
                'equation': 't=((eX-R*eX) dot q)/((R*eX) dot eX); |t| <= |qx|(sec(theta)-1)+norm(qyz)*tan(theta)',
                'assumptions': 'Rigid geometry; maintained preload and same contact branch. Shaft and knob may also rotate arbitrarily about this fixed axis. No screw overtravel, backlash, contact play or assembly tolerance is certified.'}
        if label == 'upper':
            displacement = 2*np.linalg.norm(q)*math.sin(theta/2)+travel*math.sin(theta)
            margin = cap_margin-displacement
            item['finite_contact'] = {'kind': 'flat_pad', 'maximum_transverse_displacement_mm': float(displacement),
                                      'available_inscribed_pad_radius_mm': float(cap_margin),
                                      'remaining_margin_mm': float(margin), 'passed': bool(margin > 10*tolerance)}
        else:
            # In the front frame x and z stay fixed. Norm preservation gives
            # the new Y coordinate, and bounds axial drift on both finite rods.
            candidates = [-travel, travel, float(np.clip(-q[0], -travel, travel))]
            ydelta = max(abs(math.sqrt(q[1]**2+2*q[0]*t+t*t)-abs(q[1])) for t in candidates)
            finite_margin = min(min(center[1]-r['effective_y_interval_mm'][0],
                                    r['effective_y_interval_mm'][1]-center[1]) for r in rods)-ydelta
            item['finite_contact'] = {'kind': 'two_parallel_rods', 'maximum_y_slide_mm': float(ydelta),
                                      'remaining_cylindrical_length_margin_mm': float(finite_margin),
                                      'passed': bool(finite_margin > 10*tolerance)}
        if not item['finite_contact']['passed']:
            raise ValueError('Contact may leave its actual finite pad/rod before net 4 degrees')
        actuators.append(item)
    return actuators, {'upper_flat_pad': {'component': 4, 'plane_x_mm': cap_x,
              'plane_normal_km_local': [1., 0., 0.], 'cap_triangles': len(cap_faces),
              'cap_area_mm2': cap_area, 'cap_hull_area_mm2': hull_area,
              'sphere_tangency_residual_mm': abs(cap_x-upper[0]-balls[12]['radius_mm'])},
              'lower_contact_rods': rods, 'lower_rear_branch_x_mm': float(rear_x),
              'passed': True}


def _cone(part, points, faces, center, radius, direction, tolerance):
    """Recognize an entire 45-degree cone fan, not a few nearby vertices."""
    q = part["points"]
    radial = np.linalg.norm(q[:, 1:]-center[1:], axis=1)
    # A right circular cone of half-angle 45 degrees supports this sphere
    # when its apex is r*sqrt(2) from the centre along the cone axis.
    target_x = center[0] - direction*radius*math.sqrt(2)
    apex_ids = np.flatnonzero((radial < tolerance)
                             & (np.abs(q[:, 0]-target_x) < tolerance))
    if len(apex_ids) != 1:
        return None
    apex = q[apex_ids[0]]
    advance = direction*(q[:, 0]-apex[0])
    residual = np.abs(radial-advance)
    mask = ((residual < tolerance) & (advance >= -tolerance)
            & (advance < 1.5*radius))
    cone_ids = part["vertex_ids"][mask]
    if len(cone_ids) < 20:
        return None
    selected = np.all(np.isin(faces[part["facet_ids"]], cone_ids), axis=1)
    cone_faces = faces[part["facet_ids"]][selected]
    apex_global_id = int(part["vertex_ids"][apex_ids[0]])
    ring_ids = cone_ids[cone_ids != apex_global_id]
    if (len(cone_faces) != len(ring_ids)
            or not np.all(np.any(cone_faces == apex_global_id, axis=1))
            or len(np.unique(cone_faces)) != len(cone_ids)):
        return None
    ring = points[ring_ids]
    ring_advance = direction*(ring[:, 0]-apex[0])
    opening = float(np.mean(ring_advance))
    if np.max(np.abs(ring_advance-opening)) > tolerance:
        return None
    # Each ring vertex must have two fan-edge neighbours, and there must be
    # no missing sector around the axis.  These checks reject a partial cup.
    neighbours = {int(i): set() for i in ring_ids}
    for face in cone_faces:
        edge = [int(i) for i in face if i != apex_global_id]
        neighbours[edge[0]].add(edge[1])
        neighbours[edge[1]].add(edge[0])
    if any(len(ns) != 2 for ns in neighbours.values()):
        return None
    angles = np.sort(np.arctan2(ring[:, 2]-center[2], ring[:, 1]-center[1]))
    max_gap = float(np.max(np.diff(np.r_[angles, angles[0]+2*math.pi])))
    if max_gap > math.radians(15):
        return None
    tangent_advance = radius/math.sqrt(2)
    if not tolerance < tangent_advance < opening-tolerance:
        return None
    return {
        "component": part["index"], "axis_direction": [direction, 0., 0.],
        "apex_km_local_mm": apex.tolist(), "half_angle_deg": 45.,
        "opening_radius_mm": opening, "cone_vertices": len(cone_ids),
        "cone_facets": len(cone_faces), "ring_vertices": len(ring_ids),
        "maximum_ring_sector_deg": math.degrees(max_gap),
        "maximum_cone_equation_residual_mm": float(np.max(residual[mask])),
        "sphere_apex_distance_mm": float(np.linalg.norm(center-apex)),
        "expected_sphere_apex_distance_mm": radius*math.sqrt(2),
        "sphere_cone_tangency_residual_mm": abs(
            float(np.linalg.norm(center-apex))/math.sqrt(2)-radius),
        "tangent_circle_inside_cup": True,
    }


def audit(vertices, facets=None, *, source_stl_path, tolerance_mm=2.e-5):
    """Return fail-closed geometry evidence; never certify a dynamic clearance.

    source_stl_path records the supplied mesh's source provenance. Every input
    vertex and facet is matched to that STL; both are hashed independently.
    Fixed/moving classifications are conservative:
    only the back plate containing the rear cone is fixed; every other shell
    remains moving_or_unclassified, including adjusters and their bushings.
    """
    report = {
        "schema": "km100pm_kinematic_geometry/1", "passed": False,
        "errors": [], "full_adjustment_clearance_passed": None,
        "manufacturer_specification_url": SPECIFICATION_URL,
        "manufacturer_drawing": {
            "title": "TTN005954-E0W; KM100PM/M; Rev B; 2015-09-29",
            "mirror_url": DRAWING_MIRROR_URL,
            "scope": "Manufacturer-authored metric outline drawing hosted by a third party; no pivot coordinates or joint tolerances are specified.",
        },
        "assumptions": [
            "Input geometry is in the post-import KM-root local frame, not the board or AOM frame.",
            "The back plate is fixed to the integral seat as in the supplied source assembly.",
            "The large sphere remains seated in the fixed rear cone and the moving front cone under maintained preload.",
            "The fitted nominal sphere and cones represent ideal rigid contact surfaces; STL faceting is not physical surface roughness.",
            "No real assembly tolerance, contact play, deformation, preload loss or additional translational freedom is included.",
        ],
    }
    try:
        if not 0. < tolerance_mm <= 1.e-4:
            raise ValueError("Geometry tolerance must be positive and no greater than 0.0001 mm")
        source = Path(source_stl_path).resolve(strict=True)
        report["provenance"] = {
            "source_stl_path": str(source), "source_stl_sha256": _sha256(source),
            "helper_sha256": _sha256(__file__), "geometry_tolerance_mm": tolerance_mm,
        }
        points, faces = _topology(vertices, facets)
        report["provenance"].update({
            "input_vertices_sha256": hashlib.sha256(points.astype('<f8').tobytes()).hexdigest(),
            "input_facets_sha256": hashlib.sha256(faces.astype('<i8').tobytes()).hexdigest(),
        })
        report["source_geometry_correspondence"] = _source_correspondence(
            points, faces, source, tolerance_mm)
        bounds = np.r_[points.min(axis=0), points.max(axis=0)]
        if np.max(np.abs(bounds-_EXPECTED_BOUNDS)) > tolerance_mm:
            raise ValueError("Input is not the unchanged KM100PM mesh in its documented local frame")
        parts = _components(points, faces)
        if len(parts) != 27:
            raise ValueError("Expected the 27 connected shells of the source KM100PM")
        report["components"] = [
            {"index": p["index"], "vertices": len(p["vertex_ids"]),
             "facets": len(p["facet_ids"]),
             "bounds_km_local_mm": np.r_[p["points"].min(0), p["points"].max(0)].tolist(),
             "motion_classification": "moving_or_unclassified"} for p in parts
        ]
        spheres = []
        for part in parts:
            fit = _sphere(part["points"])
            if fit and fit["maximum_radial_residual_mm"] < tolerance_mm:
                spheres.append({"component": part["index"], **fit})
        report["spheres"] = spheres
        large = [s for s in spheres if abs(s["radius_mm"]-3.96875)<tolerance_mm]
        small = [s for s in spheres if abs(s["radius_mm"]-2.38125)<tolerance_mm]
        if len(spheres) != 3 or len(large) != 1 or len(small) != 2:
            raise ValueError("Expected exactly one 5/32 inch and two 3/32 inch contact balls")
        pivot = np.asarray(large[0]["center_km_local_mm"])
        radius = large[0]["radius_mm"]
        cones = []
        for direction in (1., -1.):
            matches = [_cone(p, points, faces, pivot, radius, direction, tolerance_mm)
                       for p in parts if p["index"] not in [s["component"] for s in spheres]]
            matches = [m for m in matches if m is not None]
            if len(matches) != 1:
                raise ValueError("Expected one complete opposing cone for each side of the fixed ball")
            cones.append(matches[0])
        if cones[0]["component"] == cones[1]["component"]:
            raise ValueError("The two mating cups must belong to separate plates")
        report["opposing_cones"] = cones
        fixed = cones[0]["component"]
        moving_front = cones[1]["component"]
        report["components"][fixed]["motion_classification"] = "fixed_back_plate"
        report["fixed_component_indices"] = [fixed]
        report["moving_or_unclassified_component_indices"] = [p["index"] for p in parts if p["index"] != fixed]
        report["moving_front_plate_component"] = moving_front
        report["common_pivot"] = {
            "model": "ideal_sphere_cone_contact_in_existing_STL",
            "center_km_local_mm": pivot.tolist(),
            "center_aom_root_local_mm": (pivot+[-30.3, -16.4, -24.5]).tolist(),
            "center_aom_bore_local_mm": (pivot+[-30.3, -16.4, -24.5]-[0., -.03, -.115]).tolist(),
            "joint_condition": "A complete 45-degree cone tangent to a sphere has its local sphere centre fixed on its axis at r*sqrt(2) from the apex. Maintaining both contacts fixes that front-plate local point to the rear-plate sphere centre.",
            "manufacturer_pivot_coordinate": False,
            "assembly_tolerances_included": False,
        }
        report['actuators'], report['actuator_contact_geometry'] = _actuator_evidence(
            parts, points, faces, pivot, spheres, tolerance_mm)
        report["passed"] = True
    except Exception as exc:
        report["errors"].append(str(exc))
    return report


def audit_stl(source_stl_path):
    """Convenience for independent read-only verification without FreeCAD."""
    vertices, facets = _read_source(source_stl_path)
    return audit(vertices, facets, source_stl_path=source_stl_path)
