"""Resolve legacy mesh-contact candidates only with proven XY separation.

In FreeCAD call ``apply(report, doc, info)`` after the full engineering audit.
Actual placed mesh vertices (or BREP tessellation with its uncertainty) are
read through ta_projection_audit. No document geometry is changed. A strict
positive distance between enclosing XY convex hulls proves separation in 3D;
overlap, contact, unreadable geometry and inconclusive distances remain open.
Confirmed contacts are never replaced. This is not a new full-board pass.
"""
from copy import deepcopy
import hashlib
import math
from pathlib import Path


_SEPARATED = 'separated_by_xy_convex_hulls'
_MESH_RESOLVED = {
    'triangle_surface_contact_or_crossing', 'closed_shell_containment',
    'disjoint_actual_vertex_bounds', 'no_mesh_intersection_detected', _SEPARATED,
}
_BBOX_RESOLVED = _MESH_RESOLVED | {'solid_intersection', 'no_positive_solid_overlap'}
_CONFIRMED = {'triangle_surface_contact_or_crossing', 'closed_shell_containment', 'solid_intersection'}
_ELIGIBLE = {'unresolved_runtime_limit', 'no_surface_contact_containment_unresolved',
             'mesh_pair_check_error', 'bbox_candidate_only'}
_TOLERANCE_MM = 1.e-6


def _pair(record):
    return tuple(sorted((record['a'], record['b'])))


def _hull_distance(first, second, projection):
    """Symmetric edge-to-polygon distance, including containment in either way."""
    for hull in (first, second):
        if not hull or any(len(p) != 2 or not all(math.isfinite(float(v)) for v in p) for p in hull):
            raise ValueError('A projected hull is empty or nonfinite')
    return min(projection._polygon_distance(hull[i], hull[(i+1) % len(hull)], other)
               for hull, other in ((first, second), (second, first))
               for i in range(len(hull)))


def apply(report, doc, info):
    """Refine in place, preserve original evidence, and return the same report.

    Remaining counts use the legacy validator's accepted-status sets plus the
    new proven-separation status. All other counts and confirmed findings stay
    unchanged. Repeated calls preserve the first original report snapshots.
    """
    import ta_projection_audit as projection

    engineering = report['engineering']
    checks = engineering['mesh_pair_checks']
    boxes = engineering['bbox_overlap_candidates']
    counts = engineering['counts']
    summary = report['summary_counts']
    evidence = report.setdefault('mesh_candidate_refinement', {
        'schema': 'xy_mesh_candidate_refinement/1',
        'method': 'Symmetric edge-to-polygon distance of actual placed XY convex hulls.',
        'coordinate_frame': 'Baseplate local XY; no height-based exemptions.',
        'numeric_tolerance_mm': _TOLERANCE_MM,
        'original_engineering_counts': deepcopy(counts),
        'original_summary_counts': deepcopy(summary),
        'original_mesh_pair_checks': deepcopy(checks),
        'original_bbox_overlap_candidates': deepcopy(boxes),
        'original_engineering_result': deepcopy(engineering.get('result')),
        'attempts': [],
        'scope': 'Only unresolved mesh candidates with strictly separated enclosing projections are resolved. '
                 'Confirmed contacts and every other engineering check remain unchanged.',
    })
    if evidence.get('schema') != 'xy_mesh_candidate_refinement/1':
        raise ValueError('Unrecognized existing mesh-candidate refinement schema')
    evidence['source_provenance'] = {
        Path(path).name: hashlib.sha256(Path(path).read_bytes()).hexdigest()
        for path in (__file__, projection.__file__)
    }
    inverse_plate = info['plate'].Placement.inverse()
    cache = {}

    def geometry(name):
        if name not in cache:
            obj = doc.getObject(name)
            if obj is None:
                raise ValueError('Candidate object does not exist: '+name)
            actual = projection._board_geometry(obj, inverse_plate)
            if actual is None:
                raise ValueError('Candidate has no readable physical geometry: '+name)
            uncertainty = float(actual['uncertainty_mm'])
            if not math.isfinite(uncertainty) or uncertainty < 0:
                raise ValueError('Invalid tessellation uncertainty: '+name)
            cache[name] = {
                'object': name, 'label': obj.Label,
                'hull_xy_mm': [list(p) for p in actual['hull']],
                'source': actual['source'], 'uncertainty_mm': uncertainty,
                'vertices': len(actual['xy']), 'surface_faces': len(actual['faces']),
                'z_range_mm': list(actual['z_range_mm']),
            }
        return cache[name]

    confirmed_pairs = {_pair(item) for item in checks+boxes if item.get('status') in _CONFIRMED}
    for key in ('confirmed_mesh_contacts', 'confirmed_part_intersections'):
        confirmed_pairs.update(_pair(item) for item in engineering.get(key, []))

    for index, check in enumerate(checks):
        if check.get('status') not in _ELIGIBLE:
            continue
        pair = _pair(check)
        related = [item for item in boxes if _pair(item) == pair]
        attempt = {'mesh_check_index': index, 'a': check['a'], 'b': check['b'],
                   'original_mesh_check': deepcopy(check),
                   'original_bbox_candidates': deepcopy(related),
                   'resolved': False}
        evidence['attempts'].append(attempt)
        if pair in confirmed_pairs:
            attempt['reason'] = 'Confirmed contact evidence exists for this pair; preserved unchanged.'
            continue
        try:
            first, second = geometry(check['a']), geometry(check['b'])
            distance = _hull_distance(first['hull_xy_mm'], second['hull_xy_mm'], projection)
            uncertainty = first['uncertainty_mm']+second['uncertainty_mm']
            lower_bound = distance-uncertainty
            if not all(math.isfinite(value) for value in (distance, uncertainty, lower_bound)):
                raise ValueError('Nonfinite hull separation result')
            attempt.update(geometry_a=deepcopy(first), geometry_b=deepcopy(second),
                           hull_distance_mm=distance, combined_uncertainty_mm=uncertainty,
                           separation_lower_bound_mm=lower_bound)
            if lower_bound <= _TOLERANCE_MM:
                attempt['reason'] = 'Projection separation is not strictly above uncertainty and numeric tolerance.'
                continue
            attempt.update(resolved=True, reason='Enclosing XY hulls are strictly separated after both uncertainties.')
            update = {'status': _SEPARATED,
                      'refinement_evidence_index': len(evidence['attempts'])-1,
                      'xy_separation_lower_bound_mm': lower_bound}
            check.update(update)
            for item in related:
                if item.get('status') not in _BBOX_RESOLVED:
                    item.update(update)
        except Exception as exc:
            attempt['error'] = repr(exc)
            attempt['reason'] = 'Refinement could not prove separation; original status preserved.'

    counts['unresolved_mesh_pair_checks'] = sum(item.get('status') not in _MESH_RESOLVED for item in checks)
    counts['unresolved_bbox_candidates'] = sum(item.get('status') not in _BBOX_RESOLVED for item in boxes)
    for key in ('unresolved_mesh_pair_checks', 'unresolved_bbox_candidates'):
        summary[key] = counts[key]
    evidence['resolved_mesh_pairs'] = sum(item.get('status') == _SEPARATED for item in checks)
    evidence['remaining_unresolved_mesh_pair_checks'] = counts['unresolved_mesh_pair_checks']
    evidence['remaining_unresolved_bbox_candidates'] = counts['unresolved_bbox_candidates']
    return report
