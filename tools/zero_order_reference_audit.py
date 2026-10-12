"""Explicit RF-off, zero-order geometry scope for the Splitting board.

Mechanical occlusion, projected knobs, aperture margins and collision results
are retained. Only the legacy RF-on order-separation calculation becomes
inapplicable, with its complete original evidence archived in this report.
"""

from copy import deepcopy
import hashlib
import math
from pathlib import Path


_KIND = 'zero_order_reference_model'
_MIRRORS = {'circular_mirror', 'circular_mirror_union_optic'}
_TOL = 1.e-5


def _kind(obj):
    return type(getattr(obj, 'Proxy', None)).__name__


def _vector(values):
    import FreeCAD as App
    values = list(values)
    if len(values) == 2:
        values.append(0.)
    if len(values) != 3 or not all(math.isfinite(float(v)) for v in values):
        raise ValueError('Expected a finite 2-D or 3-D point')
    return App.Vector(*map(float, values))


def _unit(vector):
    if vector.Length < 1.e-7:
        raise ValueError('Zero-length optical segment')
    return vector/vector.Length


def _degrees(dot):
    return math.degrees(math.acos(max(-1., min(1., float(dot)))))


def apply(report, doc, info, expected_aoms=7):
    """Verify the declared model before marking RF-on screening inapplicable."""
    import FreeCAD as App
    from RubidiumLatticeV9 import output_optics

    engineering = report.get('engineering', {})
    previous = report.get(_KIND, {})
    original_output = deepcopy(previous.get('legacy_rf_on_output_optics', {}).get(
        'report', engineering.get('output_optics')))
    original_count = previous.get('legacy_output_order_feasibility_issues',
                                 engineering.get('counts', {}).get('output_order_feasibility_issues'))
    declaration = deepcopy(info.get('optical_reference_model', {}))
    result = {'schema': 'zero_order_reference_audit/1', 'passed': False,
              'declaration': declaration, 'scope': 'Declared RF-off zero-order nominal geometry only.',
              'expected_aom_count': expected_aoms, 'aoms': [], 'mirrors': [], 'segments': [], 'errors': [],
              'rf_on_first_order_readiness': 'not_evaluated_for_this_layout',
              'legacy_rf_on_output_optics': {
                  'applicable': False,
                  'reason': 'Legacy calculation assumes RF-on unwanted/desired diffraction-order separation; '
                            'the user requested RF-off zero-order transmission.',
                  'report': original_output},
              'legacy_output_order_feasibility_issues': original_count,
              'preserved_engineering_counts': deepcopy(engineering.get('counts', {})),
              'limitations': [
                  'RF-off is the explicitly declared model state, not a measurement of a connected RF source.',
                  'No RF-on first-order beam trajectory, diffraction efficiency, order rejection, or fiber coupling is certified.',
                  'All existing actual-geometry, aperture, finite-beam and XY knob checks remain authoritative.'],
              'provenance': {
                  'wrapper_path': str(Path(__file__).resolve()),
                  'wrapper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'legacy_output_optics_path': str(Path(output_optics.__file__).resolve()),
                  'legacy_output_optics_sha256': hashlib.sha256(Path(output_optics.__file__).read_bytes()).hexdigest()}}
    report[_KIND] = result
    report['optical_reference_model'] = declaration
    try:
        if (declaration.get('kind') != _KIND or declaration.get('aom_rf_state') != 'off' or
                type(declaration.get('modeled_order')) is not int or declaration['modeled_order'] != 0 or
                abs(float(declaration.get('diffraction_angle_deg', float('inf')))) > 1.e-10):
            raise ValueError('Missing explicit RF-off/order-zero/zero-deflection model declaration')
        if info.get('mode') != 'splitting' or report.get('document') != doc.Name:
            raise ValueError('Expected the current Splitting document and its full report')
        if not isinstance(original_output, dict) or original_count is None:
            raise ValueError('Missing completed legacy output-order screening evidence to preserve')
        paths = {p['name']: p for p in info.get('paths', [])}
        old_paths = {p['name']: p for p in report.get('paths', [])}
        if len(paths) != len(info.get('paths', [])) or not paths or set(paths) != set(old_paths):
            raise ValueError('Missing, duplicate, or stale optical paths')
        points = {}
        inverse_plate = info['plate'].Placement.inverse()
        for name, path in paths.items():
            current = [_vector(p) for p in path['points']]
            old = [_vector(p) for p in old_paths[name]['points']]
            if len(current) != len(old) or any((a-b).Length > _TOL for a, b in zip(current, old)):
                raise ValueError('Report differs from current path: '+name)
            if abs(float(path.get('diffraction_kink_deg', 0.))) > 1.e-10:
                raise ValueError('An RF-on diffraction-kink exception remains: '+name)
            points[name] = current
            for index, (a, b) in enumerate(zip(current, current[1:])):
                local = inverse_plate.Rotation.multVec(b-a)
                direction = _unit(local)
                axis_error = min(abs(direction.x)+abs(direction.z),
                                 abs(direction.y)+abs(direction.z))
                passed = axis_error < 1.e-8
                result['segments'].append({'path': name, 'segment': index,
                                            'board_frame_unit_direction': list(direction),
                                            'passed': passed})
                if not passed:
                    result['errors'].append({'error': 'Segment is not horizontal/vertical in the plate plane',
                                              'path': name, 'segment': index})

        roots = info.get('roots', {})
        aoms = {obj.Name: obj for obj in roots.values() if _kind(obj) == 'AOMO_3100_125'}
        if len(aoms) != expected_aoms:
            raise ValueError('Expected exactly %d actual AOM roots' % expected_aoms)
        aperture_checks = {item['object']: item for item in engineering.get('aom_aperture_checks', [])}
        if set(aperture_checks) != set(aoms):
            raise ValueError('Legacy mechanical aperture audit did not check every actual AOM')
        for name, obj in aoms.items():
            arms = [a for a in info.get('arms', []) if a.get('aom') == name]
            if len(arms) != 1 or arms[0].get('beam_path') not in points:
                raise ValueError('Missing unique own-path registration for '+name)
            path_name = arms[0]['beam_path']
            own = points[path_name]
            bore = obj.Placement.multVec(App.Vector(0., -.030, -.115))
            matches = [i for i, p in enumerate(own) if (p-bore).Length < _TOL]
            if len(matches) != 1 or matches[0] in (0, len(own)-1):
                raise ValueError('Actual AOM bore is not a unique internal path vertex: '+name)
            index = matches[0]
            incoming, outgoing = _unit(own[index]-own[index-1]), _unit(own[index+1]-own[index])
            axis = obj.Placement.Rotation.multVec(App.Vector(1, 0, 0))
            angle = float(obj.DiffractionAngle.Value)
            proxy_angle = float(getattr(obj.Proxy, 'diffraction_angle', float('inf')))
            straight_error = (incoming-outgoing).Length
            axis_error = 1.-abs(incoming.dot(axis))
            passed = (abs(angle) < 1.e-10 and abs(proxy_angle) < 1.e-10 and
                      straight_error < 1.e-8 and abs(axis_error) < 1.e-8 and
                      aperture_checks[name].get('status') == 'pass')
            result['aoms'].append({'object': name, 'path': path_name,
                                    'actual_diffraction_angle_deg': angle,
                                    'proxy_diffraction_angle_deg': proxy_angle,
                                    'actual_bore_centre_world_mm': list(bore),
                                    'straight_through_vector_error': straight_error,
                                    'actual_axis_dot_error': axis_error,
                                    'mechanical_aperture_status': aperture_checks[name].get('status'),
                                    'passed': passed})
            if not passed:
                result['errors'].append({'error': 'AOM is not a verified zero-deflection straight-through aperture',
                                          'object': name})

        mirrors = [obj for obj in roots.values() if _kind(obj) in _MIRRORS]
        if not mirrors:
            raise ValueError('No actual mirror roots were available to check')
        for obj in mirrors:
            center = obj.Placement.Base
            matches = [(name, i) for name, pts in points.items()
                       for i, point in enumerate(pts) if (point-center).Length < _TOL]
            if len(matches) != 1:
                raise ValueError('Mirror does not have one unambiguous own path vertex: '+obj.Name)
            name, index = matches[0]
            own = points[name]
            if index in (0, len(own)-1):
                raise ValueError('Mirror needs incoming and outgoing actual path segments: '+obj.Name)
            incoming, outgoing = _unit(own[index]-own[index-1]), _unit(own[index+1]-own[index])
            normal = obj.Placement.Rotation.multVec(App.Vector(1, 0, 0))
            reflected = incoming-normal*(2*incoming.dot(normal))
            incidence = _degrees(abs(incoming.dot(normal)))
            turn = _degrees(incoming.dot(outgoing))
            residual = (reflected-outgoing).Length
            front_facing = incoming.dot(normal) < 0 and outgoing.dot(normal) > 0
            passed = (abs(incidence-45.) < 1.e-6 and abs(turn-90.) < 1.e-6 and
                      residual < 1.e-8 and front_facing)
            result['mirrors'].append({'object': obj.Name, 'path': name, 'vertex': index,
                                       'actual_incidence_deg': incidence, 'turn_deg': turn,
                                       'reflection_vector_error': residual,
                                       'illuminated_front_face': front_facing, 'passed': passed})
            if not passed:
                result['errors'].append({'error': 'Actual mirror does not obey front-face 45-degree specular reflection',
                                          'object': obj.Name})
    except Exception as exc:
        result['errors'].append({'error': str(exc)})
    result['passed'] = (not result['errors'] and len(result['aoms']) == expected_aoms and
                        bool(result['mirrors']) and bool(result['segments']))
    report.setdefault('summary_counts', {})['zero_order_reference_issues'] = len(result['errors']) or int(not result['passed'])
    if result['passed']:
        engineering['output_optics'] = {
            'status': 'not_applicable_rf_off_zero_order_reference', 'nominal_feasible': None,
            'rf_state': 'off', 'modeled_order': 0, 'arms': [], 'errors': [],
            'scope': 'RF-on diffraction-order separation is not evaluated for this explicitly verified RF-off geometry.',
            'original_evidence': 'zero_order_reference_model.legacy_rf_on_output_optics.report'}
        engineering['counts']['output_order_feasibility_issues'] = 0
        report['summary_counts']['output_order_feasibility_issues'] = 0
    return report


apply_to_report = apply
