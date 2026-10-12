"""Read-only KM05T installation checks for the splitting board.

Run in FreeCAD with the board's current ``doc`` and ``info``. ``inspect_board``
wraps RubidiumLatticeV9.board_tools.inspect_board; ``apply_to_report`` augments
an already computed report. Neither changes document objects or geometry.

The old fiber audit recognizes only KA05T roots. During its synchronous call
only, this module aliases *discovery* of registered KM05T roots, then restores
the original function in a finally block. All meshes, placements, apertures,
clamp regions and cable geometry used by that audit remain the real KM05T data.
An independent audit checks the explicit tail holes and the final plate BREP;
root properties alone are never accepted as proof that a hole was machined.
"""
import math
import threading


_ROOT = 'fiberport_mount_km05T'
_HEAD = 'mirror_mount_km05T'
_ADAPTER = 'surface_adapter_fiberport_lip'
_TAP_DIAMETER = 3.4544
_REAR_OFFSET = 76.0
_C4_ROOT_LABEL = 'Output 1 KM05T (C4)'
_C4_REAR_OFFSET = 44.0
# Retained from the verified pre-shift plate: only the C4 head moved +32 mm.
_C4_TAIL_CENTER_BOARD_MM = (596.415072253436, 325.0, 0.0)
_REAR_SPACING = 18.328
_POSITION_TOL = 0.01
_RADIUS_TOL = 0.002
_VOLUME_TOL = 1.e-5
_DISCOVERY_LOCK = threading.RLock()


def _kind(obj):
    return type(getattr(obj, 'Proxy', None)).__name__


def _number(value):
    return float(getattr(value, 'Value', value))


def _resolve(doc, value):
    return doc.getObject(value) if isinstance(value, str) else value


def _name(value):
    return value if isinstance(value, str) else getattr(value, 'Name', None)


def _xyz(vector):
    return [float(vector.x), float(vector.y), float(vector.z)]


def _children(root):
    seen, pending = set(), [root]
    while pending:
        obj = pending.pop()
        if obj is None or obj.Name in seen:
            continue
        seen.add(obj.Name)
        yield obj
        pending.extend(getattr(obj, 'ChildObjects', []))


def _on_plate(obj, plate):
    seen = set()
    while obj is not None and obj.Name not in seen:
        seen.add(obj.Name)
        if getattr(obj, 'Baseplate', None) == plate:
            return True
        obj = getattr(obj, 'ParentObject', None)
    return False


def _placement(obj, plate):
    return plate.Placement.inverse().multiply(obj.Placement)


def _board_shape(shape, plate):
    result = shape.copy()
    result.Placement = plate.Placement.inverse().multiply(shape.Placement)
    return result


def _mesh_evidence(obj):
    mesh = getattr(obj, 'Mesh', None)
    if mesh is None or mesh.CountFacets <= 0:
        raise ValueError('%s has no physical mesh' % obj.Name)
    b = mesh.BoundBox
    return {'object': obj.Name, 'class': _kind(obj), 'facets': int(mesh.CountFacets),
            'world_bbox_mm': [b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax]}


def _cylinders(shape):
    """Placed vertical cylindrical faces; round only when serializing reports."""
    result = []
    for index, face in enumerate(shape.Faces):
        surface = face.Surface
        if type(surface).__name__ != 'Cylinder':
            continue
        axis = surface.Axis
        if abs(abs(float(axis.z))-1.) > 1.e-7:
            continue
        center, b = surface.Center, face.BoundBox
        result.append({'face': index+1, 'center_xy_mm': [float(center.x), float(center.y)],
                       'radius_mm': float(surface.Radius),
                       'z_range_mm': [float(b.ZMin), float(b.ZMax)],
                       'area_mm2': float(face.Area)})
    return result


def _near(a, b, tolerance=_POSITION_TOL):
    return len(a) == len(b) and all(math.isfinite(float(x)) and math.isfinite(float(y))
                                  and abs(float(x)-float(y)) <= tolerance for x, y in zip(a, b))


def _tap_faces(cylinders, xy=None):
    return [c for c in cylinders
            if abs(c['radius_mm']-_TAP_DIAMETER/2) <= _RADIUS_TOL
            and (xy is None or _near(c['center_xy_mm'], xy))]


def _distinct_centers(faces):
    result = []
    for face in faces:
        xy = face['center_xy_mm']
        if not any(_near(xy, point) for point in result):
            result.append(xy)
    return result


def _covers_z(faces, lo, hi):
    reached = lo
    for start, end in sorted(face['z_range_mm'] for face in faces):
        if end < reached-_POSITION_TOL:
            continue
        if start > reached+_POSITION_TOL:
            break
        reached = max(reached, end)
    return reached >= hi-_POSITION_TOL


def _drilled_hole(source, xy, plate, plate_shape, plate_cylinders, full_depth=False):
    """Match source cylinder, surviving hole walls and actual empty cut volume."""
    import FreeCAD as App
    import Part

    if not bool(getattr(source, 'Drill', False)):
        raise ValueError('%s has drilling disabled' % source.Name)
    drill = getattr(source, 'DrillPart', None)
    if drill is None or drill.isNull():
        raise ValueError('%s has no DrillPart' % source.Name)
    source_faces = _tap_faces(_cylinders(_board_shape(drill, plate)), xy)
    if not source_faces:
        raise ValueError('%s has no 8-32 cylinder at %s' % (source.Name, xy))
    box = plate_shape.BoundBox
    radius = _TAP_DIAMETER/2
    if not (box.XMin+radius <= xy[0] <= box.XMax-radius and
            box.YMin+radius <= xy[1] <= box.YMax-radius):
        raise ValueError('Hole at %s is not entirely inside the stock perimeter' % xy)
    top = -_number(plate.OpticsDz) if hasattr(plate, 'OpticsDz') else box.ZMax
    lo = max(float(box.ZMin), min(f['z_range_mm'][0] for f in source_faces))
    hi = min(float(top), max(f['z_range_mm'][1] for f in source_faces))
    if hi-lo <= 0.1:
        raise ValueError('Source cylinder does not drill meaningful plate depth')
    if full_depth and not _near([lo, hi], [box.ZMin, top]):
        raise ValueError('Tail tap source does not span the full plate thickness')
    walls = _tap_faces(plate_cylinders, xy)
    if not walls or not _covers_z(walls, lo, hi):
        raise ValueError('Final plate lacks matching 8-32 cylindrical wall over %.4f..%.4f at %s'
                         % (lo, hi, xy))
    # The wall requirement prevents accepting a location simply because it is
    # outside stock or inside a larger pocket; the volume test prevents a
    # stale DrillPart/metadata feature from masquerading as a finished hole.
    inset = 0.005
    probe = Part.makeCylinder(radius-inset, hi-lo-2*inset,
                              App.Vector(xy[0], xy[1], lo+inset))
    remaining = float(plate_shape.common(probe).Volume)
    if remaining > _VOLUME_TOL:
        raise ValueError('Final plate still contains %.9f mm3 in the intended tap' % remaining)
    return {'source': source.Name, 'center_board_xy_mm': list(xy),
            'diameter_mm': _TAP_DIAMETER, 'checked_z_range_mm': [lo, hi],
            'source_cylindrical_faces': source_faces, 'plate_cylindrical_faces': walls,
            'remaining_plate_volume_mm3': remaining, 'passed': True}


def installation_audit(doc, info, expected_heads=5):
    """Fail closed on omitted roots, missing meshes, wrong pairs or uncut holes."""
    import FreeCAD as App

    report = {'schema': 'km05t_installation_audit/1', 'document': doc.Name,
              'expected_counts': {'roots': expected_heads, 'physical_heads': expected_heads,
                                  'lip_adapters': expected_heads, 'tail_taps': 2*expected_heads,
                                  'adapter_taps': 2*expected_heads},
              'heads': [], 'tail_holes': [], 'adapter_holes': [], 'errors': [],
              'scope': [
                  'Real KM05T child meshes and unchanged lip-adapter classes are required.',
                  'Each root has two separate 8-32 tail taps at local y=+/-9.164 mm; rear offset is 76 mm except the registered C4 output at 44 mm.',
                  'C4 retains the original board-frame tail holes at (596.415072253436, 334.164) and (596.415072253436, 315.836) mm.',
                  'Each lip adapter must use mount_only with all three optional rear pairs disabled.',
                  'Source cylinders, final plate cylindrical hole walls and empty cut volume are checked independently.',
                  'Mesh collisions and optical aperture clearance remain the full engineering audit responsibility.',
                  'This verifies CAD tap-drill geometry, not manufactured thread form or clamp dimensions.']}

    def check(condition, message, **evidence):
        if not condition:
            report['errors'].append(dict(error=message, **evidence))
        return bool(condition)

    try:
        if not isinstance(expected_heads, int) or expected_heads <= 0:
            raise ValueError('expected_heads must be a positive integer')
        plate = _resolve(doc, info['plate'])
        if plate is None or plate.Shape.isNull() or not plate.Shape.isValid():
            raise ValueError('Valid finished plate shape is required')
        if not bool(getattr(plate, 'Drill', False)):
            raise ValueError('Finished plate drilling is disabled')
        plate_shape = _board_shape(plate.Shape, plate)
        plate_cylinders = _cylinders(plate_shape)
        roots = []
        for label, reference in info.get('roots', {}).items():
            obj = _resolve(doc, reference)
            if obj is None:
                check(False, 'Registered root is missing', label=label, reference=_name(reference))
            elif _kind(obj) == _ROOT:
                roots.append(obj)
        names = [obj.Name for obj in roots]
        actual = [obj for obj in doc.Objects if _kind(obj) == _ROOT and _on_plate(obj, plate)]
        check(len(names) == len(set(names)), 'Duplicate KM05T root registration', roots=names)
        check(len(roots) == expected_heads, 'Wrong registered KM05T root count', actual=len(roots))
        check(set(names) == {obj.Name for obj in actual}, 'Registered and actual KM05T roots differ',
              registered=names, actual=[obj.Name for obj in actual])
        c4_root = _resolve(doc, info.get('roots', {}).get(_C4_ROOT_LABEL))
        check(c4_root is not None and c4_root in roots and
              c4_root.Label == _C4_ROOT_LABEL and
              sum(obj.Label == _C4_ROOT_LABEL for obj in roots) == 1,
              'Missing or ambiguous registered C4 output for the retained tail pair')
        pairs = info.get('fiber_tail_pairs', [])
        check(len(pairs) == expected_heads, 'Wrong tail-pair metadata count', actual=len(pairs))
        pair_owners = [pair.get('owner') for pair in pairs]
        check(len(set(pair_owners)) == len(pair_owners) and set(pair_owners) == set(names),
              'Tail-pair owners must match KM05T roots exactly', owners=pair_owners)
        cuts = {_name(obj) for obj in info.get('extra_cuts', [])}
        tagged = [obj for obj in doc.Objects if getattr(obj, 'CutKind', '') == 'fiber-tail-hole'
                  and _on_plate(obj, plate)]
        check(len(tagged) == 2*expected_heads, 'Wrong explicit tail tap count', actual=len(tagged))
        declared_tail_names, head_names, adapter_names = [], [], []

        for root in roots:
            entry = {'root': root.Name, 'class': _kind(root), 'errors': []}
            before = len(report['errors'])
            report['heads'].append(entry)
            try:
                own = list(_children(root))
                heads = [obj for obj in own if _kind(obj) == _HEAD]
                adapters = [obj for obj in own if _kind(obj) == _ADAPTER]
                check(len(heads) == 1, 'Each root needs one real KM05T head', root=root.Name,
                      objects=[obj.Name for obj in heads])
                check(len(adapters) == 1, 'Each root needs one lip adapter', root=root.Name,
                      objects=[obj.Name for obj in adapters])
                head_names.extend(obj.Name for obj in heads)
                adapter_names.extend(obj.Name for obj in adapters)
                entry['physical_heads'] = [_mesh_evidence(obj) for obj in heads]
                entry['lip_adapters'] = [_mesh_evidence(obj) for obj in adapters]
                for head in heads:
                    local = root.Placement.inverse().multiply(head.Placement)
                    check(_near(_xyz(local.Base), [0., 0., 0.]) and
                          _near(_xyz(local.Rotation.multVec(App.Vector(1, 0, 0))), [1., 0., 0.]) and
                          _near(_xyz(local.Rotation.multVec(App.Vector(0, 0, 1))), [0., 0., 1.]),
                          'KM05T head attachment transform changed', head=head.Name)
                for component in ('fiber_adapter_sm05fca2', 'lens_tube_sm05l05',
                                  'lens_adapter_s05tm09', 'mounted_lens_c220tmda'):
                    found = [obj for obj in own if _kind(obj) == component]
                    check(len(found) == 1, 'Missing or duplicated fiber optical assembly child',
                          root=root.Name, component=component)
                    for obj in found:
                        _mesh_evidence(obj)
                knobs = [obj for obj in own if _kind(obj) == 'thumbscrew_hkts_5_64']
                check(len(knobs) == 2, 'KM05T head must retain both adjustment knobs', root=root.Name)
                for obj in knobs:
                    _mesh_evidence(obj)
                placement = _placement(root, plate)
                entry['origin_board_xyz_mm'] = _xyz(placement.Base)
                entry['optical_axis_board_xyz'] = _xyz(placement.Rotation.multVec(App.Vector(1, 0, 0)))
                rear_offset = _number(root.RearHoleXOffset)
                required_offset = _C4_REAR_OFFSET if root is c4_root else _REAR_OFFSET
                entry['rear_offset_mm'] = rear_offset
                entry['required_rear_offset_mm'] = required_offset
                check(_near([rear_offset, _number(root.RearHoleYSpacing)],
                            [required_offset, _REAR_SPACING]), 'Root rear-pair dimensions changed', root=root.Name)
                if root is c4_root:
                    center = placement.multVec(App.Vector(-rear_offset, 0, 0))
                    entry['retained_tail_pair_reference'] = {
                        'center_board_xyz_mm': _xyz(center),
                        'required_center_board_xyz_mm': list(_C4_TAIL_CENTER_BOARD_MM),
                        'source': 'Original C4 tail pair before the +32 mm head shift.'}
                    check(_near(_xyz(center), _C4_TAIL_CENTER_BOARD_MM) and
                          _near(entry['optical_axis_board_xyz'], [-1., 0., 0.]) and
                          _near(_xyz(placement.Rotation.multVec(App.Vector(0, 0, 1))), [0., 0., 1.]),
                          'C4 head no longer preserves the original tail-pair center and orientation',
                          root=root.Name, actual_center_xyz_mm=_xyz(center))
                metadata = [pair for pair in pairs if pair.get('owner') == root.Name]
                if len(metadata) != 1:
                    raise ValueError('Exactly one pair metadata record is required per root')
                metadata = metadata[0]
                check(metadata.get('class') == _ROOT and metadata.get('adapter_hole_config') == 'mount_only',
                      'Pair metadata has wrong class or adapter configuration', root=root.Name)
                check(_near([metadata.get('rear_offset_mm', float('nan')),
                             metadata.get('hole_spacing_mm', float('nan'))], [required_offset, _REAR_SPACING]),
                      'Tail-pair metadata dimensions changed', root=root.Name)
                hole_names = list(metadata.get('holes', []))
                declared_tail_names.extend(hole_names)
                check(len(hole_names) == 2 and len(set(hole_names)) == 2,
                      'Pair requires two distinct tail features', root=root.Name, holes=hole_names)
                check(set(hole_names) == set(root.RearHoleNames), 'Root and pair hole names disagree', root=root.Name)
                owned_taps = [obj.Name for obj in tagged if getattr(obj, 'Owner', None) == root]
                check(set(owned_taps) == set(hole_names), 'Actual owned tail taps differ from declared pair', root=root.Name)
                declared_xy = metadata.get('hole_centres_board_xy_mm', [])
                check(len(declared_xy) == 2, 'Missing metadata hole centers', root=root.Name)
                for index, name in enumerate(hole_names):
                    hole = doc.getObject(name)
                    if hole is None:
                        raise ValueError('Tail feature is missing: '+name)
                    check(_kind(hole) == 'BareTappedHole' and getattr(hole, 'Owner', None) == root
                          and getattr(hole, 'CutKind', '') == 'fiber-tail-hole',
                          'Incorrect tail feature class/ownership/type', root=root.Name, hole=name)
                    check(name in cuts and _on_plate(hole, plate), 'Tail feature missing from this board cuts', hole=name)
                    side = int(hole.RearSide)
                    check(side in (-1, 1), 'Invalid tail side', hole=name)
                    expected = placement.multVec(App.Vector(-rear_offset, side*_REAR_SPACING/2, 0))
                    xy = _xyz(expected)[:2]
                    check(_near(_xyz(_placement(hole, plate).Base), _xyz(expected)),
                          'Tail feature placement disagrees with physical root', hole=name, expected_xyz_mm=_xyz(expected))
                    check(index < len(declared_xy) and _near(declared_xy[index], xy),
                          'Tail metadata center disagrees with actual root', hole=name, expected_xy_mm=xy)
                    check(_near([_number(hole.RearOffset), _number(hole.TapDrillDiameter)],
                                [required_offset, _TAP_DIAMETER]), 'Incorrect tail tap diameter/offset', hole=name)
                    if root is c4_root:
                        fixed_xy = [_C4_TAIL_CENTER_BOARD_MM[0],
                                    _C4_TAIL_CENTER_BOARD_MM[1]-side*_REAR_SPACING/2]
                        check(_near(xy, fixed_xy) and
                              _near(_xyz(_placement(hole, plate).Base)[:2], fixed_xy),
                              'C4 actual tail feature moved from the original board coordinate',
                              hole=name, required_board_xy_mm=fixed_xy)
                    source_faces = _tap_faces(_cylinders(_board_shape(hole.DrillPart, plate)))
                    check(len(_distinct_centers(source_faces)) == 1, 'Single tail feature drills extra tap centers', hole=name)
                    evidence = _drilled_hole(hole, xy, plate, plate_shape, plate_cylinders, full_depth=True)
                    evidence['rear_offset_mm'] = rear_offset
                    if root is c4_root:
                        evidence['required_retained_center_board_xy_mm'] = fixed_xy
                    report['tail_holes'].append(evidence)
                check({int(doc.getObject(name).RearSide) for name in hole_names} == {-1, 1},
                      'Both signs of the rear pair are required', root=root.Name)
                for adapter in adapters:
                    check(adapter.HoleConfig == 'mount_only' and not any(
                        bool(getattr(adapter, flag)) for flag in ('RearPair43', 'RearPair63', 'RearPair73')),
                        'Adapter has an unwanted optional hole pattern', adapter=adapter.Name)
                    local = root.Placement.inverse().multiply(adapter.Placement)
                    check(_near(_xyz(local.Base), [-9.7, 0., -14.7]) and
                          _near(_xyz(local.Rotation.multVec(App.Vector(1, 0, 0))), [-1., 0., 0.]),
                          'Lip adapter attachment transform changed', adapter=adapter.Name)
                    adapter_placement = _placement(adapter, plate)
                    cylinder_faces = _tap_faces(_cylinders(_board_shape(adapter.DrillPart, plate)))
                    centers = _distinct_centers(cylinder_faces)
                    check(len(centers) == 2, 'mount_only adapter must drill exactly two tap centers',
                          adapter=adapter.Name, actual_centers_mm=centers)
                    for sign in (-1, 1):
                        point = adapter_placement.multVec(App.Vector(0, sign*_number(adapter.MountHoleDistance)/2, 0))
                        report['adapter_holes'].append(_drilled_hole(adapter, _xyz(point)[:2], plate,
                                                                     plate_shape, plate_cylinders))
            except Exception as exc:
                check(False, str(exc), root=root.Name)
            entry['errors'] = report['errors'][before:]
            entry['passed'] = not entry['errors']
        check(len(declared_tail_names) == len(set(declared_tail_names)) and
              set(declared_tail_names) == {obj.Name for obj in tagged},
              'Tail features must be unique and completely accounted for')
        actual_heads = {obj.Name for obj in doc.Objects if _kind(obj) == _HEAD and _on_plate(obj, plate)}
        actual_adapters = {obj.Name for obj in doc.Objects if _kind(obj) == _ADAPTER and _on_plate(obj, plate)}
        check(len(head_names) == len(set(head_names)) == expected_heads and set(head_names) == actual_heads,
              'Physical head inventory does not match exactly', assigned=head_names, actual=sorted(actual_heads))
        check(len(adapter_names) == len(set(adapter_names)) == expected_heads and set(adapter_names) == actual_adapters,
              'Lip adapter inventory does not match exactly', assigned=adapter_names, actual=sorted(actual_adapters))
        report['counts'] = {'roots': len(roots), 'physical_heads': len(actual_heads),
                            'lip_adapters': len(actual_adapters), 'tail_taps': len(tagged),
                            'verified_tail_plate_holes': len(report['tail_holes']),
                            'verified_adapter_plate_holes': len(report['adapter_holes'])}
        check(len(report['tail_holes']) == 2*expected_heads, 'Not all tail holes were verified in the finished plate')
        check(len(report['adapter_holes']) == 2*expected_heads, 'Not all adapter holes were verified in the finished plate')
    except Exception as exc:
        check(False, str(exc))
    report['failure_counts'] = {'errors': len(report['errors'])}
    report['passed'] = not report['errors']
    return report


def audit(doc, info, expected_heads=5):
    """Return both the generic physical tail audit and KM05T installation proof."""
    from RubidiumLatticeV9 import fiber_clearance

    installation = installation_audit(doc, info, expected_heads=expected_heads)
    supported = {_name(value) for value in info.get('roots', {}).values()
                 if _kind(_resolve(doc, value)) == _ROOT}
    with _DISCOVERY_LOCK:
        original = fiber_clearance._class

        def discovery(obj):
            if _kind(obj) == _ROOT and obj.Name in supported:
                return 'fiberport_mount_KA05T_holes'
            return original(obj)

        try:
            fiber_clearance._class = discovery
            clearance = fiber_clearance.audit(doc, info)
        except Exception as exc:
            clearance = {'status': 'audit_error', 'errors': [{'error': repr(exc)}],
                         'failure_counts': {'errors': 1}, 'fibers': [], 'passed': False}
        finally:
            fiber_clearance._class = original
    clearance['km05t_discovery_adapter'] = {
        'method': 'Scoped _class selection alias, restored in finally; physical classes and geometry unchanged.',
        'actual_root_class': _ROOT, 'selection_alias': 'fiberport_mount_KA05T_holes',
        'legacy_module_path': getattr(fiber_clearance, '__file__', None),
        'roots': sorted(supported), 'original_class_function_restored': fiber_clearance._class is original}
    found = [entry.get('object') for entry in clearance.get('fibers', [])]
    if len(found) != expected_heads or len(set(found)) != len(found) or set(found) != supported:
        clearance.setdefault('errors', []).append({'error': 'Generic clearance audit did not check every KM05T exactly once',
                                                   'expected_roots': sorted(supported), 'checked_roots': found})
        clearance.setdefault('failure_counts', {})['errors'] = len(clearance['errors'])
        clearance['passed'] = False
    return {'fiber_clearance': clearance, 'fiber_installation': installation,
            'passed': bool(clearance.get('passed')) and installation['passed']}


def _service_audit(doc, info):
    from RubidiumLatticeV9 import service_clearance

    with _DISCOVERY_LOCK:
        original = service_clearance.OWNER_CLASSES
        try:
            service_clearance.OWNER_CLASSES = dict(original, **{_ROOT: 'fiber_front'})
            result = service_clearance.inspect_service_clearance(doc, info)
        except Exception as exc:
            result = {'status': 'audit_error', 'errors': [{'error': repr(exc)}],
                      'failure_counts': {'errors': 1}, 'passed': False}
        finally:
            service_clearance.OWNER_CLASSES = original
    result['km05t_owner_discovery'] = {
        'method': 'Scoped owner-class registry extension; original map restored in finally.',
        'actual_root_class': _ROOT, 'service_kind': 'fiber_front',
        'legacy_module_path': getattr(service_clearance, '__file__', None),
        'original_owner_map_restored': service_clearance.OWNER_CLASSES is original}
    return result


def _resolve_self_cutters(report, doc, info, installation):
    """Resolve only a verified tail hole colliding with its own exact cutter.

    The legacy hole collector calls the bare feature its owner, while its
    cutter collector follows Owner to the KM05T root. Do not exempt the whole
    root: match feature identity, access-hole identity, coordinate and finished
    hole evidence before moving this one false positive to a retained record.
    """
    from RubidiumLatticeV9 import hole_clearance

    sub = report.get('hole_clearance')
    if not isinstance(sub, dict) or 'failure_counts' not in sub:
        sub = hole_clearance.audit(doc, info)
    verified = {entry['source']: entry for entry in installation.get('tail_holes', [])
                if entry.get('passed')}
    kept, resolved = [], list(sub.get('resolved_self_cutter_evidence', []))
    for conflict in sub.get('cutter_conflicts', []):
        obj = doc.getObject(conflict.get('cutter', ''))
        matching = [hole for hole in sub.get('holes', [])
                    if obj is not None and hole.get('source') == obj.Name
                    and hole.get('label') == conflict.get('hole')
                    and hole.get('kind') == 'bare_8_32'
                    and _near(hole.get('center_xy_mm', []), _xyz(obj.Placement.Base)[:2])]
        owner = getattr(obj, 'Owner', None) if obj is not None else None
        if (obj is not None and obj.Name in verified and _kind(obj) == 'BareTappedHole'
                and obj.Label == conflict.get('hole') and len(matching) == 1
                and getattr(obj, 'CutKind', '') == 'fiber-tail-hole' and _kind(owner) == _ROOT
                and conflict.get('cutter_owner') == owner.Name):
            resolved.append(dict(conflict, resolution='Exact same verified tail hole and its own machining cylinder; '
                                 'legacy bare-hole and cutter owner identifiers differ.',
                                 installation_evidence_source=obj.Name,
                                 matched_access_hole=matching[0]))
        else:
            kept.append(conflict)
    sub['cutter_conflicts'] = kept
    sub['resolved_self_cutter_evidence'] = resolved
    sub['failure_counts']['cutter_conflicts'] = len(kept)
    drilled = bool(getattr(_resolve(doc, info['plate']), 'Drill', False))
    sub['passed'] = drilled and not any(sub['failure_counts'].values())
    sub['status'] = ('pass' if sub['passed'] else 'conflicts_or_unresolved') if drilled else 'preview_only_unmachined'
    sub['km05t_resolution_scope'] = 'Only identical feature self-cutters resolved; foreign cutters and hardware checks unchanged.'
    return sub


def apply_to_report(report, doc, info, expected_heads=5):
    """Replace the unsupported generic fiber result in an existing report."""
    result = audit(doc, info, expected_heads=expected_heads)
    result['service_clearance'] = _service_audit(doc, info)
    try:
        result['hole_clearance'] = _resolve_self_cutters(report, doc, info, result['fiber_installation'])
    except Exception as exc:
        result['hole_clearance'] = {'status': 'audit_error', 'errors': [{'error': repr(exc)}],
                                    'failure_counts': {'errors': 1}, 'passed': False}
    keys = ('fiber_clearance', 'fiber_installation', 'service_clearance', 'hole_clearance')
    for key in keys:
        report[key] = result[key]
        count = sum(result[key]['failure_counts'].values())
        report.setdefault('summary_counts', {})[key+'_issues'] = count
    passed = all(result[key].get('passed', False) for key in keys)
    report.setdefault('restore_info', {})['fiber_tail_pairs'] = info.get('fiber_tail_pairs', [])
    report['km05t_audit'] = {
        'schema': 'km05t_board_audit/1', 'passed': passed,
        'wrapper_path': __file__, 'expected_heads': expected_heads,
        'counts': result['fiber_installation'].get('counts', {}),
        'fiber_clearance_passed': bool(result['fiber_clearance'].get('passed')),
        'installation_passed': result['fiber_installation']['passed'],
        'service_clearance_passed': bool(result['service_clearance'].get('passed')),
        'hole_clearance_passed': bool(result['hole_clearance'].get('passed')),
        'provenance': result['fiber_clearance']['km05t_discovery_adapter'],
        'service_provenance': result['service_clearance']['km05t_owner_discovery'],
        'evidence_keys': list(keys),
        'scope': 'KM05T installation and tail access; all other engineering checks remain separate.'}
    report['km05t_checks_passed'] = passed
    return report


def inspect_board(doc, info, plate_size, full=True, expected_heads=5):
    """Drop-in board_tools.inspect_board wrapper, with real KM05T support."""
    from RubidiumLatticeV9 import board_tools

    report = board_tools.inspect_board(doc, info, plate_size, full=full)
    report.setdefault('restore_info', {})['fiber_tail_pairs'] = info.get('fiber_tail_pairs', [])
    return apply_to_report(report, doc, info, expected_heads) if full else report
