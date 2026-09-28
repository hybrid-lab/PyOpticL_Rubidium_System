"""Lattice baseplate V9.2 - 24 x 14 in, 795 nm Rb-87 lattice light.

Beam order, read top to bottom in example_baseplate():

    TA -> two steering folds -> HWP -> isolator -> QWP
       -> six bare 8-32 conditioning stations (45/45 mm on the lane,
          60/100 mm along the beam after fold 2)
       -> Rb vapour cell seat (pocket only) -> SR475 shutter
       -> power-division HWP -> main PBS
            transmitted -> DP1 arm: HWP, PBS, AOM on its integral seat,
                           f = 75 mm cat-eye, QWP, order iris, retro mirror;
                           return -> telescope, HWP, rotating PBS, iris, KA05T
            reflected   -> DP2 arm: the same chain one row below

In mode='dual' a second KA05T feeds the DP2 arm from an external TA through a
two-lens telescope and an injection fold, and a blocking iris stops the
residual main-PBS beam.

Positions are millimetres in the board frame; z = 0 is the 12.7 mm optical
axis. Every number below is the audited V9.2 geometry - see
Production/LatticeBoardV9/ for the renders and the audit reports.

Run in FreeCAD (Macro > Macros..., or paste into the Python console):
    example_baseplate()                  single-TA configuration
    example_baseplate(mode='dual')       external-TA configuration
"""
import math

import FreeCAD as App
import Part

from PyOpticL import layout, optomech

# baseplate constants
base_dx = 24*layout.inch
base_dy = 14*layout.inch
base_dz = layout.inch
gap = layout.inch/8

# x-y coordinates of the table mount holes (in inches)
mount_holes = [(3, 12), (19, 0), (14, 13), (3, 0)]

# --- common path ------------------------------------------------------------
TOP_RUN_Y = 338.        # the run the TA folds sit on, above the isolator lane
TA_XY = (60., 140.)     # TA emits +y
LANE_X = 138.           # isolator lane: HWP, isolator, QWP, stations 1-3
CELL_X = LANE_X + 66.   # 204: fold 2, stations 5/6, cell, shutter, fold 3
MAIN_Y = 278.5          # top run: fold 3 -> power HWP -> main PBS
PBS_X = 273.            # main power PBS, and the column the DP2 feed turns on
HWP_X = PBS_X - 31.4    # 241.6: power-division HWP
CELL_Y = 165.
SHUTTER_Y = 240.
TA_HWP_Y = 315.
ISO_Y = 245.
QWP_Y = 181.
LOWER_RUN_Y = 42.
STATION_LANE_Y = (160., 115., 70.)   # stations 1-3, 45 mm pitch down the lane
STATION_4_DX = 22.                   # station 4, 22 mm after fold 1 on the cross-run
STATION_5_Y = 58.                    # station 4 -> 5 along the beam: 44 + 16 = 60 mm
STATION_6_Y = 98.                    # station 4 -> 6 along the beam: 44 + 56 = 100 mm

# --- double-pass arms and output rows ---------------------------------------
DP1_Y = 307.            # DP1 AOM row
DP2_Y = 100.            # DP2 AOM row
OUT1_Y = 230.           # DP1 output row
OUT2_Y = 41.            # DP2 output row
EXT_Y = 165.            # external-TA input lane
PBS_TO_AOM = 55.        # separation PBS -> AOM on both arms
IRIS_TO_LENS_TUBE = 30.         # output iris centre -> KA05T lens-tube front
LENS_TUBE_FRONT = 18.798        # KA05T lens-tube front ahead of the mount origin
REAR_CLAMP_OFFSET = 76.         # rear fiber tail-clamp pair behind each head
OUTPUT_FRONT_ACCESS = 28.       # reserved axial access in front of an output head
EXTERNAL_FRONT_ACCESS = 50.
PORT_X = PBS_X + 70. + 125. + IRIS_TO_LENS_TUBE + LENS_TUBE_FRONT   # 516.798
# An L05G lens holder carries its own 8-32 tap 8 mm behind the holder origin,
# and the holder is seated half a lens thickness behind the glass, so its tap
# lands (8 + tc/2) upstream of the lens plane. A bare hole drilled there takes
# the holder with the lens exactly on the design plane.
HOLDER_TAP_OFFSET = 8.


def holder_tap_offset(part):
    """Distance from a lens plane back to its L05G holder's own 8-32 tap."""
    return HOLDER_TAP_OFFSET + LENSES[part][1]/2

# Mid-thickness separations from the catalogue paraxial 795 nm estimates:
# (catalogue EFL, centre thickness, edge thickness, estimated EFL at 795 nm)
LENSES = {
    'LA1213-B': (49.8, 2.6, 1.8, 50.377311),
    'LA1560-B': (24.9, 3.5, 1.8, 25.188655),
    'LA1612-B': (75.0, 2.5, 2.0, 75.869444),
    'LA1289-B': (29.9, 3.2, 1.8, 30.2466184),
    'LA1540-B': (14.9, 5.1, 1.8, 15.0727296),
}
EXTERNAL_SPH_CENTER_SPACING = LENSES['LA1213-B'][3] + LENSES['LA1560-B'][3]

RED = (.85, .15, .1)
BLUE = (.1, .35, .95)
GREEN = (.05, .6, .3)
PURPLE = (.65, .15, .85)
UPSTREAM = ('Assumed upstream clearance radius 2.5 mm; TA measured q/M2 not supplied.')
DOWNSTREAM = ('Nominal 0.833 mm beam; conservative 1.2 mm diameter clearance envelope '
              'after telescope. Measured q/M2 and RF angle pending.')
STATION_NOTE = ('Bare 8-32 hole (station %d of 6); holder and optic not yet selected. '
                'The audit reserves a 10 mm round envelope at the hole and checks a 16 mm '
                'along-beam holder footprint; a longer holder would need review.')


def example_baseplate(x=0, y=0, angle=0, mode='single', drill=True):
    """Build the lattice board. mode: 'single' (one TA) or 'dual' (external TA)."""
    if mode not in ('single', 'dual'):
        raise ValueError("mode must be 'single' or 'dual'")
    if App.ActiveDocument is None:
        App.newDocument('Lattice_V9_' + mode)
    doc = App.ActiveDocument

    baseplate = layout.baseplate(base_dx, base_dy, base_dz, x=x, y=y, angle=angle, gap=gap,
                                 drill=False, mount_holes=mount_holes,
                                 name='Lattice plate 24 x 14 in')
    plate = doc.getObject(baseplate.active_baseplate)

    info = {'mode': mode, 'plate': plate, 'roots': {}, 'paths': [], 'arms': [],
            'reservations': [], 'extra_cuts': [], 'geometry_assertions': [],
            'alternate': False, 'service_regions': [], 'output_optical_routes': [],
            'layout_variant': 'Hand sketch V9',
            'layout_status': 'V9.2 machined geometry; see the saved audit report for results.'}
    hidden = []

    # ---- placement helpers, so every optic below is a single readable line ----
    def put(name, cls, px, py, pangle=0, **kw):
        obj = baseplate.place_element(name, cls, x=px, y=py, angle=pangle, **kw)
        info['roots'][name] = obj
        return obj

    def mirror(name, px, py, pangle):
        return put(name, optomech.circular_mirror_union_optic, px, py, pangle, thickness=6,
                   mount_type=optomech.mirror_mount_M05, mount_args={'thumbscrews': True})

    def bend(name, a, p, b):
        """A 45-degree M05 fold at p, turning the beam from a->p onto p->b.

        The mirror angle is the bisector normal; reversing it would put the
        unchanged M05 behind the incident ray, so the assembly is moved instead
        of flipping its reflective face.
        """
        u = (p[0]-a[0], p[1]-a[1])
        v = (b[0]-p[0], b[1]-p[1])
        du = math.hypot(*u)
        dv = math.hypot(*v)
        n = (v[0]/dv - u[0]/du, v[1]/dv - u[1]/du)
        return mirror(name, p[0], p[1], math.degrees(math.atan2(n[1], n[0])))

    def wp(name, px, py, pangle=0):
        return put(name, optomech.waveplate, px, py, pangle,
                   mount_type=optomech.rotation_stage_rsp05)

    def pbs(name, px, py, pangle=0, invert=False):
        return put(name, optomech.cube_splitter, px, py, pangle, invert=invert,
                   mount_type=optomech.cube_mount_halfinch)

    def lens(name, part, px, py, pangle=180):
        f, tc, te, f795 = LENSES[part]
        obj = put(name, optomech.circular_lens, px, py, pangle, focal_length=f, thickness=tc,
                  diameter=12.7, part_number=part,
                  # the pin-slot-free L05G: same mesh and 8-32 bore, no pin slots cut
                  mount_type=optomech.lens_holder_l05g_no_pin_slots)
        for key, value in (('CatalogEFL', f), ('EstimatedEFL795', f795),
                           ('CenterThickness', tc), ('EdgeThickness', te)):
            obj.addProperty('App::PropertyLength', key, 'Lens specification')
            setattr(obj, key, value)
        obj.addProperty('App::PropertyString', 'LensOrientation', 'Lens specification')
        obj.LensOrientation = ('Curved glass faces outward; holder angle independent of glass '
                               'orientation. CAD is envelope only.')
        return obj

    def hole(name, px, py, purpose):
        obj = put(name, optomech.BareTappedHole, px, py)
        obj.Purpose = purpose
        info['extra_cuts'].append(obj)
        info['reservations'].append({'object': obj.Name, 'reason': purpose})
        return obj

    def fiber(name, px, py, pangle):
        # px is the KA05T mount origin; the lens-tube front sits LENS_TUBE_FRONT
        # ahead of it and the rear tail-clamp pair REAR_CLAMP_OFFSET behind it.
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
        obj.addProperty('App::PropertyBool', 'Bidirectional').Bidirectional = 'double pass' in name
        if isinstance(envelope, (float, int)):
            envelope = [envelope]*len(points)
        info['paths'].append({'name': name, 'points': points, 'object': obj.Name,
                              'envelope': envelope, 'assumption': assumption})
        return obj

    # =========================================================================
    # 1. TA, the two steering folds and the isolator lane
    # =========================================================================
    # The TA points +y; two and only two steering mirrors deliver the beam down
    # the isolator's optical axis. Their M05 bodies stick 3.6 mm past the plate
    # outline and the thumbscrews ~21 mm (accepted: they sit above the plate).
    ta = put('TA', optomech.TA_butterfly_on_adapter, TA_XY[0], TA_XY[1], 90)
    supply = [TA_XY, (TA_XY[0], TOP_RUN_Y), (LANE_X, TOP_RUN_Y), (LANE_X, STATION_LANE_Y[0])]
    bend('TA steering fold 1', supply[0], supply[1], supply[2])      # (60, 338)
    bend('TA steering fold 2', supply[1], supply[2], supply[3])      # (138, 338)
    wp('TA output HWP', LANE_X, TA_HWP_Y, 90)                        # 23 mm below fold 2
    isolator = put('Hana long isolator', optomech.isolator_850_long_pocket, LANE_X, ISO_Y, 90)
    info['extra_cuts'].append(isolator)
    wp('TA output QWP', LANE_X, QWP_Y, 90)                           # 64 mm below the isolator

    # =========================================================================
    # 2. Six bare conditioning stations (holders and optics not yet selected)
    # =========================================================================
    # Only the hole spacing is fixed: 45/45 mm down the lane, then 60 mm and
    # 100 mm along the beam from station 4 through fold 2.
    lane_stations = [hole('Common station 8-32 1', LANE_X, STATION_LANE_Y[0], STATION_NOTE % 1),
                     hole('Common station 8-32 2', LANE_X, STATION_LANE_Y[1], STATION_NOTE % 2),
                     hole('Common station 8-32 3', LANE_X, STATION_LANE_Y[2], STATION_NOTE % 3)]
    sphere_stations = [hole('Common station 8-32 4', LANE_X + STATION_4_DX, LOWER_RUN_Y, STATION_NOTE % 4),
                       hole('Common station 8-32 5', CELL_X, STATION_5_Y, STATION_NOTE % 5),
                       hole('Common station 8-32 6', CELL_X, STATION_6_Y, STATION_NOTE % 6)]

    # =========================================================================
    # 3. Down the short side, east along the lower edge, north to the main PBS
    # =========================================================================
    route = [(LANE_X, STATION_LANE_Y[-1]), (LANE_X, LOWER_RUN_Y), (CELL_X, LOWER_RUN_Y),
             (CELL_X, MAIN_Y), (PBS_X, MAIN_Y)]
    bend('Common post-isolator fold 1', route[0], route[1], route[2])   # (138, 42)
    bend('Common post-isolator fold 2', route[1], route[2], route[3])   # (204, 42)
    bend('Common post-isolator fold 3', route[2], route[3], route[4])   # (204, 278.5)

    # The enclosure has not been designed yet, so nothing is modelled above the
    # plate here: the cell seat is a 3/4 in deep, beam-centred 104 x 56 mm
    # pocket with four corner 8-32 taps, and nothing else.
    cell = optomech.place_cell_pocket(baseplate, CELL_X, CELL_Y, angle=90)
    info['cell'] = dict(cell, cell=cell['root'])
    info['roots']['Rb cell seat (pocket only)'] = cell['root']
    info['extra_cuts'].extend(o for o in cell['objects'] if hasattr(o, 'DrillPart'))

    put('SRS SR475 shutter', optomech.shutter_sr475, CELL_X, SHUTTER_Y, 90)
    wp('Main power division HWP', HWP_X, MAIN_Y, 0)
    main_pbs = pbs('Main power PBS', PBS_X, MAIN_Y, 90, invert=False)

    # =========================================================================
    # 4. DP1 arm (transmitted): two folds up to the AOM row, then the double pass
    # =========================================================================
    X0 = PBS_X
    dp1_sep_x = X0 + 70.
    dp1_aom_x = dp1_sep_x + PBS_TO_AOM
    # The upper branch needs two orthogonal folds so that it also has a real
    # adjustable mirror before its AOM PBS.
    bend('DP1 input steering fold', (X0, MAIN_Y), (X0+30, MAIN_Y), (X0+30, DP1_Y))
    dp1_in = bend('DP1 input steering mirror', (X0+30, MAIN_Y), (X0+30, DP1_Y), (dp1_sep_x, DP1_Y))
    wp('DP1 input HWP', X0+50, DP1_Y, 0)
    pbs('DP1 separation PBS', dp1_sep_x, DP1_Y, 0, invert=False)
    # angle 180: RF connector toward +y, KM100PM downstream of the AOM
    dp1_aom = put('DP1 AOMO 3100-125', optomech.AOMO_3100_125, dp1_aom_x, DP1_Y, 180,
                  forward_direction=-1, backward_direction=1, diffraction_angle=0,
                  surface_adapter_args={'adapter_height': 5})
    dp1_seat = optomech.integrate_aom(baseplate, dp1_aom)
    info['extra_cuts'].append(dp1_seat)
    dp1_lens = lens('DP1 L75 LA1612-B', 'LA1612-B', dp1_aom_x+75, DP1_Y, 180)
    wp('DP1 cat eye QWP', dp1_aom_x+105, DP1_Y, 180)
    # iris 10 mm in front of the retro mirror face (the cat-eye focal plane);
    # post toward -y, the row below being 77 mm away
    put('DP1 order selection iris', optomech.pinhole_ida12, dp1_aom_x+140, DP1_Y, 0)
    dp1_retro = mirror('DP1 retro mirror', dp1_aom_x+150, DP1_Y, 180)

    # =========================================================================
    # 5. DP2 arm (reflected): one fold down to its AOM row, then the double pass
    # =========================================================================
    dp2_sep_x = X0 + 60.
    dp2_aom_x = dp2_sep_x + PBS_TO_AOM
    dp2_in = bend('DP2 input steering mirror', (X0, MAIN_Y), (X0, DP2_Y), (dp2_sep_x, DP2_Y))
    wp('DP2 input HWP', X0+35, DP2_Y, 0)
    # the DP2 output row is below its AOM row, so this cube reflects the
    # returning beam toward -y exactly like DP1's (invert=False)
    pbs('DP2 separation PBS', dp2_sep_x, DP2_Y, 0, invert=False)
    dp2_aom = put('DP2 AOMO 3100-125', optomech.AOMO_3100_125, dp2_aom_x, DP2_Y, 180,
                  forward_direction=-1, backward_direction=1, diffraction_angle=0,
                  surface_adapter_args={'adapter_height': 5})
    dp2_seat = optomech.integrate_aom(baseplate, dp2_aom)
    info['extra_cuts'].append(dp2_seat)
    dp2_lens = lens('DP2 L75 LA1612-B', 'LA1612-B', dp2_aom_x+75, DP2_Y, 180)
    wp('DP2 cat eye QWP', dp2_aom_x+105, DP2_Y, 180)
    # post toward +y here: the DP2 output row is only 59 mm below, the external
    # lane above is 65 mm away
    put('DP2 order selection iris', optomech.pinhole_ida12, dp2_aom_x+140, DP2_Y, 180)
    dp2_retro = mirror('DP2 retro mirror', dp2_aom_x+150, DP2_Y, 180)

    # =========================================================================
    # 6. The two output rows: telescope, HWP, rotating PBS, iris, fiber head
    # =========================================================================
    iris_x = PORT_X - LENS_TUBE_FRONT - IRIS_TO_LENS_TUBE          # 468.0 on both rows
    outputs = []
    for index, row_y, source_y, sep_x, aom_x, hwp_dx, rot_dx in (
            (1, OUT1_Y, DP1_Y, dp1_sep_x, dp1_aom_x, 72., 94.),
            (2, OUT2_Y, DP2_Y, dp2_sep_x, dp2_aom_x, 77., 101.)):
        tag = 'DP%d ' % index
        lens1_x = sep_x + 14.
        lens2_x = lens1_x + 45.319348
        hwp_x = sep_x + hwp_dx
        rot_x = sep_x + rot_dx
        out_mirror = bend(tag+'output steering mirror', (sep_x, source_y), (sep_x, row_y),
                          (PORT_X, row_y))
        l1 = lens(tag+'output first LA1289-B', 'LA1289-B', lens1_x, row_y, 180)
        l2 = lens(tag+'output second LA1540-B', 'LA1540-B', lens2_x, row_y, 0)
        wp(tag+'output HWP', hwp_x, row_y, 0)
        rotating_pbs(tag+'empty rotating PBS RSP05', rot_x, row_y, 0)
        # post toward +y on both rows: on DP2 the -y side is the plate edge
        out_iris = put(tag+'output filtering iris', optomech.pinhole_ida12, iris_x, row_y, 180)
        head = fiber(tag+'output KA05T', PORT_X, row_y, 180)
        outputs.append(dict(index=index, row_y=row_y, source_y=source_y, sep_x=sep_x, aom_x=aom_x,
                            mirror=out_mirror, l1=l1, l2=l2, hwp_x=hwp_x, rot_x=rot_x,
                            iris=out_iris, head=head, lens1_x=lens1_x, lens2_x=lens2_x))

    # =========================================================================
    # 7. External-TA input (installed in mode='dual' only)
    # =========================================================================
    external_head = fiber('External TA input KA05T', PORT_X, EXT_Y, 180)
    # Keep the f1+f2 optical-path separation while putting lens 2 on the
    # vertical injection leg, between the injection fold and the DP2 mirror.
    external_lens1_x = X0 + 40.                                   # 313: lens 1 plane
    external_lens2_y = EXT_Y - (EXTERNAL_SPH_CENTER_SPACING - (external_lens1_x - X0))   # 129.434
    # As at the six conditioning stations, nothing is installed here yet: the
    # two telescope positions are drilled as bare 8-32 holes. Each hole is
    # where an L05G holder's own tap lands (HOLDER_TAP_OFFSET upstream of the
    # lens plane), so the plate is drilled exactly as it would be with the
    # lenses fitted and the optics can be chosen later.
    e1 = hole('External spherical first lens 8-32',
              external_lens1_x + holder_tap_offset('LA1213-B'), EXT_Y,
              'Bare 8-32 hole for the external telescope lens 1 (LA1213-B planned); '
              'L05G tap position, lens plane %g mm downstream.' % holder_tap_offset('LA1213-B'))
    e2 = hole('External spherical second 8-32', X0,
              external_lens2_y + holder_tap_offset('LA1560-B'),
              'Bare 8-32 hole for the external telescope lens 2 (LA1560-B planned); '
              'L05G tap position, lens plane %g mm downstream.' % holder_tap_offset('LA1560-B'))
    spare = hole('External spherical spare 8-32', X0+105., EXT_Y,
                 'One optional 8-32 lens position in the external input lane.')
    external_holes = [e1, e2, spare]
    # beam direction at each: lens 1 and the spare sit on the -x lane, lens 2
    # on the -y injection leg
    external_beam_dirs = [(-1., 0.), (0., -1.), (-1., 0.)]
    injection = bend('Optional external TA injection mirror',
                     (external_lens1_x, EXT_Y), (X0, EXT_Y), (X0, DP2_Y))
    blocker = put('Optional PBS leakage blocking iris', optomech.pinhole_ida12, X0+10., 235, 90)
    blocker.addProperty('App::PropertyString', 'Installation').Installation = (
        'Installed only with external TA: the residual main-PBS beam on x = PBS_X '
        'hits the iris metal. In single-TA mode the hardware is omitted; its '
        'machined optional mounting seat remains available on the common plate.')
    blocker.addProperty('App::PropertyBool', 'InstalledInThisMode', 'Installation')
    blocker.InstalledInThisMode = (mode == 'dual')
    if mode == 'single':
        blocker.Label = 'Optional PBS leakage iris - NOT INSTALLED (single TA)'
        hidden.extend([injection, blocker])

    # =========================================================================
    # 8. Nominal beam paths (drawn, and used by the clearance audits)
    # =========================================================================
    path('TA supply', supply, RED, 2.5, UPSTREAM)
    path('Common cylindrical conditioning provision',
         [(LANE_X, STATION_LANE_Y[0]), (LANE_X, STATION_LANE_Y[1]), (LANE_X, STATION_LANE_Y[2]),
          (LANE_X, LOWER_RUN_Y), (LANE_X+STATION_4_DX, LOWER_RUN_Y), (CELL_X, LOWER_RUN_Y),
          (CELL_X, STATION_5_Y)], RED, [2.5, .9, .9, .9, .9, .9, .9],
         'Stations 1-4 are bare 8-32 holes (45/45 mm lane pitch, station 4 on the cross-run); '
         'optics unselected. The envelope is the intended conditioned beam, not modeled optics.')
    path('Common spherical telescope',
         [(CELL_X, STATION_5_Y), (CELL_X, STATION_6_Y), (CELL_X, CELL_Y), (CELL_X, SHUTTER_Y),
          (CELL_X, MAIN_Y), (PBS_X, MAIN_Y)], RED, [.9, .6, .6, .6, .6, .6],
         'Stations 5/6 are bare 8-32 holes 40 mm apart (60/100 mm from station 4 along the '
         'beam); optics unselected. ' + DOWNSTREAM)
    path('DP1 feed', [(X0, MAIN_Y), (X0+30, MAIN_Y), (X0+30, DP1_Y), (dp1_sep_x, DP1_Y)],
         BLUE, .6, DOWNSTREAM)
    path('DP1 double pass',
         [(dp1_sep_x, DP1_Y), (dp1_aom_x, DP1_Y), (dp1_aom_x+75, DP1_Y), (dp1_aom_x+105, DP1_Y),
          (dp1_aom_x+140, DP1_Y), (dp1_aom_x+150, DP1_Y)], BLUE,
         [.6, .6, .6, .36, .177, .000795*75/(math.pi*.6)], DOWNSTREAM)
    path('DP2 double pass',
         [(dp2_sep_x, DP2_Y), (dp2_aom_x, DP2_Y), (dp2_aom_x+75, DP2_Y), (dp2_aom_x+105, DP2_Y),
          (dp2_aom_x+140, DP2_Y), (dp2_aom_x+150, DP2_Y)], GREEN,
         [.6, .6, .6, .36, .177, .000795*75/(math.pi*.6)], DOWNSTREAM)
    for out in outputs:
        path('DP%d output' % out['index'],
             [(out['sep_x'], out['source_y']), (out['sep_x'], out['row_y']),
              (out['lens1_x'], out['row_y']), (out['lens1_x']+30.2466184, out['row_y']),
              (out['lens2_x'], out['row_y']), (PORT_X-LENS_TUBE_FRONT, out['row_y'])],
             BLUE if out['index'] == 1 else GREEN, [.6, .6, .6, .035, .6, .6], DOWNSTREAM)
    if mode == 'single':
        path('DP2 feed', [(X0, MAIN_Y), (X0, DP2_Y), (dp2_sep_x, DP2_Y)], GREEN, .6, DOWNSTREAM)
    else:
        external_focus_y = EXT_Y - (LENSES['LA1213-B'][3] - (external_lens1_x - X0))
        path('External TA telescope',
             [(PORT_X-LENS_TUBE_FRONT, EXT_Y), (external_lens1_x, EXT_Y), (X0, EXT_Y),
              (X0, external_focus_y), (X0, external_lens2_y), (X0, DP2_Y), (dp2_sep_x, DP2_Y)],
             PURPLE, [.9, .9, .9, .035, .6, .6, .6], DOWNSTREAM)
        # Stop the displayed beam at the deliberately offset iris metal, but keep
        # a separate full-length probe for the physical contact audit; drawing
        # that probe as a beam would look as though light passed the blocker.
        residual = doc.addObject('Part::Feature', 'PBSResidualBlocked')
        residual.Label = 'PBS residual - stops at offset iris metal'
        residual.Shape = Part.makePolygon([App.Vector(PBS_X, MAIN_Y, 0), App.Vector(PBS_X, 240., 0)])
        residual.ViewObject.LineColor = (.6, .45, .15)
        residual.addProperty('App::PropertyLength', 'VisibleStopY', 'Beam display').VisibleStopY = 240.
        residual.addProperty('App::PropertyLength', 'AuditProbeEndY', 'Beam display').AuditProbeEndY = 214.
        info['paths'].append({'name': 'PBS residual blocked', 'points': [(PBS_X, MAIN_Y), (PBS_X, 214.)],
                              'object': residual.Name, 'envelope': [.6, .6],
                              'assumption': 'Full-length collision probe; the visible line stops at '
                                            'the offset IDA12 metal. The iris is absent in single-TA operation.'})

    # =========================================================================
    # 9. Bookkeeping consumed by the audit scripts (no geometry below this line)
    # =========================================================================
    for out in outputs:
        tag = 'DP%d ' % out['index']
        info['output_optical_routes'].append({'arm': out['index'], 'events': [
            {'type': 'aom', 'name': tag+'AOM return', 'xy': (out['aom_x'], out['source_y'])},
            {'type': 'pbs', 'name': tag+'separation PBS', 'xy': (out['sep_x'], out['source_y'])},
            {'type': 'mirror', 'name': out['mirror'].Label, 'xy': (out['sep_x'], out['row_y'])},
            {'type': 'lens', 'name': out['l1'].Label, 'xy': (out['lens1_x'], out['row_y']), 'focal_mm': 30.2466184},
            {'type': 'lens', 'name': out['l2'].Label, 'xy': (out['lens2_x'], out['row_y']), 'focal_mm': 15.0727296},
            {'type': 'hwp', 'name': tag+'output HWP', 'xy': (out['hwp_x'], out['row_y'])},
            {'type': 'pbs', 'name': tag+'empty rotating PBS RSP05', 'xy': (out['rot_x'], out['row_y'])},
            {'type': 'iris', 'name': out['iris'].Label, 'xy': (iris_x, out['row_y'])},
            {'type': 'fiber', 'name': out['head'].Label, 'xy': (PORT_X-LENS_TUBE_FRONT, out['row_y'])}]})
        info['geometry_assertions'].append(
            {'name': tag+'output iris centre -> KA05T lens-tube front',
             'measured': (PORT_X-LENS_TUBE_FRONT)-iris_x, 'expected': IRIS_TO_LENS_TUBE, 'tolerance': 1e-7})
        info['geometry_assertions'].append(
            {'name': tag+'rotating PBS -> output iris', 'measured': iris_x-out['rot_x'],
             'expected': 31. if out['index'] == 1 else 34., 'tolerance': 1e-7})

    for index, aom, seat, cat, retro, arm_y, aom_x in (
            (1, dp1_aom, dp1_seat, dp1_lens, dp1_retro, DP1_Y, dp1_aom_x),
            (2, dp2_aom, dp2_seat, dp2_lens, dp2_retro, DP2_Y, dp2_aom_x)):
        tag = 'DP%d ' % index
        info['arms'].append({'id': index, 'aom': aom.Name, 'lens': cat.Name, 'retro': retro.Name,
                             'integral_seat': seat.Name, 'aom_to_cat': 75., 'cat_to_mirror': 75.})
        info['service_regions'].append(
            {'name': tag+'RF elbow neck candidate', 'kind': 'aom_connector', 'owner': aom.Name,
             'origin_xy_mm': [aom_x, arm_y+33.02], 'direction_xy': [0, 1], 'length_mm': 20., 'width_mm': 20.,
             'allowed_paths': [], 'dimensions_verified': False,
             'assumptions': ['Unconfirmed 20 mm outward neck envelope.']})
        info['service_regions'].append(
            {'name': tag+'RF elbow tail candidate', 'kind': 'aom_sma', 'owner': aom.Name,
             'origin_xy_mm': [aom_x, arm_y+53.02], 'direction_xy': [1, 0], 'length_mm': 50.8, 'width_mm': 20.,
             'allowed_paths': [], 'dimensions_verified': False,
             'assumptions': ['Provisional planar elbow, clocking not confirmed.']})

    info['service_regions'].append(
        {'name': 'TA thick bottom cable', 'kind': 'ta_cable', 'owner': ta.Name,
         'origin_xy_mm': [9.844387, 110.075], 'direction_xy': [-1., 0.], 'length_mm': 101.6,
         'width_mm': 96.25, 'allowed_paths': [], 'dimensions_verified': False,
         'assumptions': ['Conservative TA full body-width cable projection; connector dimensions '
                         'unverified. The 101.6 mm corridor extends beyond the plate left edge.']})
    for head, own in ((outputs[0]['head'], 'DP1 output'), (outputs[1]['head'], 'DP2 output'),
                      (external_head, 'External TA telescope' if mode == 'dual' else None)):
        direction = head.BasePlacement.Rotation.multVec(App.Vector(1, 0, 0))
        origin = head.BasePlacement.Base + direction*LENS_TUBE_FRONT
        is_output = 'output' in head.Label.lower()
        access = OUTPUT_FRONT_ACCESS if is_output else EXTERNAL_FRONT_ACCESS
        info['service_regions'].append(
            {'name': head.Label+' front access', 'kind': 'fiber_front', 'owner': head.Name,
             'origin_xy_mm': [origin.x, origin.y], 'direction_xy': [direction.x, direction.y],
             'length_mm': access, 'width_mm': 20., 'allowed_paths': [own] if own else [],
             'dimensions_verified': False,
             'assumptions': ['20 mm full front access width; V9.2 output heads reserve %g mm axial '
                             'access (iris centre 30 mm ahead of the lens tube, iris body 1.02 mm on '
                             'the fiber side).' % access if is_output else '20 mm full front access width.']})
    # the output heads' 28 mm front access is below the audit's 40 mm default
    info.setdefault('service_clearance', {}).setdefault('min_length_mm', {})['fiber_front'] = OUTPUT_FRONT_ACCESS
    # the rear tail-clamp pairs sit REAR_CLAMP_OFFSET behind the heads
    info.setdefault('fiber_clearance', {})['rear_offsets_mm'] = [REAR_CLAMP_OFFSET]

    beam_dir = {1: (0., -1.), 2: (0., -1.), 3: (0., -1.), 4: (1., 0.), 5: (0., 1.), 6: (0., 1.)}
    spherical_groups = [{'name': 'common', 'active_lenses': [],
                         'spare_holes': [o.Name for o in sphere_stations],
                         'stations_only': True, 'spare_required': 3}]
    for out in outputs:
        spherical_groups.append({'name': 'DP%d output' % out['index'],
                                 'active_lenses': [out['l1'].Name, out['l2'].Name],
                                 'spare_holes': [], 'spare_required': 0})
    spherical_groups.append({'name': 'external', 'active_lenses': [],
                             'spare_holes': [o.Name for o in external_holes],
                             'stations_only': True, 'spare_required': 3})
    if mode == 'dual':
        info['geometry_assertions'].append(
            {'name': 'External folded f1+f2 separation (design lens planes)',
             'measured': (external_lens1_x-X0)+(EXT_Y-external_lens2_y),
             'expected': EXTERNAL_SPH_CENTER_SPACING, 'tolerance': 1e-6})
    info['requirements'] = {
        'mirror_roles': [{'arm': 1, 'input': dp1_in.Name, 'output': outputs[0]['mirror'].Name},
                         {'arm': 2, 'input': dp2_in.Name, 'output': outputs[1]['mirror'].Name}],
        'spherical_groups': spherical_groups,
        'mount_only_cylindrical_holes': [o.Name for o in lane_stations],
        'provisional_bare_mount_envelopes': [
            {'object': o.Name, 'center_xy_mm': [o.BasePlacement.Base.x, o.BasePlacement.Base.y],
             'diameter_mm': 10.0, 'beam_direction_xy': list(d)}
            for o, d in list(zip([*lane_stations, *sphere_stations],
                                 [beam_dir[i+1] for i in range(6)]))
            + list(zip(external_holes, external_beam_dirs))]}
    info['isolator'] = {'source': 'hana-branch original isolator_850',
                        'main_pocket_mm': [113.5, 25., 5.]}
    info['pbs_path_specs'] = [
        {'role': 'main', 'cube': 'Main power PBS', 'incoming_path': 'Common spherical telescope',
         'outgoing_paths': ['DP1 feed', 'DP2 feed' if mode == 'single' else 'PBS residual blocked']},
        {'role': 'double_pass', 'cube': 'DP1 separation PBS', 'incoming_path': 'DP1 feed',
         'aom_path': 'DP1 double pass', 'output_path': 'DP1 output'},
        {'role': 'double_pass', 'cube': 'DP2 separation PBS',
         'incoming_path': 'DP2 feed' if mode == 'single' else 'External TA telescope',
         'aom_path': 'DP2 double pass', 'output_path': 'DP2 output'}]

    def station_pitch(a, b):
        return abs(a.BasePlacement.Base.y - b.BasePlacement.Base.y)

    def along_beam(a, b, corner):
        ax, ay = a.BasePlacement.Base.x, a.BasePlacement.Base.y
        bx, by = b.BasePlacement.Base.x, b.BasePlacement.Base.y
        return abs(corner[0]-ax)+abs(corner[1]-ay)+abs(bx-corner[0])+abs(by-corner[1])

    info['geometry_assertions'].extend([
        {'name': 'Stations 1-2 pitch', 'measured': station_pitch(lane_stations[0], lane_stations[1]),
         'expected': 45., 'tolerance': 1e-7},
        {'name': 'Stations 2-3 pitch', 'measured': station_pitch(lane_stations[1], lane_stations[2]),
         'expected': 45., 'tolerance': 1e-7},
        {'name': 'Station 4->5 along beam via fold 2',
         'measured': along_beam(sphere_stations[0], sphere_stations[1], (CELL_X, LOWER_RUN_Y)),
         'expected': 60., 'tolerance': 1e-7},
        {'name': 'Station 4->6 along beam via fold 2',
         'measured': along_beam(sphere_stations[0], sphere_stations[2], (CELL_X, LOWER_RUN_Y)),
         'expected': 100., 'tolerance': 1e-7}])

    # ---- cut the plate once every element and machining volume is in place ----
    doc.recompute()
    layout.redraw()
    for obj in hidden:
        for child in optomech.descendants(obj):
            child.ViewObject.hide()
    plate.Drill = drill
    plate.touch()
    doc.recompute()
    doc.Label = 'Lattice V9 - ' + ('single TA' if mode == 'single' else 'external TA')
    return info


if __name__ == "__main__":
    example_baseplate()
    layout.redraw()
