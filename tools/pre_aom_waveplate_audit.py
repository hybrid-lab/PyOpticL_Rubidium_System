"""Read-only audit of seven additional Splitting pre-AOM HWP assemblies.

Call ``apply(report, doc, info, source_module=loaded_board_module)`` after the
full native, zero-order, bonded-cube, KM05T and projection audits. A source
file path is also accepted; the default is the repository production source.
``placement_passed`` certifies inventory/registration only. ``passed`` also
requires independent native collision, aperture, hole, service/RF and knob
projection results. No old failure, geometry or external validator is changed.

The CAD waveplate class is a mechanical glass envelope. Its designation as an
HWP comes from the board source; this does not measure optical retardance.
"""

import ast
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path


_LANES = ('A', 'B1', 'B2', 'C1', 'C2', 'C3', 'C4')
_UPSTREAM_MOUNT_LANES = {'C1', 'C3'}
_MIRRORS = {'circular_mirror', 'circular_mirror_union_optic'}
_TOL = 1.e-5
_REPORT_KEY = 'pre_aom_waveplate_audit'
_ISSUE_KEY = 'pre_aom_waveplate_audit_issues'


def _kind(obj):
    return type(getattr(obj, 'Proxy', None)).__name__


def _number(value):
    value = float(getattr(value, 'Value', value))
    if not math.isfinite(value):
        raise ValueError('Non-finite audit coordinate or dimension')
    return value


def _xyz(value):
    values = list(value)
    if len(values) == 2:
        values.append(0.)
    if len(values) != 3:
        raise ValueError('Expected an XY or XYZ coordinate')
    return [_number(x) for x in values]


def _near(a, b, tolerance=_TOL):
    return len(a) == len(b) and all(abs(_number(x)-_number(y)) <= tolerance for x, y in zip(a, b))


def _same(a, b):
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def _unit(vector):
    vector = _xyz(vector)
    length = math.sqrt(sum(x*x for x in vector))
    if length <= _TOL:
        raise ValueError('Zero-length optical segment')
    return [x/length for x in vector]


def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def _source(source_module):
    source = source_module
    if source is None:
        source = Path(__file__).resolve().parents[1]/'Rubidium_system'/'Splitting_Board_V2.py'
    path = Path(getattr(source, '__file__', source)).resolve()
    data = path.read_bytes()
    constants = {}
    for node in ast.parse(data.decode('utf-8-sig')).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ('ORDER', 'PRE_AOM_HWP_TO_AOM_MM'):
                    if target.id in constants:
                        raise ValueError('Ambiguous repeated source declaration: '+target.id)
                    constants[target.id] = ast.literal_eval(node.value)
    if tuple(constants.get('ORDER', ())) != _LANES:
        raise ValueError('Source must declare the exact seven retained Splitting lanes')
    spacing = constants.get('PRE_AOM_HWP_TO_AOM_MM', {})
    if set(spacing) != set(_LANES) or any(_number(v) <= 0. for v in spacing.values()):
        raise ValueError('Source must explicitly declare a positive HWP-to-AOM spacing for all seven lanes')
    if any(abs(_number(spacing[n])-79.) > _TOL for n in _UPSTREAM_MOUNT_LANES):
        raise ValueError('Upstream-facing C1/C3 KM100PM assemblies require the declared 79 mm reference spacing')
    if hasattr(source_module, '__file__'):
        if (not _same(getattr(source_module, 'PRE_AOM_HWP_TO_AOM_MM', None), spacing) or
                tuple(getattr(source_module, 'ORDER', ())) != _LANES):
            raise ValueError('Loaded source constants differ from the source file on disk')
    return spacing, {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(),
                     'declared_hwp_to_aom_mm': deepcopy(spacing)}


def _contract(info, source_spacing):
    entries = info.get('pre_aom_waveplates', [])
    if (info.get('mode') != 'splitting' or info.get('pre_aom_waveplates_required') is not True or
            type(info.get('expected_pre_aom_waveplate_count')) is not int or
            info['expected_pre_aom_waveplate_count'] != 7 or len(entries) != 7 or
            {e.get('lane') for e in entries} != set(_LANES)):
        raise ValueError('Explicit seven-lane pre-AOM HWP requirement is missing or duplicated')
    for field in ('waveplate', 'stage', 'adapter', 'last_mirror', 'aom', 'beam_path'):
        values = [e.get(field) for e in entries]
        if not all(isinstance(v, str) and v for v in values) or len(set(values)) != 7:
            raise ValueError('Seven unique actual '+field+' registrations are required')
    for e in entries:
        lane = e['lane']
        if (e.get('object') != e['waveplate'] or e['beam_path'] != lane+' lane' or
                e.get('aom_mount_orientation') != ('U' if lane in _UPSTREAM_MOUNT_LANES else 'D') or
                type(e.get('path_vertex_index')) is not int or e['path_vertex_index'] < 1 or
                abs(_number(e.get('hwp_to_aom_mm', -1))-_number(source_spacing[lane])) > _TOL or
                _number(e.get('last_mirror_to_hwp_mm', -1)) <= 0.):
            raise ValueError('Incorrect identity, orientation, vertex or declared spacing for '+lane)
        direction = _xyz(e.get('incoming_direction_xy', []))
        if not _near(direction, _unit(direction), 1.e-8):
            raise ValueError('Incoming beam direction must be a unit XY vector for '+lane)
        angle = math.radians(_number(e.get('incoming_direction_deg')))
        if not _near(direction, [math.cos(angle), math.sin(angle), 0.], 1.e-8):
            raise ValueError('Degree and vector declarations disagree for '+lane)
        _xyz(e.get('optical_xy_mm', []))
        _number(e.get('waveplate_angle_deg'))
    return {e['lane']: e for e in entries}


def _descendants(root):
    pending, seen = [root], set()
    while pending:
        obj = pending.pop()
        if obj.Name in seen:
            continue
        seen.add(obj.Name)
        yield obj
        pending.extend(getattr(obj, 'ChildObjects', []))


def _on_plate(obj, plate):
    return getattr(obj, 'Baseplate', None) == plate


def _bounds(geometry):
    box = geometry.BoundBox
    return [box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax]


def _geometry_record(obj, snapshots):
    snapshot = snapshots.get(obj.Name)
    if (not snapshot or snapshot.get('class') != _kind(obj) or
            not _near(snapshot.get('position', []), list(obj.Placement.Base)) or
            any(any(word in str(state).lower() for word in ('invalid', 'error', 'touched')) for state in obj.State)):
        raise ValueError('Missing, stale or unrecomputed native object record: '+obj.Name)
    mesh = getattr(obj, 'Mesh', None)
    shape = getattr(obj, 'Shape', None)
    if mesh is not None and mesh.CountPoints:
        if not mesh.CountFacets:
            raise ValueError('Actual mesh has no surface facets: '+obj.Name)
        geom = mesh
        evidence = {'geometry': 'actual_placed_mesh', 'vertices': int(mesh.CountPoints),
                    'facets': int(mesh.CountFacets)}
    elif shape is not None and not shape.isNull() and shape.isValid() and shape.Volume > 0.:
        geom = shape
        evidence = {'geometry': 'actual_placed_brep', 'solids': len(shape.Solids),
                    'volume_mm3': float(shape.Volume)}
    else:
        raise ValueError('No real mesh/solid on registered optical hardware: '+obj.Name)
    current_bounds = _bounds(geom)
    if not _near(snapshot.get('bbox', []), current_bounds):
        raise ValueError('Native report geometry bounds are stale: '+obj.Name)
    evidence.update(object=obj.Name, actual_class=_kind(obj), world_bounds_mm=current_bounds,
                    world_position_mm=list(obj.Placement.Base),
                    placement_matrix=list(obj.Placement.toMatrix().A))
    return evidence


def _solid_centroid(shape):
    """Use every valid positive-volume solid, including a Compound wrapper."""
    if shape is None or shape.isNull() or not shape.isValid():
        raise ValueError('Waveplate glass shape is empty or invalid')
    solids = list(shape.Solids)
    if not solids:
        raise ValueError('Waveplate glass shape contains no solids')
    volumes, centers = [], []
    for solid in solids:
        if solid.isNull() or not solid.isValid():
            raise ValueError('Waveplate glass contains an empty or invalid solid')
        volume = _number(solid.Volume)
        if volume <= 0.:
            raise ValueError('Waveplate glass contains a non-positive-volume solid')
        volumes.append(volume)
        centers.append(_xyz(list(solid.CenterOfMass)))
    volume = math.fsum(volumes)
    if abs(_number(shape.Volume)-volume) > _TOL:
        raise ValueError('Waveplate compound volume differs from its complete solid inventory')
    center = [math.fsum(v*c[i] for v, c in zip(volumes, centers))/volume for i in range(3)]
    return center, volume, len(solids)


def _assembly(root, stage, adapter, plate, snapshots):
    import FreeCAD as App

    if (_kind(root) != 'waveplate' or _kind(stage) != 'rotation_stage_rsp05' or
            _kind(adapter) != 'surface_adapter_rotation_stage_lip' or
            any(not _on_plate(o, plate) for o in (root, stage, adapter)) or
            getattr(root, 'ParentObject', None) is not None or
            getattr(stage, 'ParentObject', None) is not root or
            getattr(adapter, 'ParentObject', None) is not stage or
            list(getattr(root, 'ChildObjects', [])) != [stage] or
            list(getattr(stage, 'ChildObjects', [])) != [adapter] or
            getattr(adapter, 'ChildObjects', [])):
        raise ValueError('HWP -> RSP05 -> lip-adapter parent chain/baseplate is not exact: '+root.Name)
    if (abs(_number(root.Diameter)-12.7) > _TOL or abs(_number(root.Thickness)-1.) > _TOL or
            bool(stage.Invert) or abs(_number(adapter.MountHoleDistance)-25.) > _TOL or
            not bool(root.Drill) or not bool(adapter.Drill) or adapter.DrillPart.isNull()):
        raise ValueError('Unexpected HWP/RSP05 mounting dimensions or disabled machining: '+root.Name)
    expected_stage = App.Placement(App.Vector(-.5, 0, 0), App.Rotation())
    expected_adapter = App.Placement(App.Vector(1.397, 0, -13.97), App.Rotation())
    for child, parent, relative in ((stage, root, expected_stage), (adapter, stage, expected_adapter)):
        if (not _near(list(child.RelativePlacement.toMatrix().A), list(relative.toMatrix().A)) or
                not _near(list(child.Placement.toMatrix().A),
                          list(parent.Placement.multiply(relative).toMatrix().A))):
            raise ValueError('Linked hardware is detached or moved from its correct optical parent: '+child.Name)
    records = [_geometry_record(obj, snapshots) for obj in (root, stage, adapter)]
    center, glass_volume, solid_count = _solid_centroid(root.Shape)
    if not _near(center, list(root.Placement.Base)):
        raise ValueError('Waveplate glass is not centred at its registered optical origin: '+root.Name)
    expected_volume = math.pi*(12.7/2.)**2
    if abs(glass_volume-expected_volume) > 1.e-5:
        raise ValueError('Waveplate glass is not the full nominal half-inch, 1 mm envelope: '+root.Name)
    records[0]['glass_centroid_evidence'] = {
        'method': 'Volume-weighted centers of all valid, positive-volume solids',
        'solid_count': solid_count, 'world_center_mm': center,
        'summed_solid_volume_mm3': glass_volume, 'nominal_volume_mm3': expected_volume,
    }
    return records


def _required_roots(doc, info, report):
    roots = info.get('roots', {})
    old = report.get('roots', {})
    if set(roots) != set(old):
        raise ValueError('Native root inventory differs from the current layout')
    for key, root in roots.items():
        if doc.getObject(root.Name) is not root or set(old[key]) != {o.Name for o in _descendants(root)}:
            raise ValueError('Native root/descendant inventory differs for '+key)
    return roots


def _check_placement(doc, info, report, entries, result):
    import FreeCAD as App

    if (report.get('document') != doc.Name or report.get('mode') != 'splitting' or
            not _same(report.get('paths'), info.get('paths')) or
            not _same(report.get('arms'), info.get('arms'))):
        raise ValueError('Current document, full lane paths and all AOM arms must match the native report')
    plate = info['plate']
    if not plate.Drill or not plate.Shape.isValid() or len(plate.Shape.Solids) != 1:
        raise ValueError('One valid, fully machined board is required')
    roots = _required_roots(doc, info, report)
    snapshots = {r['name']: r for r in report.get('objects', [])}
    if len(snapshots) != len(report.get('objects', [])) or set(snapshots) != {o.Name for o in doc.Objects}:
        raise ValueError('Native report must inventory every current document object exactly once')
    waveplates = [o for o in doc.Objects if _kind(o) == 'waveplate' and _on_plate(o, plate)]
    plain_stages = [o for o in doc.Objects if _kind(o) == 'rotation_stage_rsp05' and _on_plate(o, plate)]
    aoms = [o for o in doc.Objects if _kind(o) == 'AOMO_3100_125' and _on_plate(o, plate)]
    if len(waveplates) != 14 or len(plain_stages) != 14 or len(aoms) != 7:
        raise ValueError('Expected fourteen actual HWPs/RSP05s and seven actual retained AOMs')
    declared_names = {e['waveplate'] for e in entries.values()}
    old_hwp_names = {roots[n+' HWP'].Name for n in _LANES}
    if (declared_names & old_hwp_names or
            {o.Name for o in waveplates} != declared_names | old_hwp_names or
            {o.Name for o in aoms} != {e['aom'] for e in entries.values()}):
        raise ValueError('Entrance HWPs must be additions to all seven existing downstream HWPs and AOMs')
    result['inventory'] = {'waveplates': sorted(o.Name for o in waveplates),
                            'plain_rsp05_stages': sorted(o.Name for o in plain_stages),
                            'aoms': sorted(o.Name for o in aoms),
                            'retained_downstream_hwps': sorted(old_hwp_names)}
    paths = {p['name']: p for p in info['paths']}
    routes = {r['arm']: r for r in info.get('output_optical_routes', [])}
    if (len(paths) != len(info['paths']) or set(routes) != set(_LANES) or
            len(info.get('output_optical_routes', [])) != 7 or info.get('output_order_expected_routes') != 7 or
            info.get('expected_arm_count') != 7 or len(info['arms']) != 7):
        raise ValueError('All seven unique original downstream routes and AOM arms must remain registered')
    legacy_routes = report.get('zero_order_reference_model', {}).get('legacy_rf_on_output_optics', {}).get('report', {}).get('arms', [])
    legacy = {r['arm']: r for r in legacy_routes}
    if len(legacy_routes) != 7 or set(legacy) != set(_LANES):
        raise ValueError('Completed downstream route screening evidence is required')
    inverse = plate.Placement.inverse()
    for lane in _LANES:
        e = entries[lane]
        hwp, stage, adapter, mirror, aom = [doc.getObject(e[k]) for k in
                                          ('waveplate', 'stage', 'adapter', 'last_mirror', 'aom')]
        if any(o is None for o in (hwp, stage, adapter, mirror, aom)):
            raise ValueError('A registered component is missing in '+lane)
        if (roots.get(lane+' entrance HWP') is not hwp or roots.get(lane+' AOMO 3100-125') is not aom or
                roots.get(lane+(' M1' if lane == 'A' else ' M2')) is not mirror or _kind(mirror) not in _MIRRORS):
            raise ValueError('Entrance HWP/AOM/last mirror does not match its unique lane root: '+lane)
        assembly = _assembly(hwp, stage, adapter, plate, snapshots)
        _geometry_record(mirror, snapshots)
        _geometry_record(aom, snapshots)
        arms = [a for a in info['arms'] if a.get('lane') == lane]
        if len(arms) != 1 or arms[0].get('aom') != aom.Name or arms[0].get('beam_path') != e['beam_path']:
            raise ValueError('AOM arm identity changed for '+lane)
        if (not bool(aom.ApertureAlignmentApplied) or
                not _near(list(aom.MeshApertureLocal), [0., -.030, -.115])):
            raise ValueError('Actual AOM aperture registration is missing for '+lane)
        bore_world = aom.Placement.multVec(App.Vector(0., -.030, -.115))
        actual = [inverse.multVec(mirror.Placement.Base), inverse.multVec(hwp.Placement.Base),
                  inverse.multVec(bore_world)]
        positions = [list(p) for p in actual]
        path = paths.get(e['beam_path'])
        index = e['path_vertex_index']
        if path is None or not 0 < index < len(path['points'])-1:
            raise ValueError('Entrance HWP must be an internal registered lane vertex: '+lane)
        registered = [_xyz(p) for p in path['points'][index-1:index+2]]
        if any(not _near(a, b) for a, b in zip(positions, registered)):
            raise ValueError('Lane must contain the actual last mirror -> HWP -> AOM bore consecutively: '+lane)
        if any(abs(p[2]) > _TOL for p in positions) or not _near(positions[1], _xyz(e['optical_xy_mm'])):
            raise ValueError('Actual entrance optical axes must be at z=0 and the declared optical centre: '+lane)
        direction = _xyz(e['incoming_direction_xy'])
        steps = [[b[i]-a[i] for i in range(3)] for a, b in zip(positions, positions[1:])]
        distances = [_dot(s, direction) for s in steps]
        transverse = [math.sqrt(sum((s[i]-d*direction[i])**2 for i in range(3)))
                      for s, d in zip(steps, distances)]
        if (max(transverse) > _TOL or min(distances) <= 0. or
                not _near(distances, [e['last_mirror_to_hwp_mm'], e['hwp_to_aom_mm']])):
            raise ValueError('Non-collinear, reversed or incorrectly spaced entrance optics: '+lane)
        diagnostic_pairs = (
            ('actual_last_mirror_xy_mm', positions[0][:2]),
            ('actual_waveplate_xy_mm', positions[1][:2]),
            ('actual_aom_xy_mm', positions[2][:2]),
            ('actual_axial_distances_mm', distances),
            ('actual_cross_axis_errors_mm', transverse),
            ('actual_optical_reference_z_mm', [p[2] for p in positions]))
        if any(not _near(e.get(key, []), actual) for key, actual in diagnostic_pairs):
            raise ValueError('Source actual-pose diagnostics are stale or use the shifted AOM mesh origin: '+lane)
        if (abs(_number(e.get('actual_last_mirror_to_hwp_mm', -1))-distances[0]) > _TOL or
                abs(_number(e.get('actual_hwp_to_aom_mm', -1))-distances[1]) > _TOL):
            raise ValueError('Source actual-distance diagnostics differ from the native optical geometry: '+lane)
        normal = inverse.Rotation.multVec(hwp.Placement.Rotation.multVec(App.Vector(1, 0, 0)))
        aom_axis = inverse.Rotation.multVec(aom.Placement.Rotation.multVec(App.Vector(1, 0, 0)))
        axis_dot = _dot(list(normal), direction)
        aom_dot = _dot(list(aom_axis), direction)
        expected_pose = App.Placement(App.Vector(*_xyz(e['optical_xy_mm'])),
                                      App.Rotation(App.Vector(0, 0, 1), e['waveplate_angle_deg']))
        if (abs(abs(axis_dot)-1.) > 1.e-8 or
                abs(aom_dot-(1. if e['aom_mount_orientation'] == 'U' else -1.)) > 1.e-8 or
                not _near(list(inverse.multiply(hwp.Placement).toMatrix().A), list(expected_pose.toMatrix().A))):
            raise ValueError('Actual optical normals/mount pose disagree with the registered lane: '+lane)
        downstream = roots[lane+' HWP']
        children = list(getattr(downstream, 'ChildObjects', []))
        if len(children) != 1 or len(getattr(children[0], 'ChildObjects', [])) != 1:
            raise ValueError('Retained downstream HWP lost its mounted assembly: '+lane)
        retained = _assembly(downstream, children[0], children[0].ChildObjects[0], plate, snapshots)
        events = routes[lane]['events']
        types = [x['type'] for x in events]
        expected_types = (['aom', 'iris', 'hwp', 'pbs'] if lane in ('A', 'B1', 'B2') else
                          ['aom', 'hwp', 'pbs', 'rotation_mount', 'mirror', 'iris', 'mirror', 'fiber'] if lane == 'C1' else
                          ['aom', 'mirror', 'mirror', 'hwp', 'pbs', 'rotation_mount', 'iris', 'fiber'])
        if (types != expected_types or
                [(x['name'], x['type']) for x in events] != [(x['name'], x['type']) for x in legacy[lane]['events']]):
            raise ValueError('Original downstream route was replaced or reordered: '+lane)
        hwp_event = next(x for x in events if x['type'] == 'hwp')
        original_center = list(inverse.multVec(downstream.Placement.Base))
        downstream_indices = [i for i, p in enumerate(path['points']) if _near(_xyz(p), original_center)]
        if (hwp_event['name'] != lane+' HWP' or not _near(_xyz(hwp_event['xy']), original_center) or
                len(downstream_indices) != 1 or downstream_indices[0] <= index+1 or
                not _near(_xyz(events[0]['xy']), positions[2])):
            raise ValueError('Retained downstream HWP is not on its original post-AOM optical route: '+lane)
        result['assemblies'].append({'lane': lane, 'waveplate': hwp.Name, 'stage': stage.Name,
            'adapter': adapter.Name, 'last_mirror': mirror.Name, 'aom': aom.Name,
            'actual_mirror_hwp_bore_board_xyz_mm': positions, 'beam_path': e['beam_path'],
            'path_vertex_index': index, 'axial_distances_mm': distances,
            'cross_axis_errors_mm': transverse, 'waveplate_normal_dot_beam': axis_dot,
            'aom_axis_dot_beam': aom_dot, 'actual_aom_bore_world_xyz_mm': list(bore_world),
            'mounted_geometry': assembly, 'retained_downstream_assembly': retained,
            'retained_downstream_route': deepcopy(routes[lane]), 'passed': True})


def _clearance_gates(report, info):
    """Require independently completed checks; never infer clearance from bbox."""
    gates = []
    engineering = report.get('engineering', {})
    counts = engineering.get('counts', {})
    required_counts = ('confirmed_part_intersections', 'confirmed_mesh_contacts',
                       'centerline_intersections', 'finite_beam_sample_intersections',
                       'geometry_errors', 'beam_definition_errors', 'aom_aperture_failures',
                       'unresolved_mesh_pair_checks', 'unresolved_bbox_candidates',
                       'geometry_assertion_failures', 'drill_cut_issues', 'integral_adapter_failures')
    native_pass = all(type(counts.get(k)) is int and counts[k] == 0 for k in required_counts)
    for key in ('confirmed_part_intersections', 'confirmed_mesh_contacts', 'centerline_intersections',
                'finite_beam_sample_intersections', 'geometry_errors', 'beam_definition_errors'):
        native_pass = native_pass and engineering.get(key) == []
    gates.append({'check': 'full_native_geometry', 'passed': native_pass,
                  'counts': {k: counts.get(k) for k in required_counts}})
    for key in ('hole_clearance', 'service_clearance', 'fiber_clearance', 'km05t_audit',
                'bonded_cube_audit', 'zero_order_reference_model'):
        item = report.get(key, {})
        passed = item.get('passed') is True
        if key in ('hole_clearance', 'service_clearance', 'fiber_clearance'):
            passed = passed and bool(item.get('failure_counts')) and not any(item['failure_counts'].values())
        gates.append({'check': key, 'passed': bool(passed)})
    projection = report.get('projection_audit', {})
    keys = ('ray_crossings', 'thumbscrew_projection_hits', 'foreign_hardware_projection_conflicts',
            'unresolved_candidates', 'geometry_errors')
    passed = (projection.get('passed') is True and projection.get('mechanical_projection_passed') is True and
              all(projection.get(k) == [] and projection.get('counts', {}).get(k) == 0 for k in keys))
    gates.append({'check': 'independent_xy_beam_and_knob_projection', 'passed': passed})
    registered_rf = [r for r in info.get('service_regions', []) if r.get('kind') == 'aom_sma']
    actual_rf = [r for r in report.get('service_clearance', {}).get('regions', []) if r.get('kind') == 'aom_sma']
    aoms = {e['aom'] for e in info.get('pre_aom_waveplates', [])}
    rf_pass = (len(registered_rf) == len(actual_rf) == 7 and
               {r.get('owner') for r in actual_rf} == {r.get('owner') for r in registered_rf} == aoms)
    if rf_pass:
        for source in registered_rf:
            current = next(r for r in actual_rf if r['owner'] == source['owner'])
            rf_pass = rf_pass and current.get('name') == source.get('name')
            rf_pass = rf_pass and all(_near(current.get(k, []), source.get(k, [])) for k in
                                     ('origin_xy_mm', 'direction_xy'))
            rf_pass = rf_pass and all(abs(_number(current.get(k))-_number(source.get(k))) <= _TOL
                                     for k in ('length_mm', 'width_mm'))
            rf_pass = rf_pass and _number(current['length_mm']) >= 38.1 and _number(current['width_mm']) >= 20.
    gates.append({'check': 'seven_actual_registered_RF_reservations', 'passed': bool(rf_pass),
                  'minimum_required_length_mm': 38.1, 'native_regions': deepcopy(actual_rf)})
    exceptions = {'outside_plate_xy', 'bbox_overlap_candidates', 'unrelated_beam_proximity', _ISSUE_KEY}
    remaining = {k: v for k, v in report.get('summary_counts', {}).items() if k not in exceptions and v}
    gates.append({'check': 'all_previous_blocking_counts', 'passed': not remaining,
                  'preserved_nonzero_counts': remaining})
    return gates


def apply(report, doc, info, source_module=None):
    """Augment only this audit key and its issue counter; no exemptions."""
    result = {'schema': 'pre_aom_waveplate_audit/1', 'document': doc.Name,
              'passed': False, 'placement_passed': False, 'assemblies': [], 'errors': [],
              'declaration': deepcopy(info.get('pre_aom_waveplates', [])),
              'expected_counts': {'new_hwps': 7, 'new_rsp05_stages': 7, 'new_lip_adapters': 7,
                                  'retained_downstream_hwps': 7, 'total_hwps': 14, 'retained_aoms': 7},
              'scope': 'Actual placement, assembly identity and retained optical routes; all mechanical '
                       'clearance conclusions come from independent full native/projection/hole/service audits.',
              'source_provenance': {'audit_path': str(Path(__file__).resolve()),
                                    'audit_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
              'preserved_summary_counts': deepcopy(report.get('summary_counts', {}))}
    report[_REPORT_KEY] = result
    try:
        from PyOpticL import optomech
        spacing, source = _source(source_module)
        result['source_provenance']['board'] = source
        result['source_provenance']['optomech'] = {'path': str(Path(optomech.__file__).resolve()),
            'sha256': hashlib.sha256(Path(optomech.__file__).read_bytes()).hexdigest()}
        entries = _contract(info, spacing)
        _check_placement(doc, info, report, entries, result)
        result['placement_passed'] = len(result['assemblies']) == 7
    except Exception as exc:
        result['errors'].append({'stage': 'placement', 'error': str(exc)})
    try:
        result['independent_clearance_checks'] = _clearance_gates(report, info)
        result['errors'].extend({'stage': 'independent_clearance', 'error': g['check']+' did not pass'}
                                for g in result['independent_clearance_checks'] if not g['passed'])
    except Exception as exc:
        result['errors'].append({'stage': 'independent_clearance', 'error': str(exc)})
    result['passed'] = result['placement_passed'] and not result['errors']
    result['counts'] = {'verified_new_assemblies': len(result['assemblies']),
                        'errors': len(result['errors'])}
    report.setdefault('summary_counts', {})[_ISSUE_KEY] = len(result['errors']) or int(not result['passed'])
    return report


apply_to_report = apply
