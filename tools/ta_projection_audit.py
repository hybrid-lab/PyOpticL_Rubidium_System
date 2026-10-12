"""Read-only XY beam/hardware audit for PyOpticL board models.

Call ``audit(doc, info)`` after recompute. The return value is JSON serializable.
``info['paths']`` supplies board-frame points and beam radii, and ``roots``
identifies optical assemblies. This check deliberately ignores vertical
separation: a beam underneath a thumbscrew is a conflict.

Convex hulls provide conservative clearance bounds. Hull hits are refined
against projected mesh/BREP triangles, so hull-only candidates are distinguished
from projected-surface hits. No lane or complete assembly is exempted. Optical
exceptions apply to one object on one segment, with the reasons recorded.
This complements, rather than replaces, a 3-D collision/aperture audit.
"""

import math


_EPS = 1.e-7
# Existing TA paths round a KA05T lens face by 0.002 mm. This tolerance
# recognizes that same optical point without admitting a distinct nearby ray.
_CENTER_TOL = 0.01
_TESSELLATION_MM = 0.15
_AXIS_COS = math.cos(math.radians(2.0))

# Exact proxy names, not label substrings. An unknown housing is never silently
# promoted to an optical exception. These lists describe this branch's parts.
_OPTICS = {
    'circular_lens', 'cylindrical_lens', 'waveplate', 'cube_splitter',
    'rb_cell_cylindrical', 'mounted_lens_c220tmda', 'SlidingCellGlass',
}
_MIRRORS = {'circular_mirror', 'circular_mirror_union_optic'}
_AXIAL_BODIES = {
    'TA_butterfly', 'TA_butterfly_on_adapter', 'isolator_850',
    'isolator_850_long_pocket', 'shutter_sr475', 'AOMO_3100_125',
    'pinhole_ida12', 'rotation_stage_rsp05', 'rotation_stage_rsp05_bonded_cube',
    'SlidingCellEnclosure',
}
_CELL_PARTS = {'SlidingCellEnclosure', 'SlidingCellLid', 'SlidingCellCover', 'SlidingCellGlass'}
_FIBER_ROOTS = {'fiberport_mount_KA05T_holes', 'fiberport_mount_KA05T', 'fiberport_mount_km05T'}
_KM_BODIES = {'prism_mount_km100pm', 'prism_mount_km100pm_bridged'}
_APERTURE_PARTS = {
    'lens_holder_l05g', 'lens_holder_l05g_no_pin_slots',
    'rotation_stage_rsp05', 'cube_mount_halfinch',
    'mirror_mount_M05', 'mirror_mount_KA05T', 'mirror_mount_KA05TB', 'mirror_mount_km05T',
    'fiber_adapter_sm05fca2', 'lens_tube_sm05l05', 'lens_adapter_s05tm09',
}
_MACHINING = {
    'BareTappedHole', 'PersistentDrillVolume', 'CellPocketMachining',
    'SlidingCellSeat', 'IntegralAOMSeat',
}


def _kind(obj):
    return type(getattr(obj, 'Proxy', None)).__name__


def _knob(obj):
    text = (_kind(obj) + ' ' + obj.Name + ' ' + obj.Label).lower()
    return any(word in text for word in ('thumbscrew', 'thumb screw', 'knob', 'adjuster'))


def _cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def _distance(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])


def _point_segment(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    length2 = dx*dx + dy*dy
    t = 0. if length2 < _EPS**2 else max(0., min(1., ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/length2))
    return _distance(p, (a[0]+t*dx, a[1]+t*dy))


def _intersection(a, b, c, d):
    """Return point/overlap evidence, including T contacts and collinear overlap."""
    u, v = (b[0]-a[0], b[1]-a[1]), (d[0]-c[0], d[1]-c[1])
    den = u[0]*v[1]-u[1]*v[0]
    w = (c[0]-a[0], c[1]-a[1])
    if abs(den) > _EPS:
        t = (w[0]*v[1]-w[1]*v[0])/den
        s = (w[0]*u[1]-w[1]*u[0])/den
        if -_EPS <= t <= 1.+_EPS and -_EPS <= s <= 1.+_EPS:
            return {'kind': 'point', 'point_mm': [a[0]+t*u[0], a[1]+t*u[1]]}
        return None
    if _point_segment(c, a, b) > _EPS and abs(_cross(a, b, c)) > _EPS:
        return None
    contacts = []
    for p in (a, b, c, d):
        if _point_segment(p, a, b) <= _EPS and _point_segment(p, c, d) <= _EPS:
            if not any(_distance(p, q) <= _EPS for q in contacts):
                contacts.append(p)
    if not contacts:
        return None
    if len(contacts) == 1:
        return {'kind': 'point', 'point_mm': list(contacts[0])}
    return {'kind': 'collinear_overlap', 'overlap_ends_mm': [list(p) for p in contacts]}


def _segment_distance(a, b, c, d):
    if _intersection(a, b, c, d) is not None:
        return 0.
    return min(_point_segment(a, c, d), _point_segment(b, c, d),
               _point_segment(c, a, b), _point_segment(d, a, b))


def _hull(points):
    points = sorted(set(points))
    if len(points) <= 2:
        return points
    lower, upper = [], []
    for p in points:
        while len(lower) > 1 and _cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper) > 1 and _cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _inside(p, polygon):
    if len(polygon) < 3:
        return False
    signs = [_cross(polygon[i], polygon[(i+1) % len(polygon)], p) for i in range(len(polygon))]
    # Degenerate projected triangles have no interior.
    area2 = sum(polygon[i][0]*polygon[(i+1) % len(polygon)][1] -
                polygon[(i+1) % len(polygon)][0]*polygon[i][1] for i in range(len(polygon)))
    return abs(area2) > _EPS and (min(signs) >= -_EPS or max(signs) <= _EPS)


def _polygon_distance(a, b, polygon):
    if not polygon:
        return math.inf
    if len(polygon) == 1:
        return _point_segment(polygon[0], a, b)
    if _inside(a, polygon) or _inside(b, polygon):
        return 0.
    return min(_segment_distance(a, b, polygon[i], polygon[(i+1) % len(polygon)])
               for i in range(len(polygon)))


def _ref(obj):
    return {'object': obj.Name, 'label': obj.Label, 'proxy': _kind(obj)}


def _root_of(obj, roots):
    seen = set()
    while obj is not None and obj.Name not in seen:
        if obj.Name in roots:
            return roots[obj.Name]
        seen.add(obj.Name)
        obj = getattr(obj, 'ParentObject', None)
    return None


def _board_geometry(obj, inverse_plate):
    """Read actual placed vertices; transform world geometry into the board frame.

    FreeCAD Mesh.Topology and Shape.tessellate expose placed geometry; applying
    obj.Placement again would double-transform it. No geometry is mutated here.
    """
    mesh = getattr(obj, 'Mesh', None)
    shape = getattr(obj, 'Shape', None)
    if mesh is not None and mesh.CountPoints:
        vertices, faces = mesh.Topology
        source, uncertainty = 'actual_mesh_triangles', 0.
    elif shape is not None and not shape.isNull():
        vertices, faces = shape.tessellate(_TESSELLATION_MM)
        source, uncertainty = 'tessellated_brep', _TESSELLATION_MM
    else:
        return None
    coords, local_coords = [], []
    inverse_object = obj.Placement.inverse() if _kind(obj) in _KM_BODIES else None
    for vertex in vertices:
        p = inverse_plate.multVec(vertex)
        coords.append((float(p.x), float(p.y), float(p.z)))
        if inverse_object is not None:
            local = inverse_object.multVec(vertex)
            local_coords.append((float(local.x), float(local.y), float(local.z)))
    if not coords:
        return None
    if not faces:
        raise ValueError('Physical geometry has vertices but no projected surface faces.')
    xy = [(p[0], p[1]) for p in coords]
    hull = _hull(xy)
    return {'xy': xy, 'xyz': coords, 'local_xyz': local_coords,
            'faces': faces, 'hull': hull, 'source': source,
            'uncertainty_mm': uncertainty,
            'z_range_mm': [min(p[2] for p in coords), max(p[2] for p in coords)]}


def _km_controls(geometry):
    """Separate real connected knob/shaft shells in this branch's KM100PM STL.

    Inspection of the 117278-facet STL found 27 disconnected shells. The two
    4260-facet knurled heads and two 754-facet shafts protrude past local x=-24
    mm; no main body or spring does. Identify complete connected shells, not
    a cropped bounding-box region that would lose the inner shaft portions.
    An unexpected topology/bounds signature fails closed: the complete mount
    remains checked, including on its own optical route.
    """
    faces, local = geometry['faces'], geometry['local_xyz']
    if len(faces) != 117278 or not local:
        raise ValueError('Unrecognized KM100PM mesh; expected 117278 facets and local vertices.')
    parents = list(range(len(faces)))

    def find(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    first_face = {}
    for index, face in enumerate(faces):
        for vertex in face:
            key = tuple(round(value, 6) for value in local[vertex])
            previous = first_face.setdefault(key, index)
            a, b = find(index), find(previous)
            if a != b:
                parents[a] = b
    components = {}
    for index in range(len(faces)):
        components.setdefault(find(index), []).append(index)
    if len(components) != 27:
        raise ValueError('Unrecognized KM100PM topology: expected 27 shells, found %d.' % len(components))

    controls, used = [], set()
    # Bounds are in the imported KM mount frame, after optomech's STL transform.
    expected = {
        ('upper', 'knob'): (-37.2615, 24.0099, 30.3599, -25.8315, 38.7281, 45.0781),
        ('lower', 'knob'): (-37.2790, -13.7157, -7.3657, -25.8490, 1.0157, 7.3657),
        ('upper', 'shaft'): (-30.4035, 28.1941, 34.5450, -7.0355, 34.5439, 40.8930),
        ('lower', 'shaft'): (-30.4210, -9.5241, -3.1748, -7.0530, -3.1759, 3.1748),
    }

    def subset(indices):
        selected = [faces[i] for i in indices]
        vertices = {v for face in selected for v in face}
        return dict(geometry, faces=selected,
                    hull=_hull([geometry['xy'][v] for v in vertices]),
                    z_range_mm=[min(geometry['xyz'][v][2] for v in vertices),
                                max(geometry['xyz'][v][2] for v in vertices)])

    for indices in components.values():
        vertices = {v for index in indices for v in faces[index]}
        bounds = tuple(min(local[v][axis] for v in vertices) for axis in range(3)) + \
                 tuple(max(local[v][axis] for v in vertices) for axis in range(3))
        if bounds[0] >= -24.:
            continue
        matches = [key for key, reference in expected.items()
                   if max(abs(a-b) for a, b in zip(bounds, reference)) <= 0.01]
        if len(matches) != 1:
            raise ValueError('Unrecognized protruding KM100PM shell: %r.' % (bounds,))
        key = matches[0]
        count = 4260 if key[1] == 'knob' else 754
        if len(indices) != count or key in used:
            raise ValueError('Unexpected/duplicate KM100PM adjustment shell: %r.' % (key,))
        used.add(key)
        controls.append({'name': '%s adjustment %s' % key,
                         'local_bbox_mm': list(bounds), 'facets': len(indices),
                         'indices': set(indices), 'geometry': subset(indices)})
    if used != set(expected):
        raise ValueError('Both KM100PM heads and complete shafts must be identified before any seat exception.')
    control_faces = set().union(*(part['indices'] for part in controls))
    body = subset([i for i in range(len(faces)) if i not in control_faces])
    return body, controls


def _surface_distance(segment, geometry, cutoff):
    """Refine only triangles inside the expanded segment bounding box.

    Return the minimum within cutoff, or None. Hull-only candidates remain
    visible in the report even if no projected triangle is close enough.
    """
    a, b = segment['a'], segment['b']
    bounds = (min(a[0], b[0])-cutoff, max(a[0], b[0])+cutoff,
              min(a[1], b[1])-cutoff, max(a[1], b[1])+cutoff)
    best = math.inf
    for face in geometry['faces']:
        polygon = [geometry['xy'][index] for index in face]
        if not polygon:
            continue
        if (max(p[0] for p in polygon) < bounds[0] or min(p[0] for p in polygon) > bounds[1]
                or max(p[1] for p in polygon) < bounds[2] or min(p[1] for p in polygon) > bounds[3]):
            continue
        best = min(best, _polygon_distance(a, b, polygon))
        if best <= _EPS:
            break
    return best if best <= cutoff+_EPS else None


def _center_and_axis(root):
    """Return its board-frame optical reference, distinct from its mount tap."""
    # BasePlacement is the branch's board-frame placement. In the KA05T
    # assembly the entry lens face is 18.798 mm along local +X from the mount.
    import FreeCAD as App
    placement = root.BasePlacement
    direction = placement.Rotation.multVec(App.Vector(1, 0, 0))
    center = placement.Base
    if _kind(root) in _FIBER_ROOTS:
        center = center + direction*18.798
    elif _kind(root) == 'rotation_stage_rsp05_bonded_cube':
        # Explicit centre of the real linked 12.7 mm cube. Do not reuse the
        # former empty-mount 0.5 mm optical-plane placeholder.
        offset = float(root.CubeCentreOffset.Value)
        expected = 7.747+float(root.AdhesiveThickness.Value)+6.35
        if abs(offset-expected) > _EPS:
            raise ValueError('Inconsistent RSP05 bonded-cube optical centre')
        center = placement.multVec(App.Vector(offset, 0, 0))
    elif _kind(root) == 'rotation_stage_rsp05' and hasattr(root, 'OpticalPlaneOffset'):
        # Splitting mounts sit 0.5 mm behind the declared bonded-optic plane,
        # matching the offset of an RSP05 child of a waveplate.
        offset = float(root.OpticalPlaneOffset.Value)
        if abs(offset-0.5) > _EPS:
            raise ValueError('Unknown standalone RSP05 optical-plane offset')
        center = center + direction*offset
    elif _kind(root) == 'AOMO_3100_125':
        # integrate_aom moves the assembly by +(.030 y, .115 z). The bore
        # center is still at local (0, -.030, -.115), not at Placement.Base.
        aperture = getattr(root, 'MeshApertureLocal', App.Vector(0, -.030, -.115))
        center = placement.multVec(aperture)
    elif _kind(root) == 'SlidingCellEnclosure':
        # The cell moves transversely; the design ray remains at the seat axis.
        # This reference identifies that one intended ray, not every parallel
        # ray within the enclosure's large XY footprint.
        center = placement.multVec(App.Vector(0, -float(root.Slide.Value), 0))
    return (float(center.x), float(center.y)), (float(direction.x), float(direction.y))


def _on_axis(root, segment):
    kind = _kind(root)
    if kind not in (_OPTICS | _MIRRORS | _AXIAL_BODIES | _FIBER_ROOTS):
        return False
    if not hasattr(root, 'BasePlacement'):
        return False
    center, axis = _center_and_axis(root)
    if _point_segment(center, segment['a'], segment['b']) > _CENTER_TOL:
        return False
    if kind in _MIRRORS:
        # A fold is an endpoint, never a license for an unrelated segment
        # to cut through the assembly just because it crosses the optic center.
        return min(_distance(center, segment['a']), _distance(center, segment['b'])) <= _CENTER_TOL
    if kind == 'cube_splitter':
        # PBS transmitted and reflected axes are perpendicular in this design.
        u = segment['unit']
        dot = abs(u[0]*axis[0]+u[1]*axis[1])
        return dot >= _AXIS_COS or dot <= math.sin(math.radians(2.0))
    if kind == 'SlidingCellEnclosure':
        slide, travel = float(root.Slide.Value), float(root.Travel.Value)
        bore_radius = float(root.BoreRadius.Value)
        # A yaw-aligned intended ray must fit the actual cylindrical bore even
        # at the selected transverse slide. Metal surfaces still need the
        # independent 3-D check; XY alone cannot inspect an internal bore.
        offset = math.hypot(slide, float(root.BasePlacement.Base.z))
        dot = abs(segment['unit'][0]*axis[0]+segment['unit'][1]*axis[1])
        return (-_EPS <= slide <= travel+_EPS and dot >= 1.-1.e-9 and
                offset+segment['radius_mm'] <= bore_radius-_EPS)
    return abs(segment['unit'][0]*axis[0]+segment['unit'][1]*axis[1]) >= _AXIS_COS


def _exception(obj, root, segment, geometry, embedded_verified=False):
    if _knob(obj) or root is None or not _on_axis(root, segment):
        return None
    kind = _kind(obj)
    if kind == 'RSP05CubeAdhesive' and _kind(root) == 'rotation_stage_rsp05_bonded_cube':
        # The four actual pads sit at radius >=7.095 mm for every cube roll.
        # Only this registered axial ray can pass through their XY shadow;
        # foreign rays and every separately modeled control remain checked.
        if segment['radius_mm'] < 7.09:
            return ('Four RSP05 corner adhesive pads outside the intended axial beam '
                    '(minimum radial clearance 7.095 mm); actual rotor contact and full '
                    'cube rotation envelope require audit_rsp05_bonded_cube.')
    if _kind(root) == 'SlidingCellEnclosure' and kind in _CELL_PARTS:
        if kind == 'SlidingCellCover':
            return ('UNMACHINED V9.7 end cover: the current solid BLOCKS this ray. '
                    'Excluded only as an on-axis placement placeholder in the mechanical XY '
                    'audit; optical passage is NOT passed. Required apertures are listed separately.')
        if kind in {'SlidingCellEnclosure', 'SlidingCellLid'}:
            return ('V9.7 enclosure half around its intended axial ray, at transverse slide '
                    '%.3f mm within bore radius %.3f mm. Its XY shadow covers the ray despite '
                    'the 3-D bore; independent surface-level 3-D bore clearance remains required.'
                    % (float(root.Slide.Value), float(root.BoreRadius.Value)))
        return ('V9.7 cell glass envelope on the intended seat-axis ray; transparent material. '
                'This is a mechanical envelope exception, not optical transmission certification.')
    if kind in (_OPTICS | _MIRRORS):
        return 'Optical material of this on-axis root; transmission/reflection is intentional.'
    if obj is root and kind in _AXIAL_BODIES:
        return ('Known axial body at its optical center; its operating aperture is assumed. '
                'An independent 3-D aperture check remains required.')
    if kind in _APERTURE_PARTS:
        return ('Known aperture/mirror seat of this on-axis root, on this segment only; '
                'all separately modeled thumbscrews remain checked.')
    if kind in _KM_BODIES and embedded_verified and _kind(root) == 'AOMO_3100_125':
        return ('Known KM100PM main support on its own AOM optical axis; the two embedded '
                'knob heads AND complete shafts were separated by connected mesh shell '
                'and are independently checked against every segment. 3-D aperture audit required.')
    if ((kind == 'aom_adapter' and _kind(root) == 'AOMO_3100_125') or
            (kind == 'shutter_adapter' and _kind(root) == 'shutter_sr475')):
        if geometry['z_range_mm'][1] < -segment['radius_mm']-_EPS:
            return ('Known fixed adapter below its own on-axis beam envelope; only this '
                    'segment is exempt. Foreign rays and all adjustment hardware remain checked.')
    return None


def _segments(info, errors):
    out = []
    for path_index, path in enumerate(info.get('paths', [])):
        points = path.get('points', [])
        radii = path.get('envelope')
        if isinstance(radii, (int, float)):
            radii = [float(radii)]*len(points)
        if radii is None or len(radii) != len(points):
            errors.append({'path': path.get('name'), 'error': 'One beam radius per path point is required.'})
            continue
        for index, (a, b) in enumerate(zip(points, points[1:])):
            a, b = tuple(map(float, a[:2])), tuple(map(float, b[:2]))
            length = _distance(a, b)
            if length <= _EPS:
                errors.append({'path': path.get('name'), 'segment': index, 'error': 'Zero-length segment.'})
                continue
            radius = max(float(radii[index]), float(radii[index+1]))
            if not all(math.isfinite(v) for v in (*a, *b, radius)) or radius < 0:
                errors.append({'path': path.get('name'), 'segment': index, 'error': 'Nonfinite coordinate or invalid radius.'})
                continue
            out.append({'path': path['name'], 'path_index': path_index, 'segment': index,
                        'a': a, 'b': b, 'radius_mm': radius,
                        'unit': ((b[0]-a[0])/length, (b[1]-a[1])/length)})
    return out


def _segment_ref(segment):
    return {key: segment[key] for key in ('path', 'segment', 'radius_mm')}


def _allowed_junction(first, second, hit, roots, info):
    if hit['kind'] != 'point':
        return None
    point = hit['point_mm']
    shared = all(min(_distance(point, s['a']), _distance(point, s['b'])) <= _CENTER_TOL
                 for s in (first, second))
    if not shared:
        return None
    if first['path_index'] == second['path_index'] and abs(first['segment']-second['segment']) == 1:
        return 'Consecutive segments of one continuous optical path.'
    for root in roots.values():
        if _kind(root) != 'cube_splitter' or not hasattr(root, 'BasePlacement'):
            continue
        center, _ = _center_and_axis(root)
        if _distance(point, center) > _CENTER_TOL:
            continue
        for spec in info.get('pbs_path_specs', []):
            names = [spec.get('incoming_path')] + list(spec.get('outgoing_paths', []))
            if spec.get('cube') in (root.Name, root.Label) and first['path'] in names and second['path'] in names:
                return 'Shared endpoint of the explicitly registered PBS input/output paths.'
    # The TA script divides one continuous upstream ray into named sections.
    # Only a joined end/start with the same travel direction is a continuation.
    end_start = (_distance(first['b'], second['a']) <= _CENTER_TOL or
                 _distance(second['b'], first['a']) <= _CENTER_TOL)
    dot = first['unit'][0]*second['unit'][0]+first['unit'][1]*second['unit'][1]
    if first['path_index'] != second['path_index'] and end_start and dot >= 1.-_EPS:
        return 'Collinear end/start continuation between named path sections.'
    return None


def audit(doc, info):
    """Return evidence without recomputing, changing visibility, or writing files.

    ``mechanical_projection_passed`` excludes documented unmachined cell-cover
    placeholders. ``passed`` is additionally false while those physical beam
    obstructions remain. A true value is conditional on the explicitly listed
    aperture assumptions, not a fabrication approval.
    Distances are mm; edge margins subtract each segment's maximum beam radius.
    Positive hull clearance is a conservative lower bound. Mesh hits describe
    the mesh, and BREP hits within tessellation uncertainty remain candidates.
    """
    report = {
        'schema': 'ta_xy_projection_audit/2',
        'method': 'Actual placed mesh/BREP projection, convex-hull broad phase, triangle refinement.',
        'coordinate_frame': 'Baseplate local XY; optical plane z=0.',
        'tolerances_mm': {'center': _CENTER_TOL, 'brep_tessellation': _TESSELLATION_MM},
        'ray_crossings': [], 'allowed_shared_junctions': [],
        'thumbscrew_projection_hits': [], 'foreign_hardware_projection_conflicts': [],
        'embedded_adjustment_parts': [],
        'documented_unmachined_cell_covers': [], 'required_follow_up': [],
        'hull_only_candidates': [], 'unresolved_candidates': [],
        'optical_exceptions': [], 'excluded_objects': [], 'assumptions': [],
        'geometry_errors': [], 'minimum_margins': {},
        'counts': {}, 'passed': False, 'mechanical_projection_passed': False,
        'optical_path_readiness': 'not_certified_by_a_mechanical_projection_audit',
        'scope': 'Mechanical XY placement, with declared axial-housing exceptions; 3-D bore/aperture checks remain separate.',
    }
    plate = info.get('plate')
    if (plate is None or getattr(plate, 'Document', None) != doc or
            doc.getObject(plate.Name) != plate):
        report['geometry_errors'].append({
            'error': 'The supplied baseplate must belong to the audited document and resolve there to the same object.',
            'document': getattr(doc, 'Name', None),
            'plate': getattr(plate, 'Name', None),
            'plate_document': getattr(getattr(plate, 'Document', None), 'Name', None),
        })
        report['counts'] = {'segments': 0, 'physical_objects': 0, 'tested_object_segment_pairs': 0}
        for key in ('ray_crossings', 'thumbscrew_projection_hits', 'foreign_hardware_projection_conflicts',
                    'hull_only_candidates', 'unresolved_candidates', 'geometry_errors', 'optical_exceptions',
                    'embedded_adjustment_parts', 'documented_unmachined_cell_covers'):
            report['counts'][key] = len(report[key])
        report['status'] = 'mechanical_projection_failed'
        return report
    inverse_plate = plate.Placement.inverse()
    plate_top = -float(plate.OpticsDz.Value)
    roots = {obj.Name: obj for obj in info.get('roots', {}).values()}
    segments = _segments(info, report['geometry_errors'])
    report['assumptions'].extend([
        'Path points/envelopes use the baseplate local frame; envelopes are radii in mm.',
        'A segment uses the maximum of its endpoint radii, conservatively enclosing a taper.',
        'Separately modeled thumbscrews, knobs and adjusters are checked at every Z, including their own optical route.',
        'Known aperture exceptions do not certify aperture size, mirror incidence, crystal transmission, or unmodeled hardware.',
            'KA05T and KM05T fiber optical entry faces are local +X 18.798 mm from their assembly placement, as in this branch.',
        'AOMO optical center includes its MeshApertureLocal offset (0,-0.030,-0.115 mm).',
        'Sliding-cell body/lid exceptions apply only to the intended seat-axis ray; the selected slide must remain inside its bore.',
    ])
    minima = {}

    def minimum(category, value, evidence):
        if category not in minima or value < minima[category]['edge_margin_lower_bound_mm']:
            minima[category] = dict(evidence, edge_margin_lower_bound_mm=round(value, 6))

    # Ray crossings: same-path self intersections count too; only explicit
    # shared optical junctions and continuous section boundaries are allowed.
    for index, first in enumerate(segments):
        for second in segments[index+1:]:
            hit = _intersection(first['a'], first['b'], second['a'], second['b'])
            reason = _allowed_junction(first, second, hit, roots, info) if hit else None
            evidence = {'first': _segment_ref(first), 'second': _segment_ref(second)}
            if reason:
                report['allowed_shared_junctions'].append(dict(evidence, reason=reason, **hit))
                continue
            distance = _segment_distance(first['a'], first['b'], second['a'], second['b'])
            minimum('unconnected_rays', distance-first['radius_mm']-second['radius_mm'], evidence)
            if hit:
                report['ray_crossings'].append(dict(evidence, **hit))

    path_objects = {p.get('object') for p in info.get('paths', [])}
    relevant, tested_pairs = 0, 0
    for obj in doc.Objects:
        if obj is plate or obj.Name in path_objects:
            continue
        root = _root_of(obj, roots)
        # Check unregistered hardware too, including manually added solids with
        # no Baseplate property. Only an explicit link to another board excludes
        # an object; visibility is not evidence that hardware is uninstalled.
        object_plate = getattr(obj, 'Baseplate', None)
        if root is None and object_plate is not None and object_plate != plate:
            continue
        knob, kind = _knob(obj), _kind(obj)
        if not knob and kind in _MACHINING:
            report['excluded_objects'].append(dict(_ref(obj), reason='Machining-only proxy; no physical housing.'))
            continue
        try:
            geometry = _board_geometry(obj, inverse_plate)
        except Exception as exc:
            report['geometry_errors'].append(dict(_ref(obj), error=repr(exc)))
            continue
        if geometry is None:
            if knob:
                report['geometry_errors'].append(dict(_ref(obj), error='Thumbscrew has no readable physical geometry.'))
            else:
                report['excluded_objects'].append(dict(_ref(obj), reason='No physical Mesh or Shape; children checked independently.'))
            continue
        # Only explicitly named adapters wholly at/below the plate top can be
        # excluded. A low unknown housing, and every knob, still gets tested.
        if not knob and 'adapter' in kind.lower() and geometry['z_range_mm'][1] <= plate_top+_EPS:
            report['excluded_objects'].append(dict(_ref(obj), reason='Adapter wholly at/below plate top.',
                                                   z_range_mm=geometry['z_range_mm']))
            continue
        relevant += 1
        if kind == 'SlidingCellCover':
            affected = [_segment_ref(segment) for segment in segments
                        if root is not None and _on_axis(root, segment) and
                        _polygon_distance(segment['a'], segment['b'], geometry['hull'])
                        <= segment['radius_mm']+geometry['uncertainty_mm']]
            report['documented_unmachined_cell_covers'].append(dict(
                _ref(obj), root=None if root is None else root.Name,
                status='solid_cover_without_beam_aperture', affected_segments=affected,
                selected_slide_mm=float(root.Slide.Value) if root is not None and hasattr(root, 'Slide') else None,
                purpose=str(getattr(obj, 'Purpose', '')),
                optical_consequence='The reused V9.7 solid cover is not currently optically passable.',
                mechanical_treatment='Only the intended axial ray can receive a placement-placeholder exception; foreign rays are checked.'))
        controls, embedded_verified = [], False
        if kind in _KM_BODIES:
            try:
                geometry, controls = _km_controls(geometry)
                embedded_verified = True
                for control in controls:
                    report['embedded_adjustment_parts'].append(dict(
                        _ref(obj), subcomponent=control['name'], facets=control['facets'],
                        local_bbox_mm=control['local_bbox_mm'],
                        board_z_range_mm=control['geometry']['z_range_mm'],
                        identification='Complete connected shell; KM100PM source topology and local bounds verified.',
                        checked_against_segments=len(segments)))
            except Exception as exc:
                report['geometry_errors'].append(dict(_ref(obj), error=repr(exc),
                                                      consequence='Complete mesh checked; no KM support exception.'))
        if kind not in (_OPTICS | _MIRRORS | _AXIAL_BODIES | _FIBER_ROOTS | _APERTURE_PARTS | _KM_BODIES | _CELL_PARTS | {'RSP05CubeAdhesive'}) and not knob:
            report['assumptions'].append({'object': obj.Name, 'proxy': kind,
                                          'assumption': 'No verified axial-aperture rule; entire physical projection checked.'})

        def check_projection(segment, physical, is_knob, subcomponent=None):
            nonlocal tested_pairs
            tested_pairs += 1
            distance = _polygon_distance(segment['a'], segment['b'], physical['hull'])
            uncertainty = physical['uncertainty_mm']
            margin = distance-segment['radius_mm']-uncertainty
            evidence = dict(_ref(obj), **_segment_ref(segment),
                            root=None if root is None else root.Name,
                            axis_distance_hull_mm=round(distance, 6),
                            edge_margin_hull_lower_bound_mm=round(margin, 6),
                            z_range_mm=physical['z_range_mm'], source=physical['source'],
                            own_root_on_segment=bool(root and _on_axis(root, segment)))
            if subcomponent is not None:
                evidence['subcomponent'] = subcomponent
            category = 'thumbscrews' if is_knob else 'nonexempt_hardware'
            minimum(category, margin, evidence)
            if margin > _EPS:
                return
            try:
                exact = _surface_distance(segment, physical, segment['radius_mm']+uncertainty)
            except Exception as exc:
                report['unresolved_candidates'].append(dict(evidence, error=repr(exc)))
                return
            if exact is None:
                report['hull_only_candidates'].append(dict(evidence, status='cleared_by_projected_triangles'))
                return
            evidence['axis_distance_projected_surface_mm'] = round(exact, 6)
            evidence['edge_margin_projected_surface_mm'] = round(exact-segment['radius_mm'], 6)
            if exact > segment['radius_mm']+_EPS:
                report['unresolved_candidates'].append(dict(evidence, status='within_brep_tessellation_uncertainty'))
            else:
                target = 'thumbscrew_projection_hits' if is_knob else 'foreign_hardware_projection_conflicts'
                report[target].append(dict(evidence, status='projected_surface_hit'))

        for segment in segments:
            # Embedded heads and shafts are never passed to _exception.
            for control in controls:
                check_projection(segment, control['geometry'], True, control['name'])
            reason = _exception(obj, root, segment, geometry, embedded_verified)
            if reason:
                report['optical_exceptions'].append(dict(_ref(obj), root=root.Name,
                                                        **_segment_ref(segment), reason=reason))
            else:
                check_projection(segment, geometry, knob)

    if relevant == 0:
        report['geometry_errors'].append({
            'error': 'No physical hardware was available for the projection audit; an empty inventory cannot pass.',
        })
    report['minimum_margins'] = minima
    report['counts'] = {'segments': len(segments), 'physical_objects': relevant, 'tested_object_segment_pairs': tested_pairs}
    for key in ('ray_crossings', 'thumbscrew_projection_hits', 'foreign_hardware_projection_conflicts',
                'hull_only_candidates', 'unresolved_candidates', 'geometry_errors', 'optical_exceptions'):
        report['counts'][key] = len(report[key])
    report['counts']['embedded_adjustment_parts'] = len(report['embedded_adjustment_parts'])
    report['counts']['documented_unmachined_cell_covers'] = len(report['documented_unmachined_cell_covers'])
    report['mechanical_projection_passed'] = bool(segments) and relevant > 0 and not any(report[key] for key in (
        'ray_crossings', 'thumbscrew_projection_hits', 'foreign_hardware_projection_conflicts',
        'unresolved_candidates', 'geometry_errors'))
    if report['documented_unmachined_cell_covers']:
        report['required_follow_up'].append({
            'action': 'Design and machine a beam aperture in each reused V9.7 end cover, then rerun the 3-D optical-path audit.',
            'objects': [entry['object'] for entry in report['documented_unmachined_cell_covers']],
            'constraint': 'Apertures must clear the beam envelope over the intended 0..10.5 mm transverse slide; final dimensions are not specified here.',
            'status': 'required_before_optical_operation',
        })
        report['optical_path_readiness'] = 'blocked_by_unmachined_cell_covers'
    report['passed'] = report['mechanical_projection_passed'] and not report['required_follow_up']
    report['status'] = ('mechanical_projection_failed' if not report['mechanical_projection_passed']
                        else 'mechanical_projection_passed_with_required_follow_up' if report['required_follow_up']
                        else 'mechanical_projection_passed')
    return report
