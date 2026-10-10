"""Splitting Board V2 - 24 x 14 in: one fiber in, seven single-pass AOMs, four fibers out on one short edge.

Beam tree (every split is HWP -> PBS; no beam crosses another beam, no beam passes over or under
another element's hardware):

    input KA05T -> A:  M1 (the input head is the second steering element), AOM (+1 order), iris
                       (stops the 0 order), HWP, PBS
        A PBS transmitted -> B1: M1, M2, AOM, iris, HWP, PBS
            B1 transmitted -> C1: FR (extra 45 deg fold), M1, M2, AOM, HWP, rotating-PBS RSP05, iris -> OUT
            B1 reflected   -> C2:                     M1, M2, AOM, HWP, rotating-PBS RSP05, iris -> OUT
        A PBS reflected   -> B2: M1, M2, AOM, iris, HWP, PBS
            B2 transmitted -> C3:                     M1, M2, AOM, HWP, rotating-PBS RSP05, iris -> OUT
            B2 reflected   -> C4: FR (extra 45 deg fold), M1, M2, AOM, HWP, rotating-PBS RSP05, iris -> OUT

Geometry:
* Every mirror works at 45 deg incidence (90 deg folds). Only the mirror in front of each AOM
  (A: M1, others: M2) turns by 90 deg -+ 2*theta_B = 1.0845 deg: the leg into the AOM is pre-tilted
  (795 nm, 100 MHz, TeO2 4.2 mm/us) so the +1 order leaves every AOM exactly along a board axis.
* All four output lanes run along +x and end in a KA05T on the right short edge (tail clamps within
  0.5 mm of the edge). The two siblings of a PBS always leave perpendicular to each other, so
  one output of each pair needs one extra 45 deg fold (FR) in its feed: C1 and C4 have three mirrors
  in front of their AOM (FR, M1, M2), all other lanes two (A: one plus the input head).
* AOM centre -> iris 81 mm, -> HWP 98 mm, -> PBS 121 mm (A, B1, B2). Output lanes: AOM -> HWP (RSP05)
  -> 24.52 mm -> empty RSP05 for a rotating PBS (mount only) -> iris -> >= 30 mm -> output lens-tube
  front; AOM -> iris path >= 81 mm (0/+1 separation >= 1.53 mm at the iris).
* AOMO 3100-125 on KM100PM with the lattice V9 integral seat. Orientation D: KM100PM downstream,
  RF connector on the left of the beam; U: KM100PM upstream, RF on the right. The M2 -> AOM leg is at
  least 26 mm (D) / 79 mm (U).
* KA05T fiber ports with the 76 mm rear tail-clamp hole pair. Mirrors M05 + HKTS thumbscrews, HWPs
  RSP05, PBS cube_mount_halfinch, irises IDA12.
* Reserved free space (checked by the audits): 40 x 20 mm RF elbow at every AOM connector face, 28 mm
  front access at every output head (15 mm at the input head), 20 x 40 mm tail-clamp span and a
  straight 20 mm fiber corridor to the plate edge.
* Plate 24 x 14 x 1 in (actual 603.25 x 349.25 mm, 1/8 in edge gap). Table bolts (1/4-20,
  counterbored): two per short side, 7 in apart and centred on the short edge; the two columns
  are 22 in apart (1 in table grid).
* Mounts may overhang the plate edge; every tapped-hole centre is >= 6 mm and every pocket >= 3 mm
  inside it.

Layout found with a 2-D footprint model (FreeCAD bounding boxes of the V9.7 lattice parts) and a
sequential-LP compactor; margins between different lanes 1.8 mm (hardware), 2.5 mm (pocket walls),
1.0 mm (keep-out zones), 1.2 mm beam half-width, 3 mm from any beam to a foreign knob / KM100PM; the
CAD audits are the authority.

Run in FreeCAD (Macro > Macros..., or paste into the Python console):
    example_baseplate()          (example_baseplate(drill=False) for a fast undrilled preview)
"""
import math

import FreeCAD as App
import Part

from PyOpticL import layout, optomech

INCH = layout.inch
PLATE_IN = (24, 14)
base_dx = PLATE_IN[0]*INCH
base_dy = PLATE_IN[1]*INCH
base_dz = INCH
gap = INCH/8

# table bolts, PyOpticL grid convention: hole at ((i + 0.5) in, (j + 0.5) in)
mount_holes = [(0.027904, 3.000000), (0.027904, 10.000000), (22.027904, 3.000000), (22.027904, 10.000000)]
BOLT_ROWS_APART_IN = 7        # two bolts per short side, centred on that edge
BOLT_COLUMNS_APART_IN = 22

# ---- optics geometry -------------------------------------------------------------------
LENS_TUBE_FRONT = 18.798         # KA05T lens-tube front ahead of the mount origin
REAR_CLAMP_OFFSET = 76.          # rear tail-clamp hole pair behind every KA05T
IRIS_L = 81.                     # AOM centre -> iris (A, B lanes); minimum AOM -> iris path (C lanes)
HWP_D = 98.                      # AOM centre -> HWP (A, B)
PBS_D = 121.                     # AOM centre -> PBS (A, B)
M2_TO_AOM_MIN = {'D': 26., 'U': 79.}
HWP_TO_ROT = 24.52            # output lanes: HWP RSP05 -> rotating-PBS RSP05
ROT_TO_IRIS = {1: 19.20, -1: 15.30}     # by iris post side
IRIS_TO_FRONT_MIN = {1: 30., -1: 36.5}           # iris -> output lens-tube front (>= 30 mm)
OUT_DIR = 0.                     # every output beam runs +x into its fiber head
PORT_EDGE = 0.5              # output tail clamps end within this distance of the right plate edge
OUTPUT_FRONT_ACCESS = 28.
INPUT_FRONT_ACCESS = 15.
AOM_RF_DESIGN_HZ = 100.e6
AOM_V_SOUND_MM_S = 4.2e6
DIFF_ANGLE_RAD = 0.795e-3*AOM_RF_DESIGN_HZ/AOM_V_SOUND_MM_S   # 0.018929 rad
KAPPA = math.degrees(DIFF_ANGLE_RAD)                          # 1.0845 deg

INPUT_XY = (89.4150, 42.4155)
INPUT_DIR = 0
ORDER = ('A', 'B1', 'B2', 'C1', 'C2', 'C3', 'C4')
FEEDS = {'B1': ('A', 'T'), 'B2': ('A', 'R'), 'C1': ('B1', 'T'), 'C2': ('B1', 'R'),
         'C3': ('B2', 'T'), 'C4': ('B2', 'R')}
OUTPUT_NUMBER = {'C4': 1, 'C3': 2, 'C2': 3, 'C1': 4}     # output head number, counted from the top of the right edge
# d1: feed (PBS centre, FR or input lens-tube front) -> M1; J: M1 -> M2 jog; a2: M2 (A: M1) -> AOM.
# side: jog (A: lane) to the left (+1) / right (-1) of the feed. mode Z: the lane continues the feed
# direction, U: it runs back against it. orient D/U: see above. post: iris post side (+1 toward
# the AOM, -1 toward the fiber). inv: PBS reflection side (PyOpticL invert).
# C lanes: fmode 'pre' = extra fold FR at dR after the PBS turning the feed by 90*fr deg;
# sH: AOM -> HWP; dIF: iris -> lens-tube front.
LANES = {
    'A': {'d1': 24.0983, 'a2': 33.9461, 'side': +1, 'orient': 'D', 'post': +1, 'inv': 0},
    'B1': {'d1': 20.6871, 'J': 53.0353, 'a2': 34.6620, 'side': -1, 'mode': 'U', 'orient': 'D', 'post': +1, 'inv': 0},
    'B2': {'d1': 48.5416, 'J': 92.9594, 'a2': 26.0000, 'side': -1, 'mode': 'U', 'orient': 'D', 'post': +1, 'inv': 0},
    'C1': {'fmode': 'pre', 'dR': 43.1227, 'fr': +1, 'd1': 126.2710, 'J': 47.8219, 'a2': 79.0000, 'side': +1, 'mode': 'Z', 'orient': 'U', 'post': +1, 'sH': 37.2800, 'dIF': 30.0000},
    'C2': {'fmode': 'none', 'd1': 82.8844, 'J': 57.5677, 'a2': 58.9636, 'side': +1, 'mode': 'Z', 'orient': 'D', 'post': +1, 'sH': 88.2675, 'dIF': 41.9318},
    'C3': {'fmode': 'none', 'd1': 21.2740, 'J': 56.0364, 'a2': 127.0032, 'side': -1, 'mode': 'Z', 'orient': 'U', 'post': +1, 'sH': 37.2800, 'dIF': 41.7401},
    'C4': {'fmode': 'pre', 'dR': 43.5128, 'fr': -1, 'd1': 65.2904, 'J': 45.2633, 'a2': 46.6523, 'side': -1, 'mode': 'Z', 'orient': 'D', 'post': +1, 'sH': 85.8401, 'dIF': 30.0001},
}

RED = (.85, .15, .1)
BLUE = (.1, .35, .95)
GREEN = (.05, .6, .3)
PURPLE = (.65, .15, .85)
ORANGE = (.9, .5, .05)
LANE_COLOR = {'A': RED, 'B1': ORANGE, 'B2': ORANGE, 'C1': GREEN, 'C2': BLUE, 'C3': PURPLE, 'C4': (.85, .1, .55)}
BEAM = ('Nominal 0.6 mm beam radius (collimated ~0.43 mm 1/e2 radius from a f = 4.5 mm fiber '
        'collimator, rounded up); +1 order on the board axis, 0 order 2*theta_B off it. '
        'Measured q/M2 and RF tuning range pending.')


def _u(deg):
    return (math.cos(math.radians(deg)), math.sin(math.radians(deg)))


def _add(p, d, t):
    return (p[0] + d[0]*t, p[1] + d[1]*t)


def _pbs_reflect(pang, invert, incoming):
    a_norm = pang + 180 + (-135 if invert else 135)
    return (2*a_norm - incoming - 180) % 360


def lane_geometry():
    """Every nominal point of the seven lanes (board frame, mm)."""
    geo = {}
    for name in ORDER:
        q = LANES[name]
        if name == 'A':
            src, d0 = _add(INPUT_XY, _u(INPUT_DIR), LENS_TUBE_FRONT), INPUT_DIR
        else:
            parent, port = FEEDS[name]
            src = geo[parent]['pbs']
            d0 = geo[parent]['T'] if port == 'T' else geo[parent]['R']
        g = dict(src=src, d_src=d0 % 360)
        p0 = src
        if name.startswith('C') and q['fmode'] == 'pre':
            g['fr'] = _add(src, _u(d0), q['dR'])
            d0 = (d0 + 90*q['fr']) % 360
            p0 = g['fr']
        g.update(p0=p0, d0=d0 % 360)
        m1 = _add(p0, _u(d0), q['d1'])
        if name == 'A':
            lane_dir = (d0 + 90*q['side']) % 360
            in_dir = lane_dir + (KAPPA if q['orient'] == 'D' else -KAPPA)
            m2 = None
            aom = _add(m1, _u(in_dir), q['a2'])
        else:
            jog = (d0 + 90*q['side']) % 360
            lane_dir = d0 % 360 if q['mode'] == 'Z' else (d0 + 180) % 360
            in_dir = lane_dir + (KAPPA if q['orient'] == 'D' else -KAPPA)
            m2 = _add(m1, _u(jog), q['J'])
            aom = _add(m2, _u(in_dir), q['a2'])
        g.update(lane_dir=lane_dir, in_dir=in_dir, m1=m1, m2=m2, aom=aom,
                 aom_angle=(lane_dir if q['orient'] == 'U' else lane_dir + 180) % 360,
                 rf_side=_u(lane_dir - 90 if q['orient'] == 'U' else lane_dir + 90))
        if name.startswith('C'):
            d = _u(lane_dir)
            g['hwp'] = _add(aom, d, q['sH'])
            g['rot'] = _add(g['hwp'], d, HWP_TO_ROT)
            g['iris'] = _add(g['rot'], d, ROT_TO_IRIS[q['post']])
            g['front'] = _add(g['iris'], d, q['dIF'])
            g['port'] = _add(g['front'], d, LENS_TUBE_FRONT)
            g['iris_angle'] = (lane_dir if q['post'] < 0 else lane_dir + 180) % 360
        else:
            g['iris'] = _add(aom, _u(lane_dir), IRIS_L)
            g['iris_angle'] = (lane_dir if q['post'] < 0 else lane_dir + 180) % 360
            g['hwp'] = _add(aom, _u(lane_dir), HWP_D)
            g['pbs'] = _add(aom, _u(lane_dir), PBS_D)
            g['pang'] = lane_dir
            g['T'] = lane_dir
            g['R'] = _pbs_reflect(lane_dir, q['inv'], lane_dir)
        geo[name] = g
    return geo


def lane_points(name, g):
    """Nominal +1-order axis of a lane, from its feed to its last element."""
    pts = [g['src']]
    if 'fr' in g:
        pts.append(g['fr'])
    pts.append(g['m1'])
    if g['m2'] is not None:
        pts.append(g['m2'])
    pts.append(g['aom'])
    if name.startswith('C'):
        pts += [g['hwp'], g['rot'], g['iris'], g['front']]
    else:
        pts += [g['iris'], g['hwp'], g['pbs']]
    return pts


def beam_crossings(geo):
    """Pairs of beam segments of different lanes that touch (shared PBS split points excepted)."""
    segs = []
    for name in ORDER:
        pts = lane_points(name, geo[name])
        for k in range(len(pts) - 1):
            segs.append((name, k, pts[k], pts[k + 1]))

    def cross(p, q, r, s):
        d = (q[0]-p[0])*(s[1]-r[1]) - (q[1]-p[1])*(s[0]-r[0])
        if abs(d) < 1e-12:
            return False
        t = ((r[0]-p[0])*(s[1]-r[1]) - (r[1]-p[1])*(s[0]-r[0]))/d
        u = ((r[0]-p[0])*(q[1]-p[1]) - (r[1]-p[1])*(q[0]-p[0]))/d
        return -1e-9 <= t <= 1 + 1e-9 and -1e-9 <= u <= 1 + 1e-9

    out = []
    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            a, b = segs[i], segs[j]
            if a[0] == b[0]:
                continue
            shared = any(math.hypot(x[0]-y[0], x[1]-y[1]) < 1e-6 for x in (a[2], a[3]) for y in (b[2], b[3]))
            if shared:
                continue
            if cross(a[2], a[3], b[2], b[3]):
                out.append(('%s#%d' % (a[0], a[1]), '%s#%d' % (b[0], b[1])))
    return out


def build(x=0, y=0, angle=0, drill=True):
    """Build the Splitting Board V2 in a new document; returns (doc, info)."""
    doc = App.newDocument('Splitting_Board_V2') if App.ActiveDocument is None else App.ActiveDocument
    baseplate = layout.baseplate(base_dx, base_dy, base_dz, x=x, y=y, angle=angle, gap=gap,
                                 drill=False, mount_holes=mount_holes,
                                 name='Splitting plate %d x %d in' % PLATE_IN)
    plate = doc.getObject(baseplate.active_baseplate)
    info = {'mode': 'splitting', 'plate': plate, 'roots': {}, 'paths': [], 'arms': [],
            'reservations': [], 'extra_cuts': [], 'geometry_assertions': [],
            'alternate': False, 'service_regions': [], 'output_optical_routes': [],
            'requirements': {'mirror_roles': [], 'spherical_groups': []},
            'isolator': None, 'cell': None,
            'plate_size_mm': [base_dx, base_dy, base_dz],
            'layout_status': 'Splitting Board V2 (1 -> 2 -> 4, seven single-pass AOMs, outputs on one short '
                             'edge, no beam crossings); not machined.'}
    info['mount_holes_mm'] = [((mx + .5)*INCH, (my + .5)*INCH) for mx, my in mount_holes]

    def put(name, cls, px, py, pangle=0, **kw):
        obj = baseplate.place_element(name, cls, x=px, y=py, angle=pangle, **kw)
        info['roots'][name] = obj
        return obj

    def fold_angle(a, p, b):
        u = (p[0]-a[0], p[1]-a[1]); v = (b[0]-p[0], b[1]-p[1])
        nu, nv = math.hypot(*u), math.hypot(*v)
        n = (v[0]/nv - u[0]/nu, v[1]/nv - u[1]/nu)
        return math.degrees(math.atan2(n[1], n[0]))

    def bend(name, a, p, b):
        return put(name, optomech.circular_mirror_union_optic, p[0], p[1], fold_angle(a, p, b),
                   thickness=6, mount_type=optomech.mirror_mount_M05, mount_args={'thumbscrews': True})

    def path(name, points, color):
        obj = doc.addObject('Part::Feature', name)
        obj.Label = name + ' (nominal axis)'
        obj.Shape = Part.makePolygon([App.Vector(px, py, 0) for px, py in points])
        obj.ViewObject.LineColor = color
        obj.ViewObject.LineWidth = 2.5
        obj.addProperty('App::PropertyString', 'Scope').Scope = BEAM
        obj.addProperty('App::PropertyBool', 'Bidirectional').Bidirectional = False
        obj.addProperty('App::PropertyAngle', 'DiffractionKink').DiffractionKink = KAPPA
        info['paths'].append({'name': name, 'points': [tuple(map(float, p)) for p in points],
                              'object': obj.Name, 'envelope': [0.6]*len(points), 'assumption': BEAM,
                              'diffraction_kink_deg': KAPPA})
        return obj

    def service(name, kind, owner, origin, direction, length, width, allowed=(), note=''):
        info['service_regions'].append({
            'name': name, 'kind': kind, 'owner': owner.Name, 'origin_xy_mm': [float(origin[0]), float(origin[1])],
            'direction_xy': [float(direction[0]), float(direction[1])], 'length_mm': float(length),
            'width_mm': float(width), 'allowed_paths': list(allowed), 'dimensions_verified': False,
            'assumptions': [note] if note else []})

    geo = lane_geometry()
    inport = put('Input KA05T', optomech.fiberport_mount_KA05T_holes, INPUT_XY[0], INPUT_XY[1], INPUT_DIR,
                 rear_hole_x_offset=REAR_CLAMP_OFFSET, mount_args={'thumbscrews': True})
    ports, aoms = {}, {}
    for k, name in enumerate(ORDER):
        q, g = LANES[name], geo[name]
        if 'fr' in g:
            fr = bend(name + ' FR', g['src'], g['fr'], g['m1'])
            fr.addProperty('App::PropertyString', 'Purpose').Purpose = (
                'Extra 45 deg routing fold: the PBS sibling outputs are perpendicular, this lane must turn '
                'once more so its fiber head sits on the output edge.')
        if name == 'A':
            bend(name + ' M1', g['p0'], g['m1'], g['aom'])
        else:
            bend(name + ' M1', g['p0'], g['m1'], g['m2'])
            bend(name + ' M2', g['m1'], g['m2'], g['aom'])
        aom = put(name + ' AOMO 3100-125', optomech.AOMO_3100_125, g['aom'][0], g['aom'][1], g['aom_angle'],
                  forward_direction=-1, backward_direction=1, diffraction_angle=KAPPA,
                  surface_adapter_args={'adapter_height': 5})
        seat = optomech.integrate_aom(baseplate, aom)
        info['extra_cuts'].append(seat)
        aoms[name] = aom
        if name.startswith('C'):
            out_no = OUTPUT_NUMBER[name]
            put(name + ' HWP', optomech.waveplate, g['hwp'][0], g['hwp'][1], g['lane_dir'],
                mount_type=optomech.rotation_stage_rsp05)
            # empty RSP05 (same placement as the HWP mount: 0.5 mm behind the optic plane)
            dl = _u(g['lane_dir'])
            rot = put(name + ' rotating-PBS RSP05', optomech.rotation_stage_rsp05,
                      g['rot'][0] - 0.5*dl[0], g['rot'][1] - 0.5*dl[1], g['lane_dir'])
            rot.addProperty('App::PropertyString', 'Purpose').Purpose = (
                'Empty RSP05: user bonds a PBS to the rotating front face; no PBS or waveplate modeled.')
            put(name + ' iris', optomech.pinhole_ida12, g['iris'][0], g['iris'][1], g['iris_angle'])
            ports[name] = put('Output %d KA05T (%s)' % (out_no, name), optomech.fiberport_mount_KA05T_holes,
                              g['port'][0], g['port'][1], (g['lane_dir'] + 180) % 360,
                              rear_hole_x_offset=REAR_CLAMP_OFFSET, mount_args={'thumbscrews': True})
        else:
            put(name + ' iris', optomech.pinhole_ida12, g['iris'][0], g['iris'][1], g['iris_angle'])
            put(name + ' HWP', optomech.waveplate, g['hwp'][0], g['hwp'][1], g['lane_dir'],
                mount_type=optomech.rotation_stage_rsp05)
            put(name + ' PBS', optomech.cube_splitter, g['pbs'][0], g['pbs'][1], g['pang'],
                invert=bool(q['inv']), mount_type=optomech.cube_mount_halfinch)
        path(name + ' lane', lane_points(name, g), LANE_COLOR[name])
        info['arms'].append({'id': k + 1, 'lane': name, 'aom': aom.Name, 'integral_seat': seat.Name,
                             'beam_path': name + ' lane', 'single_pass': True, 'diffraction_kink_deg': KAPPA})
        rf = g['rf_side']
        service(name + ' AOM RF elbow', 'aom_sma', aom, _add(g['aom'], rf, 33.02), rf, 40., 20.,
                note='Connector on the AOM face away from the beam (STL box); 40 mm of free space for the '
                     'L-shaped SMB elbow; cable taped down afterwards.')
        # paraxial 0-order screen: AOM -> iris (-> HWP -> PBS) | AOM -> HWP -> RSP05 -> iris -> fiber
        events = [{'type': 'aom', 'name': name + ' AOM', 'xy': g['aom']}]
        if name.startswith('C'):
            events += [{'type': 'hwp', 'name': name + ' HWP', 'xy': g['hwp']},
                       {'type': 'rotation_mount', 'name': name + ' rotating-PBS RSP05', 'xy': g['rot']},
                       {'type': 'iris', 'name': name + ' iris', 'xy': g['iris']},
                       {'type': 'fiber', 'name': name + ' output KA05T', 'xy': g['front']}]
        else:
            events += [{'type': 'iris', 'name': name + ' iris', 'xy': g['iris']},
                       {'type': 'hwp', 'name': name + ' HWP', 'xy': g['hwp']},
                       {'type': 'pbs', 'name': name + ' PBS', 'xy': g['pbs']}]
        info['output_optical_routes'].append({'arm': name, 'events': events})
    info['expected_arm_count'] = len(ORDER)
    info['output_order_expected_routes'] = len(ORDER)

    # fiber heads: front access, tail clamps
    for name, port in ports.items():
        g = geo[name]
        d = _u(g['lane_dir'] + 180)
        service(port.Label + ' front access', 'fiber_front', port, g['front'], d, OUTPUT_FRONT_ACCESS, 20.,
                allowed=[name + ' lane'], note='20 mm full front access width; 28 mm axial access.')
    service('Input KA05T front access', 'fiber_front', inport,
            _add(INPUT_XY, _u(INPUT_DIR), LENS_TUBE_FRONT), _u(INPUT_DIR), INPUT_FRONT_ACCESS, 20.,
            allowed=['A lane'], note='20 mm full front access width; 15 mm axial access (input head).')
    info['service_clearance'] = {'min_length_mm': {'fiber_front': INPUT_FRONT_ACCESS, 'aom_sma': 40.}}
    info['fiber_clearance'] = {'rear_offsets_mm': [REAR_CLAMP_OFFSET], 'clamp_width_mm': 30.}
    info['hole_clearance'] = {'platform_beam_crossings_allowed': True}
    info['pbs_path_specs'] = [
        {'role': 'main', 'cube': 'A PBS', 'incoming_path': 'A lane', 'outgoing_paths': ['B1 lane', 'B2 lane']},
        {'role': 'main', 'cube': 'B1 PBS', 'incoming_path': 'B1 lane', 'outgoing_paths': ['C1 lane', 'C2 lane']},
        {'role': 'main', 'cube': 'B2 PBS', 'incoming_path': 'B2 lane', 'outgoing_paths': ['C3 lane', 'C4 lane']}]

    # ---- geometry assertions -------------------------------------------------------------
    def dist(p, q):
        return math.hypot(q[0]-p[0], q[1]-p[1])

    def turn(a, p, b):
        u = (p[0]-a[0], p[1]-a[1]); v = (b[0]-p[0], b[1]-p[1])
        c = (u[0]*v[0] + u[1]*v[1])/(math.hypot(*u)*math.hypot(*v))
        return math.degrees(math.acos(max(-1., min(1., c))))

    A = info['geometry_assertions']
    right_edge = base_dx - gap
    for name in ORDER:
        q, g = LANES[name], geo[name]
        if 'fr' in g:
            A.append({'name': name + ': FR folds the beam by exactly 90 deg (45 deg incidence)',
                      'measured': turn(g['src'], g['fr'], g['m1']), 'expected': 90., 'tolerance': 1e-7})
        if name == 'A':
            A.append({'name': 'A: M1 fold = 90 deg -+ 2 theta_B (|turn - 90| in deg; pre-tilted AOM input)',
                      'measured': abs(turn(g['p0'], g['m1'], g['aom']) - 90.), 'expected': KAPPA, 'tolerance': 1e-7})
            A.append({'name': 'A: M1 -> AOM >= KM100PM clearance (excess, mm)',
                      'measured': min(0., dist(g['m1'], g['aom']) - M2_TO_AOM_MIN[q['orient']]), 'expected': 0.,
                      'tolerance': 1e-7})
        else:
            A.append({'name': name + ': M1 folds the beam by exactly 90 deg', 'measured': turn(g['p0'], g['m1'], g['m2']),
                      'expected': 90., 'tolerance': 1e-7})
            A.append({'name': name + ': M2 fold = 90 deg -+ 2 theta_B (|turn - 90| in deg; pre-tilted AOM input)',
                      'measured': abs(turn(g['m1'], g['m2'], g['aom']) - 90.), 'expected': KAPPA, 'tolerance': 1e-7})
            A.append({'name': name + ': M2 -> AOM >= KM100PM clearance (excess, mm)',
                      'measured': min(0., dist(g['m2'], g['aom']) - M2_TO_AOM_MIN[q['orient']]), 'expected': 0.,
                      'tolerance': 1e-7})
        A.append({'name': name + ': +1 order leaves the AOM along a board axis (deg off axis)',
                  'measured': min(g['lane_dir'] % 90, 90 - g['lane_dir'] % 90), 'expected': 0., 'tolerance': 1e-9})
        if name.startswith('C'):
            A.append({'name': name + ': output beam runs +x into its fiber head (deg)',
                      'measured': min(abs(g['lane_dir'] - OUT_DIR) % 360, 360 - abs(g['lane_dir'] - OUT_DIR) % 360),
                      'expected': 0., 'tolerance': 1e-9})
            path_to_iris = dist(g['aom'], g['hwp']) + dist(g['hwp'], g['rot']) + dist(g['rot'], g['iris'])
            A.append({'name': name + ': AOM -> iris path >= 81 mm (0/+1 separation >= 1.53 mm; shortfall mm)',
                      'measured': min(0., path_to_iris - IRIS_L), 'expected': 0., 'tolerance': 1e-7})
            A.append({'name': name + ': HWP -> rotating-PBS RSP05', 'measured': dist(g['hwp'], g['rot']),
                      'expected': HWP_TO_ROT, 'tolerance': 1e-7})
            A.append({'name': name + ': iris -> output lens-tube front >= 30 mm (shortfall mm)',
                      'measured': min(0., dist(g['iris'], g['front']) - IRIS_TO_FRONT_MIN[q['post']]),
                      'expected': 0., 'tolerance': 1e-7})
            clamp_end = g['port'][0] + REAR_CLAMP_OFFSET + 10.
            A.append({'name': name + ': output tail clamp within %g mm of the right plate edge (excess mm)' % PORT_EDGE,
                      'measured': max(0., right_edge - clamp_end - PORT_EDGE), 'expected': 0., 'tolerance': 0.05})
        else:
            A.append({'name': name + ': AOM -> iris (0/+1 separation 1.53 mm)', 'measured': dist(g['aom'], g['iris']),
                      'expected': IRIS_L, 'tolerance': 1e-7})
            A.append({'name': name + ': AOM -> HWP', 'measured': dist(g['aom'], g['hwp']), 'expected': HWP_D,
                      'tolerance': 1e-7})
            A.append({'name': name + ': AOM -> PBS', 'measured': dist(g['aom'], g['pbs']), 'expected': PBS_D,
                      'tolerance': 1e-7})
    A.append({'name': 'No beam crosses another beam (crossing pairs)', 'measured': len(beam_crossings(geo)),
              'expected': 0, 'tolerance': 0.})
    xs = sorted(set(round(x, 6) for x, _ in info['mount_holes_mm']))
    ys = sorted(set(round(y, 6) for _, y in info['mount_holes_mm']))
    A.append({'name': 'Table bolts: columns %d in apart' % BOLT_COLUMNS_APART_IN, 'measured': xs[-1] - xs[0],
              'expected': BOLT_COLUMNS_APART_IN*INCH, 'tolerance': 1e-6})
    A.append({'name': 'Table bolts: rows %d in apart (<= 10 in)' % BOLT_ROWS_APART_IN, 'measured': ys[-1] - ys[0],
              'expected': BOLT_ROWS_APART_IN*INCH, 'tolerance': 1e-6})
    A.append({'name': 'Table bolts centred on the short edge (offset mm)', 'measured': (ys[0] + ys[-1])/2 - base_dy/2,
              'expected': 0., 'tolerance': 1e-6})
    info['lane_geometry'] = {n: {k: (list(v) if isinstance(v, tuple) else v) for k, v in g.items()}
                             for n, g in geo.items()}
    info['beam_crossings'] = beam_crossings(geo)

    # ---- cut the plate once every element and machining volume is in place ----
    doc.recompute()
    layout.redraw()
    plate.Drill = drill
    plate.touch()
    doc.recompute()
    doc.Label = 'Splitting Board V2 (%d x %d in)' % PLATE_IN
    return doc, info


def example_baseplate(x=0, y=0, angle=0, drill=True):
    """Repository entry point (as for the other boards): build the board, return the info dict."""
    doc, info = build(x=x, y=y, angle=angle, drill=drill)
    return info


if __name__ == '__main__':
    example_baseplate()
    layout.redraw()
