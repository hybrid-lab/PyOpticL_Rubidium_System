"""TA baseplate V9.8 - 14 x 17.5 in, the seed board for the 795 nm lattice light.

Beam order, read top to bottom in example_baseplate():

    TA -> two steering folds -> HWP -> isolator -> QWP
       -> six bare 8-32 conditioning stations
       -> lattice V9.7 sliding Rb cell enclosure -> folds 3 and 4
       -> power-division HWP -> main PBS
            transmitted -> AOM (integral seat) -> SR475 shutter -> fold 5
                           -> L1, L2, HWP, rotating PBS, iris, KA05T
            reflected   -> one steering fold down the right edge
                           -> L1, L2, HWP, rotating PBS, KA05T (no iris)

The isolator and conditioning lanes move left; their optical ordering and
specified conditioning pitches are preserved. Both output telescopes retain
their spacings. The AOM output runs left along the bottom; the direct output
runs down the right edge with one fold. The shutter-to-fold run leaves room
for the RF elbow above the common-path mirror. Coordinates are in board frame.

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
base_dy = 17.5*layout.inch
base_dz = layout.inch
gap = layout.inch/8

# Table mount grid indices: hole centres are (index + 0.5) inches.
mount_holes = [(1, 0), (13, 0), (8, 16), (13, 16)]


def board_xy(px, py):
    """Board-frame coordinate pair (shared by placement and audit metadata)."""
    return px, py


def board_direction(dx, dy):
    return dx, dy

# --- common path (lattice component order and conditioning pitches) ----------
TOP_RUN_Y = 394.
TA_XY = (55., 196.)
LANE_X = 125.
CELL_X = 191.
TA_HWP_Y = 371.
ISO_Y = 301.
QWP_Y = 237.
LOWER_RUN_Y = 98.
STATION_LANE_Y = (216., 171., 126.)
STATION_4_DX = 22.
STATION_5_Y = 114.
STATION_6_Y = 154.
CELL_Y = 255.
FOLD3_Y = 352.4

# --- the column and the two output rows --------------------------------------
# The 40 mm RF elbow lies between conditioning stations 5 and 6. The output
# lane clears the common-path knobs in XY, regardless of knob height.
# The direct fiber tail has a full 60 x 20 mm clamp region.
COLUMN_X = 266.5
COLUMN_HWP_Y = FOLD3_Y - 25.
PBS_Y = COLUMN_HWP_Y - 31.4
AOM_Y = 134.
SHUTTER_Y = AOM_Y - 40.67
AOM_ROW_Y = 50.
REFLECT_FOLD_X = 321.5
REFLECT_ROW_Y = PBS_Y

# output-chain offsets from each row's fold mirror (the lattice DP-output chain)
OUT = {'lens1': 14., 'lens2': 14.+45.319348, 'hwp': 72., 'rot': 94., 'iris': 125.,
       'fiber_face': 167.35, 'port': 186.15}
# the reflected branch has no iris, so its fiber face sits 50 mm behind the
# rotating PBS: 40 mm front access plus the RSP05 body (7.25 mm) and 2.75 mm
OUT_NO_IRIS = {'lens1': 14., 'lens2': 14.+45.319348, 'hwp': 72., 'rot': 94.,
               'fiber_face': 144., 'port': 144.+18.798}
REAR_CLAMP_OFFSET = 54.              # direct head: clear the shutter and bottom fold
AOM_REAR_CLAMP_OFFSET = 64.          # full 60 x 20 envelope remains on the plate

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
                                 name='TA plate V9.8 compact 14 x 17.5 in')
    plate = doc.getObject(baseplate.active_baseplate)
    info = {'mode': 'ta', 'plate': plate, 'roots': {}, 'paths': [], 'arms': [],
            'reservations': [], 'extra_cuts': [], 'geometry_assertions': [], 'alternate': False,
            'service_regions': [], 'output_optical_routes': [],
            'requirements': {'mirror_roles': [], 'spherical_groups': []},
            'isolator': None, 'cell': None,
            'layout_status': 'V9.8 compact TA board; see the saved audit report for results.',
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
    # The TA emits +y with its thick cable on the -x side, off the plate, as on
    # the lattice board; the U is therefore traversed up, right, then down.
    ta = put('TA', optomech.TA_butterfly_on_adapter, TA_XY[0], TA_XY[1], 90)
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

    # Exactly the lattice V9.7 lower half, lid, covers, glass and sliding seat.
    cell = optomech.place_sliding_cell(baseplate, CELL_X, CELL_Y, angle=90, slide=cell_slide)
    info['cell'] = dict(cell)
    info['roots']['Rb cell seat (V9.7 pocket + 2 slot taps)'] = cell['root']
    info['roots']['Rb cell enclosure (V9.7 lower half, lid, covers, cell)'] = cell['cell']
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
                 (COLUMN_X-OUT['lens1'], AOM_ROW_Y))

    # =========================================================================
    # 5. Reflected arm: one fold down the right edge
    # =========================================================================
    # The direct fiber exits at the bottom; the AOM fiber exits to the left.
    fold6 = bend('Reflected branch fold 6', (COLUMN_X, PBS_Y), (REFLECT_FOLD_X, PBS_Y),
                 (REFLECT_FOLD_X, PBS_Y-OUT_NO_IRIS['lens1']))

    # =========================================================================
    # 6. The two output chains (the lattice DP-output geometry)
    # =========================================================================
    rows = []
    for tag, x0, row_y, with_iris, theta in (
            ('AOM branch', COLUMN_X, AOM_ROW_Y, True, 180),
            ('Reflected branch', REFLECT_FOLD_X, REFLECT_ROW_Y, False, -90)):
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
          rows[0]['xy']['lens1'], rows[0]['xy']['lens2'], rows[0]['xy']['fiber_face']],
         BLUE, [.6, .6, .6, .6, .6, .035, .6],
         'Single-pass AOM; the first order is modeled straight (RF deflection ~1 deg absorbed '
         'by fold 5). ' + DOWNSTREAM)
    path('Reflected branch',
         [(COLUMN_X, PBS_Y), (REFLECT_FOLD_X, PBS_Y), rows[1]['xy']['lens1'],
          rows[1]['xy']['lens2'], rows[1]['xy']['fiber_face']],
         GREEN, [.6, .6, .6, .035, .6], DOWNSTREAM)

    # =========================================================================
    # 8. Bookkeeping consumed by the audit scripts (no geometry below this line)
    # =========================================================================
    beam_dir = {1: (0., -1.), 2: (0., -1.), 3: (0., -1.), 4: (1., 0.), 5: (0., 1.), 6: (0., 1.)}
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
            events = [{'type': 'aom', 'name': 'AOM (single pass)', 'xy': (COLUMN_X, AOM_Y)},
                      {'type': 'mirror', 'name': fold5.Label, 'xy': (COLUMN_X, AOM_ROW_Y)}]
        else:
            events = [{'type': 'pbs', 'name': main_pbs.Label, 'xy': (COLUMN_X, PBS_Y)},
                      {'type': 'mirror', 'name': fold6.Label, 'xy': (REFLECT_FOLD_X, PBS_Y)}]
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
        # In design coordinates the fronts face +x (AOM) and +y (direct).
        design_direction = (1., 0.) if row['with_iris'] else (0., 1.)
        service(row['head'].Label+' front access', 'fiber_front', row['head'],
                row['xy']['fiber_face'], design_direction, 40., 20.,
                allowed=[tag], assumptions=['20 mm full front access width; 40 mm axial access.'])

    service('TA thick left cable', 'ta_cable', ta, (4.844387, 166.075), (-1., 0.), 101.6, 96.25,
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
    info['fiber_clearance'] = {'rear_offsets_mm': [AOM_REAR_CLAMP_OFFSET, REAR_CLAMP_OFFSET]}
    info['requirements']['mirror_roles'].append({'arm': 1, 'input': fold4.Name, 'output': fold5.Name})
    info['requirements']['single_steering_mirror_routes'] = [{'arm': 2, 'mirror': fold6.Name}]

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
        {'name': 'Direct branch has one steering mirror',
         'measured': sum(e['type'] == 'mirror' for e in info['output_optical_routes'][1]['events']),
         'expected': 1, 'tolerance': 0.},
        {'name': 'Reflected KA05T rear-hole axis to bottom plate edge (mm)',
         'measured': PBS_Y-OUT_NO_IRIS['port']-REAR_CLAMP_OFFSET-gap,
         'expected': 76.027, 'tolerance': 0.1},
        {'name': 'AOM-branch KA05T rear holes inside plate (margin mm)',
         'measured': COLUMN_X-OUT['port']-AOM_REAR_CLAMP_OFFSET-gap,
         'expected': 13.175, 'tolerance': 0.1},
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
    info['plate_size_mm'] = [base_dx, base_dy, base_dz]
    doc.Label = 'TA board - V9.8 compact'
    return info


if __name__ == "__main__":
    example_baseplate()
    layout.redraw()
