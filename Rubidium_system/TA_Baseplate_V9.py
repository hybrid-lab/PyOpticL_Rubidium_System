"""TA baseplate V9 - 25 x 14 in, the seed board for the 795 nm lattice light.

Beam order, read top to bottom in example_baseplate():

    TA -> two steering folds -> HWP -> isolator -> QWP
       -> six bare 8-32 conditioning stations
       -> Rb vapour cell seat (pocket only) -> folds 3 and 4
       -> power-division HWP -> main PBS
            transmitted -> AOM (integral seat) -> SR475 shutter -> fold 5
                           -> L1, L2, HWP, rotating PBS, iris, KA05T
            reflected   -> folds 6 and 7 out to the short edge
                           -> L1, L2, HWP, rotating PBS, KA05T (no iris)

The TA section, the isolator lane, the six stations and folds 1-2 sit at the
same coordinates as on the lattice board, so "same function -> same hardware
and same spacing" holds across the two boards. The lattice plate was
compressed to 24 in in V9.2; this board keeps the earlier 90 mm TA-to-lane
spacing, which its own 25 in width allows.

Positions are millimetres in the board frame; z = 0 is the 12.7 mm optical
axis. See Production/TABoardV9/ for the renders and the audit report.

Run in FreeCAD (Macro > Macros..., or paste into the Python console):
    example_baseplate()
"""
import math

import FreeCAD as App
import Part

from PyOpticL import layout, optomech

# baseplate constants
base_dx = 25*layout.inch
base_dy = 14*layout.inch
base_dz = layout.inch
gap = layout.inch/8

# x-y coordinates of the table mount holes (in inches) - Hana's TA V2 pattern
mount_holes = [(0, 0), (0, 10), (15, 0), (17, 10)]

# --- common path (same geometry as the lattice board) ------------------------
TOP_RUN_Y = 338.
TA_XY = (60., 140.)
LANE_X = 150.                        # 90 mm right of the TA beam
CELL_X = 216.
TA_HWP_Y = 315.
ISO_Y = 245.
QWP_Y = 181.
LOWER_RUN_Y = 42.
STATION_LANE_Y = (160., 115., 70.)
STATION_4_DX = 22.
STATION_5_Y = 58.
STATION_6_Y = 98.
CELL_Y = 199.
FOLD3_Y = 262.4                      # fold 3 mount sits 3 mm above the cell pocket

# --- the column and the two output rows --------------------------------------
# COLUMN_X: the cell pocket reaches x <= 247; 3 mm + 33 mm AOM half body +
# 40 mm RF elbow = 323 at the cell's height. At the AOM's height only station
# 6 is on that side, so 304 keeps the 40 mm elbow space free.
COLUMN_X = 304.
COLUMN_HWP_Y = FOLD3_Y - 25.         # 237.4
PBS_Y = COLUMN_HWP_Y - 31.4          # 206.0, the lattice HWP -> PBS spacing
AOM_Y = PBS_Y - 85.                  # 121.0: the KM100PM sits upstream of the AOM
SHUTTER_Y = AOM_Y - 40.67            # 80.33: shutter top 2 mm below the AOM adapter
AOM_ROW_Y = SHUTTER_Y - 31.          # 49.33
REFLECT_FOLD_X = COLUMN_X + 62.      # 366: fold 7's M05 body clears the KM100PM
REFLECT_ROW_Y = AOM_ROW_Y + 85.      # 134.33

# output-chain offsets from each row's fold mirror (the lattice DP-output chain)
OUT = {'lens1': 14., 'lens2': 14.+45.319348, 'hwp': 72., 'rot': 94., 'iris': 125.,
       'fiber_face': 167.35, 'port': 186.15}
# the reflected branch has no iris, so its fiber face sits 50 mm behind the
# rotating PBS: 40 mm front access plus the RSP05 body (7.25 mm) and 2.75 mm
OUT_NO_IRIS = {'lens1': 14., 'lens2': 14.+45.319348, 'hwp': 72., 'rot': 94.,
               'fiber_face': 144., 'port': 144.+18.798}
REAR_CLAMP_OFFSET = 82.7             # KA05T rear tail-clamp pair behind each head

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


def example_baseplate(x=0, y=0, angle=0, drill=True):
    """Build the TA board."""
    if App.ActiveDocument is None:
        App.newDocument('TA_Board_V9')
    doc = App.ActiveDocument

    baseplate = layout.baseplate(base_dx, base_dy, base_dz, x=x, y=y, angle=angle, gap=gap,
                                 drill=False, mount_holes=mount_holes,
                                 name='TA plate 25 x 14 in')
    plate = doc.getObject(baseplate.active_baseplate)
    info = {'mode': 'ta', 'plate': plate, 'roots': {}, 'paths': [], 'arms': [],
            'reservations': [], 'extra_cuts': [], 'geometry_assertions': [], 'alternate': False,
            'service_regions': [], 'output_optical_routes': [],
            'requirements': {'mirror_roles': [], 'spherical_groups': []},
            'isolator': None, 'cell': None,
            'layout_status': 'V9 TA board; see the saved audit report for results.',
            'mount_holes_mm': [[(hx+.5)*layout.inch, (hy+.5)*layout.inch] for hx, hy in mount_holes]}

    # ---- placement helpers, so every optic below is a single readable line ----
    def put(name, cls, px, py, pangle=0, **kw):
        obj = baseplate.place_element(name, cls, x=px, y=py, angle=pangle, **kw)
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

    def fiber(name, px, py, pangle):
        return put(name, optomech.fiberport_mount_KA05T_holes, px, py, pangle,
                   rear_hole_x_offset=REAR_CLAMP_OFFSET, mount_args={'thumbscrews': True})

    def rotating_pbs(name, px, py, pangle):
        obj = put(name, optomech.rotation_stage_rsp05, px, py, pangle)
        obj.addProperty('App::PropertyString', 'Purpose').Purpose = (
            'Empty RSP05: user bonds PBS to rotating front face; no PBS or waveplate modeled.')
        return obj

    def path(name, points, color, envelope, assumption):
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
            return (float(o[0]), float(o[1]))
        pa, pb = as_xy(a), as_xy(b)
        info['geometry_assertions'].append(
            {'name': name, 'measured': math.hypot(pa[0]-pb[0], pa[1]-pb[1]),
             'expected': float(expected), 'tolerance': tol})

    # =========================================================================
    # 1. TA, the two steering folds and the isolator lane
    # =========================================================================
    # The TA emits +y with its thick cable on the -x side, off the plate, as on
    # the lattice board; the U is therefore traversed up, right, then down.
    ta = put('TA', optomech.TA_butterfly, TA_XY[0], TA_XY[1], 90)
    supply = [TA_XY, (TA_XY[0], TOP_RUN_Y), (LANE_X, TOP_RUN_Y), (LANE_X, STATION_LANE_Y[0])]
    bend('TA steering fold 1', supply[0], supply[1], supply[2])
    bend('TA steering fold 2', supply[1], supply[2], supply[3])
    wp('TA output HWP', LANE_X, TA_HWP_Y, 90)
    isolator = put('Hana long isolator', optomech.isolator_850_long_pocket, LANE_X, ISO_Y, 90)
    info['extra_cuts'].append(isolator)
    wp('TA output QWP', LANE_X, QWP_Y, 90)

    # =========================================================================
    # 2. Six bare conditioning stations (holders and optics not yet selected)
    # =========================================================================
    lane_stations = [hole('Common station 8-32 1', LANE_X, STATION_LANE_Y[0], STATION_NOTE % 1),
                     hole('Common station 8-32 2', LANE_X, STATION_LANE_Y[1], STATION_NOTE % 2),
                     hole('Common station 8-32 3', LANE_X, STATION_LANE_Y[2], STATION_NOTE % 3)]
    sphere_stations = [hole('Common station 8-32 4', LANE_X+STATION_4_DX, LOWER_RUN_Y, STATION_NOTE % 4),
                       hole('Common station 8-32 5', CELL_X, STATION_5_Y, STATION_NOTE % 5),
                       hole('Common station 8-32 6', CELL_X, STATION_6_Y, STATION_NOTE % 6)]

    # =========================================================================
    # 3. Folds 1-4, the cell seat, and up the column to the power PBS
    # =========================================================================
    route = [(LANE_X, STATION_LANE_Y[-1]), (LANE_X, LOWER_RUN_Y), (CELL_X, LOWER_RUN_Y),
             (CELL_X, FOLD3_Y), (COLUMN_X, FOLD3_Y), (COLUMN_X, COLUMN_HWP_Y)]
    fold1 = bend('Common post-isolator fold 1', route[0], route[1], route[2])
    fold2 = bend('Common post-isolator fold 2', route[1], route[2], route[3])
    fold3 = bend('Common post-isolator fold 3', route[2], route[3], route[4])
    fold4 = bend('Common post-isolator fold 4', route[3], route[4], route[5])

    # As on the lattice board: no holder or enclosure is installed, only the
    # 3/4 in deep, beam-centred 104 x 56 mm pocket and its four corner taps.
    cell = optomech.place_cell_pocket(baseplate, CELL_X, CELL_Y, angle=90)
    info['cell'] = dict(cell, cell=cell['root'])
    info['roots']['Rb cell seat (pocket only)'] = cell['root']
    info['extra_cuts'].extend(o for o in cell['objects'] if hasattr(o, 'DrillPart'))
    info['isolator'] = {'source': 'hana-branch original isolator_850',
                        'main_pocket_mm': [113.5, 25., 5.]}

    wp('Main power division HWP', COLUMN_X, COLUMN_HWP_Y, -90)
    # beam travels -y into the cube, reflected toward +x; mount across the beam
    main_pbs = put('Main power PBS', optomech.cube_splitter, COLUMN_X, PBS_Y, -90,
                   invert=False, mount_type=optomech.cube_mount_halfinch)
    info['roots']['Main power PBS'] = main_pbs

    # =========================================================================
    # 4. Transmitted arm: AOM, shutter, fold 5 down to the output row
    # =========================================================================
    # In the column the AOM is turned so its RF SMB connector faces -x, toward
    # the cell lane, where 40 mm is reserved for the L-shaped elbow.
    aom = put('TA AOMO 3100-125', optomech.AOMO_3100_125, COLUMN_X, AOM_Y, -90,
              forward_direction=-1, backward_direction=1, diffraction_angle=0,
              surface_adapter_args={'adapter_height': 5})
    seat = optomech.integrate_aom(baseplate, aom)
    info['extra_cuts'].append(seat)
    put('SRS SR475 shutter', optomech.shutter_sr475, COLUMN_X, SHUTTER_Y, 90)
    fold5 = bend('AOM branch output steering mirror', (COLUMN_X, SHUTTER_Y), (COLUMN_X, AOM_ROW_Y),
                 (COLUMN_X+OUT['lens1'], AOM_ROW_Y))

    # =========================================================================
    # 5. Reflected arm: two folds out to the short edge
    # =========================================================================
    # Two folds are needed because the fiber must leave from the short (right)
    # edge; a single fold would send the chain to the long edge.
    fold6 = bend('Reflected branch fold 6', (COLUMN_X, PBS_Y), (REFLECT_FOLD_X, PBS_Y),
                 (REFLECT_FOLD_X, REFLECT_ROW_Y))
    fold7 = bend('Reflected branch output steering mirror', (REFLECT_FOLD_X, PBS_Y),
                 (REFLECT_FOLD_X, REFLECT_ROW_Y), (REFLECT_FOLD_X+OUT['lens1'], REFLECT_ROW_Y))

    # =========================================================================
    # 6. The two output chains (the lattice DP-output geometry)
    # =========================================================================
    rows = []
    for tag, x0, row_y, with_iris in (('AOM branch', COLUMN_X, AOM_ROW_Y, True),
                                      ('Reflected branch', REFLECT_FOLD_X, REFLECT_ROW_Y, False)):
        O = OUT if with_iris else OUT_NO_IRIS
        l1 = lens(tag+' output first LA1289-B', 'LA1289-B', x0+O['lens1'], row_y, 180)
        l2 = lens(tag+' output second LA1540-B', 'LA1540-B', x0+O['lens2'], row_y, 0)
        wp(tag+' output HWP', x0+O['hwp'], row_y, 0)
        rotating_pbs(tag+' empty rotating PBS RSP05', x0+O['rot'], row_y, 0)
        if with_iris:
            # body on the rotating-PBS side, as on the lattice DP1 row
            put(tag+' output filtering iris', optomech.pinhole_ida12, x0+O['iris'], row_y, 180)
        head = fiber(tag+' output KA05T', x0+O['port'], row_y, 180)
        rows.append(dict(tag=tag, x0=x0, row_y=row_y, head=head, l1=l1, l2=l2, O=O, with_iris=with_iris))

    # =========================================================================
    # 7. Nominal beam paths
    # =========================================================================
    path('TA supply', supply, RED, 2.5, UPSTREAM)
    path('Common cylindrical conditioning provision',
         [(LANE_X, STATION_LANE_Y[0]), (LANE_X, STATION_LANE_Y[1]), (LANE_X, STATION_LANE_Y[2]),
          (LANE_X, LOWER_RUN_Y), (LANE_X+STATION_4_DX, LOWER_RUN_Y), (CELL_X, LOWER_RUN_Y),
          (CELL_X, STATION_5_Y)], RED, [2.5, .9, .9, .9, .9, .9, .9],
         'Stations 1-4 are bare 8-32 holes; optics unselected. The envelope is the intended '
         'conditioned beam.')
    path('Common spherical telescope',
         [(CELL_X, STATION_5_Y), (CELL_X, STATION_6_Y), (CELL_X, CELL_Y), (CELL_X, FOLD3_Y),
          (COLUMN_X, FOLD3_Y), (COLUMN_X, COLUMN_HWP_Y), (COLUMN_X, PBS_Y)],
         RED, [.9, .6, .6, .6, .6, .6, .6],
         'Stations 5/6 are bare 8-32 holes; optics unselected. ' + DOWNSTREAM)
    path('AOM branch',
         [(COLUMN_X, PBS_Y), (COLUMN_X, AOM_Y), (COLUMN_X, SHUTTER_Y), (COLUMN_X, AOM_ROW_Y),
          (COLUMN_X+OUT['lens1'], AOM_ROW_Y), (COLUMN_X+OUT['lens2'], AOM_ROW_Y),
          (COLUMN_X+OUT['fiber_face'], AOM_ROW_Y)], BLUE, [.6, .6, .6, .6, .6, .035, .6],
         'Single-pass AOM; the first order is modeled straight (RF deflection ~1 deg absorbed '
         'by fold 5). ' + DOWNSTREAM)
    path('Reflected branch',
         [(COLUMN_X, PBS_Y), (REFLECT_FOLD_X, PBS_Y), (REFLECT_FOLD_X, REFLECT_ROW_Y),
          (REFLECT_FOLD_X+OUT_NO_IRIS['lens1'], REFLECT_ROW_Y),
          (REFLECT_FOLD_X+OUT_NO_IRIS['lens2'], REFLECT_ROW_Y),
          (REFLECT_FOLD_X+OUT_NO_IRIS['fiber_face'], REFLECT_ROW_Y)],
         GREEN, [.6, .6, .6, .6, .035, .6], DOWNSTREAM)

    # =========================================================================
    # 8. Bookkeeping consumed by the audit scripts (no geometry below this line)
    # =========================================================================
    beam_dir = {1: (0., -1.), 2: (0., -1.), 3: (0., -1.), 4: (1., 0.), 5: (0., 1.), 6: (0., 1.)}
    info['requirements']['mount_only_cylindrical_holes'] = [o.Name for o in lane_stations]
    info['requirements']['provisional_bare_mount_envelopes'] = [
        {'object': o.Name, 'center_xy_mm': [o.BasePlacement.Base.x, o.BasePlacement.Base.y],
         'diameter_mm': 10.0, 'beam_direction_xy': list(beam_dir[i+1])}
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
            events = [{'type': 'aom', 'name': 'AOM (single pass)', 'xy': (COLUMN_X, AOM_Y)},
                      {'type': 'mirror', 'name': fold5.Label, 'xy': (COLUMN_X, AOM_ROW_Y)}]
        else:
            events = [{'type': 'pbs', 'name': main_pbs.Label, 'xy': (COLUMN_X, PBS_Y)},
                      {'type': 'mirror', 'name': fold6.Label, 'xy': (REFLECT_FOLD_X, PBS_Y)},
                      {'type': 'mirror', 'name': fold7.Label, 'xy': (REFLECT_FOLD_X, REFLECT_ROW_Y)}]
        events += [{'type': 'lens', 'name': row['l1'].Label, 'xy': (x0+O['lens1'], row_y), 'focal_mm': 30.2466184},
                   {'type': 'lens', 'name': row['l2'].Label, 'xy': (x0+O['lens2'], row_y), 'focal_mm': 15.0727296},
                   {'type': 'hwp', 'name': tag+' output HWP', 'xy': (x0+O['hwp'], row_y)},
                   {'type': 'pbs', 'name': tag+' empty rotating PBS RSP05', 'xy': (x0+O['rot'], row_y)}]
        if row['with_iris']:
            events.append({'type': 'iris', 'name': tag+' output filtering iris', 'xy': (x0+O['iris'], row_y)})
        events.append({'type': 'fiber', 'name': row['head'].Label, 'xy': (x0+O['fiber_face'], row_y)})
        info['output_optical_routes'].append({'arm': 1 if row['with_iris'] else 2, 'events': events})
        assert_distance(tag+': L1 -> L2 = f1 + f2 (795 nm)', row['l1'], row['l2'], 45.319348)
        assert_distance(tag+': rotating PBS -> fiber face', (x0+O['rot'], row_y),
                        (x0+O['fiber_face'], row_y), O['fiber_face']-O['rot'])
        if row['with_iris']:
            assert_distance(tag+': rotating PBS -> iris (>= 20 required)', (x0+O['rot'], row_y),
                            (x0+O['iris'], row_y), 31.)
            assert_distance(tag+': iris -> fiber face (>= 40 required)', (x0+O['iris'], row_y),
                            (x0+O['fiber_face'], row_y), 42.35)
        # front access in front of each head, as on the lattice heads
        direction = row['head'].BasePlacement.Rotation.multVec(App.Vector(1, 0, 0))
        origin = row['head'].BasePlacement.Base + direction*18.798
        service(row['head'].Label+' front access', 'fiber_front', row['head'],
                (origin.x, origin.y), (direction.x, direction.y), 40., 20.,
                allowed=[tag], assumptions=['20 mm full front access width; 40 mm axial access.'])

    service('TA thick bottom cable', 'ta_cable', ta, (9.844387, 110.075), (-1., 0.), 101.6, 96.25,
            assumptions=['Conservative TA full body-width cable projection; connector dimensions '
                         'unverified. The 101.6 mm corridor extends beyond the plate left edge.'])
    # the RF SMB elbow: 40 mm outward from the connector face, which is the
    # body face away from the beam (33.02 mm from the axis on the mount side)
    service(aom.Label+' RF elbow', 'aom_sma', aom, (COLUMN_X-33.02, AOM_Y), (-1., 0.), 40., 20.,
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
    info['requirements']['mirror_roles'].append({'arm': 1, 'input': fold4.Name, 'output': fold5.Name})
    info['requirements']['mirror_roles'].append({'arm': 2, 'input': fold6.Name, 'output': fold7.Name})

    def along_beam(a, b, corner):
        return abs(corner[0]-a[0])+abs(corner[1]-a[1])+abs(b[0]-corner[0])+abs(b[1]-corner[1])

    station_4 = (LANE_X+STATION_4_DX, LOWER_RUN_Y)
    info['geometry_assertions'].extend([
        {'name': 'Stations 1-2 pitch', 'measured': STATION_LANE_Y[0]-STATION_LANE_Y[1],
         'expected': 45., 'tolerance': 1e-9},
        {'name': 'Stations 2-3 pitch', 'measured': STATION_LANE_Y[1]-STATION_LANE_Y[2],
         'expected': 45., 'tolerance': 1e-9},
        {'name': 'Station 4->5 along beam via fold 2',
         'measured': along_beam(station_4, (CELL_X, STATION_5_Y), (CELL_X, LOWER_RUN_Y)),
         'expected': 60., 'tolerance': 1e-9},
        {'name': 'Station 4->6 along beam via fold 2',
         'measured': along_beam(station_4, (CELL_X, STATION_6_Y), (CELL_X, LOWER_RUN_Y)),
         'expected': 100., 'tolerance': 1e-9},
        {'name': 'Reflected KA05T rear holes inside plate (margin mm)',
         'measured': base_dx-(REFLECT_FOLD_X+OUT_NO_IRIS['port']+REAR_CLAMP_OFFSET),
         'expected': 23.5, 'tolerance': 0.1},
        {'name': 'AOM-branch KA05T rear holes inside plate (margin mm)',
         'measured': base_dx-(COLUMN_X+OUT['port']+REAR_CLAMP_OFFSET),
         'expected': 62.15, 'tolerance': 0.1},
        {'name': 'RF elbow space beyond connector face (mm)', 'measured': 40.,
         'expected': 40., 'tolerance': 0.}])
    assert_distance('HWP -> PBS (lattice 31.4)', (COLUMN_X, COLUMN_HWP_Y), main_pbs, 31.4)
    assert_distance('PBS -> AOM (nominal axis)', main_pbs, (COLUMN_X, AOM_Y), PBS_Y-AOM_Y)
    assert_distance('Cell -> fold 3', (CELL_X, CELL_Y), (CELL_X, FOLD3_Y), FOLD3_Y-CELL_Y)

    # ---- cut the plate once every element and machining volume is in place ----
    doc.recompute()
    layout.redraw()
    plate.Drill = drill
    plate.touch()
    doc.recompute()
    doc.Label = 'TA board - V9'
    return info


if __name__ == "__main__":
    example_baseplate()
    layout.redraw()
