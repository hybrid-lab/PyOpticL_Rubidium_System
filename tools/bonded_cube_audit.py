"""Resolve only verified axial glass contacts of the registered bonded PBS cubes.

The legacy validator tests a child's optical axis at its assembly root origin.
An upstream bonded cube lies 14.297 mm away from that RSP05 reference, so the
HWP-to-cube segment ends before the root and its intentional glass contacts are
reported as obstructions. This bridge retains every original event and checks
the actual cube transform, registered lane, finite beam envelope, and current
bond/sweep audit before reclassifying that exact glass object. No validator,
CAD object, housing, adhesive, or adjustment-control geometry is modified.
"""

from copy import deepcopy
import hashlib
import math
from pathlib import Path
import threading


_STAGE = 'rotation_stage_rsp05_bonded_cube'
_KEYS = ('centerline_intersections', 'finite_beam_sample_intersections')
_TOL = 1.e-4
_VALIDATION_LOCK = threading.RLock()


def _kind(obj):
    return type(getattr(obj, 'Proxy', None)).__name__


def _xyz(value):
    values = list(value)
    if len(values) == 2:
        values.append(0.)
    if len(values) != 3 or not all(math.isfinite(float(v)) for v in values):
        raise ValueError('Expected a finite 2-D or 3-D coordinate')
    return [float(v) for v in values]


def _near(a, b, tol=_TOL):
    return max(abs(x-y) for x, y in zip(_xyz(a), _xyz(b))) <= tol


def _radii(path):
    raw = path.get('envelope')
    if not isinstance(raw, (list, tuple)) or len(raw) != len(path['points']):
        raise ValueError('Missing explicit finite beam envelope')
    result = []
    for value in raw:
        if isinstance(value, dict):
            pair = [float(value['rx']), float(value['ry'])]
        elif isinstance(value, (int, float)):
            pair = [float(value), float(value)]
        else:
            pair = [float(v) for v in value]
        if len(pair) != 2 or not all(math.isfinite(v) for v in pair):
            raise ValueError('Invalid beam semiaxes')
        result.append(pair)
    return result


def _physical_objects(doc, info):
    """Mirror the registered physical tree; do not include ray/cutter drawings."""
    pending = list(info['roots'].values())+[info['plate']]
    pending += [obj for obj in doc.Objects if _kind(obj) == 'baseplate_mount']
    result, seen = [], set()
    while pending:
        obj = pending.pop()
        if obj.Name in seen:
            continue
        seen.add(obj.Name)
        pending.extend(getattr(obj, 'ChildObjects', []))
        if ((hasattr(obj, 'Mesh') and obj.Mesh.CountPoints) or
                (hasattr(obj, 'Shape') and not obj.Shape.isNull())):
            result.append(obj)
    return result


def _verified_event(event, key, registration, path):
    import FreeCAD as App

    cube = registration['cube_object']
    if event.get('class') != 'cube_splitter' or event.get('root') != registration['root_key']:
        raise ValueError('Event does not identify the registered glass and its exact parent root')
    if event.get('path') != registration['path_name']:
        raise ValueError('Foreign path: only the explicitly registered own lane is eligible')
    segment = event.get('segment')
    if type(segment) is not int or not 0 <= segment < len(path['points'])-1:
        raise ValueError('Invalid segment index')
    sample = event.get('sample')
    allowed = {'r%.1f_a%d' % (f, angle) for f in (.5, 1.) for angle in range(0, 360, 45)}
    if (key == _KEYS[0] and sample != 'center') or (key == _KEYS[1] and sample not in allowed):
        raise ValueError('Unexpected validator sample identity')
    envelope = _radii(path)
    radii = [envelope[segment], envelope[segment+1]]
    reported_radii = event.get('semiaxes_rx_ry_at_start_end_mm')
    if (not isinstance(reported_radii, (list, tuple)) or len(reported_radii) != 2 or
            any(len(row) != 2 for row in reported_radii) or
            any(abs(float(reported_radii[i][j])-radii[i][j]) > 1.e-6
                for i in range(2) for j in range(2))):
        raise ValueError('Event envelope differs from the current explicit path envelope')
    inverse = cube.Placement.inverse()
    start, end = [inverse.multVec(App.Vector(*_xyz(p)))
                  for p in path['points'][segment:segment+2]]
    delta = end-start
    length = delta.Length
    if length < 1.e-7 or abs(delta.x)/length < 1.-1.e-10:
        raise ValueError('Segment is not parallel to the actual cube transmission axis')
    offset = max(math.hypot(start.y, start.z), math.hypot(end.y, end.z))
    if offset > _TOL or not min(start.x, end.x)-_TOL <= 0 <= max(start.x, end.x)+_TOL:
        raise ValueError('Actual cube centre is not on this finite chief-ray segment')
    radius = max(abs(v) for row in radii for v in row)
    half_size = float(cube.CubeSize.Value)/2
    if not 0 < radius < half_size-offset-_TOL:
        raise ValueError('Finite beam envelope does not fit inside the cube face')
    points = event.get('points')
    if not isinstance(points, list) or not points or event.get('number_of_surface_crossings', 0) < len(points):
        raise ValueError('Missing actual surface-intersection evidence')
    for point in points:
        local = inverse.multVec(App.Vector(*_xyz(point)))
        if (abs(local.x) > half_size+_TOL or
                math.hypot(local.y, local.z) > radius+offset+_TOL):
            raise ValueError('Reported hit lies outside this cube or its bounded own-axis beam')
    return {'cube': cube.Name, 'stage': registration['stage_object'].Name,
            'registered_lane': registration['lane'], 'path': path['name'], 'segment': segment,
            'actual_cube_centre_world_mm': _xyz(cube.Placement.Base),
            'cube_local_segment_mm': [_xyz(start), _xyz(end)],
            'chief_ray_axis_offset_mm': offset, 'maximum_beam_radius_mm': radius,
            'cube_face_margin_lower_bound_mm': half_size-offset-radius,
            'reason': 'Verified intended transmission through the exact bonded glass cube; '
                      'legacy validator used the displaced RSP05 root origin. Refraction and polarization are not simulated.'}


def apply(report, doc, info, expected_count=4):
    """Refine an existing board report in place, returning the same report.

    Fail closed: missing registrations, stale coordinates, failed bond audits,
    off-axis/foreign rays, unrecognized samples, and oversized beams are retained
    as failures. Reapplication restores and rechecks the preserved raw events.
    The resulting ``bonded_cube_audit.passed`` must be an export guard.
    """
    from PyOpticL import optomech
    from RubidiumLatticeV9 import validation

    previous = report.get('bonded_cube_audit', {})
    engineering = report.get('engineering', {})
    raw = deepcopy(previous.get('original_intersections',
                                {key: engineering.get(key, []) for key in _KEYS}))
    result = {'schema': 'bonded_cube_optical_bridge/1', 'passed': False,
              'expected_count': expected_count, 'original_intersections': raw,
              'assemblies': [], 'resolved_optical_contacts': [], 'retained_cube_contacts': [],
              'errors': [], 'registrations': [],
              'scope': 'Only registered bonded cube_splitter glass on its own verified axial lane. '
                       'All other optical, housing, adhesive, mount, knob, and physical-collision checks remain unchanged.',
              'provenance': {'wrapper_path': str(Path(__file__).resolve()),
                             'wrapper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                             'optomech_path': str(Path(optomech.__file__).resolve()),
                             'legacy_module_path': str(Path(validation.__file__).resolve()),
                             'legacy_module_sha256': hashlib.sha256(Path(validation.__file__).read_bytes()).hexdigest(),
                             'legacy_limitation': 'validation._expected/_at_axis reference child optics at their root origin.'}}
    report['bonded_cube_audit'] = result
    registered = {}
    paths = {p['name']: p for p in info.get('paths', [])}
    report_paths = {p['name']: p for p in report.get('paths', [])}
    objects = {o['name']: o for o in report.get('objects', [])}
    stages = {o.Name: (key, o) for key, o in info.get('roots', {}).items() if _kind(o) == _STAGE}
    metadata = info.get('bonded_output_pbs', [])
    try:
        if report.get('document') != doc.Name:
            raise ValueError('Report document does not match the current document')
        if not isinstance(engineering, dict) or any(not isinstance(engineering.get(k), list) for k in _KEYS):
            raise ValueError('A completed full engineering report is required')
        if len(stages) != expected_count or len(metadata) != expected_count:
            raise ValueError('Expected exactly %d real stages and registrations' % expected_count)
        if {m['stage'] for m in metadata} != set(stages) or len({m['cube'] for m in metadata}) != expected_count:
            raise ValueError('Stage/cube registration is missing or duplicated')
        physical = _physical_objects(doc, info)
        for entry in metadata:
            key, stage = stages[entry['stage']]
            cube, glue = stage.BondedCube, stage.BondedAdhesive
            if (entry['cube'] != cube.Name or entry['adhesive'] != glue.Name or
                    _kind(cube) != 'cube_splitter' or _kind(glue) != 'RSP05CubeAdhesive' or
                    getattr(cube, 'ParentObject', None) is not stage or
                    getattr(glue, 'ParentObject', None) is not stage or
                    cube not in stage.ChildObjects or glue not in stage.ChildObjects or
                    abs(float(cube.CubeSize.Value)-12.7) > 1.e-6):
                raise ValueError('Incorrect actual bonded assembly links for '+stage.Name)
            if any(any(s in ('Touched', 'Invalid', 'Error') for s in obj.State)
                   for obj in (stage, cube, glue)):
                raise ValueError('Bonded assembly is not stably recomputed: '+stage.Name)
            if not cube.Shape.isValid() or cube.Shape.Volume <= 0:
                raise ValueError('Invalid actual optical glass geometry: '+cube.Name)
            if (not _near(entry['cube_centre_xy_mm'], cube.BasePlacement.Base) or
                    not _near(entry['stage_reference_xy_mm'], stage.BasePlacement.Base)):
                raise ValueError('Registration does not match actual board-frame placement')
            current = objects.get(cube.Name, {})
            bound = cube.Shape.BoundBox
            actual_bounds = [bound.XMin, bound.YMin, bound.ZMin, bound.XMax, bound.YMax, bound.ZMax]
            if (current.get('class') != 'cube_splitter' or len(current.get('bbox', [])) != 6 or
                    any(abs(a-float(b)) > _TOL for a, b in zip(actual_bounds, current['bbox']))):
                raise ValueError('Report cube geometry is stale or missing: '+cube.Name)
            lanes = [a for a in info.get('arms', []) if a.get('lane') == entry['lane']]
            explicit_path = entry.get('beam_path')
            if explicit_path is not None:
                if (not isinstance(explicit_path, str) or not explicit_path or len(lanes) > 1 or
                        (lanes and lanes[0].get('beam_path') != explicit_path)):
                    raise ValueError('Conflicting explicit own-lane registration for '+cube.Name)
                path_name = explicit_path
            else:
                if len(lanes) != 1:
                    raise ValueError('Missing unique own-lane registration for '+cube.Name)
                path_name = lanes[0]['beam_path']
            path, old_path = paths.get(path_name), report_paths.get(path_name)
            if (not path or not old_path or len(path['points']) != len(old_path['points']) or
                    not all(_near(a, b) for a, b in zip(path['points'], old_path['points'])) or
                    _radii(path) != _radii(old_path)):
                raise ValueError('Report path differs from current registered path: '+path_name)
            routes = [r for r in info.get('output_optical_routes', []) if r.get('arm') == entry['lane']]
            if len(routes) != 1 or not any(e.get('type') == 'pbs' and
                    _near(e['xy'], cube.BasePlacement.Base) for e in routes[0].get('events', [])):
                raise ValueError('Current optical route does not explicitly contain the actual cube centre')
            bond = optomech.audit_rsp05_bonded_cube(stage, physical)
            result['assemblies'].append(bond)
            if bond.get('passed') is not True:
                raise ValueError('Actual face/bond/rotation-envelope audit failed: '+stage.Name)
            registered[cube.Name] = dict(stage_object=stage, cube_object=cube, root_key=key,
                                         lane=entry['lane'], path_name=path_name)
            result['registrations'].append(dict(stage=stage.Name, cube=cube.Name, adhesive=glue.Name,
                                                 root_key=key, lane=entry['lane'], path=path_name))
    except Exception as exc:
        result['errors'].append({'error': str(exc)})
        registered.clear()  # Partial discovery cannot authorize any refinement.

    for key in _KEYS:
        retained = []
        for event in raw.get(key, []):
            registration = registered.get(event.get('object'))
            if registration is None:
                retained.append(deepcopy(event))
                continue
            try:
                evidence = _verified_event(event, key, registration, paths[registration['path_name']])
            except Exception as exc:
                retained.append(deepcopy(event))
                result['retained_cube_contacts'].append({'source_list': key, 'original_event': deepcopy(event),
                                                          'reason_retained': str(exc)})
            else:
                result['resolved_optical_contacts'].append({'source_list': key, 'original_event': deepcopy(event),
                                                             'verification': evidence})
        engineering[key] = retained
        engineering.setdefault('counts', {})[key] = len(retained)
        report.setdefault('summary_counts', {})[key] = len(retained)
    result['counts'] = {'registered_stages': len(registered),
                        'resolved_centerline_contacts': sum(e['source_list'] == _KEYS[0] for e in result['resolved_optical_contacts']),
                        'resolved_finite_beam_contacts': sum(e['source_list'] == _KEYS[1] for e in result['resolved_optical_contacts']),
                        'retained_cube_contacts': len(result['retained_cube_contacts']), 'errors': len(result['errors'])}
    result['passed'] = (len(registered) == expected_count and not result['errors'] and
                        not result['retained_cube_contacts'])
    report['summary_counts']['bonded_cube_audit_issues'] = (len(result['errors'])+
        len(result['retained_cube_contacts'])+int(len(registered) != expected_count))
    issue_counts = {k: v for k, v in engineering.get('counts', {}).items()
                    if k not in ('bbox_overlap_candidates', 'unrelated_beam_proximity')}
    engineering['result'] = ('Issues or unresolved candidates recorded; review evidence and stated exclusions'
                             if any(issue_counts.values()) or not result['passed'] else
                             'No issue found by these limited nominal CAD checks; physical clearance not certified')
    return report


apply_to_report = apply


def inspect_board(doc, info, plate_size, full=True, expected_heads=5,
                  expected_count=4, mesh_pair_seconds=30.):
    """Run the KM05T board audit and the strictly bounded optical refinement.

    board_tools reloads validation immediately before running it. A temporary
    proxy for *that module's* importlib reference installs the time-budget
    wrapper after the real reload. The process-wide importlib module itself is
    untouched. Both references are restored in finally; triangle SAT, BVH,
    containment tests, tolerances, and all failure statuses are unchanged.
    """
    from RubidiumLatticeV9 import board_tools, validation
    import km05t_audit

    seconds = float(mesh_pair_seconds)
    if not math.isfinite(seconds) or seconds < 5.:
        raise ValueError('Mesh-pair budget must be finite and at least the legacy 5 seconds')
    if not full:
        return km05t_audit.inspect_board(doc, info, plate_size, full=False,
                                         expected_heads=expected_heads)
    budget = {'seconds_per_pair': seconds, 'legacy_default_seconds': 5.,
              'method': 'Scoped time-budget argument only; unchanged triangle BVH/SAT and containment algorithm.',
              'validation_module_path': str(Path(validation.__file__).resolve()),
              'validation_module_sha256': hashlib.sha256(Path(validation.__file__).read_bytes()).hexdigest(),
              'installed_after_real_module_reload': False}
    with _VALIDATION_LOCK:
        original_importlib = board_tools.importlib
        original_check = None

        class ScopedReload:
            def __getattr__(self, name):
                return getattr(original_importlib, name)

            def reload(self, module):
                nonlocal original_check
                loaded = original_importlib.reload(module)
                if loaded is validation:
                    original_check = loaded._mesh_pair_check
                    actual_check = original_check

                    def extended_check(a, b, seconds=None):
                        allowance = mesh_pair_seconds if seconds is None else seconds
                        return actual_check(a, b, seconds=float(allowance))

                    loaded._mesh_pair_check = extended_check
                    budget['installed_after_real_module_reload'] = True
                return loaded

        try:
            board_tools.importlib = ScopedReload()
            report = km05t_audit.inspect_board(doc, info, plate_size, full=True,
                                               expected_heads=expected_heads)
        finally:
            if original_check is not None:
                validation._mesh_pair_check = original_check
            board_tools.importlib = original_importlib
            budget['mesh_function_restored'] = (original_check is not None and
                                                 validation._mesh_pair_check is original_check)
            budget['board_tools_importlib_reference_restored'] = board_tools.importlib is original_importlib
    report = apply(report, doc, info, expected_count=expected_count)
    report['bonded_cube_audit']['mesh_pair_runtime_budget'] = budget
    if not all(budget.get(k) for k in ('installed_after_real_module_reload', 'mesh_function_restored',
                                      'board_tools_importlib_reference_restored')):
        report['bonded_cube_audit']['errors'].append({'error': 'Mesh time-budget hook was not installed/restored as expected'})
        report['bonded_cube_audit']['passed'] = False
        report['bonded_cube_audit']['counts']['errors'] += 1
        report['summary_counts']['bonded_cube_audit_issues'] += 1
    if info.get('optical_reference_model', {}).get('kind') == 'zero_order_reference_model':
        import zero_order_reference_audit
        zero_order_reference_audit.apply(report, doc, info)
    return report
