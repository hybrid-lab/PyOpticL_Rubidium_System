"""Read-only TA board + hardware + cable fit in a 15 x 28 inch table area.

``audit(doc, info)`` reports actual placed geometry in the plate's local frame.
The cable exits the +Y short edge; a full four inches is reserved BEYOND the
nominal plate edge even when the modeled connector starts inside that edge.
The resulting translation proves a free-placement rectangular fit only. Table
thread-grid alignment and mechanical support of overhanging mounts are not
inferred from this envelope calculation.
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


def audit(doc, info):
    """JSON-safe extent evidence; ``passed`` is a dimensional fit, not mounting certification."""
    import FreeCAD as App

    table_width, table_length = 15*INCH, 28*INCH
    cable_length, rf_minimum = 4*INCH, 1.5*INCH
    report = {'schema': 'table_envelope_audit/1', 'document': doc.Name,
              'coordinate_frame': 'Plate-local XY; board short edge is along X, cable exits +Y.',
              'table_size_mm': [table_width, table_length],
              'table_bounds_xy_mm': [0., 0., table_width, table_length],
              'board_limit_mm': [14*INCH, 24*INCH],
              'required_cable_beyond_plate_edge_mm': cable_length,
              'required_rf_elbow_length_mm': rf_minimum,
              'physical_objects': [], 'service_regions': [], 'overhangs': [],
              'body_overhangs': [], 'knob_overhangs': [], 'small_overhangs': [],
              'excluded_objects': [], 'errors': [], 'assumptions': [
                  'Every modeled hardware vertex is included at every height, including adjustment knobs and below-plate adapters.',
                  'The full nominal plate rectangle is reserved; the machined edge gap does not reduce allocated table area.',
                  'The TA cable is a conservative 96.25 mm full-width service envelope; actual plug and bend dimensions remain unverified.',
                  'A separate four-inch cable envelope begins at the nominal +Y plate edge, even if the connector is inset.',
                  'All declared service regions are included in the occupied rectangle; their obstruction checks remain the service-clearance audit.',
                  'Overhanging physical bodies are reported, not silently clipped. Their mount holes and support need separate mechanical checks.',
                  'The suggested translation allows continuous free placement; matching the table thread grid is unverified.'],
              'mounting_grid_alignment': {'status': 'unverified',
                                         'reason': 'No absolute table-hole origin or permissible board translation grid was supplied.'},
              'passed': False}

    def check(condition, message, **evidence):
        if not condition:
            report['errors'].append(dict(error=message, **evidence))
        return bool(condition)

    try:
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
        check(0 < dx <= 14*INCH+_TOL and 0 < dy <= 24*INCH+_TOL and dx <= dy+_TOL,
              'Board exceeds 14 x 24 inches or +Y is not its short-edge exit', actual_size_mm=[dx, dy])
        plate_geometry = _geometry_bbox(plate, inverse)
        if plate_geometry is None or not plate.Shape.isValid():
            raise ValueError('Valid physical plate geometry is required')
        plate_bounds = [plate_geometry['xyz_bounds_mm'][i] for i in (0, 1, 3, 4)]
        report['actual_plate_bounds_xy_mm'] = plate_bounds
        contributions = [{'name': 'Nominal plate allocation', 'kind': 'nominal_plate', 'bounds_xy_mm': nominal},
                         {'name': plate.Name, 'kind': 'physical_plate', 'bounds_xy_mm': plate_bounds}]
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
        report['plate_and_hardware_bounds_xy_mm'] = _union([nominal, plate_bounds]+hardware_boxes)
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
                  'TA cable must exit the +Y short edge', actual_direction=cable['direction_xy'])
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
                  'Actual TA connector side is not facing the +Y short edge')
            extension_origin = [cable['origin_xy_mm'][0], nominal[3]]
            extension = _rectangle(extension_origin, [0., 1.], cable_length, max(96.25, cable['width_mm']))
            report['conservative_cable_beyond_edge'] = {
                'origin_xy_mm': extension_origin, 'direction_xy': [0., 1.],
                'length_mm': cable_length, 'width_mm': max(96.25, cable['width_mm']),
                'corners_xy_mm': extension, 'bounds_xy_mm': _xy_bbox(extension)}
            contributions.append({'name': 'Four-inch TA cable beyond plate edge',
                                  'kind': 'conservative_cable_extension', 'bounds_xy_mm': _xy_bbox(extension)})

        aom_roots = {obj.Name for obj in roots if _kind(obj) == 'AOMO_3100_125'}
        rf = [(entry, owner) for entry, owner in services if entry['kind'] == 'aom_sma']
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
        report['support_review_required'] = bool(report['body_overhangs'])
        report['overhang_policy'] = 'All overhangs count toward table fit. Body support is reported separately and is not certified by passed.'
    except Exception as exc:
        check(False, repr(exc))
    report['failure_counts'] = {'errors': len(report['errors'])}
    report['passed'] = not report['errors']
    report['status'] = 'fits_with_continuous_translation_grid_alignment_unverified' if report['passed'] else 'failed_or_unresolved'
    return report
