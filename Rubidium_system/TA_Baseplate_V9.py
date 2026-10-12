"""TA baseplate V9.9 - 14 x 21.5 in, with the TA cable at a short edge.

Beam order, read top to bottom in example_baseplate():

    TA -> two steering folds -> HWP -> isolator -> QWP
       -> six bare 8-32 conditioning stations
       -> lattice V9.7 sliding Rb cell enclosure -> folds 3 and 4
       -> power-division HWP -> main PBS
            transmitted -> AOM (integral seat) -> SR475 shutter -> fold 5
                           -> L1, L2, HWP, rotating PBS, iris, KA05T
            reflected   -> one steering fold left across the middle
                           -> L1, L2, HWP, rotating PBS, KA05T (no iris)

The TA emits right and its thick cable exits the upper short edge. The common
conditioning train runs left, down, then right through the sliding cell.
The AOM output runs down the left edge; the direct output runs left above it.
All optical segments remain orthogonal, and the conditioning and telescope
spacings are preserved. Coordinates are in the board frame.

Positions are millimetres; z = 0 is the 12.7 mm optical
axis. See Production/TABoardV9/ for the renders and the audit report.

Run in FreeCAD (Macro > Macros..., or paste into the Python console):
    example_baseplate()
"""
import math

import FreeCAD as App
import Part

from PyOpticL import layout, optomech

# baseplate constants
base_dx = 14*layout.inch
base_dy = 21.5*layout.inch
base_dz = layout.inch
gap = layout.inch/8

# Table mount grid indices: hole centres are (index + 0.5) inches.
mount_holes = [(0, 1), (13, 0), (0, 20), (9, 20)]


def board_xy(px, py):
    """Board-frame coordinate pair (shared by placement and audit metadata)."""
    return px, py


def board_direction(dx, dy):
    return dx, dy

# --- common path: lattice ordering and conditioning pitches -----------------
TA_XY = (105., 491.)
TA_FOLD1_XY = (327., 491.)
TA_FOLD2_XY = (327., 418.)
TA_HWP_XY = (305., 418.)
ISO_XY = (235., 418.)
QWP_XY = (171., 418.)
STATIONS_XY = ((150., 418.), (105., 418.), (60., 418.),
               (32., 396.), (48., 352.), (88., 352.))
COMMON_FOLD1_XY = (32., 418.)
COMMON_FOLD2_XY = (32., 352.)
CELL_XY = (189., 352.)
COMMON_FOLD3_XY = (327., 352.)
COMMON_FOLD4_XY = (327., 250.)
POWER_HWP_XY = (312., 250.)
PBS_XY = (280.6, 250.)

# --- the two output branches ------------------------------------------------
AOM_XY = (213.6, 250.)
SHUTTER_XY = (116.6, 250.)
AOM_FOLD_XY = (40., 250.)
DIRECT_FOLD_XY = (280.6, 305.5)

# output-chain offsets from each row's fold mirror (the lattice DP-output chain)
OUT = {'lens1': 14., 'lens2': 14.+45.319348, 'hwp': 72., 'rot': 94., 'iris': 125.,
       'fiber_face': 167.35, 'port': 186.15}
# the reflected branch has no iris, so its fiber face sits 50 mm behind the
# rotating PBS: 40 mm front access plus the RSP05 body (7.25 mm) and 2.75 mm
OUT_NO_IRIS = {'lens1': 14., 'lens2': 14.+45.319348, 'hwp': 72., 'rot': 94.,
               'fiber_face': 144., 'port': 144.+18.798}
REAR_CLAMP_OFFSET = 54.              # direct head: clear the shutter and bottom fold
AOM_REAR_CLAMP_OFFSET = 46.          # full 60 x 20 envelope remains on the plate

LENSES = {
    'LA1289-B': (29.9, 3.2, 1.8, 30.2466184),
    'LA1540-B': (14.9, 5.1, 1.8, 15.0727296),
}
RED = (.85, .15, .1)
BLUE = (.1, .35, .95)
GREEN = (.05, .6, .3)
UPSTREAM = 'Assumed upstream clearance radius 2.5 mm; TA measured q/M2 not supplied.'
DOWNSTREAM = 'Nominal conditioned beam envelope, not a measured Gaussian mode or RF trace.'
STATION_NOTE = ('Bare 8-32 hole (station %d of 6); holder and optic not yet selected. '
                'The audit reserves a 10 mm round envelope at the hole and checks a 16 mm '
                'along-beam holder footprint.')


def example_baseplate(x=0, y=0, angle=0, drill=True, cell_slide=0.):
    """Build the TA board."""
    if App.ActiveDocument is None:
        App.newDocument('TA_Board_V9')
    doc = App.ActiveDocument

    baseplate = layout.baseplate(base_dx, base_dy, base_dz, x=x, y=y, angle=angle, gap=gap,
                                 drill=False, mount_holes=mount_holes,
                                 name='TA plate V9.9 14 x 21.5 in')
    plate = doc.getObject(baseplate.active_baseplate)
    info = {'mode': 'ta', 'plate': plate, 'roots': {}, 'paths': [], 'arms': [],
            'reservations': [], 'extra_cuts': [], 'geometry_assertions': [], 'alternate': False,
            'service_regions': [], 'output_optical_routes': [],
            'requirements': {'mirror_roles': [], 'spherical_groups': []},
            'isolator': None, 'cell': None,
            'layout_status': 'V9.9 short-edge cable layout; see the saved audit report for results.',
            'mount_holes_mm': [[(hx+.5)*layout.inch, (hy+.5)*layout.inch] for hx, hy in mount_holes]}

    # ---- placement helpers, so every optic below is a single readable line ----
    def put(name, cls, px, py, pangle=0, **kw):
        bx, by = board_xy(px, py)
        obj = baseplate.place_element(name, cls, x=bx, y=by, angle=pangle, **kw)
        info['roots'][name] = obj
        return obj

    def mirror(name, px, py, pangle):
        return put(name, optomech.circular_mirror_union_optic, px, py, pangle, thickness=6,
                   mount_type=optomech.mirror_mount_M05, mount_args={'thumbscrews': True})

    def bend(name, a, p, b):
        """A 45-degree M05 fold at p, turning the beam a->p onto p->b."""
        u = (p[0]-a[0], p[1]-a[1])
        v = (b[0]-p[0], b[1]-p[1])
        du = math.hypot(*u)
        dv = math.hypot(*v)
        n = (v[0]/dv - u[0]/du, v[1]/dv - u[1]/du)
        return mirror(name, p[0], p[1], math.degrees(math.atan2(n[1], n[0])))

    def wp(name, px, py, pangle=0):
        return put(name, optomech.waveplate, px, py, pangle,
                   mount_type=optomech.rotation_stage_rsp05)

    def lens(name, part, px, py, pangle=180):
        f, tc, te, f795 = LENSES[part]
        obj = put(name, optomech.circular_lens, px, py, pangle, focal_length=f, thickness=tc,
                  diameter=12.7, part_number=part,
                  mount_type=optomech.lens_holder_l05g_no_pin_slots)
        for key, value in (('CatalogEFL', f), ('EstimatedEFL795', f795),
                           ('CenterThickness', tc), ('EdgeThickness', te)):
            obj.addProperty('App::PropertyLength', key, 'Lens specification')
            setattr(obj, key, value)
        obj.addProperty('App::PropertyString', 'LensOrientation', 'Lens specification')
        obj.LensOrientation = ('Holder angle is independent of glass orientation. '
                               'CAD is envelope only.')
        return obj

    def hole(name, px, py, purpose):
        obj = put(name, optomech.BareTappedHole, px, py)
        obj.Purpose = purpose
        info['extra_cuts'].append(obj)
        info['reservations'].append({'object': obj.Name, 'reason': purpose})
        return obj

    def fiber(name, px, py, pangle, rear=REAR_CLAMP_OFFSET):
        return put(name, optomech.fiberport_mount_KA05T_holes, px, py, pangle,
                   rear_hole_x_offset=rear, mount_args={'thumbscrews': True})

    def rotating_pbs(name, px, py, pangle):
        obj = put(name, optomech.rotation_stage_rsp05, px, py, pangle)
        obj.addProperty('App::PropertyString', 'Purpose').Purpose = (
            'Empty RSP05: user bonds PBS to rotating front face; no PBS or waveplate modeled.')
        return obj

    def path(name, points, color, envelope, assumption):
        points = [board_xy(*p) for p in points]
        obj = doc.addObject('Part::Feature', name)
        obj.Label = name + ' (nominal axis)'
        obj.Shape = Part.makePolygon([App.Vector(px, py, 0) for px, py in points])
        obj.ViewObject.LineColor = color
        obj.ViewObject.LineWidth = 2.5
        obj.addProperty('App::PropertyString', 'Scope').Scope = assumption
        obj.addProperty('App::PropertyBool', 'Bidirectional').Bidirectional = False
        if isinstance(envelope, (float, int)):
            envelope = [envelope]*len(points)
        info['paths'].append({'name': name, 'points': [tuple(map(float, p)) for p in points],
                              'object': obj.Name, 'envelope': envelope, 'assumption': assumption})
        return obj

    def service(name, kind, owner, origin_xy, direction_xy, length, width, allowed=(), assumptions=()):
        origin_xy = board_xy(*origin_xy)
        direction_xy = board_direction(*direction_xy)
        info['service_regions'].append({
            'name': name, 'kind': kind, 'owner': owner.Name if hasattr(owner, 'Name') else owner,
            'origin_xy_mm': [float(origin_xy[0]), float(origin_xy[1])],
            'direction_xy': [float(direction_xy[0]), float(direction_xy[1])],
            'length_mm': float(length), 'width_mm': float(width),
            'allowed_paths': list(allowed), 'dimensions_verified': False,
            'assumptions': list(assumptions)})

    def assert_distance(name, a, b, expected, tol=1e-6):
        def as_xy(o):
            if hasattr(o, 'BasePlacement'):
                return (o.BasePlacement.Base.x, o.BasePlacement.Base.y)
            return board_xy(float(o[0]), float(o[1]))
        pa, pb = as_xy(a), as_xy(b)
        info['geometry_assertions'].append(
            {'name': name, 'measured': math.hypot(pa[0]-pb[0], pa[1]-pb[1]),
             'expected': float(expected), 'tolerance': tol})

    # =========================================================================
    # 1. TA, the two steering folds and the isolator lane
    # =========================================================================
    # The TA emits +x; its thick cable points +y through the upper short edge.
    ta = put('TA', optomech.TA_butterfly_on_adapter, *TA_XY, 0)
    supply = [TA_XY, TA_FOLD1_XY, TA_FOLD2_XY, STATIONS_XY[0]]
    bend('TA steering fold 1', supply[0], supply[1], supply[2])
    bend('TA steering fold 2', supply[1], supply[2], supply[3])
    wp('TA output HWP', *TA_HWP_XY, 0)
    isolator = put('Hana long isolator', optomech.isolator_850_long_pocket, *ISO_XY, 0)
    info['extra_cuts'].append(isolator)
    wp('TA output QWP', *QWP_XY, 0)

    # =========================================================================
    # 2. Six bare conditioning stations (holders and optics not yet selected)
    # =========================================================================
    lane_stations = [hole('Common station 8-32 '+str(i+1), *STATIONS_XY[i], STATION_NOTE % (i+1))
                     for i in range(3)]
    sphere_stations = [hole('Common station 8-32 '+str(i+1), *STATIONS_XY[i], STATION_NOTE % (i+1))
                       for i in range(3, 6)]

    # =========================================================================
    # 3. Folds 1-4, the cell seat, and up the column to the power PBS
    # =========================================================================
    route = [STATIONS_XY[2], COMMON_FOLD1_XY, COMMON_FOLD2_XY,
             COMMON_FOLD3_XY, COMMON_FOLD4_XY, POWER_HWP_XY]
    fold1 = bend('Common post-isolator fold 1', route[0], route[1], route[2])
    fold2 = bend('Common post-isolator fold 2', route[1], route[2], route[3])
    fold3 = bend('Common post-isolator fold 3', route[2], route[3], route[4])
    fold4 = bend('Common post-isolator fold 4', route[3], route[4], route[5])

    # Exactly the lattice V9.7 lower half, lid, covers, glass and sliding seat.
    cell = optomech.place_sliding_cell(baseplate, *CELL_XY, angle=0, slide=cell_slide)
    info['cell'] = dict(cell)
    info['roots']['Rb cell seat (V9.7 pocket + 2 slot taps)'] = cell['root']
    info['roots']['Rb cell enclosure (V9.7 lower half, lid, covers, cell)'] = cell['cell']
    info['extra_cuts'].extend(o for o in cell['objects'] if hasattr(o, 'DrillPart'))
    info['isolator'] = {'source': 'hana-branch original isolator_850',
                        'main_pocket_mm': [113.5, 25., 5.]}

    wp('Main power division HWP', *POWER_HWP_XY, 180)
    # Incoming -x; inversion makes the reflected branch point +y.
    main_pbs = put('Main power PBS', optomech.cube_splitter, *PBS_XY, 180,
                   invert=True, mount_type=optomech.cube_mount_halfinch)
    info['roots']['Main power PBS'] = main_pbs

    # =========================================================================
    # 4. Transmitted arm: AOM, shutter, fold 5 down to the output row
    # =========================================================================
    # The beam travels -x, with the KM100PM downstream and RF elbow toward -y.
    aom = put('TA AOMO 3100-125', optomech.AOMO_3100_125, *AOM_XY, 0,
              forward_direction=-1, backward_direction=1, diffraction_angle=0,
              surface_adapter_args={'adapter_height': 5})
    seat = optomech.integrate_aom(baseplate, aom)
    info['extra_cuts'].append(seat)
    put('SRS SR475 shutter', optomech.shutter_sr475, *SHUTTER_XY, 0)
    fold5 = bend('AOM branch output steering mirror', SHUTTER_XY, AOM_FOLD_XY,
                 (AOM_FOLD_XY[0], AOM_FOLD_XY[1]-OUT['lens1']))

    # =========================================================================
    # 5. Reflected arm: one fold left above the AOM row
    # =========================================================================
    # The direct fiber exits at the left; the AOM fiber exits at the bottom.
    fold6 = bend('Reflected branch fold 6', PBS_XY, DIRECT_FOLD_XY,
                 (DIRECT_FOLD_XY[0]-OUT_NO_IRIS['lens1'], DIRECT_FOLD_XY[1]))

    # =========================================================================
    # 6. The two output chains (the lattice DP-output geometry)
    # =========================================================================
    rows = []
    for tag, x0, row_y, with_iris, theta in (
            ('AOM branch', *AOM_FOLD_XY, True, -90),
            ('Reflected branch', *DIRECT_FOLD_XY, False, 180)):
        O = OUT if with_iris else OUT_NO_IRIS
        ux, uy = round(math.cos(math.radians(theta))), round(math.sin(math.radians(theta)))
        def at(key):
            return (x0+ux*O[key], row_y+uy*O[key])
        l1 = lens(tag+' output first LA1289-B', 'LA1289-B', *at('lens1'), 180+theta)
        l2 = lens(tag+' output second LA1540-B', 'LA1540-B', *at('lens2'), theta)
        wp(tag+' output HWP', *at('hwp'), theta)
        rotating_pbs(tag+' empty rotating PBS RSP05', *at('rot'), theta)
        if with_iris:
            # body on the rotating-PBS side, as on the lattice DP1 row
            put(tag+' output filtering iris', optomech.pinhole_ida12, *at('iris'), 180+theta)
        head = fiber(tag+' output KA05T', *at('port'), 180+theta,
                     rear=AOM_REAR_CLAMP_OFFSET if with_iris else REAR_CLAMP_OFFSET)
        rows.append(dict(tag=tag, x0=x0, row_y=row_y, head=head, l1=l1, l2=l2, O=O,
                         with_iris=with_iris, xy={key:at(key) for key in O}))

    # =========================================================================
    # 7. Nominal beam paths
    # =========================================================================
    path('TA supply', supply, RED, 2.5, UPSTREAM)
    path('Common cylindrical conditioning provision',
         [STATIONS_XY[0], STATIONS_XY[1], STATIONS_XY[2], COMMON_FOLD1_XY,
          STATIONS_XY[3], COMMON_FOLD2_XY, STATIONS_XY[4]],
         RED, [2.5, .9, .9, .9, .9, .9, .9],
         'Stations 1-4 are bare 8-32 holes; optics unselected. The envelope is the intended '
         'conditioned beam.')
    path('Common spherical telescope',
         [STATIONS_XY[4], STATIONS_XY[5], CELL_XY, COMMON_FOLD3_XY,
          COMMON_FOLD4_XY, POWER_HWP_XY, PBS_XY],
         RED, [.9, .6, .6, .6, .6, .6, .6],
         'Stations 5/6 are bare 8-32 holes; optics unselected. ' + DOWNSTREAM)
    path('AOM branch',
         [PBS_XY, AOM_XY, SHUTTER_XY, AOM_FOLD_XY,
          rows[0]['xy']['lens1'], rows[0]['xy']['lens2'], rows[0]['xy']['fiber_face']],
         BLUE, [.6, .6, .6, .6, .6, .035, .6],
         'Single-pass AOM; the first order is modeled straight (RF deflection ~1 deg absorbed '
         'by fold 5). ' + DOWNSTREAM)
    path('Reflected branch',
         [PBS_XY, DIRECT_FOLD_XY, rows[1]['xy']['lens1'],
          rows[1]['xy']['lens2'], rows[1]['xy']['fiber_face']],
         GREEN, [.6, .6, .6, .035, .6], DOWNSTREAM)

    # =========================================================================
    # 8. Bookkeeping consumed by the audit scripts (no geometry below this line)
    # =========================================================================
    beam_dir = {1: (-1., 0.), 2: (-1., 0.), 3: (-1., 0.),
                4: (0., -1.), 5: (1., 0.), 6: (1., 0.)}
    info['requirements']['mount_only_cylindrical_holes'] = [o.Name for o in lane_stations]
    info['requirements']['provisional_bare_mount_envelopes'] = [
        {'object': o.Name, 'center_xy_mm': [o.BasePlacement.Base.x, o.BasePlacement.Base.y],
         'diameter_mm': 10.0, 'beam_direction_xy': list(board_direction(*beam_dir[i+1]))}
        for i, o in enumerate([*lane_stations, *sphere_stations])]
    info['requirements']['spherical_groups'].append(
        {'name': 'common', 'active_lenses': [], 'spare_holes': [o.Name for o in sphere_stations],
         'stations_only': True, 'spare_required': 3})

    for row in rows:
        tag, x0, row_y, O = row['tag'], row['x0'], row['row_y'], row['O']
        info['requirements']['spherical_groups'].append(
            {'name': tag+' output', 'active_lenses': [row['l1'].Name, row['l2'].Name],
             'spare_holes': [], 'spare_required': 0})
        if row['with_iris']:
            events = [{'type': 'aom', 'name': 'AOM (single pass)', 'xy': AOM_XY},
                      {'type': 'mirror', 'name': fold5.Label, 'xy': AOM_FOLD_XY}]
        else:
            events = [{'type': 'pbs', 'name': main_pbs.Label, 'xy': PBS_XY},
                      {'type': 'mirror', 'name': fold6.Label, 'xy': DIRECT_FOLD_XY}]
        events += [{'type': 'lens', 'name': row['l1'].Label, 'xy': row['xy']['lens1'], 'focal_mm': 30.2466184},
                   {'type': 'lens', 'name': row['l2'].Label, 'xy': row['xy']['lens2'], 'focal_mm': 15.0727296},
                   {'type': 'hwp', 'name': tag+' output HWP', 'xy': row['xy']['hwp']},
                   {'type': 'pbs', 'name': tag+' empty rotating PBS RSP05', 'xy': row['xy']['rot']}]
        if row['with_iris']:
            events.append({'type': 'iris', 'name': tag+' output filtering iris', 'xy': row['xy']['iris']})
        events.append({'type': 'fiber', 'name': row['head'].Label, 'xy': row['xy']['fiber_face']})
        for event in events:
            event['xy'] = board_xy(*event['xy'])
        info['output_optical_routes'].append({'arm': 1 if row['with_iris'] else 2, 'events': events})
        assert_distance(tag+': L1 -> L2 = f1 + f2 (795 nm)', row['l1'], row['l2'], 45.319348)
        assert_distance(tag+': rotating PBS -> fiber face', row['xy']['rot'],
                        row['xy']['fiber_face'], O['fiber_face']-O['rot'])
        if row['with_iris']:
            assert_distance(tag+': rotating PBS -> iris (>= 20 required)', row['xy']['rot'],
                            row['xy']['iris'], 31.)
            assert_distance(tag+': iris -> fiber face (>= 40 required)', row['xy']['iris'],
                            row['xy']['fiber_face'], 42.35)
        # front access in front of each head, as on the lattice heads
        # In board coordinates the fronts face +y (AOM) and +x (direct).
        design_direction = (0., 1.) if row['with_iris'] else (1., 0.)
        service(row['head'].Label+' front access', 'fiber_front', row['head'],
                row['xy']['fiber_face'], design_direction, 40., 20.,
                allowed=[tag], assumptions=['20 mm full front access width; 40 mm axial access.'])

    cable_origin = ta.BasePlacement.multVec(App.Vector(-29.925, 50.155613, 0))
    cable_direction = ta.BasePlacement.Rotation.multVec(App.Vector(0, 1, 0))
    service('TA thick short-edge cable', 'ta_cable', ta,
            (cable_origin.x, cable_origin.y), (cable_direction.x, cable_direction.y), 101.6, 96.25,
            assumptions=['Conservative TA full body-width cable projection; connector dimensions '
                         'unverified. The 101.6 mm corridor extends beyond the upper short edge.'])
    # the RF SMB elbow: 40 mm outward from the connector face, which is the
    # body face away from the beam (33.02 mm from the axis on the mount side)
    service(aom.Label+' RF elbow', 'aom_sma', aom, (AOM_XY[0], AOM_XY[1]-33.02), (0., -1.), 40., 20.,
            assumptions=['Connector on the AOM face away from the beam (unverified STL box); '
                         '40 mm of free space for the L-shaped SMB elbow; cable taped down afterwards.'])
    info.setdefault('service_clearance', {}).setdefault('min_length_mm', {})['aom_sma'] = 40.

    info['pbs_path_specs'] = [{'role': 'main', 'cube': main_pbs.Label,
                               'incoming_path': 'Common spherical telescope',
                               'outgoing_paths': ['AOM branch', 'Reflected branch']}]
    info['arms'].append({'id': 1, 'aom': aom.Name, 'lens': None, 'retro': None,
                         'integral_seat': seat.Name, 'single_pass': True, 'beam_path': 'AOM branch'})
    info['output_order_expected_routes'] = 2
    info['expected_arm_count'] = 1
    info['routes_without_iris'] = [2]
    info['fiber_clearance'] = {'rear_offsets_mm': [AOM_REAR_CLAMP_OFFSET, REAR_CLAMP_OFFSET]}
    info['requirements']['mirror_roles'].append({'arm': 1, 'input': fold4.Name, 'output': fold5.Name})
    info['requirements']['single_steering_mirror_routes'] = [{'arm': 2, 'mirror': fold6.Name}]

    def along_beam(a, b, corner):
        return abs(corner[0]-a[0])+abs(corner[1]-a[1])+abs(b[0]-corner[0])+abs(b[1]-corner[1])

    station_4 = STATIONS_XY[3]
    info['geometry_assertions'].extend([
        {'name': 'Stations 1-2 pitch', 'measured': STATIONS_XY[0][0]-STATIONS_XY[1][0],
         'expected': 45., 'tolerance': 1e-9},
        {'name': 'Stations 2-3 pitch', 'measured': STATIONS_XY[1][0]-STATIONS_XY[2][0],
         'expected': 45., 'tolerance': 1e-9},
        {'name': 'Station 4->5 along beam via fold 2',
         'measured': along_beam(station_4, STATIONS_XY[4], COMMON_FOLD2_XY),
         'expected': 60., 'tolerance': 1e-9},
        {'name': 'Station 4->6 along beam via fold 2',
         'measured': along_beam(station_4, STATIONS_XY[5], COMMON_FOLD2_XY),
         'expected': 100., 'tolerance': 1e-9},
        {'name': 'Direct branch has one steering mirror',
         'measured': sum(e['type'] == 'mirror' for e in info['output_optical_routes'][1]['events']),
         'expected': 1, 'tolerance': 0.},
        {'name': 'Reflected KA05T rear-hole axis to left plate edge (mm)',
         'measured': DIRECT_FOLD_XY[0]-OUT_NO_IRIS['port']-REAR_CLAMP_OFFSET-gap,
         'expected': 60.627, 'tolerance': 0.1},
        {'name': 'AOM-branch KA05T rear-hole axis to bottom plate edge (mm)',
         'measured': AOM_FOLD_XY[1]-OUT['port']-AOM_REAR_CLAMP_OFFSET-gap,
         'expected': 14.675, 'tolerance': 0.1},
        {'name': 'RF elbow space beyond connector face (mm)', 'measured': 40.,
         'expected': 40., 'tolerance': 0.}])
    assert_distance('HWP -> PBS (lattice 31.4)', POWER_HWP_XY, main_pbs, 31.4)
    assert_distance('PBS -> AOM (nominal axis)', main_pbs, AOM_XY, 67.)
    assert_distance('Cell -> fold 3', CELL_XY, COMMON_FOLD3_XY, 138.)

    # ---- cut the plate once every element and machining volume is in place ----
    doc.recompute()
    layout.redraw()
    plate.Drill = drill
    plate.touch()
    doc.recompute()
    info['plate_size_mm'] = [base_dx, base_dy, base_dz]
    doc.Label = 'TA board - V9.9 short-edge cable'
    return info


if __name__ == "__main__":
    example_baseplate()
    layout.redraw()
