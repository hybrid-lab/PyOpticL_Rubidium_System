"""Native proof of the authorized AOM side channel and shallow front recess.

apply(report, doc, info=None, baseline_shape=old_plate.Shape.copy()) returns the
audit dictionary and stores it under report['aom_machining_relief_audit'].
The explicit baseline must precede the relief and share the current Shape's
coordinate frame. No document property, placement, shape or visibility is changed.
This proves a subtract-only machining change and ideal single-axis adapter
clearance; it does not certify strength, tolerances, combined motion or the
mount's internal motion. Other board audits are never replaced or cleared.
"""

import ast
import hashlib
import math
import traceback
from pathlib import Path

import numpy as np

KEY = 'aom_machining_relief_audit'
VOLUME_TOLERANCE_MM3 = 1.e-5
GEOMETRY_TOLERANCE_MM = 2.e-5
TAP_DIAMETER_MM = 3.4544
PIVOT_KM_LOCAL_MM = (-7.613349863079749, 31.36899851232241, 9.573720082389573e-8)
SOURCE_HASHES = {
    'KM100PM.stl': '96c641fdd94c6908d56a2fc949bca242eecb8b6c1ae41a4441cab61481e3450d',
    'aom_adapter.stl': 'bbdd79ad8c17b7970d37d62ec9f57e825847c8e588ffdd1218e2f52e9527e876',
    'aomo_3100-125.stl': '1a729521ef4a9a5d4221584ffd78dc6a44f9f4e148bf7399feaa36d6854b26a7',
}
GENERATOR_HASHES = {
    '_bounding_box': '7ae9906970262ecfefdf31b85a6d79259451991fa6356b2aca1cf7c7efff4157',
    '_km_clearance': 'e2e046ce5a528ce89bb646efdb64a93eb50dd225f33a302404bc787a550b6dab',
    '_aom_side_relief_bounds': 'afbc8c7a56e930bb88b23560d5b6b1c17e75b74e4ad9bb19138f75ebeffbcbdb',
    '_aom_installation_relief': '3e338bc7982019a37a92b428e4a627cdbbe23f4b393c9764bfeb14792a12088c',
    '_geometry': 'b305c46da8ded5b70cc42d80966199cab838d4522f09028dd59e1cb2aa806ecf',
}
CONSTANTS = {
    'SEAT_X_MIN': -9.179, 'SEAT_X_MAX': 5.2,
    'PILL_MAX_OFFSET': (-30.8, -38., 0.), 'KNOB_FLOOR_OFFSET': -.4,
    'LIP_X': -7.15, 'LIP_Y': -15., 'LIP_WIDTH': 2., 'LIP_LENGTH': 30.,
    'LIP_HEIGHT': 2., 'BEARING_FACE_Z': -1.231, 'TAP_DIAMETER': TAP_DIAMETER_MM,
    'AOM_APERTURE_LOCAL': (0., -.03, -.115),
    'AOM_SIDE_CLEARANCE_MM': 6., 'AOM_SIDE_RELIEF_RADIUS_MM': 3.,
    'AOM_FRONT_RELIEF_DEPTH_MM': 4.,
    'AOM_FRONT_RELIEF_XY_MM': (21.4, -35., 62.5272, 27.051),
    'AOM_FRONT_RELIEF_RADIUS_MM': 3.,
}


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _kind(obj):
    return type(getattr(obj, 'Proxy', None)).__name__


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _near(actual, expected):
    a, b = np.asarray(actual, float), np.asarray(expected, float)
    return a.shape == b.shape and np.all(np.isfinite(a)) and np.max(np.abs(a-b)) <= GEOMETRY_TOLERANCE_MM


def _volume(shape):
    if shape.isNull():
        return 0.
    _require(shape.isValid(), 'Invalid native Boolean result')
    volume = float(shape.Volume)
    _require(math.isfinite(volume) and volume >= -VOLUME_TOLERANCE_MM3, 'Invalid signed native volume')
    return max(0., volume)


def _same_shape(a, b, name):
    ab, ba = _volume(a.cut(b)), _volume(b.cut(a))
    _require(max(ab, ba) <= VOLUME_TOLERANCE_MM3, name+' differs in native Boolean geometry')
    return {'first_minus_second_mm3': ab, 'second_minus_first_mm3': ba}


def _placed(shape, placement):
    copy = shape.copy()
    copy.Placement = placement.multiply(copy.Placement)
    return copy


def _pose(placement, base, basis, name):
    import FreeCAD as App
    _require(_near(tuple(placement.Base), base), name+' translation changed')
    for vector, expected in zip(((1, 0, 0), (0, 1, 0), (0, 0, 1)), basis):
        _require(_near(tuple(placement.Rotation.multVec(App.Vector(*vector))), expected), name+' orientation changed')


def _coordinate_extrema(points, pivot, lower_deg=0., upper_deg=4.):
    """Exact coordinate extrema of every triangle vertex during local-Y pitch."""
    points, pivot = np.asarray(points, float), np.asarray(pivot, float)
    _require(points.ndim == 2 and points.shape[1] == 3 and len(points) and
             np.all(np.isfinite(points)) and pivot.shape == (3,) and np.all(np.isfinite(pivot)),
             'Finite source vertices and pivot are required')
    _require(lower_deg == 0. and upper_deg == 4., 'Only the authorized 0..4-degree pitch interval is supported')
    q = points-pivot
    low, high = math.radians(lower_deg), math.radians(upper_deg)

    def extrema(a, b, origin):
        angles = [np.full(len(q), low), np.full(len(q), high)]
        critical = np.arctan2(b, a)
        for k in range(-2, 3):
            angles.append(np.clip(critical+k*math.pi, low, high))
        values = np.stack([origin+a*np.cos(t)+b*np.sin(t) for t in angles])
        return [float(values.min()), float(values.max())]

    return {'x': extrema(q[:, 0], q[:, 2], pivot[0]),
            'y': [float(points[:, 1].min()), float(points[:, 1].max())],
            'z': extrema(q[:, 2], -q[:, 0], pivot[2])}


def _tap_wall(plate_shape, placement, floor, bearing):
    """Verify a full cylindrical wall, open bore and an actual 3-mm stock ring."""
    import FreeCAD as App
    import Part
    inverse = placement.inverse()
    radius = TAP_DIAMETER_MM/2
    intervals = []
    for face in plate_shape.Faces:
        surface = face.Surface
        if not isinstance(surface, Part.Cylinder) or abs(surface.Radius-radius) > GEOMETRY_TOLERANCE_MM:
            continue
        axis = inverse.Rotation.multVec(surface.Axis)
        centre = inverse.multVec(surface.Center)
        if abs(abs(axis.z)-1.) > 1.e-7 or math.hypot(centre.x, centre.y) > GEOMETRY_TOLERANCE_MM:
            continue
        u0, u1, unused_v0, unused_v1 = face.ParameterRange
        if abs(abs(u1-u0)-2*math.pi) > 1.e-5:
            continue
        z = [inverse.multVec(v.Point).z for v in face.Vertexes]
        if z:
            intervals.append([min(z), max(z)])
    cursor = floor+.02
    for lo, hi in sorted(intervals):
        if hi < cursor-GEOMETRY_TOLERANCE_MM:
            continue
        _require(lo <= cursor+GEOMETRY_TOLERANCE_MM, 'Central tap has a gap in its full cylindrical wall')
        cursor = max(cursor, hi)
        if cursor >= bearing-.02:
            break
    _require(cursor >= bearing-.02, 'Actual 3.4544-mm full circular tap wall is missing')
    height = bearing-floor-.04
    _require(height > 0., 'No stock below AOM bearing face')
    outer = Part.makeCylinder(radius+3., height, App.Vector(0, 0, floor+.02))
    inner = Part.makeCylinder(radius+.0001, height, App.Vector(0, 0, floor+.02))
    ring = _placed(outer.cut(inner), placement)
    missing = _volume(ring.cut(plate_shape))
    _require(missing <= VOLUME_TOLERANCE_MM3, 'Central tap does not retain its 3-mm annular stock')
    bore = _placed(Part.makeCylinder(radius-.0001, bearing-floor+.04,
                                    App.Vector(0, 0, floor-.02)), placement)
    blocked = _volume(bore.common(plate_shape))
    _require(blocked <= VOLUME_TOLERANCE_MM3, 'Central tap bore is not open through the remaining stock')
    return {'diameter_mm': TAP_DIAMETER_MM, 'full_cylindrical_wall_intervals_seat_z_mm': intervals,
            'radial_stock_mm': 3., 'ring_probe_end_inset_mm': .02,
            'missing_ring_stock_mm3': missing, 'bore_obstruction_mm3': blocked,
            'bearing_to_plate_bottom_stock_mm': bearing-floor}


def _covers(intervals, lower, upper):
    """Require continuous native-face coverage, allowing only modelling tolerance."""
    cursor = lower
    for lo, hi in sorted(intervals):
        if hi < cursor-GEOMETRY_TOLERANCE_MM:
            continue
        if lo > cursor+GEOMETRY_TOLERANCE_MM:
            return False
        cursor = max(cursor, hi)
        if cursor >= upper-GEOMETRY_TOLERANCE_MM:
            return True
    return False


def _side_channel_proof(plate_shape, placement, km, top):
    """Check the actual solid against an independently built rounded rectangle.

    No machining-generator/helper call is used. The matched actual KM mesh
    supplies the old knob-pocket Y bounds; its established 3-mm allowance is
    applied directly to the vertices. Boxes and four cylinders build the R3
    target, independently of the generator's filleted-box implementation.
    """
    import FreeCAD as App
    import Part
    inverse = placement.inverse()
    points = np.asarray([tuple(inverse.multVec(v)) for v in km.Mesh.Topology[0]])
    _require(points.ndim == 2 and points.shape[1] == 3 and len(points) and
             np.all(np.isfinite(points)), 'Actual KM vertices are missing')
    x0, x1, radius, bearing = -13.15, 5.2, 3., -1.231
    y0, y1 = float(points[:, 1].min()-3.), float(points[:, 1].max()+3.)
    _require(_near((y0, y1), (-29.46571578979492, 28.97811577320099)),
             'Actual knob-pocket Y bounds differ from the retained mesh installation')
    width, length, height = x1-x0, y1-y0, top+1.-bearing
    _require(width > 2*radius and length > 2*radius and height > 0.,
             'Invalid side-channel proof dimensions')
    parts = [Part.makeBox(width-2*radius, length, height,
                         App.Vector(x0+radius, y0, bearing)),
             Part.makeBox(width, length-2*radius, height,
                         App.Vector(x0, y0+radius, bearing))]
    parts += [Part.makeCylinder(radius, height, App.Vector(x, y, bearing))
              for x in (x0+radius, x1-radius) for y in (y0+radius, y1-radius)]
    target = parts[0]
    for part in parts[1:]:
        target = target.fuse(part)
    target = target.removeSplitter()
    expected_volume = (width*length-(4.-math.pi)*radius**2)*height
    _require(target.isValid() and len(target.Solids) == 1 and
             abs(_volume(target)-expected_volume) <= VOLUME_TOLERANCE_MM3,
             'Independent rounded-rectangle construction failed')
    lip = Part.makeBox(2., 30., 3.231, App.Vector(-7.15, -15., bearing))
    target = target.cut(lip).removeSplitter()
    _require(target.isValid() and len(target.Solids) == 1,
             'Independent lip-preserving side probe is invalid')
    residual = _volume(plate_shape.common(_placed(target, placement)))
    _require(residual <= VOLUME_TOLERANCE_MM3,
             'Side channel retains stock inside the full R3 no-step target')
    # A second, simple prism proves the complete 6-mm gap alongside the lip
    # and its continuation through the positive-Y straight transition.
    straight = Part.makeBox(6., y1-radius+15., height,
                            App.Vector(x0, -15., bearing))
    straight_residual = _volume(plate_shape.common(_placed(straight, placement)))
    _require(straight_residual <= VOLUME_TOLERANCE_MM3,
             'Six-mm clearance from the lip outer face is obstructed')
    local_plate = _placed(plate_shape, inverse)
    mid_z = (bearing+top)/2.
    wall_intervals, top_intervals, corners = [], [], []
    for face in local_plate.Faces:
        surface, bounds = face.Surface, face.BoundBox
        if not (bounds.ZMin <= mid_z-GEOMETRY_TOLERANCE_MM and
                bounds.ZMax >= mid_z+GEOMETRY_TOLERANCE_MM):
            continue
        if isinstance(surface, Part.Plane):
            u0, u1, v0, v1 = face.ParameterRange
            normal = face.normalAt((u0+u1)/2., (v0+v1)/2.)
            centre = face.CenterOfMass
            if abs(abs(normal.x)-1.) < 1.e-7 and abs(centre.x-x0) <= GEOMETRY_TOLERANCE_MM:
                wall_intervals.append([bounds.YMin, bounds.YMax])
            if abs(abs(normal.y)-1.) < 1.e-7 and abs(centre.y-y1) <= GEOMETRY_TOLERANCE_MM:
                top_intervals.append([bounds.XMin, bounds.XMax])
        elif isinstance(surface, Part.Cylinder):
            centre, axis = surface.Center, surface.Axis
            if (abs(surface.Radius-radius) <= GEOMETRY_TOLERANCE_MM and
                    abs(abs(axis.z)-1.) < 1.e-7 and
                    _near((centre.x, centre.y), (x0+radius, y1-radius))):
                u0, u1, unused_v0, unused_v1 = face.ParameterRange
                span = abs(u1-u0)
                if span >= math.pi/2.-1.e-5:
                    corners.append({'centre_xy_mm': [centre.x, centre.y],
                                    'radius_mm': surface.Radius, 'angular_span_rad': span})
    # Negative Y already opens into the larger old main cavity: a 6-mm
    # minimum void is required there, not a fictitious wall at exactly 6 mm.
    _require(_covers(wall_intervals, 0., y1-radius),
             'Actual positive-Y side wall is not continuously at seat x=-13.15')
    _require(_covers(top_intervals, x0+radius, x1-radius),
             'Actual top transition is not flush with the old knob-pocket Y edge')
    _require(bool(corners), 'Actual upper outside R3 cylindrical corner is missing')
    return {'passed': True, 'coordinate_frame': 'retained seat local frame',
            'reference': 'locating lip outer face toward the cavity wall, not its centreline',
            'lip_outer_face_x_mm': -7.15, 'side_wall_x_mm': x0,
            'minimum_clearance_mm': -7.15-x0,
            'rounded_rectangle_xy_mm': [x0, y0, x1, y1], 'radius_mm': radius,
            'floor_z_mm': bearing, 'lip_length_y_mm': [-15., 15.],
            'straight_no_step_y_mm': [-15., y1-radius],
            'rounded_target_residual_mm3': residual,
            'straight_gap_residual_mm3': straight_residual,
            'actual_wall_y_intervals_mm': wall_intervals,
            'actual_top_edge_x_intervals_mm': top_intervals,
            'actual_upper_outside_corner': corners,
            'method': 'Independent exact boxes/cylinders target minus unchanged lip; '
                      'native final-plate intersection and plane/cylinder surface evidence.'}


def apply(report, doc, info=None, baseline_shape=None):
    """Return this audit; failures stay explicit and do not modify other checks."""
    result = {'schema': 'aom_machining_relief_audit/2', 'passed': False,
              'document': doc.Name, 'seat_count': 0, 'seats': [], 'errors': [],
              'parameters': {'side_clearance_mm': 6., 'side_corner_radius_mm': 3.,
                             'side_clearance_datum': 'locating lip outer face',
                             'front_relief_depth_mm': 4.,
                             'front_corner_radius_mm': 3.},
              'scope': {'subtract_only_native_geometry': True,
                        'component_mounting_poses_preserved': False,
                        'all_other_hole_inventory_checked_here': False,
                        'adjacent_component_bearing_surfaces_checked_here': False,
                        'combined_axes_certified': False, 'internal_mount_motion_certified': False,
                        'manufacturing_tolerances_certified': False, 'strength_certified': False},
              'source_provenance': {'audit_path': str(Path(__file__).resolve()),
                                    'audit_sha256': _hash(__file__)}}
    report[KEY] = result
    try:
        import FreeCAD as App
        import Part
        from PyOpticL import optomech
        import aom_adjustment_audit as mesh_check
        import km100pm_kinematic_geometry as joint

        _require(baseline_shape is not None and not baseline_shape.isNull() and
                 baseline_shape.isValid() and len(baseline_shape.Solids) == 1,
                 'Explicit valid original one-solid plate Shape is required')
        plates = [o for o in doc.Objects if _kind(o) == 'IntegralAOMBaseplate']
        plate = (info or {}).get('plate')
        if plate is None:
            _require(len(plates) == 1, 'Exactly one native integral-AOM plate is required')
            plate = plates[0]
        _require(plate in plates and plate.Document == doc and doc.getObject(plate.Name) == plate,
                 'Plate/document mismatch')
        _require(plate.Drill and plate.Shape.isValid() and len(plate.Shape.Solids) == 1,
                 'Current machined plate must be one valid solid')
        _require(_near((plate.dx.Value, plate.dz.Value, plate.OpticsDz.Value), (609.6, 25.4, 12.7)),
                 'Only the original Splitting/Lattice thickness and optical datum are authorized')
        expected_count = 7 if abs(plate.dy.Value-355.6) < GEOMETRY_TOLERANCE_MM else 2
        _require(expected_count == 7 or abs(plate.dy.Value-381.) < GEOMETRY_TOLERANCE_MM,
                 'Only the 24x14 Splitting and 24x15 Lattice boards are authorized')
        seats = [o for o in doc.Objects if _kind(o) == 'IntegralAOMSeat' and o.Baseplate == plate]
        aoms = [o for o in doc.Objects if _kind(o) == 'AOMO_3100_125' and o.Baseplate == plate]
        _require(len(seats) == len(aoms) == expected_count and
                 {s.AOMRoot.Name for s in seats} == {a.Name for a in aoms},
                 'Actual AOM and seat inventories differ from the authorized board')
        result['seat_count'] = len(seats)
        source = Path(optomech.__file__).read_text(encoding='utf-8-sig')
        hashes = {n.name: hashlib.sha256(ast.get_source_segment(source, n).encode()).hexdigest()
                  for n in ast.parse(source).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))
                  and n.name in GENERATOR_HASHES}
        _require(hashes == GENERATOR_HASHES, 'Machining generator differs from the approved implementation')
        for key, expected in CONSTANTS.items():
            _require(_near(getattr(optomech, key), expected), 'Installation/relief constant changed: '+key)
        repo = Path(__file__).resolve().parents[1]
        for filename, digest in SOURCE_HASHES.items():
            _require(_hash(repo/'stl'/filename) == digest, 'Original component STL changed: '+filename)
        _require(_hash(joint.__file__) == '64815b6539d28b81ae94e832c9abcba54def6ad6ea52bd2eff0b62c698f2e3d8',
                 'Ideal-pivot source geometry helper changed')
        result['source_provenance'].update({'optomech_path': str(Path(optomech.__file__).resolve()),
            'optomech_sha256': _hash(optomech.__file__), 'generator_hashes': hashes,
            'stl_hashes': dict(SOURCE_HASHES), 'mesh_correspondence_helper_sha256': _hash(mesh_check.__file__),
            'ideal_pivot_helper_sha256': _hash(joint.__file__)})
        identity = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
        yaw_minus_90 = ((0, -1, 0), (1, 0, 0), (0, 0, 1))
        cutters, protected = [], []
        for seat in seats:
            _require(seat.Drill and getattr(seat, 'MachiningRelief', None) is True,
                     'Every seat must explicitly enable the approved machining relief')
            aom = seat.AOMRoot
            _require(aom.Document == doc and doc.getObject(aom.Name) == aom, 'AOM belongs to another document')
            _pose(seat.SeatRelativePlacement, (-44.4, -3.65, -30.), identity, 'Seat relative pose')
            placement = optomech.seat_placement(seat)
            on_plate = plate.Placement.inverse().multiply(placement)
            _require(_near(tuple(on_plate.Rotation.multVec(App.Vector(0, 0, 1))), (0, 0, 1)) and
                     abs(on_plate.Base.z+29.885) <= GEOMETRY_TOLERANCE_MM,
                     'Seat installation height or board-normal axis changed')
            children = mesh_check._children(aom)
            def one(kind):
                choices = [o for o in children if _kind(o) == kind]
                _require(len(choices) == 1, 'One actual '+kind+' required per AOM')
                return choices[0]
            km, adapter = one('prism_mount_km100pm_bridged'), one('aom_adapter')
            _require(not any(_kind(o) == 'surface_adapter_aom' for o in children), 'Obsolete lower adapter remains')
            _pose(aom.Placement.inverse().multiply(km.Placement), (-30.3, -16.4, -24.5), identity, 'KM relative pose')
            _pose(aom.Placement.inverse().multiply(adapter.Placement), (-17., -7.65, -17.1), yaw_minus_90, 'Adapter relative pose')
            _require(aom.ApertureAlignmentApplied and _near(tuple(aom.MeshApertureLocal), (0., -.03, -.115)),
                     'AOM optical bore alignment differs from the retained installation')
            references = {
                'km': (km, joint._read_source(repo/'stl/KM100PM.stl')),
                'adapter': (adapter, optomech._import_stl('aom_adapter.stl', (0, 0, 0), (0, 0, 0)).Topology),
                'aom': (aom, optomech._import_stl('aomo_3100-125.stl', (0, 0, -90), (0, -7.65, -7.1)).Topology),
            }
            matches = {name: mesh_check._mesh_matches(mesh_check._local_topology(obj), reference)
                       for name, (obj, reference) in references.items()}
            top = -float(plate.OpticsDz.Value)-on_plate.Base.z
            floor = top-float(plate.dz.Value)
            expected, empty = optomech._geometry(seat)
            _require(empty.isNull() and seat.SupportPart.isNull(), 'Standalone support geometry is not allowed')
            identity_check = _same_shape(seat.DrillPart, expected, 'Actual complete seat cutter')
            cutter = _placed(optomech._aom_installation_relief(seat, top), placement)
            _require(not cutter.isNull() and cutter.isValid(), 'Approved relief cutter is missing or invalid')
            cutters.append(cutter)
            cb = optomech._km_clearance(km, placement).BoundBox
            support = _placed(Part.makeBox(14.379, cb.YLength, -1.231-floor,
                              App.Vector(-9.179, cb.YMin, floor)), placement)
            lip = _placed(Part.makeBox(2., 30., 3.231, App.Vector(-7.15, -15., -1.231)), placement)
            protected.append((seat, placement, floor, support, lip))
            side_proof = _side_channel_proof(plate.Shape, placement, km, top)
            inverse = placement.inverse()
            actual_points = np.asarray([tuple(inverse.multVec(v)) for v in adapter.Mesh.Topology[0]])
            pivot = np.asarray(tuple(inverse.multVec(km.Placement.multVec(App.Vector(*PIVOT_KM_LOCAL_MM)))))
            _require(_near(pivot, (6.486650136920247, 18.618998512322378, 5.5000000957371995)),
                     'Actual ideal pivot differs in the retained seat frame')
            sweep = _coordinate_extrema(actual_points, pivot)
            # A rounded rectangle equals the Minkowski sum of its inner rectangle
            # and a radius-3 disk. Its inner rectangle must contain the full sweep.
            inner_lo = np.array([21.4+3., -35.+3.])
            inner_hi = np.array([62.5272-3., 27.051-3.])
            _require(np.all(np.array([sweep['x'][0], sweep['y'][0]]) >= inner_lo-1.e-9) and
                     np.all(np.array([sweep['x'][1], sweep['y'][1]]) <= inner_hi+1.e-9),
                     'Rounded front pocket does not provide the full 3-mm sweep dilation')
            gap = sweep['z'][0]-(top-4.)
            _require(gap >= 1., 'Continuous adapter-to-front-floor clearance is less than 1 mm')
            result['seats'].append({'seat': seat.Name, 'aom': aom.Name, 'km': km.Name,
                'upper_adapter': adapter.Name, 'source_mesh_correspondence': matches,
                'side_channel': side_proof,
                'actual_cutter_identity': identity_check, 'pivot_seat_mm': pivot.tolist(),
                'plate_top_seat_z_mm': top, 'front_floor_seat_z_mm': top-4.,
                'front_floor_stock_mm': top-4.-floor, 'adapter_sweep_bounds_seat_mm': sweep,
                'minimum_floor_gap_mm': gap, 'minimum_sidewall_gap_mm': 3.})
        union = cutters[0]
        for cutter in cutters[1:]:
            union = union.fuse(cutter)
        expected_plate = baseline_shape.cut(union).removeSplitter()
        _require(expected_plate.isValid() and len(expected_plate.Solids) == 1,
                 'Approved relief would not leave a valid single plate solid')
        result['plate_identity'] = _same_shape(plate.Shape, expected_plate, 'Current plate versus original minus approved relief')
        added = _volume(plate.Shape.cut(baseline_shape))
        removed = baseline_shape.cut(plate.Shape)
        removed_volume = _volume(removed)
        _require(added <= VOLUME_TOLERANCE_MM3 and removed_volume > VOLUME_TOLERANCE_MM3,
                 'Expected a nonempty subtract-only change from the explicit original plate')
        result['native_subtract_only'] = {'added_mm3': added, 'removed_mm3': removed_volume,
            'baseline_volume_mm3': _volume(baseline_shape), 'current_volume_mm3': _volume(plate.Shape),
            'current_valid': True, 'current_solids': 1, 'volume_tolerance_mm3': VOLUME_TOLERANCE_MM3}
        for entry, data, cutter in zip(result['seats'], protected, cutters):
            seat, placement, floor, support, lip = data
            support_loss = _volume(removed.common(support))
            lip_loss = _volume(removed.common(lip))
            _require(max(support_loss, lip_loss) <= VOLUME_TOLERANCE_MM3,
                     'Relief removes protected bearing stock or locating lip at '+seat.Name)
            entry['protected_geometry'] = {'support_removed_mm3': support_loss, 'lip_removed_mm3': lip_loss,
                'removed_within_this_relief_mm3': _volume(baseline_shape.common(cutter)),
                'baseline_tap': _tap_wall(baseline_shape, placement, floor, -1.231),
                'current_tap': _tap_wall(plate.Shape, placement, floor, -1.231)}
        result['single_axis_adapter_clearance'] = {
            'pitch_down_interval_deg': [0., 4.],
            'minimum_floor_gap_mm': min(e['minimum_floor_gap_mm'] for e in result['seats']),
            'minimum_sidewall_gap_mm': 3.,
            'method': 'Exact extrema of matched original triangle vertices about the ideal source pivot; '
                      'the R3 front pocket contains the full sweep AABB plus a 3-mm disk.',
            'combined_axes_certified': False, 'internal_mount_motion_certified': False,
            'manufacturing_tolerances_certified': False}
        result['scope']['component_mounting_poses_preserved'] = True
        result['passed'] = True
    except Exception as exc:
        result['errors'].append(str(exc))
        result['failure_traceback'] = traceback.format_exc()
    report.setdefault('summary_counts', {})[KEY+'_issues'] = len(result['errors']) or int(not result['passed'])
    return result
