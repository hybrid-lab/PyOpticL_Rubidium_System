"""Read-only native support check for the six TA M05 mirror mounts.

Call ``audit(doc, info)`` after drilling/recompute, or ``apply(report, doc, info)``.
No objects, placements, visibility, or machining are changed. This complements
collision/beam checks; it does not modify their exemptions or certify strength.

The actual horizontal mesh facets within 0.02 mm of the plate top are projected
onto a thin probe centred 0.05 mm below it. Non-overlapping bottom triangles are
assembled as a compound, so support uses one hole subtraction and one plate
intersection per mount, not an expensive boolean for every mesh facet. Only the
mount's own actual vertical cylindrical DrillPart bore is removed from its
required footprint. Other holes/pockets remain missing support.

In addition, an M05 body may not project over the foreign TA-adapter pocket,
even when it is vertically separated. Actual DrillPart at the same probe height
defines that pocket. A body convex hull is only a broad phase: candidate mesh
triangles are cheaply screened in 2D, then an exact native intersection proves
a hit. An unresolved broad-phase overlap fails closed and is NOT labelled a
physical collision. Same-root TA/adapter support and intended light through
optical apertures are outside this six-mount audit. It is not a general check of
other support interfaces, screw engagement, overhang strength, or alignment.
"""
import hashlib
import math
from pathlib import Path


_BOTTOM_TOL = 0.02
_PROBE_DEPTH = 0.05
_PROBE_THICKNESS = 0.02
_AREA_TOL = 1.e-4
_TESSELLATION = 0.02
_MAX_REFINEMENT_BOOLEANS = 64
_MIRRORS = {'circular_mirror', 'circular_mirror_union_optic'}


def _kind(obj):
    return type(getattr(obj, 'Proxy', None)).__name__


def _board_shape(obj, inverse, attribute='Shape'):
    shape = getattr(obj, attribute, None)
    if shape is None or shape.isNull() or not shape.isValid():
        raise ValueError(obj.Name+': missing/invalid '+attribute)
    shape = shape.copy()
    shape.Placement = inverse.multiply(shape.Placement)
    return shape


def _area(shape):
    if not shape.isNull() and not shape.isValid():
        raise ValueError('Invalid native support/intersection shape')
    value = 0. if shape.isNull() else float(shape.Volume)/_PROBE_THICKNESS
    if not math.isfinite(value) or value < -_AREA_TOL:
        raise ValueError('Invalid native projected area')
    return max(0., value)


def _polygon_prism(points, z):
    import FreeCAD as App
    import Part
    vectors = [App.Vector(float(x), float(y), z) for x, y in points]
    face = Part.Face(Part.makePolygon(vectors+[vectors[0]]))
    if face.isNull() or not face.isValid():
        raise ValueError('Invalid projected polygon')
    return face.extrude(App.Vector(0., 0., _PROBE_THICKNESS))


def _cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def _triangle_intersection_area(first, second):
    """Cheap convex clipping; never used alone to certify a native contact."""
    polygon = list(first)
    clip = list(second)
    if _cross(*clip) < 0:
        clip.reverse()
    for a, b in zip(clip, clip[1:]+clip[:1]):
        output = []
        if not polygon:
            return 0.
        for p, q in zip(polygon, polygon[1:]+polygon[:1]):
            dp, dq = _cross(a, b, p), _cross(a, b, q)
            if dp >= 0:
                output.append(p)
            if (dp >= 0) != (dq >= 0):
                ratio = dp/(dp-dq)
                output.append(tuple(p[i]+ratio*(q[i]-p[i]) for i in range(2)))
        polygon = output
    return abs(sum(p[0]*q[1]-p[1]*q[0]
                   for p, q in zip(polygon, polygon[1:]+polygon[:1])))/2.


def _bounds(points):
    return [min(p[0] for p in points), min(p[1] for p in points),
            max(p[0] for p in points), max(p[1] for p in points)]


def _disjoint(a, b):
    return a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1]


def _slice_triangles(solid, top):
    """Projected triangles of actual horizontal top faces of a thin slice."""
    output = []
    for face in solid.Faces:
        box = face.BoundBox
        if abs(box.ZMin-top) > 1.e-6 or abs(box.ZMax-top) > 1.e-6:
            continue
        vertices, facets = face.tessellate(_TESSELLATION)
        for indices in facets:
            triangle = [(vertices[i].x, vertices[i].y) for i in indices]
            if abs(_cross(*triangle)) > 1.e-10:
                output.append((triangle, _bounds(triangle)))
    if not output:
        raise ValueError('Pocket slice has no readable top-face projection')
    return output


def _own_bore(obj, inverse, z):
    import FreeCAD as App
    import Part
    drill = _board_shape(obj, inverse, 'DrillPart')
    cylinders = {}
    for face in drill.Faces:
        surface = face.Surface
        if type(surface).__name__ != 'Cylinder' or abs(abs(surface.Axis.z)-1.) > 1.e-7:
            continue
        if not (face.BoundBox.ZMin <= z and face.BoundBox.ZMax >= z+_PROBE_THICKNESS):
            continue
        key = (round(surface.Center.x, 6), round(surface.Center.y, 6), round(surface.Radius, 6))
        record = cylinders.setdefault(key, {'xy_mm': [surface.Center.x, surface.Center.y],
            'radius_mm': float(surface.Radius), 'angular_span_rad': 0.})
        u0, u1, _, _ = face.ParameterRange
        record['angular_span_rad'] += abs(u1-u0)
    if len(cylinders) != 1:
        raise ValueError(obj.Name+': expected one actual vertical M05 mounting bore')
    record = next(iter(cylinders.values()))
    if (abs(record['angular_span_rad']-2.*math.pi) > 1.e-5 or
            abs(2.*record['radius_mm']-3.4544) > 1.e-4):
        raise ValueError(obj.Name+': actual bore is not a complete 8-32 tap cylinder')
    bore = Part.makeCylinder(record['radius_mm'], _PROBE_THICKNESS,
        App.Vector(*record['xy_mm'], z), App.Vector(0., 0., 1.))
    # This checks the actual cutter itself, not an assumed centre or catalog hole.
    if abs(_area(bore.common(drill))-_area(bore)) > _AREA_TOL:
        raise ValueError(obj.Name+': mounting bore reconstruction differs from DrillPart')
    return bore, record


def _bottom_prisms(geometry, plate_top, z):
    import Part
    facets, seen = [], set()
    for indices in geometry['faces']:
        points = [geometry['xyz'][i] for i in indices]
        if len(points) != 3 or any(abs(p[2]-plate_top) > _BOTTOM_TOL for p in points):
            continue
        u = [points[1][i]-points[0][i] for i in range(3)]
        v = [points[2][i]-points[0][i] for i in range(3)]
        normal = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
        length = math.sqrt(sum(n*n for n in normal))
        if length <= 1.e-12 or abs(normal[2])/length < 1.-1.e-7:
            continue
        xy = [p[:2] for p in points]
        key = tuple(sorted(tuple(round(value, 7) for value in p) for p in xy))
        if key in seen:
            continue
        seen.add(key)
        facets.append(xy)
    if not facets:
        raise ValueError('No actual horizontal mirror-base facets near the plate top')
    # STL bottom triangles share edges but not interiors. Duplicate facets are
    # removed; a compound avoids repeated fuse operations over this flat mesh.
    solid = Part.makeCompound([_polygon_prism(triangle, z) for triangle in facets])
    if solid.isNull() or not solid.isValid():
        raise ValueError('Invalid actual bottom-facet probe')
    return solid, facets


def _body_pocket_overlap(geometry, pocket, pocket_triangles, z):
    hull = _polygon_prism(geometry['hull'], z)
    conservative = _area(hull.common(pocket))
    result = {'body_hull_xy_mm': geometry['hull'],
              'conservative_hull_pocket_overlap_mm2': conservative,
              'native_triangle_intersections': 0, 'resolved': conservative <= _AREA_TOL,
              'actual_body_overlap': False, 'witness_overlap_mm2': 0.}
    if result['resolved']:
        return result
    seen = set()
    for index, indices in enumerate(geometry['faces']):
        triangle = [geometry['xy'][i] for i in indices]
        if len(triangle) != 3 or abs(_cross(*triangle)) <= 1.e-10:
            continue
        key = tuple(sorted(tuple(round(v, 7) for v in p) for p in triangle))
        if key in seen:
            continue
        seen.add(key)
        bounds = _bounds(triangle)
        if not any(not _disjoint(bounds, box) and _triangle_intersection_area(triangle, other) > 1.e-8
                   for other, box in pocket_triangles):
            continue
        result['native_triangle_intersections'] += 1
        overlap = _area(_polygon_prism(triangle, z).common(pocket))
        if overlap > _AREA_TOL:
            result.update(resolved=True, actual_body_overlap=True,
                          witness_overlap_mm2=overlap, witness_triangle_index=index,
                          witness_triangle_xy_mm=triangle)
            return result
        if result['native_triangle_intersections'] >= _MAX_REFINEMENT_BOOLEANS:
            break
    # Approximate pocket tessellation is used only to select witness candidates.
    # It cannot turn a conservative overlap into a clean native result.
    result['reason'] = 'Body hull overlaps pocket; no decisive native triangle witness. Remains unresolved.'
    return result


def audit(doc, info):
    """Return JSON evidence without creating or changing any document object."""
    import FreeCAD as App
    import Part
    import ta_projection_audit as projection
    result = {'schema': 'ta_mount_support_audit/1', 'document': doc.Name, 'passed': False,
        'expected_m05_count': 6, 'mounts': [], 'foreign_pockets': [], 'errors': [],
        'settings': {'bottom_plane_tolerance_mm': _BOTTOM_TOL, 'probe_depth_mm': _PROBE_DEPTH,
                     'probe_thickness_mm': _PROBE_THICKNESS, 'area_tolerance_mm2': _AREA_TOL},
        'scope': 'Six actual TA M05 bottom footprints on the final plate, excluding only their own bore; '
                 'foreign TA-adapter pocket/body projection is forbidden regardless of Z. '
                 'Other support interfaces and structural strength are not certified.',
        'method': 'Compound bottom probes, own actual bore subtraction, final-plate intersection; '
                  'foreign pocket native slice with hull broad phase and actual triangle witnesses.',
        'source_provenance': {Path(path).name: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                              for path in (__file__, projection.__file__)}}
    try:
        plate = info['plate']
        if info.get('mode') != 'ta' or plate.Document != doc:
            raise ValueError('Current TA document and plate required')
        inverse = plate.Placement.inverse()
        solid = _board_shape(plate, inverse)
        if len(solid.Solids) != 1 or getattr(plate, 'Drill', True) is False:
            raise ValueError('One final drilled plate solid required')
        top = float(solid.BoundBox.ZMax)
        if abs(top+float(plate.OpticsDz.Value)) > 1.e-5:
            raise ValueError('Final plate top differs from the registered mounting plane')
        z = top-_PROBE_DEPTH-_PROBE_THICKNESS/2.
        result['plate_top_z_mm'] = top
        result['probe_z_range_mm'] = [z, z+_PROBE_THICKNESS]
        roots = {o.Name: o for o in info['roots'].values()}
        mirrors = [o for o in roots.values() if _kind(o) in _MIRRORS]
        mounts = [o for o in doc.Objects if _kind(o) == 'mirror_mount_M05'
                  and projection._root_of(o, roots) in mirrors]
        if len(mirrors) != 6 or len(mounts) != 6 or len({projection._root_of(o, roots).Name for o in mounts}) != 6:
            raise ValueError('Expected six distinct mirror roots, each with one actual M05')
        adapters = [o for o in doc.Objects if _kind(o) == 'TA_adapter'
                    and getattr(o, 'Baseplate', None) == plate]
        if len(adapters) != 1:
            raise ValueError('Expected exactly one actual TA adapter')
        pockets = []
        for obj in adapters:
            owner = projection._root_of(obj, roots)
            if owner is None or _kind(owner) not in ('TA_butterfly', 'TA_butterfly_on_adapter'):
                raise ValueError('TA adapter has no registered TA owning root')
            drill = _board_shape(obj, inverse, 'DrillPart')
            box = drill.BoundBox
            slab = Part.makeBox(box.XLength+2., box.YLength+2., _PROBE_THICKNESS,
                                App.Vector(box.XMin-1., box.YMin-1., z))
            pocket = drill.common(slab)
            if pocket.isNull() or not pocket.isValid() or _area(pocket) <= _AREA_TOL:
                raise ValueError('TA adapter lacks a valid actual pocket at the support probe plane')
            triangles = _slice_triangles(pocket, z+_PROBE_THICKNESS)
            geometry = projection._board_geometry(obj, inverse)
            if geometry is None:
                raise ValueError('TA adapter has no actual geometry')
            pockets.append((obj, owner, pocket, triangles))
            result['foreign_pockets'].append({'object': obj.Name, 'root': owner.Name,
                'slice_area_mm2': _area(pocket), 'slice_bbox_xy_mm':
                [pocket.BoundBox.XMin, pocket.BoundBox.YMin, pocket.BoundBox.XMax, pocket.BoundBox.YMax],
                'adapter_z_range_mm': geometry['z_range_mm'],
                'adapter_body_hull_xy_mm': geometry['hull'],
                'source': 'Actual placed TA_adapter.DrillPart native thin slice; includes foreign holes.'})
        for obj in mounts:
            owner = projection._root_of(obj, roots)
            item = {'object': obj.Name, 'root': owner.Name, 'passed': False,
                    'errors': [], 'foreign_pocket_checks': []}
            result['mounts'].append(item)
            try:
                geometry = projection._board_geometry(obj, inverse)
                if geometry is None or geometry['source'] != 'actual_mesh_triangles':
                    raise ValueError('M05 requires its actual placed mesh, not a proxy box')
                bottom, facets = _bottom_prisms(geometry, top, z)
                bore, bore_record = _own_bore(obj, inverse, z)
                required = bottom.cut(bore)
                if required.isNull() or not required.isValid():
                    raise ValueError('No valid bearing footprint after own-bore subtraction')
                raw, required_area = _area(bottom), _area(required)
                supported = _area(required.common(solid))
                if required_area <= _AREA_TOL or supported > required_area+_AREA_TOL:
                    raise ValueError('Inconsistent actual native bearing/support areas')
                unsupported = max(0., required_area-supported)
                item.update(bottom_facet_count=len(facets), bottom_facets_xy_mm=facets,
                    body_z_range_mm=geometry['z_range_mm'], own_bore=bore_record,
                    raw_bottom_area_mm2=raw, excluded_own_bore_area_mm2=raw-required_area,
                    required_support_area_mm2=required_area, supported_area_mm2=supported,
                    unsupported_area_mm2=unsupported, supported_fraction=supported/required_area)
                if unsupported > _AREA_TOL:
                    item['errors'].append('Actual mirror bottom is not fully supported by the final plate')
                for adapter, adapter_root, pocket, triangles in pockets:
                    if adapter_root is owner:
                        raise ValueError('A mirror unexpectedly shares the TA adapter owning root')
                    check = _body_pocket_overlap(geometry, pocket, triangles, z)
                    check.update(adapter=adapter.Name, adapter_root=adapter_root.Name,
                                 bottom_pocket_overlap_mm2=_area(required.common(pocket)))
                    item['foreign_pocket_checks'].append(check)
                    if check['actual_body_overlap']:
                        item['errors'].append('Actual M05 body projects over a foreign TA-adapter pocket')
                    elif not check['resolved']:
                        item['errors'].append('Foreign pocket/body projection is unresolved')
                    if check['bottom_pocket_overlap_mm2'] > _AREA_TOL:
                        item['errors'].append('Actual mirror bearing footprint overlaps the foreign TA-adapter pocket')
                item['passed'] = not item['errors']
            except Exception as exc:
                item['errors'].append(str(exc))
        result['passed'] = len(result['mounts']) == 6 and all(m['passed'] for m in result['mounts'])
    except Exception as exc:
        result['errors'].append(str(exc))
    result['counts'] = {'checked_mounts': len(result['mounts']),
                        'failed_mounts': sum(not m['passed'] for m in result['mounts']),
                        'errors': len(result['errors'])}
    return result


def apply(report, doc, info):
    """Append this evidence/counter; leave all other audits unchanged."""
    result = audit(doc, info)
    report['mount_support_audit'] = result
    issues = result['counts']['failed_mounts']+result['counts']['errors']
    report.setdefault('summary_counts', {})['mount_support_audit_issues'] = max(1, issues) if not result['passed'] else 0
    return report


apply_to_report = apply
