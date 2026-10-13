"""Verify the explicitly authorized four bare TA conditioning stations.

Run ``apply(report, doc, info)`` after the full native board audit. Only its
legacy three-cylinder/six-total *count assumptions* can be reclassified. Raw
evidence is retained; no object, geometry, external module or other check is
modified. Schema 1 leaves holders unselected. Schema 2 uses the user's
selected POLARIS-L05G: native probe objects verify actual meshes and mounting
axes, while the production document keeps bare taps and unselected optics.

Required ``info['requirements']['conditioning_stations']``::

    {'schema': 'conditioning_stations/1',
     'cylindrical_holes': [two_actual_object_names],
     'spherical_holes': [two_actual_object_names],
     'expected_counts': {'cylindrical': 2, 'spherical': 2, 'total': 4},
     'round_envelope_diameter_mm': 16.0, 'holders_unselected': True}

The ordinary cylindrical list, common stations-only spherical group and four
provisional envelopes must agree with this declaration. Each envelope requires
a 16 mm circle and its actual beam direction; the existing L05G/bonded-lens
footprint check remains active as an additional conservative reservation.
"""

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path


_COUNTS = {'cylindrical': 2, 'spherical': 2, 'total': 4}
_TOL = 1.e-5
_OLD_SIX_ERROR = {'kind': 'six_common_stations',
                  'error': 'Expected six common stations (bare 8-32 holes)'}


def _kind(obj):
    return type(getattr(obj, 'Proxy', None)).__name__


def _name(value):
    return value if isinstance(value, str) else getattr(value, 'Name', None)


def _same(a, b):
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def _near(a, b):
    return (len(a) == len(b) and all(math.isfinite(float(x)) and math.isfinite(float(y))
            and abs(float(x)-float(y)) <= _TOL for x, y in zip(a, b)))


def _contract(info):
    """Reject omitted, extra, duplicate or ambiguous station declarations."""
    if info.get('mode') != 'ta':
        raise ValueError('Four-station authorization is scoped to the TA board')
    req = info.get('requirements', {})
    declaration = req.get('conditioning_stations', {})
    selected_l05g = (declaration.get('schema') == 'conditioning_stations/2'
                     and declaration.get('holder_model') == 'POLARIS-L05G'
                     and declaration.get('holder_class') == 'lens_holder_l05g_no_pin_slots'
                     and declaration.get('holder_selection_confirmed') is True
                     and declaration.get('holders_unselected') is False
                     and declaration.get('optics_unselected') is True)
    legacy_unselected = (declaration.get('schema') == 'conditioning_stations/1'
                         and declaration.get('holders_unselected') is True)
    if (not (selected_l05g or legacy_unselected) or
            declaration.get('expected_counts') != _COUNTS or
            declaration.get('round_envelope_diameter_mm') != 16.):
        raise ValueError('Explicit two-cylinder/two-spherical bare-station declaration is required')
    cylinder = declaration.get('cylindrical_holes', [])
    sphere = declaration.get('spherical_holes', [])
    names = list(cylinder)+list(sphere)
    if (len(cylinder) != 2 or len(sphere) != 2 or
            not all(isinstance(n, str) and n for n in names) or len(set(names)) != 4):
        raise ValueError('Exactly four distinct object names, two in each group, are required')
    if req.get('mount_only_cylindrical_holes') != cylinder:
        raise ValueError('The original cylindrical requirement must name exactly the two declared holes')
    common = [g for g in req.get('spherical_groups', []) if g.get('name') == 'common']
    if (len(common) != 1 or common[0].get('active_lenses') != [] or
            common[0].get('spare_holes') != sphere or
            common[0].get('stations_only') is not True or common[0].get('spare_required') != 2):
        raise ValueError('Common spherical requirement must explicitly request two bare spare holes')
    envelopes = req.get('provisional_bare_mount_envelopes', [])
    if (len(envelopes) != 4 or {e.get('object') for e in envelopes} != set(names) or
            any(e.get('diameter_mm') != 16. for e in envelopes)):
        raise ValueError('All four distinct stations require their own 16 mm round reservation')
    for envelope in envelopes:
        direction = envelope.get('beam_direction_xy', [])
        center = envelope.get('center_xy_mm', [])
        if (len(center) != 2 or not all(math.isfinite(float(x)) for x in center) or
                len(direction) != 2 or not all(math.isfinite(float(x)) for x in direction) or
                abs(math.hypot(*direction)-1.) > _TOL):
            raise ValueError('Each reservation needs a finite centre and unit beam direction')
    return declaration, names, envelopes


def _actual_l05g_fit(doc, info, specs):
    """Build four real holders in a disposable native document.

    Their actual cutters must align with the four bare taps. Their complete
    projected meshes must match the already checked L05G reservations.
    This does not install lenses or change the production document/BOM.
    """
    import FreeCAD as App
    from PyOpticL import optomech
    from RubidiumLatticeV9 import hole_clearance as hc
    import ta_projection_audit as projection

    probe = App.newDocument('TA_conditioning_holder_fit_probe')
    entries = []
    try:
        for index, spec in enumerate(specs):
            center, direction = spec['center_xy_mm'], spec['beam_direction_xy']
            root = [center[i]+8.*direction[i] for i in range(2)]
            yaw = math.degrees(math.atan2(direction[1], direction[0]))
            obj = probe.addObject('Mesh::FeaturePython', 'POLARIS_L05G_fit_'+str(index+1))
            optomech.lens_holder_l05g_no_pin_slots(obj)
            obj.Placement = App.Placement(App.Vector(root[0], root[1], 0.),
                                          App.Rotation(App.Vector(0., 0., 1.), yaw))
            probe.recompute()
            if (not obj.Mesh.CountFacets or obj.DrillPart.isNull() or not obj.DrillPart.isValid()
                    or any('Error' in state or 'Invalid' in state for state in obj.State)):
                raise ValueError('Actual holder/cutter did not build: '+obj.Name)
            bore_faces = [face for face in obj.DrillPart.Faces
                          if type(face.Surface).__name__ == 'Cylinder'
                          and abs(2*face.Surface.Radius-3.4544)<1.e-6]
            if len(bore_faces) != 1:
                raise ValueError('Actual POLARIS holder does not have one 8-32 mounting axis')
            axis = bore_faces[0].Surface.Center
            if not _near([axis.x, axis.y], center):
                raise ValueError('Actual holder mounting axis misses the bare tap')
            points, facets = obj.Mesh.Topology
            actual = hc._convex_hull_xy([(point.x, point.y) for point in points])
            planned = hc._holder_rectangles(center, direction)['l05g_body']
            # Rounded hull construction can retain different collinear points
            # after a quarter-turn. Compare complete boundaries, not vertex sets.
            boundary_delta = max(min(projection._point_segment(p, other[i], other[(i+1)%len(other)])
                                     for i in range(len(other)))
                                 for first,other in ((actual,planned),(planned,actual)) for p in first)
            if boundary_delta>0.0015:  # two 0.001 mm coordinate roundings
                raise ValueError('Actual installed holder contour differs from the reserved STL: '+str(boundary_delta))
            entries.append({'station': spec['object'], 'model': 'POLARIS-L05G',
                            'holder_root_xy_mm': root, 'yaw_deg': yaw,
                            'actual_mounting_axis_xy_mm': [axis.x, axis.y],
                            'mounting_axis_error_mm': math.dist([axis.x, axis.y], center),
                            'vertices': len(points), 'triangles': len(facets),
                            'actual_hull_xy_mm': actual,
                            'rounded_outline_boundary_difference_mm':boundary_delta,
                            'actual_mesh_matches_checked_reservation': True,
                            'local_tap_offset_mm': [-8., 0., -12.7]})
        mesh_path = Path(optomech.stl_path)/'POLARIS-L05G-Step.stl'
        fresh_actual=_fresh_footprints(doc, info, specs,
                                      actual_hulls={e['station']: e['actual_hull_xy_mm'] for e in entries})
        return {'passed': len(entries) == 4 and fresh_actual['passed'], 'holders': entries,
                'actual_installed_footprint_clearance':fresh_actual,
                'mesh_sha256': hashlib.sha256(mesh_path.read_bytes()).hexdigest(),
                'scope': 'Actual single-hole holder mounting and full XY footprint fit; optics remain unselected.'}
    finally:
        App.closeDocument(probe.Name)
        App.setActiveDocument(doc.Name)


def _axis_matches(center, direction, paths):
    matches = []
    for path in paths:
        if path.get('name') not in ('Common cylindrical conditioning provision', 'Common spherical telescope'):
            continue
        for index, (a, b) in enumerate(zip(path['points'], path['points'][1:])):
            delta = [b[i]-a[i] for i in range(2)]
            length = math.hypot(*delta)
            if length <= _TOL:
                continue
            unit = [x/length for x in delta]
            offset = [center[i]-a[i] for i in range(2)]
            along = sum(offset[i]*unit[i] for i in range(2))
            normal = abs(offset[0]*unit[1]-offset[1]*unit[0])
            if -_TOL <= along <= length+_TOL and normal <= _TOL and _near(direction, unit):
                matches.append({'path': path['name'], 'segment': index,
                                'axis_distance_mm': normal, 'beam_direction_xy': unit})
    return matches


def _fresh_footprints(doc, info, specs, actual_hulls=None):
    """Recheck present triangles, not just a saved footprint PASS.

    This uses the native audit's unchanged projection algorithms. No owning
    assembly is skipped: a bare station has no installed owner hardware.
    Below-plate material is clipped as in the ordinary future-holder audit;
    elevated knobs are checked at every height above the physical plate top.
    """
    import numpy as np
    from RubidiumLatticeV9 import hole_clearance as hc

    plate = info['plate']
    # The external footprint implementation uses world XY and a horizontal
    # plate. Refuse a moved/rotated plate rather than mix its board-frame paths
    # and reservations with world-frame triangle coordinates.
    if not _near(list(plate.Placement.Base), [0., 0., 0.]) or abs(plate.Placement.Rotation.Angle) > 1.e-9:
        raise ValueError('Conditioning footprint refinement currently requires an origin, unrotated plate')
    box = plate.Shape.BoundBox
    records, _, skipped = hc._installed_geometry(doc, info)
    if skipped:
        raise ValueError('Inactive geometry cannot be excluded from the four-station audit')
    top = float(box.ZMax)
    output, conflicts, triangles_by_name = [], [], {}
    for spec in specs:
        center = np.asarray(spec['center_xy_mm'], float)
        rectangles = hc._holder_rectangles(center, spec['beam_direction_xy'])
        if actual_hulls is not None:
            rectangles['l05g_body']=actual_hulls[spec['object']]
        item = {'object': spec['object'], 'center_xy_mm': center.tolist(), 'diameter_mm': 16.,
                'holder_footprint_xy_mm': {k: np.asarray(v).tolist() for k, v in rectangles.items()}}
        output.append(item)
        if not (box.XMin+8. <= center[0] <= box.XMax-8. and
                box.YMin+8. <= center[1] <= box.YMax-8.):
            conflicts.append({'object': spec['object'], 'part': 'round_envelope', 'reason': 'outside finished plate'})
        for key, polygon in rectangles.items():
            c = np.asarray(polygon)
            if not (box.XMin <= c[:, 0].min() and c[:, 0].max() <= box.XMax and
                    box.YMin <= c[:, 1].min() and c[:, 1].max() <= box.YMax):
                conflicts.append({'object': spec['object'], 'part': key, 'reason': 'outside finished plate'})
        reach = max([8.]+[float(np.linalg.norm(np.asarray(p)-center, axis=1).max())
                          for p in rectangles.values()])
        for record in records:
            bb = record['bbox']
            if (bb[5] <= top+1.e-5 or bb[3] < center[0]-reach or bb[0] > center[0]+reach or
                    bb[4] < center[1]-reach or bb[1] > center[1]+reach):
                continue
            if record['name'] not in triangles_by_name:
                triangles_by_name[record['name']] = hc.fc._above_plane(
                    hc.fc._placed_triangles(record, .04), top, 1.e-5)
            triangles = triangles_by_name[record['name']]
            tests = {'round_envelope': hc._triangle_circle_hits(triangles, center, 8.)}
            tests.update({key: hc._triangle_polygon_hits(triangles, polygon)
                          for key, polygon in rectangles.items()})
            for key, hits in tests.items():
                if len(hits):
                    conflicts.append({'object': spec['object'], 'part': key,
                                      'hardware': record['name'], 'projected_facets': int(len(hits))})
    for index, a in enumerate(output):
        for b in output[index+1:]:
            if math.dist(a['center_xy_mm'], b['center_xy_mm']) < 16.-_TOL:
                conflicts.append({'object': a['object'], 'other': b['object'], 'reason': 'round reservations overlap'})
            for ka, pa in a['holder_footprint_xy_mm'].items():
                for kb, pb in b['holder_footprint_xy_mm'].items():
                    # The L05G silhouette has many vertices. Triangulate the
                    # whole convex outline, not just its first four points.
                    tri = np.asarray([[pb[0], pb[i], pb[i+1]] for i in range(1, len(pb)-1)])
                    tri = np.concatenate([tri, np.zeros((len(tri), 3, 1))], axis=2)
                    if len(hc._triangle_polygon_hits(tri, pa)):
                        conflicts.append({'object': a['object'], 'other': b['object'],
                                          'part': ka+'_vs_'+kb, 'reason': 'holder reservations overlap'})
    return {'envelopes': output, 'conflicts': conflicts, 'passed': not conflicts,
            'actual_geometry_records': len(records), 'narrow_phase_objects': len(triangles_by_name)}


def _geometry(doc, info, report, result):
    import km05t_audit as taps

    declaration, names, specs = _contract(info)
    result['declaration'] = deepcopy(declaration)
    plate = info['plate']
    if (not plate.Drill or plate.Shape.isNull() or not plate.Shape.isValid() or
            len(plate.Shape.Solids) != 1):
        raise ValueError('One valid, drilled final plate solid is required')
    inventory = [o for o in doc.Objects if _kind(o) == 'BareTappedHole' and taps._on_plate(o, plate)]
    result['actual_bare_station_inventory'] = [o.Name for o in inventory]
    if len(inventory) != 4 or {o.Name for o in inventory} != set(names):
        raise ValueError('Actual plate must have exactly the four declared bare station objects')
    if any(_kind(o) == 'cylindrical_lens' and taps._on_plate(o, plate) for o in doc.Objects):
        raise ValueError('A physical cylindrical lens exists despite the bare-station declaration')
    roots = {_name(o) for o in info.get('roots', {}).values()}
    cuts = {_name(o) for o in info.get('extra_cuts', [])}
    reservations = [r.get('object') for r in info.get('reservations', [])]
    if not set(names) <= roots or not set(names) <= cuts or any(reservations.count(n) != 1 for n in names):
        raise ValueError('Every station must be one registered root, cutter and explicit bare reservation')
    if (report.get('document') != doc.Name or report.get('mode') != 'ta' or
            not _same(report.get('restore_info', {}).get('requirements'), info['requirements']) or
            not _same(report.get('paths'), info.get('paths'))):
        raise ValueError('Native report must carry the current document, requirements and optical paths')
    solid = taps._board_shape(plate.Shape, plate)
    cylinders = taps._cylinders(solid)
    inverse = plate.Placement.inverse()
    by_spec = {s['object']: s for s in specs}
    for obj in inventory:
        if (str(obj.Thread) != '8-32 UNC' or abs(float(obj.TapDrillDiameter.Value)-3.4544) > 1.e-7 or
                not obj.Shape.isNull() or getattr(obj, 'ChildObjects', []) or
                getattr(obj, 'ParentObject', None) is not None or getattr(obj, 'Owner', None) is not None):
            raise ValueError('Station must be an unowned empty 8-32 BareTappedHole: '+obj.Name)
        center3 = inverse.multVec(obj.Placement.Base)
        center = [center3.x, center3.y]
        spec = by_spec[obj.Name]
        if not _near(spec['center_xy_mm'], center):
            raise ValueError('Reservation centre differs from the actual hole: '+obj.Name)
        matches = _axis_matches(center, spec['beam_direction_xy'], info['paths'])
        if not matches:
            raise ValueError('Station/holder direction is not on an actual registered common beam segment: '+obj.Name)
        evidence = taps._drilled_hole(obj, center, plate, solid, cylinders, full_depth=True)
        # Demand complete cylinder circumference as well as depth and empty
        # volume: an open slot, pocket edge or partial arc is not a bare tap.
        span = 0.
        for face in solid.Faces:
            surf = face.Surface
            if (type(surf).__name__ == 'Cylinder' and abs(abs(surf.Axis.z)-1.) < 1.e-7 and
                    abs(surf.Radius-3.4544/2) < 1.e-6 and
                    _near([surf.Center.x, surf.Center.y], center)):
                u0, u1, _, _ = face.ParameterRange
                span += abs(u1-u0)
        if abs(span-2*math.pi) > 1.e-5:
            raise ValueError('Final plate station is not one full cylindrical tap wall: '+obj.Name)
        evidence.update(role='cylindrical' if obj.Name in declaration['cylindrical_holes'] else 'spherical',
                        wall_angular_span_rad=span, registered_axis_matches=matches)
        result['stations'].append(evidence)
    result['footprints'] = _fresh_footprints(doc, info, specs)
    if not result['footprints']['passed']:
        raise ValueError('Current 16 mm circles or additional planned holder footprints conflict')
    if declaration['schema'] == 'conditioning_stations/2':
        result['actual_selected_holder_fit'] = _actual_l05g_fit(doc, info, specs)
        if not result['actual_selected_holder_fit']['passed']:
            raise ValueError('All four selected actual POLARIS-L05G holders must fit')


def _transition(report, declaration, legacy):
    """Return exact replacements without mutating anything until all checks pass."""
    eng, holes = report['engineering'], report['hole_clearance']
    old_cylinder = legacy['cylindrical_hole_check']
    cylinder = declaration['cylindrical_holes']
    if old_cylinder != {'holes': cylinder, 'visible_cylindrical_lenses': [], 'status': 'fail'}:
        raise ValueError('Only the exact legacy two-hole/no-installed-cylinder count failure can be refined')
    replacement = dict(deepcopy(old_cylinder), status='pass', expected_holes=2,
                       verification='conditioning_station_audit: actual four-station geometry and machining')
    if eng.get('cylindrical_hole_check') not in (old_cylinder, replacement):
        raise ValueError('Current cylindrical evidence contains an unrelated change')
    cylinder_count = int(eng['cylindrical_hole_check'] == old_cylinder)
    if (eng['counts'].get('cylindrical_hole_failures') != cylinder_count or
            report['summary_counts'].get('cylindrical_hole_failures') != cylinder_count):
        raise ValueError('Cylindrical failure counts do not match the actual preserved evidence')
    old_errors = legacy['hole_errors']
    if old_errors.count(_OLD_SIX_ERROR) != 1 or legacy['six_common_stations'].get('count') != 4:
        raise ValueError('Exactly one original six-station count error with four discovered holes is required')
    remaining = [deepcopy(e) for e in old_errors if e != _OLD_SIX_ERROR]
    if holes.get('errors') not in (old_errors, remaining):
        raise ValueError('Current hole errors differ from the original or exact count-only refinement')
    if (holes['failure_counts'].get('errors') != len(holes['errors']) or
            report['summary_counts'].get('hole_clearance_issues') != sum(holes['failure_counts'].values())):
        raise ValueError('Hole failure totals do not match their underlying evidence')
    # All non-count failures remain unchanged, even if unrelated to stations.
    counts = dict(holes['failure_counts'], errors=len(remaining))
    return replacement, remaining, counts


def apply(report, doc, info):
    """Verify native geometry; reclassify only the two obsolete count rules."""
    previous = report.get('conditioning_station_audit', {})
    result = {'schema': 'conditioning_station_audit/1', 'document': doc.Name,
              'passed': False, 'expected_counts': deepcopy(_COUNTS), 'stations': [],
              'errors': [], 'resolved_legacy_assumptions': [],
              'scope': 'Four unselected conditioning-holder provisions; not optical prescriptions or manufactured threads.'}
    if previous.get('legacy_evidence'):
        result['legacy_evidence'] = deepcopy(previous['legacy_evidence'])
    report['conditioning_station_audit'] = result
    try:
        from RubidiumLatticeV9 import validation, hole_clearance
        import km05t_audit
        result['source_provenance'] = {str(Path(m.__file__).resolve()):
            hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()
            for m in (validation, hole_clearance, km05t_audit)}
        _geometry(doc, info, report, result)
        declaration = result['declaration']
        engineering, holes = report['engineering'], report['hole_clearance']
        legacy = deepcopy(previous.get('legacy_evidence') or {
            'cylindrical_hole_check': engineering.get('cylindrical_hole_check'),
            'six_common_stations': holes.get('six_common_stations'),
            'hole_errors': holes.get('errors'), 'hole_failure_counts': holes.get('failure_counts'),
            'cylindrical_hole_failures': engineering.get('counts', {}).get('cylindrical_hole_failures'),
            'summary_hole_clearance_issues': report.get('summary_counts', {}).get('hole_clearance_issues')})
        result['legacy_evidence'] = legacy
        common = [g for g in engineering.get('lens_reservation_checks', []) if g.get('name') == 'common']
        if (len(common) != 1 or common[0].get('status') != 'pass' or
                common[0].get('spare_holes') != declaration['spherical_holes'] or
                common[0].get('active_lenses') != [] or common[0].get('spare_required') != 2):
            raise ValueError('The unchanged spherical audit must already pass the two actual spare stations')
        saved = holes.get('future_mount_envelopes', [])
        current = result['footprints']['envelopes']
        if len(saved) != 4 or {s.get('object') for s in saved} != {s['object'] for s in current}:
            raise ValueError('Native report does not include all four future-holder checks')
        for actual in current:
            old = next(s for s in saved if s['object'] == actual['object'])
            if (old.get('diameter_mm') != 16. or not _near(old['center_xy_mm'], actual['center_xy_mm']) or
                    set(old.get('holder_footprint_xy_mm', {})) != set(actual['holder_footprint_xy_mm']) or
                    any(len(points) != len(old['holder_footprint_xy_mm'][k])
                        for k, points in actual['holder_footprint_xy_mm'].items()) or
                    any(not _near(a, b) for k, points in actual['holder_footprint_xy_mm'].items()
                        for a, b in zip(points, old['holder_footprint_xy_mm'][k]))):
                raise ValueError('Saved future-holder geometry differs from the current 16 mm provision')
        replacement, errors, counts = _transition(report, declaration, legacy)
        engineering['cylindrical_hole_check'] = replacement
        engineering['counts']['cylindrical_hole_failures'] = 0
        report['summary_counts']['cylindrical_hole_failures'] = 0
        holes['errors'], holes['failure_counts'] = errors, counts
        holes['passed'] = not any(counts.values()) and holes.get('plate_drilled') is True
        holes['status'] = 'pass' if holes['passed'] else 'conflicts_or_unresolved'
        # Keep the six_common_stations diagnostic verbatim as legacy evidence;
        # the named current field prevents its historical prose being a claim.
        holes['conditioning_stations'] = {'count': 4, 'cylindrical': 2, 'spherical': 2,
                                         'verification': 'conditioning_station_audit'}
        report['summary_counts']['hole_clearance_issues'] = sum(counts.values())
        result['resolved_legacy_assumptions'] = [
            {'source': 'engineering.cylindrical_hole_check', 'original': deepcopy(legacy['cylindrical_hole_check'])},
            {'source': 'hole_clearance.errors', 'original': deepcopy(_OLD_SIX_ERROR)}]
        issues = {key: value for key, value in engineering['counts'].items()
                  if key not in ('bbox_overlap_candidates', 'unrelated_beam_proximity')}
        engineering['result'] = ('Issues or unresolved candidates recorded; review evidence and stated exclusions'
                                 if any(issues.values()) else
                                 'No issue found by these limited nominal CAD checks; physical clearance not certified')
        result['passed'] = True
    except Exception as exc:
        result['errors'].append({'error': str(exc)})
    result['counts'] = {'actual_verified_stations': len(result['stations']),
                        'resolved_count_assumptions': len(result['resolved_legacy_assumptions']),
                        'errors': len(result['errors'])}
    report.setdefault('summary_counts', {})['conditioning_station_audit_issues'] = len(result['errors'])
    return report


apply_to_report = apply
