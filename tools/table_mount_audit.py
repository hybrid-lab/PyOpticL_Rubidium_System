"""Check table-mount grid and edge offsets against the actual machined plate.

Run in FreeCAD. This verifies the relative one-inch hole pattern; the optical
table's first-hole distance from its edges is not known and is not assumed.
Hardware, pocket, and tool access remain covered by the board's hole audit.
"""
import math

import FreeCAD as App


def _platform_cylinders(solid):
    """Inventory platform-sized cylinders over the whole solid, not just roots."""
    axes = {}
    for face in solid.Faces:
        surf = face.Surface
        if type(surf).__name__ != 'Cylinder' or abs(abs(surf.Axis.z)-1)>1.e-7:
            continue
        diameter = round(2*surf.Radius, 5)
        if diameter not in (6.604, 14.2875):
            continue
        key = (round(surf.Center.x, 6), round(surf.Center.y, 6), diameter)
        entry = axes.setdefault(key, dict(center_xy_mm=[surf.Center.x, surf.Center.y],
                                         diameter_mm=2*surf.Radius, angular_span=0.,
                                         z_min=math.inf, z_max=-math.inf))
        u0, u1, _, _ = face.ParameterRange
        entry['angular_span'] += abs(u1-u0)
        entry['z_min'] = min(entry['z_min'], face.BoundBox.ZMin)
        entry['z_max'] = max(entry['z_max'], face.BoundBox.ZMax)
    return list(axes.values())


def _relocated_anchor_target(info, box, relocated):
    """Validate an explicit grid relocation; no bore/solid checks are waived."""
    prior = relocated['prior_anchor_xy_mm']
    shift = relocated['board_translation_xy_mm']
    increments = relocated['relocation_in']
    old_size = relocated['prior_plate_size_mm']
    current_size = info['plate_size_mm']
    if info.get('mode') == 'splitting':
        # Only the unchanged 24 x 14 x 1 inch board may use this new contract.
        # The original datum remains one inch from the real machined edges;
        # the actual anchor may move by whole inches with user authorization.
        if (relocated.get('schema') != 'integer_grid_relocation/1'
                or not isinstance(relocated.get('authorization'), str)
                or not relocated['authorization'].strip()
                or any(len(v) != 2 for v in (prior, shift, increments))
                or not all(math.isfinite(float(v)) for pair in (prior, shift, increments) for v in pair)
                or any(isinstance(v, bool) or abs(v-round(v))>1.e-9 for v in increments)
                or any(abs(v)>1.e-9 for v in shift)
                or len(old_size)!=3 or len(current_size)!=3
                or not all(math.isfinite(float(v)) for size in (old_size, current_size) for v in size)
                or any(abs(float(v)-expected)>1.e-6 for size in (old_size, current_size)
                       for v, expected in zip(size, (609.6, 355.6, 25.4)))
                or abs(prior[0]-(box.XMax-25.4))>1.e-6
                or abs(prior[1]-(box.YMin+25.4))>1.e-6
                or abs(box.XMin-3.175)>1.e-6 or abs(box.YMin-3.175)>1.e-6
                or abs(box.XLength-603.25)>1.e-6 or abs(box.YLength-349.25)>1.e-6
                or abs(box.ZLength-25.4)>1.e-6):
            raise ValueError('Invalid unchanged Splitting board, original edge datum or whole-inch relocation authorization')
    else:
        # Preserve the separately authorized TA cropped-grid contract.
        trim = float(relocated['bottom_trim_mm'])
        extension = float(relocated['top_extension_mm'])
        if (info.get('mode') != 'ta' or relocated.get('schema') != 'cropped_grid_reference/1'
                or not relocated.get('authorization') or any(len(v) != 2 for v in (prior, shift, increments))
                or not all(math.isfinite(float(v)) for pair in (prior, shift, increments) for v in pair)
                or any(abs(v-round(v))>1.e-9 for v in increments)
                or abs(shift[0])>1.e-9 or shift[1]>=0
                or abs(prior[0]-(box.XMax-25.4))>1.e-6
                or abs(prior[1]-(box.YMin+25.4))>1.e-6
                or len(old_size)!=3 or len(current_size)!=3
                or not all(math.isfinite(float(v)) for v in old_size+current_size+[trim,extension])
                or trim<=0 or extension<0 or abs(shift[1]+trim)>1.e-6
                or abs(old_size[0]-current_size[0])>1.e-6 or abs(old_size[2]-current_size[2])>1.e-6
                or abs(old_size[1]-trim+extension-current_size[1])>1.e-6
                or abs(box.XLength-(current_size[0]-6.35))>1.e-6
                or abs(box.YLength-(current_size[1]-6.35))>1.e-6):
            raise ValueError('Invalid TA cropped-grid authorization or original anchor datum')
    return [prior[i]+shift[i]+25.4*increments[i] for i in range(2)]


def audit(doc, info):
    plate = info['plate']
    inverse = plate.Placement.inverse()
    solid = plate.Shape.copy()
    solid.Placement = inverse.multiply(solid.Placement)
    box = solid.BoundBox
    errors, holes = [], []
    mounts = [o for o in doc.Objects
              if type(getattr(o, 'Proxy', None)).__name__ == 'baseplate_mount'
              and o.Baseplate == plate]
    if len(mounts) != 4:
        errors.append('Expected exactly four platform fixing holes')
    cylinder_inventory = _platform_cylinders(solid)
    target = [box.XMax-25.4, box.YMin+25.4]
    relocated = info.get('table_mount_pattern', {}).get('relocated_anchor')
    if relocated is not None:
        try:
            target = _relocated_anchor_target(info, box, relocated)
        except Exception as exc:
            errors.append('Invalid relocated anchor: '+str(exc))
    for obj in mounts:
        p = inverse.multVec(obj.Placement.Base)
        center = [p.x, p.y]
        offsets = [(center[i]-target[i])/25.4 for i in range(2)]
        residual = max(abs(v-round(v))*25.4 for v in offsets)
        if residual > 1.e-6:
            errors.append(obj.Name+': not on the anchor one-inch grid')
        edges = dict(left=p.x-box.XMin, right=box.XMax-p.x,
                     bottom=p.y-box.YMin, top=box.YMax-p.y)
        if min(edges.values()) < 14.2875/2:
            errors.append(obj.Name+': counterbore extends beyond a plate edge')
        cylinders = {}
        for face in solid.Faces:
            surf = face.Surface
            if (type(surf).__name__ != 'Cylinder' or abs(abs(surf.Axis.z)-1)>1.e-7
                    or math.hypot(surf.Center.x-p.x, surf.Center.y-p.y)>1.e-5):
                continue
            key = round(2*surf.Radius, 5)
            entry = cylinders.setdefault(key, dict(diameter_mm=2*surf.Radius,
                                                   angular_span=0., z_min=math.inf, z_max=-math.inf))
            u0, u1, _, _ = face.ParameterRange
            entry['angular_span'] += abs(u1-u0)
            entry['z_min'] = min(entry['z_min'], face.BoundBox.ZMin)
            entry['z_max'] = max(entry['z_max'], face.BoundBox.ZMax)
        for diameter in (6.604, 14.2875):
            feature = cylinders.get(round(diameter, 5))
            if feature is None or abs(feature['angular_span']-2*math.pi)>1.e-5:
                errors.append(obj.Name+': missing complete diameter %g bore' % diameter)
        small = cylinders.get(6.604)
        large = cylinders.get(14.2875)
        if small and large:
            if (abs(small['z_min']-box.ZMin)>1.e-5 or
                    abs(large['z_max']-box.ZMax)>1.e-5 or
                    abs(large['z_min']-small['z_max'])>1.e-5 or
                    abs(large['z_max']-large['z_min']-10.)>1.e-5):
                errors.append(obj.Name+': incorrect through-bore or 10 mm counterbore depth')
        head = obj.Shape.copy()
        head.Placement = inverse.multiply(head.Placement)
        holes.append(dict(object=obj.Name, center_xy_mm=center,
                          offset_from_anchor_in=offsets, grid_residual_mm=residual,
                          distance_to_finished_edges_mm=edges,
                          head_recess_below_plate_mm=box.ZMax-head.BoundBox.ZMax,
                          machined_cylinders=list(cylinders.values())))
    anchors = [h for h in holes if math.dist(h['center_xy_mm'], target)<1.e-6]
    if len(anchors) != 1:
        errors.append('Exactly one hole must match the required finished-edge or authorized relocated anchor')
    centers = [h['center_xy_mm'] for h in holes]
    if len({tuple(round(v,6) for v in c) for c in centers}) != 4:
        errors.append('Platform fixing hole centres must be distinct')
    complete_axes = {}
    for diameter, label in ((6.604, 'clearance bore'), (14.2875, 'counterbore')):
        axes = [c['center_xy_mm'] for c in cylinder_inventory
                if round(c['diameter_mm'], 5) == diameter
                and abs(c['angular_span']-2*math.pi)<1.e-5]
        complete_axes[label] = axes
        if (len(axes) != 4 or
                any(sum(math.dist(c, a)<1.e-5 for a in axes) != 1 for c in centers) or
                any(sum(math.dist(c, a)<1.e-5 for c in centers) != 1 for a in axes)):
            errors.append('Whole plate must contain exactly four complete diameter %g %ss '
                          'matching the four mounting features' % (diameter, label))
    expected = info.get('mount_holes_mm', [])
    if len(expected) != 4 or any(not any(math.dist(c, e)<1.e-6 for c in centers) for e in expected):
        errors.append('Actual mounting features do not match the source mount_holes_mm')
    return dict(schema='table_mount_grid/1', passed=not errors, errors=errors,
                pitch_mm=25.4, anchor_xy_mm=target,
                anchor_basis=('User-authorized whole-inch relocation on the unchanged Splitting plate grid'
                              if relocated is not None and info.get('mode') == 'splitting' else
                              'User-authorized integer-inch relocation on the previous grid after bottom crop'
                              if relocated is not None else 'One inch from actual right and bottom finished edges'),
                relocated_anchor=relocated,
                finished_plate_bounds_xy_mm=[box.XMin,box.YMin,box.XMax,box.YMax],
                platform_cylinder_inventory=cylinder_inventory,
                complete_clearance_bore_axes_xy_mm=complete_axes['clearance bore'],
                complete_counterbore_axes_xy_mm=complete_axes['counterbore'],
                holes=holes, installation_note=info.get('table_mount_pattern', {}).get('installation_note'),
                scope='Four actual fixing features and full bores in the machined solid; '
                      'one-inch relative grid. Optical-table edge-to-first-hole phase is not specified.')
