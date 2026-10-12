"""Read-only TA board + hardware + cable fit in a 15 x 28 inch table area.

``audit(doc, info, board_report=None)`` reports actual placed geometry in the
plate's local frame. Legacy TA boards use a 15 x 28 inch free-placement fit.
Explicit ``single_output_design`` boards use a 28 x 15 inch table, a +Y long
edge cable exit, and the confirmed one-inch table grid. Their actual machined
plate, hardware and services must all fit at one grid-aligned translation;
the empty nominal edge inset is not physical stock. Both modes reserve a full
four inches BEYOND the nominal +Y edge. New single-output boards also require
the completed engineering report to include the real fiber service envelopes.
"""
import math


INCH = 25.4
_MACHINING = {'BareTappedHole', 'PersistentDrillVolume', 'CellPocketMachining',
              'SlidingCellSeat', 'IntegralAOMSeat'}
_TA_CLASSES = {'TA_butterfly', 'TA_butterfly_on_adapter'}
_TOL = 1.e-5


def _kind(obj):
    return type(getattr(obj, 'Proxy', None)).__name__


def _number(value):
    result = float(getattr(value, 'Value', value))
    if not math.isfinite(result):
        raise ValueError('Non-finite dimension')
    return result


def _resolve(doc, value):
    return doc.getObject(value) if isinstance(value, str) else value


def _pair(value):
    if len(value) != 2:
        raise ValueError('Expected an XY pair')
    return [_number(x) for x in value]


def _knob(obj):
    text = (_kind(obj)+' '+obj.Name+' '+obj.Label).lower()
    return any(word in text for word in ('thumbscrew', 'thumb screw', 'knob', 'adjuster'))


def _plate_link(obj):
    seen = set()
    while obj is not None and obj.Name not in seen:
        seen.add(obj.Name)
        plate = getattr(obj, 'Baseplate', None)
        if plate is not None:
            return plate
        obj = getattr(obj, 'ParentObject', None)
    return None


def _geometry_bbox(obj, inverse_plate):
    """Read mesh vertices at every Z, or the exact transformed BREP bounds.

    Mesh.Topology points already carry the object's placement. Never apply
    obj.Placement a second time. A BREP copy changes only the temporary shape's
    frame; neither the document object nor its stored geometry is modified.
    """
    mesh = getattr(obj, 'Mesh', None)
    if mesh is not None and mesh.CountPoints:
        if not mesh.CountFacets:
            raise ValueError('Mesh has points but no physical surface facets')
        points, _ = mesh.Topology
        coords = [inverse_plate.multVec(point) for point in points]
        bounds = [min(p.x for p in coords), min(p.y for p in coords), min(p.z for p in coords),
                  max(p.x for p in coords), max(p.y for p in coords), max(p.z for p in coords)]
        source = 'actual_placed_mesh_vertices'
    else:
        shape = getattr(obj, 'Shape', None)
        if shape is None or shape.isNull() or not shape.Faces:
            return None
        copy = shape.copy()
        copy.Placement = inverse_plate.multiply(shape.Placement)
        b = copy.BoundBox
        bounds = [b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax]
        source = 'exact_placed_brep_bounds'
    return {'xyz_bounds_mm': [_number(x) for x in bounds], 'geometry_source': source}


def _xy_bbox(points):
    return [min(p[0] for p in points), min(p[1] for p in points),
            max(p[0] for p in points), max(p[1] for p in points)]


def _union(bounds):
    return [min(b[0] for b in bounds), min(b[1] for b in bounds),
            max(b[2] for b in bounds), max(b[3] for b in bounds)]


def _rectangle(origin, direction, length, width):
    dx, dy = direction
    nx, ny = -dy*width/2, dx*width/2
    x, y = origin
    return [[x+nx, y+ny], [x+dx*length+nx, y+dy*length+ny],
            [x+dx*length-nx, y+dy*length-ny], [x-nx, y-ny]]


def _overhang(bounds, perimeter):
    return {'left': max(0., perimeter[0]-bounds[0]),
            'bottom': max(0., perimeter[1]-bounds[1]),
            'right': max(0., bounds[2]-perimeter[2]),
            'top': max(0., bounds[3]-perimeter[3])}


def _grid_translations(centers, occupied, table_size, pitch=INCH, edge_offset=INCH):
    """Enumerate every translation satisfying containment and the real hole field.

    The first table row/column is one inch from each edge. Plate holes are
    already verified against the drilled BREP before this solver is called.
    No nominal outline enters the containment intervals.
    """
    if len(centers) != 4:
        raise ValueError('Exactly four verified fixing-hole centres are required')
    axis_candidates = []
    for axis in range(2):
        low, high = -occupied[axis], table_size[axis]-occupied[axis+2]
        phase = edge_offset-centers[0][axis]
        first = math.ceil((low-phase-_TOL)/pitch)
        last = math.floor((high-phase+_TOL)/pitch)
        values = []
        for index in range(first, last+1):
            translation = phase+index*pitch
            valid = True
            for center in centers:
                coordinate = center[axis]+translation
                grid = (coordinate-edge_offset)/pitch
                if (abs(grid-round(grid))*pitch > _TOL or
                        coordinate < edge_offset-_TOL or
                        coordinate > table_size[axis]-edge_offset+_TOL):
                    valid = False
                    break
            if valid:
                values.append(translation)
        axis_candidates.append(values)
    candidates = [[x, y] for x in axis_candidates[0] for y in axis_candidates[1]]
    ideal = [(table_size[i]-occupied[i+2]-occupied[i])/2 for i in range(2)]
    candidates.sort(key=lambda point: (sum((point[i]-ideal[i])**2 for i in range(2)), point))
    return candidates


def _translated(bounds, translation):
    return [bounds[i]+translation[i % 2] for i in range(4)]


def audit(doc, info, board_report=None):
    """JSON-safe geometry and fit evidence; body support/strength remains separate."""
    import FreeCAD as App

    single = bool(info.get('single_output_design'))
    table_width, table_length = (28*INCH, 15*INCH) if single else (15*INCH, 28*INCH)
    board_limit = [14*INCH, 11*INCH] if single else [14*INCH, 24*INCH]
    exit_edge = '+Y long edge' if single else '+Y short edge'
    cable_length, rf_minimum = 4*INCH, 1.5*INCH
    report = {'schema': 'table_envelope_audit/1', 'document': doc.Name,
              'coordinate_frame': 'Plate-local XY; cable exits the '+exit_edge+'.',
              'table_size_mm': [table_width, table_length],
              'table_bounds_xy_mm': [0., 0., table_width, table_length],
              'board_limit_mm': board_limit,
              'required_cable_beyond_plate_edge_mm': cable_length,
              'required_rf_elbow_length_mm': rf_minimum,
              'physical_objects': [], 'service_regions': [], 'overhangs': [],
              'body_overhangs': [], 'knob_overhangs': [], 'small_overhangs': [],
              'excluded_objects': [], 'errors': [], 'assumptions': [
                  'Every modeled hardware vertex is included at every height, including adjustment knobs and below-plate adapters.',
                  ('Only the finished machined plate is physical stock; its empty nominal edge inset is not a containment constraint.' if single else
                   'The full nominal plate rectangle is reserved; the machined edge gap does not reduce allocated table area.'),
                  'The TA cable is a conservative 96.25 mm full-width service envelope; actual plug and bend dimensions remain unverified.',
                  'A separate four-inch cable envelope begins at the nominal +Y plate edge, even if the connector is inset.',
                  'All declared service regions are included in the occupied rectangle; their obstruction checks remain the service-clearance audit.',
                  'Overhanging physical bodies are reported, not silently clipped. Their mount holes and support need separate mechanical checks.',
                  ('The selected translation must align all four real fixing holes with a 25.4 mm grid whose outermost row is 25.4 mm from each table edge.' if single else
                   'The suggested translation allows continuous free placement; matching the table thread grid is unverified.')],
              'mounting_grid_alignment': {'status': 'unverified',
                                         'reason': 'No absolute table-hole origin or permissible board translation grid was supplied.'},
              'passed': False}

    def check(condition, message, **evidence):
        if not condition:
            report['errors'].append(dict(error=message, **evidence))
        return bool(condition)

    try:
        if single:
            design = info['single_output_design']
            if not isinstance(design, dict) or design.get('kind') != 'ta_single_output':
                raise ValueError('Explicit ta_single_output design metadata is required')
            check(design.get('expected_aom_count') == 0,
                  'Single-output metadata must explicitly declare zero AOMs')
            check(all(abs(a-b) <= _TOL for a, b in zip(_pair(design.get('table_size_mm', [])), [table_width, table_length]))
                  and all(abs(a-b) <= _TOL for a, b in zip(_pair(design.get('board_limit_mm', [])), board_limit))
                  and abs(_number(design.get('table_edge_hole_offset_mm', 0))-INCH) <= _TOL
                  and design.get('cable_exit') == '+Y_long_edge',
                  'Single-output table dimensions, edge phase or cable-exit metadata disagree with the confirmed specification')
            report['design_mode'] = 'ta_single_output_absolute_grid'
        plate = _resolve(doc, info['plate'])
        if plate is None or not hasattr(plate, 'Placement'):
            raise ValueError('Plate reference is missing')
        inverse = plate.Placement.inverse()
        dx, dy = _number(plate.dx), _number(plate.dy)
        ox = _number(getattr(plate, 'xOffset', 0.))
        oy = _number(getattr(plate, 'yOffset', 0.))
        nominal = [ox, oy, ox+dx, oy+dy]
        report['nominal_plate_bounds_xy_mm'] = nominal
        report['nominal_plate_size_mm'] = [dx, dy, _number(plate.dz)]
        check(0 < dx <= board_limit[0]+_TOL and 0 < dy <= board_limit[1]+_TOL
              and (dy <= dx+_TOL if single else dx <= dy+_TOL),
              'Board exceeds its size/orientation limit for the '+exit_edge,
              actual_size_mm=[dx, dy], limit_mm=board_limit)
        plate_geometry = _geometry_bbox(plate, inverse)
        if plate_geometry is None or not plate.Shape.isValid():
            raise ValueError('Valid physical plate geometry is required')
        plate_bounds = [plate_geometry['xyz_bounds_mm'][i] for i in (0, 1, 3, 4)]
        report['actual_plate_bounds_xy_mm'] = plate_bounds
        contributions = [{'name': plate.Name, 'kind': 'physical_plate', 'bounds_xy_mm': plate_bounds}]
        if not single:
            contributions.insert(0, {'name': 'Nominal plate allocation', 'kind': 'nominal_plate', 'bounds_xy_mm': nominal})
        roots = []
        for label, value in info.get('roots', {}).items():
            obj = _resolve(doc, value)
            if obj is None:
                check(False, 'Declared root is missing', label=label)
            else:
                roots.append(obj)
        root_names = {obj.Name for obj in roots}
        paths = {p.get('object') for p in info.get('paths', [])}
        for obj in doc.Objects:
            if obj == plate or obj.Name in paths:
                continue
            attached = _plate_link(obj)
            if attached is not None and attached != plate:
                report['excluded_objects'].append({'object': obj.Name, 'reason': 'Explicitly belongs to another plate.'})
                continue
            kind, knob = _kind(obj), _knob(obj)
            if kind in _MACHINING and not knob:
                report['excluded_objects'].append({'object': obj.Name, 'reason': 'Machining-only proxy.'})
                continue
            try:
                geometry = _geometry_bbox(obj, inverse)
                if geometry is None:
                    if knob:
                        check(False, 'Adjustment knob has no readable geometry', object=obj.Name)
                    else:
                        report['excluded_objects'].append({'object': obj.Name, 'reason': 'No physical surface; children checked separately.'})
                    continue
                bounds = [geometry['xyz_bounds_mm'][i] for i in (0, 1, 3, 4)]
                entry = dict(geometry, object=obj.Name, label=obj.Label, **{'class': kind},
                             bounds_xy_mm=bounds, adjustment_knob=knob,
                             ownership='board_link' if attached == plate else 'conservatively_included_unlinked_geometry')
                report['physical_objects'].append(entry)
                contributions.append({'name': obj.Name, 'kind': 'hardware', 'bounds_xy_mm': bounds})
                extent = _overhang(bounds, plate_bounds)
                if max(extent.values()) > _TOL:
                    overhang = {'object': obj.Name, 'label': obj.Label, 'class': kind,
                                'bounds_xy_mm': bounds, 'beyond_actual_plate_mm': extent,
                                'beyond_nominal_plate_mm': _overhang(bounds, nominal)}
                    report['overhangs'].append(overhang)
                    if max(extent.values()) <= 0.2:
                        report['small_overhangs'].append(overhang)
                    elif knob:
                        report['knob_overhangs'].append(overhang)
                    else:
                        overhang['support_check'] = 'Separate attachment-hole and supported-footprint review required.'
                        if kind in {'prism_mount_km100pm', 'prism_mount_km100pm_bridged'}:
                            overhang['embedded_controls_note'] = 'This mesh includes adjustment controls; whole-mesh bounds cannot assign the overhang to the body alone.'
                        report['body_overhangs'].append(overhang)
            except Exception as exc:
                check(False, repr(exc), object=obj.Name)
        check(bool(report['physical_objects']), 'No physical hardware was checked')
        hardware_boxes = [entry['bounds_xy_mm'] for entry in report['physical_objects']]
        report['plate_and_hardware_bounds_xy_mm'] = _union(([plate_bounds] if single else [nominal, plate_bounds])+hardware_boxes)
        report['hardware_only_bounds_xy_mm'] = _union(hardware_boxes) if hardware_boxes else None

        services = []
        for source in info.get('service_regions', []):
            try:
                origin, direction = _pair(source['origin_xy_mm']), _pair(source['direction_xy'])
                length, width = _number(source['length_mm']), _number(source['width_mm'])
                norm = math.hypot(*direction)
                if norm <= _TOL or length <= 0 or width <= 0:
                    raise ValueError('Service direction, length and width must be positive/nonzero')
                check(abs(norm-1) < _TOL, 'Service direction is not unit length', region=source.get('name'))
                direction = [component/norm for component in direction]
                owner = _resolve(doc, source.get('owner'))
                if owner is None:
                    owner = _resolve(doc, info.get('roots', {}).get(source.get('owner')))
                if owner is None or owner.Name not in root_names:
                    raise ValueError('Service region needs a declared physical root owner')
                corners = _rectangle(origin, direction, length, width)
                entry = {'name': source.get('name'), 'kind': source.get('kind'), 'owner': owner.Name,
                         'origin_xy_mm': origin, 'direction_xy': direction, 'length_mm': length,
                         'width_mm': width, 'corners_xy_mm': corners, 'bounds_xy_mm': _xy_bbox(corners),
                         'dimensions_verified': bool(source.get('dimensions_verified', False))}
                services.append((entry, owner))
                report['service_regions'].append(entry)
                contributions.append({'name': entry['name'], 'kind': 'service_region', 'bounds_xy_mm': entry['bounds_xy_mm']})
            except Exception as exc:
                check(False, repr(exc), region=source.get('name'))

        ta_roots = {obj.Name for obj in roots if _kind(obj) in _TA_CLASSES}
        cables = [(entry, owner) for entry, owner in services if entry['kind'] == 'ta_cable']
        check(len(ta_roots) == 1 and len(cables) == 1, 'Exactly one TA root and one TA cable region are required',
              ta_roots=sorted(ta_roots), cable_regions=len(cables))
        for cable, owner in cables:
            check(owner.Name in ta_roots, 'TA cable owner is not the real TA root', owner=owner.Name)
            check(abs(cable['direction_xy'][0]) <= _TOL and abs(cable['direction_xy'][1]-1) <= _TOL,
                  'TA cable must exit the '+exit_edge, actual_direction=cable['direction_xy'])
            check(cable['length_mm'] >= cable_length-_TOL and cable['width_mm'] >= 96.25-_TOL,
                  'TA cable reservation is smaller than 101.6 x 96.25 mm', region=cable['name'])
            placement = inverse.multiply(owner.Placement)
            expected_origin = placement.multVec(App.Vector(-29.925, 50.155613, 0))
            expected_direction = placement.Rotation.multVec(App.Vector(0, 1, 0))
            check(math.hypot(expected_origin.x-cable['origin_xy_mm'][0],
                             expected_origin.y-cable['origin_xy_mm'][1]) <= 0.05,
                  'TA cable origin does not follow the actual TA placement',
                  expected_origin_xy_mm=[expected_origin.x, expected_origin.y])
            check(abs(expected_direction.x) <= _TOL and abs(expected_direction.y-1) <= _TOL
                  and abs(expected_direction.z) <= _TOL,
                  'Actual TA connector side is not facing the '+exit_edge)
            extension_origin = [cable['origin_xy_mm'][0], nominal[3]]
            extension = _rectangle(extension_origin, [0., 1.], cable_length, max(96.25, cable['width_mm']))
            report['conservative_cable_beyond_edge'] = {
                'origin_xy_mm': extension_origin, 'direction_xy': [0., 1.],
                'length_mm': cable_length, 'width_mm': max(96.25, cable['width_mm']),
                'corners_xy_mm': extension, 'bounds_xy_mm': _xy_bbox(extension)}
            contributions.append({'name': 'Four-inch TA cable beyond plate edge',
                                  'kind': 'conservative_cable_extension', 'bounds_xy_mm': _xy_bbox(extension)})

        aom_roots = {obj.Name for obj in roots if _kind(obj) == 'AOMO_3100_125'}
        actual_aoms = {obj.Name for obj in doc.Objects if _kind(obj) == 'AOMO_3100_125'
                       and _plate_link(obj) in (None, plate)}
        rf = [(entry, owner) for entry, owner in services if entry['kind'] == 'aom_sma']
        if single:
            check(not actual_aoms and not aom_roots and not rf,
                  'Single-output TA must contain no physical AOM, AOM root or RF region',
                  actual_aom_objects=sorted(actual_aoms), declared_aom_roots=sorted(aom_roots),
                  rf_regions=[entry['name'] for entry, _ in rf])
            report['rf_requirement'] = {'status': 'not_applicable' if not actual_aoms and not aom_roots and not rf else 'failed',
                                        'reason': 'Actual placed hardware inventory, root inventory and RF-region inventory all contain zero AOMs.',
                                        'actual_aom_objects': sorted(actual_aoms), 'declared_aom_roots': sorted(aom_roots)}
        else:
            check(bool(aom_roots), 'No physical AOM root found for RF elbow check')
        check({owner.Name for _, owner in rf} == aom_roots and len(rf) == len(aom_roots),
              'Each AOM needs exactly one RF elbow service region', aom_roots=sorted(aom_roots))
        report['rf_elbow_checks'] = []
        for region, owner in rf:
            passed = region['length_mm'] >= rf_minimum-_TOL
            check(passed, 'RF elbow reservation is shorter than 38.1 mm', region=region['name'])
            report['rf_elbow_checks'].append({'owner': owner.Name, 'name': region['name'],
                                               'length_mm': region['length_mm'], 'required_mm': rf_minimum,
                                               'passed': passed})

        if single:
            if not board_report or board_report.get('document') != doc.Name:
                raise ValueError('Single-output fit requires the current full board report for fiber services')
            fiber_report = board_report.get('fiber_clearance', {})
            fibers = fiber_report.get('fibers', [])
            actual_fibers = {obj.Name: obj for obj in doc.Objects
                             if _kind(obj).startswith('fiberport_mount')
                             and (_plate_link(obj) == plate or obj.Name in root_names)}
            if (fiber_report.get('passed') is not True or len(actual_fibers) != 1 or
                    len(fibers) != 1 or {f.get('object') for f in fibers} != set(actual_fibers)):
                raise ValueError('Exactly one real fiber head and its passing clearance result are required')
            report['fiber_service_regions'] = []
            for fiber in fibers:
                head = actual_fibers[fiber['object']]
                origin = _pair(fiber['origin_xy_mm'])
                if math.hypot(origin[0]-head.Placement.Base.x, origin[1]-head.Placement.Base.y) > _TOL:
                    raise ValueError('Fiber service report is stale: '+head.Name)
                for key in ('clamp_reserved_span_xy_mm', 'corridor_xy_mm'):
                    points = [_pair(point) for point in fiber[key]]
                    if len(points) < 3:
                        raise ValueError('Fiber service polygon has fewer than three corners')
                    local = [inverse.multVec(App.Vector(x, y, plate.Placement.Base.z)) for x, y in points]
                    corners = [[point.x, point.y] for point in local]
                    bounds = _xy_bbox(corners)
                    entry = {'name': head.Name+' '+key, 'kind': 'fiber_service',
                             'bounds_xy_mm': bounds, 'corners_xy_mm': corners}
                    contributions.append(entry)
                    report['fiber_service_regions'].append(entry)

        occupied = _union([item['bounds_xy_mm'] for item in contributions])
        span = [occupied[2]-occupied[0], occupied[3]-occupied[1]]
        translation = [-occupied[0], -occupied[1]]
        margins = [table_width-span[0], table_length-span[1]]
        fit = all(margin >= -_TOL for margin in margins)
        check(fit, 'Plate, actual hardware and reserved services exceed the 15 x 28 inch area',
              occupied_size_mm=span, available_size_mm=[table_width, table_length])
        report.update({'occupied_bounds_xy_mm': occupied, 'occupied_size_mm': span,
                       'occupied_size_in': [value/INCH for value in span],
                       'translation_xy_mm': translation,
                       'translated_occupied_bounds_xy_mm': [0., 0., span[0], span[1]],
                       'table_bounds_in_board_frame_xy_mm': [occupied[0], occupied[1],
                                                             occupied[0]+table_width, occupied[1]+table_length],
                       'centered_translation_xy_mm': [translation[0]+margins[0]/2,
                                                       translation[1]+margins[1]/2],
                       'remaining_width_length_mm': margins, 'free_placement_fit': fit,
                       'extent_contributions': contributions,
                       'limiting_objects': {side: [item['name'] for item in contributions
                                                   if abs(item['bounds_xy_mm'][index]-occupied[index]) < _TOL]
                                            for side, index in (('left', 0), ('bottom', 1), ('right', 2), ('top', 3))}})
        if single:
            import table_mount_audit

            mount_report = table_mount_audit.audit(doc, info)
            report['actual_mount_hole_audit'] = mount_report
            check(mount_report.get('passed') is True,
                  'Actual platform holes failed the machined-solid check',
                  details=mount_report.get('errors', []))
            centers = [hole['center_xy_mm'] for hole in mount_report.get('holes', [])]
            table_size = [table_width, table_length]
            candidates = (_grid_translations(centers, occupied, table_size)
                          if mount_report.get('passed') is True else [])
            grid = {'status': 'failed', 'passed': False, 'pitch_mm': INCH,
                    'outermost_hole_offset_from_table_edge_mm': INCH,
                    'table_size_mm': table_size,
                    'feasible_translation_intervals_xy_mm': [[-occupied[i], table_size[i]-occupied[i+2]]
                                                             for i in range(2)],
                    'candidate_count': len(candidates), 'candidate_translations_xy_mm': candidates,
                    'nominal_outline_used_for_containment': False,
                    'allowed_hardware_or_service_overhang_mm': 0.,
                    'reason': 'No translation contains all physical geometry/services and aligns all four drilled holes.'}
            check(bool(candidates), 'No fully contained installation on the confirmed one-inch table grid',
                  occupied_bounds_xy_mm=occupied, machined_plate_bounds_xy_mm=plate_bounds,
                  actual_fixing_centers_xy_mm=centers)
            if candidates:
                translation = candidates[0]
                translated_occupied = _translated(occupied, translation)
                translated_plate = _translated(plate_bounds, translation)
                table_bounds = [0., 0., table_width, table_length]
                outside = _overhang(translated_occupied, table_bounds)
                fully_contained = max(outside.values()) <= _TOL
                holes = []
                for source in mount_report['holes']:
                    q = [source['center_xy_mm'][i]+translation[i] for i in range(2)]
                    indices = [round(value/INCH) for value in q]
                    residual = max(abs(value-index*INCH) for value, index in zip(q, indices))
                    holes.append({'object': source['object'], 'center_in_board_xy_mm': source['center_xy_mm'],
                                  'center_on_table_xy_mm': q, 'integer_grid_indices_from_table_edge': indices,
                                  'grid_residual_mm': residual})
                grid.update(status='verified', passed=fully_contained,
                            reason='All four actual drilled holes align with the confirmed table grid, with complete physical/service containment.',
                            translation_xy_mm=translation, holes=holes,
                            actual_plate_bounds_on_table_xy_mm=translated_plate,
                            actual_hardware_bounds_on_table_xy_mm=_translated(report['hardware_only_bounds_xy_mm'], translation),
                            occupied_bounds_on_table_xy_mm=translated_occupied,
                            actual_plate_fully_inside_table=max(_overhang(translated_plate, table_bounds).values()) <= _TOL,
                            hardware_and_services_fully_inside_table=fully_contained,
                            beyond_table_mm=outside,
                            minimum_table_edge_margin_mm=min(translated_occupied[0], translated_occupied[1],
                                                             table_width-translated_occupied[2], table_length-translated_occupied[3]))
                report.update(translation_xy_mm=translation,
                              translated_occupied_bounds_xy_mm=translated_occupied,
                              table_bounds_in_board_frame_xy_mm=[-translation[0], -translation[1],
                                                                 table_width-translation[0], table_length-translation[1]])
                check(fully_contained, 'Selected grid installation has a physical/service overhang', beyond_table_mm=outside)
            report['mounting_grid_alignment'] = grid
            report['grid_installation'] = grid
        report['support_review_required'] = bool(report['body_overhangs'])
        report['overhang_policy'] = 'All overhangs count toward table fit. Body support is reported separately and is not certified by passed.'
    except Exception as exc:
        check(False, repr(exc))
    report['failure_counts'] = {'errors': len(report['errors'])}
    report['passed'] = not report['errors']
    report['status'] = (('fits_on_confirmed_table_grid_with_complete_containment' if single else
                         'fits_with_continuous_translation_grid_alignment_unverified')
                        if report['passed'] else 'failed_or_unresolved')
    return report
