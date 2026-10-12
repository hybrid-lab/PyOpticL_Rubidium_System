"""Verify the TA's actual single output before retiring AOM-order screening.

This checks inventory, registered geometry and component order. It does not
certify Gaussian mode matching, PBS polarization, or unfinished cell apertures.
All unrelated collision, aperture, finite-beam and projected-knob evidence is
preserved. Run after board_tools.inspect_board and before production export.
"""

from copy import deepcopy
import hashlib
import math
from pathlib import Path


KIND = 'single_output_no_aom'
_TOL = 1.e-5
_MIRRORS = {'circular_mirror', 'circular_mirror_union_optic'}
_HEADS = {'fiberport_mount_KA05T', 'fiberport_mount_KA05T_holes'}
_STAGE = 'rotation_stage_rsp05_bonded_cube'
_FORBIDDEN = {'AOMO_3100_125', 'IntegralAOMSeat', 'shutter_sr475'}
_EMPTY_PBS_SPEC = 'PBS path specifications must be a nonempty list'


def _kind(obj):
    return type(getattr(obj, 'Proxy', None)).__name__


def _vector(value):
    import FreeCAD as App
    values = list(value)
    if len(values) == 2:
        values.append(0.)
    if len(values) != 3 or not all(math.isfinite(float(v)) for v in values):
        raise ValueError('Expected a finite 2-D or 3-D coordinate')
    return App.Vector(*map(float, values))


def _unit(vector):
    if vector.Length < _TOL:
        raise ValueError('Degenerate optical segment')
    return vector/vector.Length


def _verified_geometry(obj, snapshot):
    """Compare a real leaf's current physical bounds with the full report."""
    old = snapshot.get(obj.Name, {})
    geometry = obj.Shape if hasattr(obj, 'Shape') and not obj.Shape.isNull() else getattr(obj, 'Mesh', None)
    if geometry is None or (hasattr(geometry, 'CountPoints') and not geometry.CountPoints):
        raise ValueError('Missing actual optical geometry: '+obj.Name)
    box = geometry.BoundBox
    bounds = [box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax]
    if (old.get('class') != _kind(obj) or len(old.get('bbox', [])) != 6 or
            any(abs(a-float(b)) > _TOL for a, b in zip(bounds, old['bbox']))):
        raise ValueError('Stale or missing report geometry for '+obj.Name)
    return {'object': obj.Name, 'class': _kind(obj), 'actual_bbox_mm': bounds}


def _verified_fiber_assembly(head, snapshot, report, info):
    """KA05T roots are containers; their linked parts hold the real geometry."""
    old = snapshot.get(head.Name, {})
    if (old.get('class') != _kind(head) or 'position' not in old or
            (_vector(old['position'])-head.Placement.Base).Length > _TOL):
        raise ValueError('Stale or missing actual fiber assembly root placement')
    evidence, seen, pending = [], {head.Name}, [head]
    while pending:
        parent = pending.pop()
        for child in getattr(parent, 'ChildObjects', []):
            if child.Name in seen or getattr(child, 'ParentObject', None) is not parent:
                raise ValueError('Duplicated or incorrectly linked KA05T child: '+child.Name)
            if getattr(child, 'Baseplate', None) != info['plate']:
                raise ValueError('KA05T child belongs to a different or missing baseplate')
            seen.add(child.Name)
            pending.append(child)
            evidence.append(_verified_geometry(child, snapshot))
    required = {'mirror_mount_KA05T', 'fiber_adapter_sm05fca2', 'lens_tube_sm05l05',
                'lens_adapter_s05tm09', 'mounted_lens_c220tmda'}
    if any(sum(e['class'] == kind for e in evidence) != 1 for kind in required):
        raise ValueError('KA05T must retain its real mount, fiber adapter, tube, lens adapter and lens')
    keys = [key for key, root in info['roots'].items() if root is head]
    if len(keys) != 1 or set(report.get('roots', {}).get(keys[0], [])) != seen:
        raise ValueError('Report KA05T assembly tree differs from the actual linked children')
    return evidence


def _scoped_pbs_result():
    return {'status': 'not_applicable_single_transmitted_output', 'passed': None, 'failure_count': 0,
            'checks': [], 'errors': [],
            'scope': 'Legacy multi-port PBS path specifications are inapplicable to the verified one-cube axial output.',
            'original_evidence': 'single_output_audit.legacy_pbs_paths'}


def apply(report, doc, info):
    """Fail closed unless actual geometry proves the declared no-AOM train."""
    import FreeCAD as App
    from RubidiumLatticeV9 import output_optics, pbs_path_check

    engineering = report.get('engineering', {})
    previous = report.get('single_output_audit', {})
    original = deepcopy(previous.get('legacy_output_optics', engineering.get('output_optics')))
    old_count = previous.get('legacy_output_order_feasibility_issues',
                             engineering.get('counts', {}).get('output_order_feasibility_issues'))
    old_pbs = deepcopy(previous.get('legacy_pbs_paths', engineering.get('pbs_paths')))
    old_pbs_count = previous.get('legacy_pbs_path_failures',
                                engineering.get('counts', {}).get('pbs_path_failures'))
    declaration = deepcopy(info.get('optical_reference_model', {}))
    result = {'schema': 'single_output_audit/1', 'passed': False, 'declaration': declaration,
              'scope': 'Actual post-cell order and single KA05T output with no AOM or shutter.',
              'legacy_output_optics': original, 'legacy_output_order_feasibility_issues': old_count,
              'legacy_pbs_paths': old_pbs, 'legacy_pbs_path_failures': old_pbs_count,
              'preserved_engineering_counts': deepcopy(engineering.get('counts', {})),
              'inventory': {}, 'events': [], 'mirrors': [], 'errors': [],
              'limitations': [
                  'AOM RF/order-separation calculations are inapplicable because no AOM is installed.',
                  'Gaussian mode matching, coupling efficiency and PBS polarization are not certified.',
                  'Cell-cover optical readiness and all independent mechanical audits remain authoritative.'],
              'provenance': {'wrapper_path': str(Path(__file__).resolve()),
                             'wrapper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                             'legacy_output_optics_path': str(Path(output_optics.__file__).resolve()),
                             'legacy_output_optics_sha256': hashlib.sha256(Path(output_optics.__file__).read_bytes()).hexdigest(),
                             'legacy_pbs_paths_path': str(Path(pbs_path_check.__file__).resolve()),
                             'legacy_pbs_paths_sha256': hashlib.sha256(Path(pbs_path_check.__file__).read_bytes()).hexdigest()}}
    report['single_output_audit'] = result
    report['optical_reference_model'] = declaration
    try:
        if (info.get('mode') != 'ta' or report.get('mode') != 'ta' or
                report.get('document') != doc.Name or declaration.get('kind') != KIND):
            raise ValueError('Expected the current TA document and explicit single-output/no-AOM declaration')
        if not isinstance(original, dict) or old_count is None:
            raise ValueError('Completed legacy output-order evidence is required before applying this scope')
        if info.get('arms') != [] or info.get('expected_arm_count') != 0:
            raise ValueError('No AOM arms may remain; expected_arm_count must explicitly be zero')
        if info.get('pbs_path_specs') or any(r.get('kind') == 'aom_sma' for r in info.get('service_regions', [])):
            raise ValueError('Old split-PBS or AOM RF-service metadata remains')
        plate = info['plate']
        actual = [o for o in doc.Objects if getattr(o, 'Baseplate', plate) == plate]
        by_name = {o.Name: o for o in actual}
        roots = {o.Name for o in info['roots'].values()}
        forbidden = [o.Name for o in actual if _kind(o) in _FORBIDDEN]
        heads = [o for o in actual if _kind(o).startswith('fiberport_mount_')]
        stages = [o for o in actual if _kind(o) == _STAGE]
        cubes = [o for o in actual if _kind(o) == 'cube_splitter']
        glues = [o for o in actual if _kind(o) == 'RSP05CubeAdhesive']
        result['inventory'] = {'forbidden_aom_shutter_or_seat': forbidden,
                               'fiber_heads': [o.Name for o in heads],
                               'bonded_stages': [o.Name for o in stages],
                               'actual_pbs_cubes': [o.Name for o in cubes],
                               'adhesive_parts': [o.Name for o in glues]}
        if forbidden or len(heads) != 1 or _kind(heads[0]) not in _HEADS or heads[0].Name not in roots:
            raise ValueError('Expected no AOM/shutter/seat and exactly one actual KA05T assembly root')
        if len(stages) != 1 or len(cubes) != 1 or len(glues) != 1 or stages[0].Name not in roots:
            raise ValueError('Expected one actual bonded rotating PBS and no remaining main-power cube')
        stage, cube, glue, head = stages[0], cubes[0], glues[0], heads[0]
        if stage.BondedCube is not cube or stage.BondedAdhesive is not glue:
            raise ValueError('The actual cube and adhesive are not linked to the one rotating stage')
        size = float(cube.CubeSize.Value)
        expected_reflection = -135. if bool(cube.Invert) else 135.
        reflection = float(getattr(cube.Proxy, 'reflection_angle', float('nan')))
        if (not math.isfinite(size) or abs(size-12.7) > _TOL or
                getattr(cube.Proxy, 'transmission', None) is not True or
                not math.isfinite(reflection) or abs(reflection-expected_reflection) > _TOL):
            raise ValueError('Actual 12.7 mm PBS transmission/reflection fields do not match cube_splitter')
        result['pbs_transmission_fields'] = {'object': cube.Name, 'cube_size_mm': size,
                                            'transmission': True, 'invert': bool(cube.Invert),
                                            'proxy_reflection_angle_deg': reflection,
                                            'reflected_output_scope': 'Not modelled or certified; only the axial transmitted output is retained.'}
        lane, path_name = declaration.get('output_lane'), declaration.get('beam_path')
        if not isinstance(lane, str) or not lane or not isinstance(path_name, str) or not path_name:
            raise ValueError('Declare a nonempty output_lane and beam_path')
        routes = info.get('output_optical_routes', [])
        if (len(routes) != 1 or routes[0].get('arm') != lane or
                info.get('output_order_expected_routes') != 1):
            raise ValueError('Expected exactly one declared output route matching the registered lane')
        events = routes[0].get('events', [])
        types = [e.get('type') for e in events]
        # Mirrors can fold propagation between the lenses. Removing only
        # mirrors must leave the exact ordered optical train, and the fiber
        # remains the final physical event, never an intermediate waypoint.
        if (types.count('mirror') < 1 or
                [kind for kind in types if kind != 'mirror'] != ['lens', 'lens', 'hwp', 'pbs', 'fiber'] or
                types[-1] != 'fiber'):
            raise ValueError('Mirror folds must retain two lenses, HWP, bonded PBS, then one terminal fiber')
        if len({e.get('object') for e in events}) != len(events):
            raise ValueError('Every optical event must name a distinct actual object')
        paths = [p for p in info.get('paths', []) if p.get('name') == path_name]
        old_paths = [p for p in report.get('paths', []) if p.get('name') == path_name]
        if len(paths) != 1 or len(old_paths) != 1:
            raise ValueError('Missing or ambiguous current/report output path')
        path, old_path = paths[0], old_paths[0]
        points = [_vector(p) for p in path['points']]
        old_points = [_vector(p) for p in old_path['points']]
        if (len(points) != len(events)+1 or len(points) != len(old_points) or
                any((a-b).Length > _TOL for a, b in zip(points, old_points)) or
                path.get('envelope') != old_path.get('envelope')):
            raise ValueError('Output path must run from the fixed cell axis through each current event exactly once')
        cell = by_name.get(declaration.get('cell'))
        if cell is None or _kind(cell) != 'SlidingCellEnclosure' or cell.Name not in roots:
            raise ValueError('Declare the actual full sliding-cell enclosure root')
        cell_axis = cell.BasePlacement.multVec(App.Vector(0., -float(cell.Slide.Value), 0.))
        if (points[0]-cell_axis).Length > _TOL:
            raise ValueError('Output path does not start on the fixed cell optical axis')
        metadata = info.get('bonded_output_pbs', [])
        if (len(metadata) != 1 or metadata[0].get('stage') != stage.Name or
                metadata[0].get('cube') != cube.Name or metadata[0].get('adhesive') != glue.Name or
                metadata[0].get('lane') != lane or metadata[0].get('beam_path') != path_name):
            raise ValueError('The one bonded cube must register this exact output path and lane')
        snapshot = {o['name']: o for o in report.get('objects', [])}
        checked = []
        allowed = {'mirror': _MIRRORS, 'lens': {'circular_lens'}, 'hwp': {'waveplate'},
                   'pbs': {'cube_splitter'}, 'fiber': _HEADS}
        for index, event in enumerate(events):
            obj = by_name.get(event.get('object'))
            event_type = event['type']
            if obj is None or _kind(obj) not in allowed[event_type]:
                raise ValueError('Optical event has the wrong actual class: '+str(event.get('object')))
            if event_type != 'pbs' and obj.Name not in roots:
                raise ValueError('Optical event is not a declared physical root: '+obj.Name)
            if (event_type == 'pbs' and obj is not cube) or (event_type == 'fiber' and obj is not head):
                raise ValueError('Output event does not reference the unique actual PBS/fiber')
            if event_type == 'fiber':
                result['fiber_assembly_geometry'] = _verified_fiber_assembly(obj, snapshot, report, info)
            else:
                _verified_geometry(obj, snapshot)
            axis = obj.BasePlacement.Rotation.multVec(App.Vector(1., 0., 0.))
            center = obj.BasePlacement.Base
            if event_type == 'fiber':
                center = center+axis*18.798
            if (center-_vector(event['xy'])).Length > _TOL or (center-points[index+1]).Length > _TOL:
                raise ValueError('Event/path does not use the actual optical centre: '+obj.Name)
            incoming = _unit(points[index+1]-points[index])
            outgoing = _unit(points[index+2]-points[index+1]) if index+2 < len(points) else None
            row = {'object': obj.Name, 'class': _kind(obj), 'type': event_type,
                   'actual_optical_centre_xy_mm': [center.x, center.y],
                   'distance_from_previous_mm': (points[index+1]-points[index]).Length}
            if event_type == 'mirror':
                reflected = incoming-axis*(2*incoming.dot(axis))
                incidence = math.degrees(math.acos(min(1., abs(incoming.dot(axis)))))
                residual = (reflected-outgoing).Length
                front = incoming.dot(axis) < 0 and outgoing.dot(axis) > 0
                row.update(incidence_deg=incidence, reflection_vector_error=residual, illuminated_front_face=front)
                result['mirrors'].append(deepcopy(row))
                if abs(incidence-45.) > 1.e-6 or residual > 1.e-8 or not front:
                    raise ValueError('Mirror does not implement a front-face 45-degree fold: '+obj.Name)
            elif abs(abs(incoming.dot(axis))-1.) > 1.e-8 or (outgoing is not None and (incoming-outgoing).Length > 1.e-8):
                raise ValueError('Output optic is not on the actual straight transmission axis: '+obj.Name)
            if event_type == 'fiber' and incoming.dot(axis) > -1.+1.e-8:
                raise ValueError('Beam enters the rear of the actual KA05T optical assembly')
            if event_type == 'lens':
                focal = float(obj.EstimatedEFL795.Value)
                if not math.isfinite(focal) or focal <= 0 or abs(focal-float(event.get('focal_mm', 0.))) > _TOL:
                    raise ValueError('Lens event does not carry the actual 795-nm focal-length property')
                row['estimated_focal_length_795_mm'] = focal
            result['events'].append(row)
            checked.append(obj)
        lens_indices = [index for index, kind in enumerate(types) if kind == 'lens']
        lens1, lens2 = [checked[index] for index in lens_indices]
        chord = (lens1.BasePlacement.Base-lens2.BasePlacement.Base).Length
        propagation = []
        for index in range(lens_indices[0]+1, lens_indices[1]+1):
            propagation.append({'path_segment': index,
                                'start_xy_mm': [points[index].x, points[index].y],
                                'end_xy_mm': [points[index+1].x, points[index+1].y],
                                'length_mm': (points[index+1]-points[index]).Length})
        distance = sum(segment['length_mm'] for segment in propagation)
        expected = float(lens1.EstimatedEFL795.Value)+float(lens2.EstimatedEFL795.Value)
        result['lens_pair'] = {'lens_objects': [lens1.Name, lens2.Name],
                               'path': path_name, 'chord_mm': chord,
                               'optical_path_distance_mm': distance,
                               'sum_estimated_focal_lengths_mm': expected,
                               'propagation_segments': propagation,
                               'scope': 'Geometric propagation distance along the verified registered path between model lens centres; '
                                        'ideal mirror unfolding, not refractive optical phase or measured principal-plane spacing.'}
        if abs(distance-expected) > _TOL:
            raise ValueError('Lens-to-lens propagation along the actual registered path does not equal the 795-nm focal sum')
        hwp = checked[types.index('hwp')]
        result['output_spacings_mm'] = {
            'hwp_to_stage_reference': (hwp.BasePlacement.Base-stage.BasePlacement.Base).Length,
            'hwp_to_actual_cube': (hwp.BasePlacement.Base-cube.BasePlacement.Base).Length,
            'actual_cube_to_fiber_face': (cube.BasePlacement.Base-points[-1]).Length}
        # The old PBS checker only accepts splitting/return-path specifications.
        # Reclassify exactly its empty-specification error after the real single
        # transmitted train above has passed. Any other evidence stays blocking.
        if (not isinstance(old_pbs, dict) or old_pbs.get('document') != doc.Name or
                old_pbs.get('mode') != 'ta' or old_pbs.get('explicit_subassembly_scope') is not True or
                old_pbs.get('errors') != [_EMPTY_PBS_SPEC] or old_pbs.get('checks') != [] or
                old_pbs.get('passed') is not False or old_pbs.get('failure_count') != 1 or old_pbs_count != 1):
            raise ValueError('Unrelated or missing legacy PBS evidence retained; only the exact empty-specification error is inapplicable')
        current_pbs = engineering.get('pbs_paths', {})
        previously_scoped = (current_pbs == _scoped_pbs_result() and
                             engineering.get('counts', {}).get('pbs_path_failures') == 0 and
                             report.get('summary_counts', {}).get('pbs_path_failures') == 0)
        if not previously_scoped and (current_pbs != old_pbs or
                                      engineering.get('counts', {}).get('pbs_path_failures') != 1 or
                                      report.get('summary_counts', {}).get('pbs_path_failures') != 1):
            raise ValueError('Current PBS evidence contains additional changes or failures; retained unchanged')
    except Exception as exc:
        result['errors'].append({'error': str(exc)})
    result['passed'] = not result['errors']
    report.setdefault('summary_counts', {})['single_output_audit_issues'] = len(result['errors'])
    if result['passed']:
        engineering['output_optics'] = {
            'status': 'not_applicable_no_aom', 'nominal_feasible': None, 'arms': [], 'errors': [],
            'scope': 'No AOM exists in the verified single-output train; RF/order separation is inapplicable.',
            'original_evidence': 'single_output_audit.legacy_output_optics'}
        engineering['counts']['output_order_feasibility_issues'] = 0
        report['summary_counts']['output_order_feasibility_issues'] = 0
        engineering['pbs_paths'] = _scoped_pbs_result()
        engineering['counts']['pbs_path_failures'] = 0
        report['summary_counts']['pbs_path_failures'] = 0
        issues = {key: value for key, value in engineering['counts'].items()
                  if key not in ('bbox_overlap_candidates', 'unrelated_beam_proximity')}
        engineering['result'] = ('Issues or unresolved candidates recorded; review evidence and stated exclusions'
                                 if any(issues.values()) else
                                 'No issue found by these limited nominal CAD checks; physical clearance not certified')
    return report


apply_to_report = apply
