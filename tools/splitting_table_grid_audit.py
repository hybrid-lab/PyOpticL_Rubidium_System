"""Fresh native proof for the agreed Splitting installation on a 28 x 15 table.

Call audit(doc, info, report, source_module=loaded_splitting_module) in FreeCAD,
with repo/tools on sys.path. No document, source or existing report is changed.
This checks the fixed (+53.975, +22.225) mm installation, not a free-placement
fit. Only the previously accepted top hardware/RF extension is allowed, capped
at 5.4512777506515 mm. Other collision/beam/hole audits remain mandatory.
"""
import hashlib
import math
from pathlib import Path


TRANSLATION = (53.975, 22.225)
TABLE_SIZE = (711.2, 381.)
PITCH = 25.4
MAX_TOP = 5.4512777506515
TOL = 1.e-5


def _shift(bounds):
    return [float(v)+TRANSLATION[i % 2] for i, v in enumerate(bounds)]


def _outside(bounds):
    return dict(left=max(0., -bounds[0]), bottom=max(0., -bounds[1]),
                right=max(0., bounds[2]-TABLE_SIZE[0]),
                top=max(0., bounds[3]-TABLE_SIZE[1]))


def _grid_point(center):
    table = [float(center[i])+TRANSLATION[i] for i in range(2)]
    index = [round(v/PITCH) for v in table]
    residual = max(abs(table[i]-index[i]*PITCH) for i in range(2))
    inside = all(PITCH-TOL <= table[i] <= TABLE_SIZE[i]-PITCH+TOL for i in range(2))
    return dict(center_in_board_xy_mm=list(center), center_on_table_xy_mm=table,
                integer_grid_indices_from_table_edge=index, grid_residual_mm=residual,
                inside_table_hole_field=inside, passed=residual <= TOL and inside)


def _accepted(bounds, kind):
    excess = _outside(_shift(bounds))
    top_limit = MAX_TOP if kind in ('physical_hardware', 'aom_sma') else 0.
    return (max(excess[k] for k in ('left', 'right', 'bottom')) <= TOL
            and excess['top'] <= top_limit+TOL)


def audit(doc, info, board_report, *, source_module):
    """Return JSON-safe fresh evidence; never reuse an old installation PASS."""
    import FreeCAD as App
    import km05t_audit
    import table_envelope_audit as geometry
    import table_mount_audit

    errors, contributions, holes = [], [], []
    result = dict(schema='table_grid_installation/2', passed=False, errors=errors,
                  document=doc.Name, translation_xy_mm=list(TRANSLATION),
                  table_size_mm=list(TABLE_SIZE), pitch_mm=PITCH,
                  outermost_hole_offset_from_table_edge_mm=PITCH,
                  table_bounds_in_board_frame_xy_mm=[-TRANSLATION[0], -TRANSLATION[1],
                      TABLE_SIZE[0]-TRANSLATION[0], TABLE_SIZE[1]-TRANSLATION[1]],
                  allowed_overhang_mm=dict(left=0., bottom=0., right=0., top=MAX_TOP),
                  allowed_top_overhang_kinds=['physical_hardware', 'aom_sma'],
                  user_approved_protrusion=True, holes=holes,
                  extent_contributions=contributions,
                  scope='Installation boundary and actual fixing-grid proof. '
                        'Physical contacts, beams, knob projections, machining and access '
                        'must also pass their independent full audits.')

    def check(ok, message):
        if not ok:
            errors.append(message)

    def include(name, kind, bounds, **evidence):
        bounds = [float(v) for v in bounds]
        if len(bounds) != 4 or not all(math.isfinite(v) for v in bounds):
            raise ValueError('Invalid bounds for '+name)
        if bounds[2] < bounds[0] or bounds[3] < bounds[1]:
            raise ValueError('Reversed bounds for '+name)
        entry = dict(name=name, kind=kind, bounds_xy_mm=bounds,
                     bounds_on_table_xy_mm=_shift(bounds),
                     beyond_table_mm=_outside(_shift(bounds)),
                     accepted=_accepted(bounds, kind), **evidence)
        contributions.append(entry)
        check(entry['accepted'], name+': exceeds the explicitly allowed table boundary')

    try:
        plate = info['plate']
        inverse = plate.Placement.inverse()
        check(plate.Placement.Base.Length <= TOL and
              abs(plate.Placement.Rotation.Angle) <= TOL,
              'This source/service contract requires a board built at x=y=angle=0')
        if errors:
            return result
        paths = {p['object'] for p in info['paths']}
        check(set(o.Name for o in doc.Objects) == {o['name'] for o in board_report['objects']},
              'Full report object inventory differs from the current document')
        check(board_report.get('pre_aom_waveplate_audit', {}).get('passed') is True,
              'Current pre-AOM placement plus independent full-audit gate must pass first')
        check(board_report.get('document') == doc.Name, 'Full report document is stale')
        source_hash = hashlib.sha256(Path(source_module.__file__).read_bytes()).hexdigest()
        pre_source = board_report.get('pre_aom_waveplate_audit', {}).get('source_provenance', {}).get('board', {})
        check(pre_source.get('sha256') == source_hash,
              'Pre-AOM/full-audit gate does not belong to this source revision')
        recorded_objects = {o['name']: o for o in board_report['objects']}
        for obj in doc.Objects:
            recorded = recorded_objects.get(obj.Name, {})
            p = obj.Placement.Base
            check(math.dist(recorded.get('position', [math.inf]*3), [p.x, p.y, p.z]) <= TOL,
                  obj.Name+': current position differs from full native report')

        fresh_mount = table_mount_audit.audit(doc, info)
        result['fresh_table_mount_grid'] = fresh_mount
        check(fresh_mount['passed'], 'Fresh actual BREP platform-hole audit failed')
        source_size = [float(source_module.base_dx), float(source_module.base_dy),
                       float(source_module.base_dz)]
        check(all(abs(a-b) <= TOL for a, b in zip(source_size, info['plate_size_mm'])),
              'Source plate dimensions differ from current info')
        check(source_size[0] <= 24*PITCH+TOL and source_size[1] <= 14*PITCH+TOL,
              'Splitting board exceeds the retained 24 x 14 inch size')
        source_holes = [[float(source_module.TABLE_MOUNT_ANCHOR_MM[i])+PITCH*offset[i]
                         for i in range(2)] for offset in source_module.TABLE_MOUNT_OFFSETS_IN]
        check(len(source_holes) == 4, 'Source must declare exactly four table holes')
        for hole in fresh_mount['holes']:
            entry = dict(object=hole['object'], **_grid_point(hole['center_xy_mm']))
            holes.append(entry)
            check(entry['passed'], hole['object']+': off absolute table grid or outside hole field')
            check(sum(math.dist(hole['center_xy_mm'], p) <= TOL for p in source_holes) == 1,
                  hole['object']+': actual drilled position differs from source mount constants')
        result['source_mount_holes_mm'] = source_holes
        result['nominal_outline_xy_mm'] = [0., 0., source_size[0], source_size[1]]
        result['nominal_outline_used_for_physical_containment'] = False
        include(plate.Name, 'machined_plate', fresh_mount['finished_plate_bounds_xy_mm'])

        physical_names = []
        for obj in doc.Objects:
            if obj == plate or obj.Name in paths or geometry._kind(obj) in geometry._MACHINING:
                continue
            actual = geometry._geometry_bbox(obj, inverse)
            if not actual:
                continue
            owner = geometry._plate_link(obj)
            check(owner == plate, obj.Name+': physical object has ambiguous/different plate ownership')
            physical_names.append(obj.Name)
            bounds = actual['xyz_bounds_mm']
            include(obj.Name, 'physical_hardware', [bounds[i] for i in (0, 1, 3, 4)],
                    label=obj.Label, object_class=geometry._kind(obj), **actual)
        result['physical_object_count'] = len(physical_names)

        # Re-run native fiber installation and clearance from actual heads and taps.
        # Do not trust the previous report's polygons or PASS as fresh evidence.
        fresh_fiber = km05t_audit.audit(doc, info)
        result['fresh_fiber_audit'] = fresh_fiber
        check(fresh_fiber['passed'], 'Fresh five-head fiber/tail installation audit failed')
        for fiber in fresh_fiber['fiber_clearance'].get('fibers', []):
            for key in ('clamp_reserved_span_xy_mm', 'corridor_xy_mm'):
                corners = fiber[key]
                include(fiber['object']+' '+key, 'fiber_service', geometry._xy_bbox(corners),
                        owner=fiber['object'], corners_xy_mm=corners)

        fresh_service = km05t_audit._service_audit(doc, info)
        result['fresh_service_audit'] = fresh_service
        check(fresh_service['passed'], 'Fresh hardware/RF/fiber-front access audit failed')
        regions = info['service_regions']
        actual_aoms = {o.Name for o in doc.Objects if geometry._kind(o) == 'AOMO_3100_125'}
        actual_heads = {o.Name for o in doc.Objects
                        if geometry._kind(o) == 'fiberport_mount_km05T'}
        rf = [r for r in regions if r['kind'] == 'aom_sma']
        front = [r for r in regions if r['kind'] == 'fiber_front']
        check(len(rf) == 7 and {r['owner'] for r in rf} == actual_aoms,
              'RF inventory must cover seven actual AOMs exactly once')
        check(len(front) == 5 and {r['owner'] for r in front} == actual_heads,
              'Front-access inventory must cover five actual KM05Ts exactly once')
        check(len(regions) == 12, 'Unexpected/missing service region kind')
        source_geometry = source_module.lane_geometry()
        for arm in info['arms']:
            owner = doc.getObject(arm['aom'])
            bore = owner.Placement.multVec(App.Vector(0., -.030, -.115))
            check(math.dist([bore.x, bore.y], source_geometry[arm['lane']]['aom']) <= TOL,
                  owner.Name+': actual bore differs from current source lane geometry')
        for region in regions:
            owner = doc.getObject(region['owner'])
            direction = region['direction_xy']
            check(abs(math.hypot(*direction)-1.) <= TOL, region['name']+': non-unit service direction')
            if region['kind'] == 'aom_sma':
                bore = owner.Placement.multVec(App.Vector(0., -.030, -.115))
                vector = owner.Placement.Rotation.multVec(App.Vector(0., -1., 0.))
                expected = [bore.x+33.02*vector.x, bore.y+33.02*vector.y]
                check(region['length_mm'] >= 38.1-TOL and region['width_mm'] >= 20.-TOL,
                      region['name']+': RF allowance smaller than 1.5 in x 20 mm')
            elif region['kind'] == 'fiber_front':
                vector = owner.Placement.Rotation.multVec(App.Vector(1., 0., 0.))
                origin = owner.Placement.multVec(App.Vector(18.798, 0., 0.))
                expected = [origin.x, origin.y]
            else:
                continue
            check(math.dist(direction, [vector.x, vector.y]) <= TOL and
                  math.dist(region['origin_xy_mm'], expected) <= TOL,
                  region['name']+': reservation detached from actual connector/head datum')
            corners = geometry._rectangle(region['origin_xy_mm'], direction,
                                          region['length_mm'], region['width_mm'])
            include(region['name'], region['kind'], geometry._xy_bbox(corners),
                    owner=owner.Name, corners_xy_mm=corners)

        occupied = geometry._union([c['bounds_xy_mm'] for c in contributions])
        worst = max(contributions, key=lambda c: c['beyond_table_mm']['top'])
        result.update(occupied_bounds_xy_mm=occupied,
                      occupied_bounds_on_table_xy_mm=_shift(occupied),
                      actual_plate_bounds_on_table_xy_mm=_shift(fresh_mount['finished_plate_bounds_xy_mm']),
                      actual_plate_fully_inside_table=_accepted(fresh_mount['finished_plate_bounds_xy_mm'], 'machined_plate'),
                      hardware_and_services_fully_inside_table=max(_outside(_shift(occupied)).values()) <= TOL,
                      maximum_top_overhang_mm=worst['beyond_table_mm']['top'],
                      maximum_top_overhang_owner=worst['name'],
                      top_overhang_contributions=[c for c in contributions if c['beyond_table_mm']['top'] > TOL],
                      source_provenance={Path(p).name: hashlib.sha256(Path(p).read_bytes()).hexdigest()
                                         for p in (__file__, source_module.__file__, geometry.__file__,
                                                   table_mount_audit.__file__, km05t_audit.__file__)})
    except Exception as exc:
        errors.append('Fresh grid audit error: '+repr(exc))
    result['passed'] = not errors
    return result
