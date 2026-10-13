"""Splitting Board V2 with seven entrance HWPs - 24 x 14 in: one fiber in, seven single-pass AOMs, four fibers out on one short edge.

Beam tree (every split remains HWP -> PBS). The design requires no beam crossings or
hardware underpasses; see the saved native production validation report:

    input KM05T -> A:  M1 (the input head is the second steering element), entrance HWP, AOM (RF off, order 0),
                       iris, HWP, PBS
        A PBS transmitted -> B1: M1, M2, entrance HWP, AOM, iris, HWP, PBS
            B1 transmitted -> C1: FR, M1, M2, entrance HWP, AOM, HWP, bonded PBS, output fold, iris, output fold -> OUT
            B1 reflected   -> C2:                     M1, M2, entrance HWP, AOM, two output folds, HWP, bonded PBS, iris -> OUT
        A PBS reflected   -> B2: M1, M2, entrance HWP, AOM, iris, HWP, PBS
            B2 transmitted -> C3:                     M1, M2, entrance HWP, AOM, two output folds, HWP, bonded PBS, iris -> OUT
            B2 reflected   -> C4: FR (extra 45 deg fold), M1, M2, entrance HWP, AOM, two output folds, HWP, bonded PBS, iris -> OUT

Geometry:
* AOM RF is off. The drawn beam is the undeflected zero order. Every mirror works at 45 deg
  incidence, every turn is 90 deg, and every free-space leg is horizontal or vertical. This is
  a mechanical zero-order reference layout, not a validated RF-on first-order optical system.
* All four output lanes have two steering mirrors, then run along +x into a KM05T on the
  right short edge (tail clamps within
  0.5 mm of the edge). The two siblings of a PBS always leave perpendicular to each other, so
  one output of each pair needs one extra 45 deg fold (FR) in its feed: C1 and C4 have three mirrors
  in front of their AOM (FR, M1, M2), all other lanes two (A: one plus the input head).
* AOM centre -> iris 81 mm (A, B1, B2). B1/B2 retain -> HWP 98 mm and -> PBS 121 mm.
  A retains 96.5 mm and 119.5 mm to those optics; downstream HWP -> PBS remains 23 mm.
  Output lanes retain AOM
  -> HWP (first RSP05) -> real 12.7 mm PBS cube bonded upstream of the second RSP05 -> iris
  -> >= 30 mm -> output lens-tube front. The HWP and second stage references are 32 mm apart;
  reversing the second stage puts the cube centre 14.297 mm upstream of its reference. Four
  modelled 0.2 mm adhesive pads join cube corners to the engraved rotor. Adhesive thickness is
  an assembly assumption; bond strength and coating compatibility are not certified.
  C1's two added mirrors straddle its iris; C2-C4's two mirrors precede their HWP. AOM -> iris
  path >= 81 mm is retained as a mechanical spacing. The iris is not claimed to reject order 0.
* A dedicated entrance HWP on a real RSP05 and its lip adapter precedes each AOM,
  in addition to all seven existing downstream HWPs. Entrance optical-centre spacings
  are A 28.3 mm, B1 27.8 mm, B2/C2/C4 28 mm and C1/C3 81 mm. The U-facing KM100PM
  extends about 67.58 mm upstream, so C1/C3 sit before that assembly.
  In-plane translations provide adjustment clearance around these HWPs and C1's
  existing downstream HWP while retaining all five fiber heads, tail-clamp holes,
  table holes and the board outline. The AOM upper adapters, integral seats and
  mounting depths remain identical to the lattice installation. The catalogue
  +/-4-degree mount travel is not guaranteed by this board: the unchanged seat
  limits some pitch/combined settings. See the explicit motion-audit scope.
* AOMO 3100-125 on KM100PM with the lattice V9 integral seat. Orientation D: KM100PM downstream,
  RF connector on the left of the beam; U: KM100PM upstream, RF on the right. The M2 -> AOM leg is at
  least 26 mm (D) / 79 mm (U).
* KM05T fiber ports on the unchanged Surface_Adapter_fiberport_lip. Each adapter uses its two
  mounting taps; its optional Y-shape and rear-hole patterns are disabled. Two board-level
  BareTappedHole features retain the original rear tail-clamp X positions: 76 mm behind each
  head except C4, whose head moves 32 mm toward its unchanged pair (44 mm rear offset). The lens
  tube, lens adapter, fiber adapter and optical reference are unchanged from the KA05T assembly.
  Mirrors M05 + HKTS thumbscrews, HWPs RSP05, PBS cube_mount_halfinch, irises IDA12.
* Reserved free space (checked by the audits): 40 x 20 mm RF elbow at every AOM connector face, 28 mm
  front access at every output head (15 mm at the input head), 20 x 40 mm tail-clamp span and a
  straight 20 mm fiber corridor to the plate edge.
* Plate 24 x 14 x 1 in (actual 603.25 x 349.25 mm, 1/8 in edge gap). Table bolts (1/4-20,
  counterbored): lower-right anchor 1 in from both finished edges; the other three lie
  (-22, +2), (-22, +12), and (0, +10) in from that anchor. The two columns are 22 in apart,
  with 10 in between each column's bolts and staggered rows on a shared 1 in table grid.
* C1 FR and C1 M1 each have a lower mirror-mount body corner overhanging the plate (conservative
  bounding-box overhang about 6.44 mm), in addition to the listed adjustment-knob overhangs.
  Their mounting taps remain on the plate; the edge audit checks every tapped-hole centre
  >= 6 mm and every pocket >= 3 mm inside it. Inspect the supported contact area before assembly.

Output folds and upstream feed distances are arranged around the actual M05/HKTS and KM100PM
hardware. The CAD projection, service, machining, and bonded-cube sweep audits are the authority;
no claim of mechanical clearance is inferred from the drawn centre lines alone.

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

# Anchor one inch from the actual right and lower machined edges. The remaining
# three bolts share its one-inch table grid, with staggered rows for clearance.
TABLE_MOUNT_ANCHOR_MM = (base_dx-gap-INCH, gap+INCH)
TABLE_MOUNT_OFFSETS_IN = ((0, 0), (-22, 2), (-22, 12), (0, 10))
mount_holes = [(TABLE_MOUNT_ANCHOR_MM[0]/INCH+dx-.5,
                TABLE_MOUNT_ANCHOR_MM[1]/INCH+dy-.5)
               for dx, dy in TABLE_MOUNT_OFFSETS_IN]

# ---- optics geometry -------------------------------------------------------------------
LENS_TUBE_FRONT = 18.798         # common KM05T/KA05T lens-tube front ahead of the mount origin
REAR_CLAMP_OFFSET = 76.          # default rear tail-clamp offset; C4 moves within its fixed pair
OUTPUT_REAR_CLAMP_OFFSETS = {'C1': 76., 'C2': 76., 'C3': 76., 'C4': 44.}
REAR_CLAMP_HOLE_SPACING = 18.328
IRIS_L = 81.                     # AOM centre -> iris (A, B lanes); minimum AOM -> iris path (C lanes)
HWP_D = 98.                      # default AOM centre -> HWP (B1/B2; A has an explicit override)
PBS_D = 121.                     # default AOM centre -> PBS (B1/B2; A has an explicit override)
M2_TO_AOM_MIN = {'D': 26., 'U': 79.}
# Optical-centre separation to the AOM, in the incoming propagation direction.
# U-facing mounts occupy the upstream 67.58 mm, so their HWP sits before KM100PM.
PRE_AOM_HWP_TO_AOM_MM = {'A': 28.3, 'B1': 27.8, 'B2': 28., 'C1': 81.,
                        'C2': 28., 'C3': 81., 'C4': 28.}
HWP_TO_ROT = 32.              # HWP optical plane -> reversed rotating-PBS stage reference
ROT_TO_IRIS = {1: 19.20, -1: 15.30}     # by iris post side
IRIS_TO_FRONT_MIN = {1: 30., -1: 36.5}           # iris -> output lens-tube front (>= 30 mm)
OUT_DIR = 0.                     # every output beam runs +x into its fiber head
PORT_EDGE = 0.5              # output tail clamps end within this distance of the right plate edge
OUTPUT_FRONT_ACCESS = 28.
INPUT_FRONT_ACCESS = 15.
AOM_RF_DESIGN_HZ = 100.e6
AOM_V_SOUND_MM_S = 4.2e6
DIFF_ANGLE_RAD = 0.795e-3*AOM_RF_DESIGN_HZ/AOM_V_SOUND_MM_S  # future RF-on estimate only; unused by geometry
KAPPA = 0.                       # RF off: order 0 passes straight through every AOM

INPUT_XY = (89.4150, 41.5155)
INPUT_DIR = 0
ORDER = ('A', 'B1', 'B2', 'C1', 'C2', 'C3', 'C4')
FEEDS = {'B1': ('A', 'T'), 'B2': ('A', 'R'), 'C1': ('B1', 'T'), 'C2': ('B1', 'R'),
         'C3': ('B2', 'T'), 'C4': ('B2', 'R')}
OUTPUT_NUMBER = {'C4': 1, 'C3': 2, 'C2': 3, 'C1': 4}     # output head number, counted from the top of the right edge
# d1: feed (PBS centre, FR or input lens-tube front) -> M1; J: M1 -> M2 jog; a2: M2 (A: M1) -> AOM.
# side: jog (A: lane) to the left (+1) / right (-1) of the feed. mode Z: the lane continues the feed
# direction, U: it runs back against it. orient D/U: see above. post: iris post side (+1 toward
# the AOM, -1 toward the fiber). inv: PBS reflection side (PyOpticL invert).
# C lanes: fmode 'pre' = extra fold FR at dR after the PBS turning the feed by 90*fr deg.
LANES = {
    'A': {'d1': 24.0983, 'a2': 33.9461, 'side': +1, 'orient': 'D', 'post': +1, 'inv': 0},
    'B1': {'d1': 20.6871, 'J': 53.0353, 'a2': 34.6620, 'side': -1, 'mode': 'U', 'orient': 'D', 'post': +1, 'inv': 0},
    'B2': {'d1': 48.5416, 'J': 92.9594, 'a2': 26.0000, 'side': -1, 'mode': 'U', 'orient': 'D', 'post': +1, 'inv': 0},
    'C1': {'fmode': 'pre', 'dR': 43.1227, 'fr': +1, 'd1': 126.2710, 'J': 47.8219, 'a2': 79.0000, 'side': +1, 'mode': 'Z', 'orient': 'U', 'post': +1},
    'C2': {'fmode': 'none', 'd1': 82.8844, 'J': 57.5677, 'a2': 58.9636, 'side': +1, 'mode': 'Z', 'orient': 'D', 'post': +1},
    'C3': {'fmode': 'none', 'd1': 21.2740, 'J': 56.0364, 'a2': 127.0032, 'side': -1, 'mode': 'Z', 'orient': 'U', 'post': +1},
    'C4': {'fmode': 'pre', 'dR': 43.5128, 'fr': -1, 'd1': 65.2904, 'J': 45.2633, 'a2': 46.6523, 'side': -1, 'mode': 'Z', 'orient': 'D', 'post': +1},
}

# Two 45-degree output folds preserve four fibres on the same short edge.
# Every AOM is modelled with an undeflected, axis-aligned zero-order beam.
LANES['C1']['d1'] -= 14.
LANES['C1']['dR'] -= 2.
LANES['C1']['J'] -= 2.       # raise only FR/M1; keep the AOM and its M2 fixed
LANES['C2']['d1'] -= 14.
LANES['C2']['a2'] = 26.
LANES['C3']['a2'] = 79.
LANES['C3']['J'] += 3.3
LANES['C4']['orient'] = 'D'
LANES['C4']['a2'] = 47.6523
LANES['C4']['dR'] -= 6.
LANES['C4']['J'] -= 8.5
LANES['C4']['post'] = -1        # keep the upper output's iris post on the board
# Entrance HWPs: retain all A/B PBS coordinates so every downstream feed stays fixed.
# A's input/M1 move -0.9 mm in Y, while AOM/iris move +1.5 mm for adapter clearance.
# Shorten only A's post-AOM distances to keep its existing HWP/PBS in place.
LANES['A']['a2'] += 2.4
LANES['A']['post_hwp_distance'] = HWP_D - 1.5
LANES['A']['post_pbs_distance'] = PBS_D - 1.5
# Increase B2's reflected feed and final leg together to move only its two mirrors.
LANES['B2']['d1'] += 11.
LANES['B2']['a2'] += 11.
LANES['C1']['a2'] += 18.
LANES['C2']['a2'] += 11.
LANES['C3']['a2'] += 18.
# Adjustment clearance: move optics in plane only. The shared lattice AOM
# adapter, integral seat, bearing stock and mounting depth remain unchanged.
# Reserve the external hardware against a 4-degree any-axis rotation cone
# about the ideal sphere/cone contact centre, with 1 mm extra separation.
# This is NOT a full +/-4-degree board-clearance qualification: the unchanged
# lattice seat can restrict pitch before the mount's catalogue limit.
LANES['A']['a2'] += 9.5
LANES['B1']['a2'] += 9.5
LANES['B2']['d1'] += 8.5
LANES['B2']['J'] -= 9.5
LANES['B2']['a2'] += 8.5
LANES['C1']['d1'] -= 8.5
LANES['C2']['d1'] -= 8.5
LANES['C2']['a2'] += 8.5
OUTPUT_DOGLEGS = {
    'C1': {'x': 464., 'y': 31., 'hwp_distance': 15.},
    'C2': {'x': 397.5, 'y': 146.5, 'hwp_distance': 15.},
    'C3': {'x': 400., 'y': 207., 'hwp_distance': 15.},
    'C4': {'x': 434.8, 'y': 325., 'hwp_distance': 15.},
}
OUTPUT_PORT_X = {'C1': 520.4149980904114, 'C2': 519.9148874122972,
                 'C3': 519.9150781884387, 'C4': 552.415072253436}
BONDED_CUBE_CENTRE_OFFSET = 14.297  # 7.747 mm rotor face + 0.2 mm glue + 6.35 mm

RED = (.85, .15, .1)
BLUE = (.1, .35, .95)
GREEN = (.05, .6, .3)
PURPLE = (.65, .15, .85)
ORANGE = (.9, .5, .05)
LANE_COLOR = {'A': RED, 'B1': ORANGE, 'B2': ORANGE, 'C1': GREEN, 'C2': BLUE, 'C3': PURPLE, 'C4': (.85, .1, .55)}
BEAM = ('AOM RF off: undeflected zero-order reference beam, nominal 0.6 mm radius '
        '(collimated ~0.43 mm 1/e2 radius from a f = 4.5 mm fiber collimator, rounded up). '
        'All free-space legs are axis-aligned. RF-on first-order coupling and order rejection '
        'are outside this model; measured q/M2 remains pending.')


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
        g['pre_aom_hwp'] = _add(aom, _u(in_dir), -PRE_AOM_HWP_TO_AOM_MM[name])
        # Reverse the RSP05 assembly to minimize its downstream intrusion.
        # The waveplate transmission axis is the same undirected optical line.
        g['pre_aom_hwp_angle'] = (in_dir + 180.) % 360.
        if name.startswith('C'):
            d = _u(lane_dir)
            out = OUTPUT_DOGLEGS[name]
            g['out_m1'] = (out.get('first_x', out['x']), aom[1])
            g['out_m2'] = (out['x'], out['y'])
            g['hwp'] = _add(g['out_m2'], d, out['hwp_distance'])
            g['rot'] = _add(g['hwp'], d, HWP_TO_ROT)
            g['cube'] = _add(g['rot'], d, -BONDED_CUBE_CENTRE_OFFSET)
            g['iris'] = _add(g['rot'], d, ROT_TO_IRIS[q['post']])
            g['port'] = (OUTPUT_PORT_X[name], out['y'])
            g['front'] = _add(g['port'], d, -LENS_TUBE_FRONT)
            g['iris_angle'] = (lane_dir if q['post'] < 0 else lane_dir + 180) % 360
            g['output_sequence'] = ['out_m1', 'out_m2', 'hwp', 'cube', 'rot', 'iris', 'front']
            if name == 'C1':
                # Its RF connector points down. Keep the HWP/PBS on the AOM
                # row and place the iris between the two output folds, so no
                # output-mirror hardware occupies the RF service rectangle.
                g.update(hwp=(414., aom[1]), rot=(446., aom[1]),
                         cube=(446.-BONDED_CUBE_CENTRE_OFFSET, aom[1]),
                         iris=(464., 45.5), iris_angle=90.)
                g['output_sequence'] = ['hwp', 'cube', 'rot', 'out_m1', 'iris', 'out_m2', 'front']
        else:
            g['iris'] = _add(aom, _u(lane_dir), IRIS_L)
            g['iris_angle'] = (lane_dir if q['post'] < 0 else lane_dir + 180) % 360
            g['hwp'] = _add(aom, _u(lane_dir), q.get('post_hwp_distance', HWP_D))
            g['pbs'] = _add(aom, _u(lane_dir), q.get('post_pbs_distance', PBS_D))
            g['pang'] = lane_dir
            g['T'] = lane_dir
            g['R'] = _pbs_reflect(lane_dir, q['inv'], lane_dir)
        geo[name] = g
    return geo


def lane_points(name, g):
    """RF-off zero-order axis of a lane, from its feed to its last element."""
    pts = [g['src']]
    if 'fr' in g:
        pts.append(g['fr'])
    pts.append(g['m1'])
    if g['m2'] is not None:
        pts.append(g['m2'])
    pts += [g['pre_aom_hwp'], g['aom']]
    if name.startswith('C'):
        # The cube is this assembly's optical centre. Keep the collinear stage
        # reference out of the polyline so it is not mistaken for a new optic.
        pts += [g[key] for key in g['output_sequence'] if key != 'rot']
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
    doc = App.newDocument('Splitting_Board_V2')
    baseplate = layout.baseplate(base_dx, base_dy, base_dz, x=x, y=y, angle=angle, gap=gap,
                                 drill=False, mount_holes=mount_holes,
                                 name='Splitting plate %d x %d in' % PLATE_IN)
    plate = doc.getObject(baseplate.active_baseplate)
    info = {'mode': 'splitting', 'plate': plate, 'roots': {}, 'paths': [], 'arms': [],
            'reservations': [], 'extra_cuts': [], 'geometry_assertions': [],
            'alternate': False, 'service_regions': [], 'output_optical_routes': [],
            'fiber_tail_pairs': [], 'bonded_output_pbs': [], 'pre_aom_waveplates': [],
            'requirements': {'mirror_roles': [], 'spherical_groups': []},
            'isolator': None, 'cell': None,
            'plate_size_mm': [base_dx, base_dy, base_dz],
            'optical_reference_model': {'kind': 'zero_order_reference_model', 'aom_rf_state': 'off',
                                        'modeled_order': 0, 'diffraction_angle_deg': 0.0},
            'layout_status': 'Splitting Board V2 with entrance-HWP adjustment clearance (RF-off zero order); '
                             'see the saved native production audit; not machined.'}
    info['aom_adjustment_design'] = {
        'required': True, 'external_net_rotation_cone_deg': 4.,
        'external_clearance_margin_mm': 1.,
        'preserve_lattice_installation': True,
        'full_catalogue_travel_certified': False,
        'scope': 'External hardware reserve around an ideal sphere/cone contact pivot; '
                 'unchanged lattice seat restricts pitch/combined travel; RF-on optical coupling not certified.',
    }
    info['mount_holes_mm'] = [((mx + .5)*INCH, (my + .5)*INCH) for mx, my in mount_holes]
    info['table_mount_pattern'] = {'pitch_mm': INCH, 'right_lower_edge_offset_mm': INCH,
                                  'edge_datum': 'finished machined plate edges',
                                  'offsets_in': TABLE_MOUNT_OFFSETS_IN,
                                  'installation_note': 'Fasten the lower-right table bolt before installing the C1/Output 4 fiber tail clamp and routing its fiber; reverse this order for removal.'}

    def put(name, cls, px, py, pangle=0, **kw):
        obj = baseplate.place_element(name, cls, x=px, y=py, angle=pangle, **kw)
        info['roots'][name] = obj
        return obj

    def fiber(name, px, py, pangle, rear_offset=REAR_CLAMP_OFFSET):
        # Use the repository's KM05T and lip-adapter geometry without changing
        # the optical origin. "mount_only" keeps the two adapter attachment
        # taps and omits the optional Y-shape pattern; all optional rear pairs
        # are off because their 52.7/72.7/82.7 mm offsets are not this board's
        # board-level clamp positions.
        obj = put(name, optomech.fiberport_mount_km05T, px, py, pangle,
                  hole_config='mount_only', mount_args={'thumbscrews': True},
                  adapter_args={'rear_pair_43': False, 'rear_pair_63': False, 'rear_pair_73': False})
        obj.addProperty('App::PropertyLength', 'RearHoleXOffset', 'Tail clamp').RearHoleXOffset = rear_offset
        obj.addProperty('App::PropertyLength', 'RearHoleYSpacing', 'Tail clamp').RearHoleYSpacing = REAR_CLAMP_HOLE_SPACING
        obj.addProperty('App::PropertyStringList', 'RearHoleNames', 'Tail clamp')
        direction = _u(pangle)
        sideways = (-direction[1], direction[0])
        rear = _add((px, py), direction, -rear_offset)
        holes, positions = [], []
        for sign in (-1, 1):
            position = _add(rear, sideways, sign*REAR_CLAMP_HOLE_SPACING/2)
            hole = put(name + ' rear clamp tap %+d' % sign, optomech.BareTappedHole, *position)
            hole.Purpose = '8-32 tail-clamp pair at the retained rear X position, %g mm behind the KM05T optical mount origin.' % rear_offset
            hole.addProperty('App::PropertyLink', 'Owner', 'Tail clamp').Owner = obj
            hole.addProperty('App::PropertyString', 'CutKind', 'Tail clamp').CutKind = 'fiber-tail-hole'
            hole.addProperty('App::PropertyLength', 'RearOffset', 'Tail clamp').RearOffset = rear_offset
            hole.addProperty('App::PropertyInteger', 'RearSide', 'Tail clamp').RearSide = sign
            info['extra_cuts'].append(hole)
            info['reservations'].append({'object': hole.Name, 'reason': hole.Purpose})
            holes.append(hole)
            positions.append(list(position))
        # Store names rather than links: each hole already links to its Owner,
        # so back-links here would introduce a FreeCAD dependency cycle.
        obj.RearHoleNames = [hole.Name for hole in holes]
        info['fiber_tail_pairs'].append({'owner': obj.Name, 'class': 'fiberport_mount_km05T',
                                         'holes': [hole.Name for hole in holes],
                                         'rear_offset_mm': rear_offset,
                                         'hole_spacing_mm': REAR_CLAMP_HOLE_SPACING,
                                         'hole_centres_board_xy_mm': positions,
                                         'adapter_hole_config': 'mount_only'})
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
    inport = fiber('Input KM05T', INPUT_XY[0], INPUT_XY[1], INPUT_DIR)
    ports, aoms, output_mirrors, entrance_mirrors = {}, {}, {}, {}
    for k, name in enumerate(ORDER):
        q, g = LANES[name], geo[name]
        if 'fr' in g:
            fr = bend(name + ' FR', g['src'], g['fr'], g['m1'])
            fr.addProperty('App::PropertyString', 'Purpose').Purpose = (
                'Extra 45 deg routing fold: the PBS sibling outputs are perpendicular, this lane must turn '
                'once more so its fiber head sits on the output edge.')
        if name == 'A':
            entrance_mirrors[name] = bend(name + ' M1', g['p0'], g['m1'], g['pre_aom_hwp'])
        else:
            bend(name + ' M1', g['p0'], g['m1'], g['m2'])
            entrance_mirrors[name] = bend(name + ' M2', g['m1'], g['m2'], g['pre_aom_hwp'])
        entrance_hwp = put(name + ' entrance HWP', optomech.waveplate,
                           *g['pre_aom_hwp'], g['pre_aom_hwp_angle'],
                           mount_type=optomech.rotation_stage_rsp05)
        entrance_hwp.addProperty('App::PropertyString', 'Purpose').Purpose = (
            'Dedicated pre-AOM half-wave plate on RSP05; existing downstream HWP retained. '
            + ('Located before the upstream KM100PM assembly with explicit adjustment clearance.'
               if q['orient'] == 'U' else 'Located immediately before the AOM entrance assembly.'))
        entrance_stage = next(child for child in entrance_hwp.ChildObjects
                              if child.Proxy.__class__.__name__ == 'rotation_stage_rsp05')
        entrance_adapter = next(child for child in entrance_stage.ChildObjects
                                if child.Proxy.__class__.__name__ == 'surface_adapter_rotation_stage_lip')
        aom = put(name + ' AOMO 3100-125', optomech.AOMO_3100_125, g['aom'][0], g['aom'][1], g['aom_angle'],
                  forward_direction=-1, backward_direction=1, diffraction_angle=KAPPA,
                  surface_adapter_args={'adapter_height': 5})
        seat = optomech.integrate_aom(baseplate, aom)
        info['extra_cuts'].append(seat)
        aoms[name] = aom
        info['pre_aom_waveplates'].append({
            'lane': name, 'object': entrance_hwp.Name, 'waveplate': entrance_hwp.Name,
            'stage': entrance_stage.Name, 'adapter': entrance_adapter.Name,
            'last_mirror': entrance_mirrors[name].Name, 'aom': aom.Name,
            'beam_path': name + ' lane',
            'path_vertex_index': lane_points(name, g).index(g['pre_aom_hwp']),
            'optical_xy_mm': list(g['pre_aom_hwp']),
            'incoming_direction_deg': g['in_dir'] % 360.,
            'incoming_direction_xy': list(_u(g['in_dir'])),
            'waveplate_angle_deg': g['pre_aom_hwp_angle'],
            'aom_mount_orientation': q['orient'],
            'last_mirror_to_hwp_mm': q['a2'] - PRE_AOM_HWP_TO_AOM_MM[name],
            'hwp_to_aom_mm': PRE_AOM_HWP_TO_AOM_MM[name],
            'spacing_basis': ('HWP precedes the upstream KM100PM envelope; the declared spacing is the optical-centre '
                              'distance to the AOM, not free space to its outer housing.'
                              if q['orient'] == 'U' else
                              'HWP lies on the final incoming leg immediately before the AOM assembly.')})
        if name.startswith('C'):
            out_no = OUTPUT_NUMBER[name]
            sequence = ['aom'] + g['output_sequence']
            for number, key in ((1, 'out_m1'), (2, 'out_m2')):
                index = sequence.index(key)
                output_mirrors[name, key] = bend(name + ' output steering mirror %d' % number,
                                               g[sequence[index-1]], g[key], g[sequence[index+1]])
            put(name + ' HWP', optomech.waveplate, g['hwp'][0], g['hwp'][1], g['lane_dir'],
                mount_type=optomech.rotation_stage_rsp05)
            # The verified engraved rotor face is local +X. Reverse the whole
            # stage to bond its cube upstream, between the HWP and the RSP05.
            rot = put(name + ' rotating-PBS RSP05', optomech.rotation_stage_rsp05_bonded_cube,
                      *g['rot'], (g['lane_dir']+180) % 360, cube_roll_deg=0.)
            rot.addProperty('App::PropertyString', 'Purpose').Purpose = (
                '12.7 mm PBS cube bonded to the reversed RSP05 engraved rotor; '
                'cube lies between the HWP and the stage. This second stage holds no waveplate.')
            info['bonded_output_pbs'].append({
                'lane': name, 'stage': rot.Name, 'cube': rot.BondedCube.Name,
                'adhesive': rot.BondedAdhesive.Name,
                'stage_reference_xy_mm': list(g['rot']), 'cube_centre_xy_mm': list(g['cube']),
                'stage_angle_deg': (g['lane_dir']+180) % 360,
                'hwp_to_stage_reference_mm': HWP_TO_ROT, 'cube_side': 'upstream',
                'cube_size_mm': 12.7, 'cube_roll_deg': 0.,
                'adhesive_thickness_mm': float(rot.AdhesiveThickness.Value),
                'assumptions': rot.BondAssumptions})
            put(name + ' iris', optomech.pinhole_ida12, g['iris'][0], g['iris'][1], g['iris_angle'])
            ports[name] = fiber('Output %d KM05T (%s)' % (out_no, name),
                                g['port'][0], g['port'][1], (g['lane_dir'] + 180) % 360,
                                rear_offset=OUTPUT_REAR_CLAMP_OFFSETS[name])
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
        # Events describe the RF-off zero-order reference, including the real cube centre.
        events = [{'type': 'aom', 'name': name + ' AOM', 'xy': g['aom']}]
        if name.startswith('C'):
            kinds = {'out_m1': ('mirror', ' output steering mirror 1'),
                     'out_m2': ('mirror', ' output steering mirror 2'),
                     'hwp': ('hwp', ' HWP'), 'cube': ('pbs', ' bonded PBS cube'),
                     'rot': ('rotation_mount', ' rotating-PBS RSP05'),
                     'iris': ('iris', ' iris'), 'front': ('fiber', ' output KM05T')}
            events += [{'type': kinds[key][0], 'name': name + kinds[key][1], 'xy': g[key]}
                       for key in g['output_sequence']]
        else:
            events += [{'type': 'iris', 'name': name + ' iris', 'xy': g['iris']},
                       {'type': 'hwp', 'name': name + ' HWP', 'xy': g['hwp']},
                       {'type': 'pbs', 'name': name + ' PBS', 'xy': g['pbs']}]
        info['output_optical_routes'].append({'arm': name, 'events': events})
    info['expected_pre_aom_waveplate_count'] = len(ORDER)
    info['pre_aom_waveplates_required'] = True
    info['expected_arm_count'] = len(ORDER)
    info['output_order_expected_routes'] = len(ORDER)

    # fiber heads: front access, tail clamps
    for name, port in ports.items():
        g = geo[name]
        d = _u(g['lane_dir'] + 180)
        service(port.Label + ' front access', 'fiber_front', port, g['front'], d, OUTPUT_FRONT_ACCESS, 20.,
                allowed=[name + ' lane'], note='20 mm full front access width; 28 mm axial access.')
    service('Input KM05T front access', 'fiber_front', inport,
            _add(INPUT_XY, _u(INPUT_DIR), LENS_TUBE_FRONT), _u(INPUT_DIR), INPUT_FRONT_ACCESS, 20.,
            allowed=['A lane'], note='20 mm full front access width; 15 mm axial access (input head).')
    info['service_clearance'] = {'min_length_mm': {'fiber_front': INPUT_FRONT_ACCESS, 'aom_sma': 40.}}
    info['fiber_clearance'] = {'rear_offsets_mm': sorted(set([REAR_CLAMP_OFFSET] + list(OUTPUT_REAR_CLAMP_OFFSETS.values()))),
                               'clamp_width_mm': 30.}
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
            A.append({'name': 'A: M1 fold = 90 deg (zero-order reference)',
                      'measured': abs(turn(g['p0'], g['m1'], g['aom']) - 90.), 'expected': KAPPA, 'tolerance': 1e-7})
            A.append({'name': 'A: M1 -> AOM >= KM100PM clearance (excess, mm)',
                      'measured': min(0., dist(g['m1'], g['aom']) - M2_TO_AOM_MIN[q['orient']]), 'expected': 0.,
                      'tolerance': 1e-7})
        else:
            A.append({'name': name + ': M1 folds the beam by exactly 90 deg', 'measured': turn(g['p0'], g['m1'], g['m2']),
                      'expected': 90., 'tolerance': 1e-7})
            A.append({'name': name + ': M2 fold = 90 deg (zero-order reference)',
                      'measured': abs(turn(g['m1'], g['m2'], g['aom']) - 90.), 'expected': KAPPA, 'tolerance': 1e-7})
            A.append({'name': name + ': M2 -> AOM >= KM100PM clearance (excess, mm)',
                      'measured': min(0., dist(g['m2'], g['aom']) - M2_TO_AOM_MIN[q['orient']]), 'expected': 0.,
                      'tolerance': 1e-7})
        A.append({'name': name + ': undeflected zero order follows a board axis (deg off axis)',
                  'measured': min(g['lane_dir'] % 90, 90 - g['lane_dir'] % 90), 'expected': 0., 'tolerance': 1e-9})
        if name.startswith('C'):
            A.append({'name': name + ': output beam runs +x into its fiber head (deg)',
                      'measured': min(abs(g['lane_dir'] - OUT_DIR) % 360, 360 - abs(g['lane_dir'] - OUT_DIR) % 360),
                      'expected': 0., 'tolerance': 1e-9})
            sequence = ['aom'] + g['output_sequence']
            route = [g[key] for key in sequence]
            iris_index = sequence.index('iris')
            path_to_iris = sum(dist(a, b) for a, b in zip(route[:iris_index], route[1:iris_index+1]))
            iris_to_front = sum(dist(a, b) for a, b in zip(route[iris_index:], route[iris_index+1:]))
            for number, key in ((1, 'out_m1'), (2, 'out_m2')):
                index = sequence.index(key)
                before, point, after = route[index-1:index+2]
                u = App.Vector(point[0]-before[0], point[1]-before[1], 0)
                v = App.Vector(after[0]-point[0], after[1]-point[1], 0)
                u.normalize()
                v.normalize()
                normal = output_mirrors[name, key].BasePlacement.Rotation.multVec(App.Vector(1, 0, 0))
                reflected = u-normal*(2*u.dot(normal))
                incidence = math.degrees(math.acos(min(1., abs(u.dot(normal)))))
                A.append({'name': name + ': output mirror %d obeys specular reflection (vector error)' % number,
                          'measured': (reflected-v).Length, 'expected': 0., 'tolerance': 1e-7})
                A.append({'name': name + ': output mirror %d incidence <= 45 deg (excess)' % number,
                          'measured': max(0., incidence-45.), 'expected': 0., 'tolerance': 1e-7})
                A.append({'name': name + ': output mirror %d turns exactly 90 deg' % number,
                          'measured': turn(before, point, after), 'expected': 90., 'tolerance': 1e-7})
            A.append({'name': name + ': AOM -> iris mechanical path >= 81 mm (shortfall mm)',
                      'measured': min(0., path_to_iris - IRIS_L), 'expected': 0., 'tolerance': 1e-7})
            A.append({'name': name + ': HWP -> rotating-PBS RSP05', 'measured': dist(g['hwp'], g['rot']),
                      'expected': HWP_TO_ROT, 'tolerance': 1e-7})
            A.append({'name': name + ': iris -> output lens-tube front >= 30 mm (shortfall mm)',
                      'measured': min(0., iris_to_front - IRIS_TO_FRONT_MIN[q['post']]),
                      'expected': 0., 'tolerance': 1e-7})
            clamp_end = g['port'][0] + OUTPUT_REAR_CLAMP_OFFSETS[name] + 10.
            A.append({'name': name + ': output tail clamp within %g mm of the right plate edge (excess mm)' % PORT_EDGE,
                      'measured': max(0., right_edge - clamp_end - PORT_EDGE), 'expected': 0., 'tolerance': 0.05})
            if name == 'C4':
                A.append({'name': 'C4: rear-clamp pair centre retains its board XY position (mm)',
                          'measured': dist((g['port'][0] + OUTPUT_REAR_CLAMP_OFFSETS[name], g['port'][1]),
                                           (596.415072253436, 325.)),
                          'expected': 0., 'tolerance': 1e-7})
        else:
            A.append({'name': name + ': AOM -> iris mechanical spacing', 'measured': dist(g['aom'], g['iris']),
                      'expected': IRIS_L, 'tolerance': 1e-7})
            A.append({'name': name + ': AOM -> HWP', 'measured': dist(g['aom'], g['hwp']),
                      'expected': q.get('post_hwp_distance', HWP_D), 'tolerance': 1e-7})
            A.append({'name': name + ': AOM -> PBS', 'measured': dist(g['aom'], g['pbs']),
                      'expected': q.get('post_pbs_distance', PBS_D), 'tolerance': 1e-7})
            A.append({'name': name + ': retained downstream HWP -> PBS spacing',
                      'measured': dist(g['hwp'], g['pbs']), 'expected': PBS_D-HWP_D, 'tolerance': 1e-7})
    A.append({'name': 'No beam crosses another beam (crossing pairs)', 'measured': len(beam_crossings(geo)),
              'expected': 0, 'tolerance': 0.})
    # Finished-edge distances and the nonrectangular table grid are checked
    # against the actual machined solid by tools/table_mount_audit.py.
    info['lane_geometry'] = {n: {k: (list(v) if isinstance(v, tuple) else v) for k, v in g.items()}
                             for n, g in geo.items()}
    info['beam_crossings'] = beam_crossings(geo)

    # ---- cut the plate once every element and machining volume is in place ----
    doc.recompute()
    layout.redraw()
    plate.Drill = drill
    plate.touch()
    doc.recompute()
    # Measure the recomputed world optical references in the plate frame.
    # integrate_aom shifts its body datum by local (0, +0.030, +0.115) mm;
    # optical_center maps the real aperture at local (0, -0.030, -0.115) mm.
    # Do not mistake the displaced body origin for the beam or suppress errors.
    inverse_plate = plate.Placement.inverse()
    for entry in info['pre_aom_waveplates']:
        name = entry['lane']
        mirror, hwp, aom = [doc.getObject(entry[key]) for key in ('last_mirror', 'waveplate', 'aom')]
        optical_points = [inverse_plate.multVec(point) for point in
                          (mirror.Placement.Base, hwp.Placement.Base, optomech.optical_center(aom))]
        points_xyz = [[float(point.x), float(point.y), float(point.z)] for point in optical_points]
        points = [point[:2] for point in points_xyz]
        heights = [point[2] for point in points_xyz]
        direction = entry['incoming_direction_xy']
        steps = [[b[0]-a[0], b[1]-a[1]] for a, b in zip(points, points[1:])]
        axial = [v[0]*direction[0]+v[1]*direction[1] for v in steps]
        transverse = [abs(v[0]*direction[1]-v[1]*direction[0]) for v in steps]
        axis = inverse_plate.Rotation.multVec(hwp.Placement.Rotation.multVec(App.Vector(1, 0, 0)))
        entry['actual_last_mirror_xy_mm'], entry['actual_waveplate_xy_mm'], entry['actual_aom_xy_mm'] = points
        entry['actual_last_mirror_xyz_mm'], entry['actual_waveplate_xyz_mm'], entry['actual_aom_xyz_mm'] = points_xyz
        entry['actual_last_mirror_to_hwp_mm'] = (optical_points[1]-optical_points[0]).Length
        entry['actual_hwp_to_aom_mm'] = (optical_points[2]-optical_points[1]).Length
        body_datum = inverse_plate.multVec(aom.Placement.Base)
        entry['actual_aom_body_datum_xyz_mm'] = [float(body_datum.x), float(body_datum.y), float(body_datum.z)]
        entry['aom_aperture_local_xyz_mm'] = list(optomech.AOM_APERTURE_LOCAL)
        entry['actual_optical_datum_basis'] = 'World optomech.optical_center(aom), transformed by inverse plate Placement'
        entry['actual_axial_distances_mm'] = axial
        entry['actual_cross_axis_errors_mm'] = transverse
        entry['actual_optical_reference_z_mm'] = heights
        A.append({'name': name + ': actual last input mirror -> entrance HWP axial distance',
                  'measured': axial[0], 'expected': entry['last_mirror_to_hwp_mm'], 'tolerance': 1e-7})
        A.append({'name': name + ': actual entrance HWP -> AOM axial distance',
                  'measured': axial[1], 'expected': entry['hwp_to_aom_mm'], 'tolerance': 1e-7})
        A.append({'name': name + ': actual last mirror / entrance HWP / AOM collinearity error',
                  'measured': max(transverse), 'expected': 0., 'tolerance': 1e-7})
        A.append({'name': name + ': actual last mirror / entrance HWP / AOM optical-height error',
                  'measured': max(heights)-min(heights), 'expected': 0., 'tolerance': 1e-7})
        A.append({'name': name + ': actual entrance HWP transmission axis alignment error',
                  'measured': abs(abs(axis.x*direction[0]+axis.y*direction[1])-1.),
                  'expected': 0., 'tolerance': 1e-7})
        A.append({'name': name + ': actual entrance HWP lies strictly between last mirror and AOM',
                  'measured': int(not all(value > 0. for value in axial)), 'expected': 0, 'tolerance': 0.})
        registered = lane_points(name, geo[name])[entry['path_vertex_index']]
        A.append({'name': name + ': actual entrance HWP lies at its registered path vertex',
                  'measured': dist(points[1], registered), 'expected': 0., 'tolerance': 1e-7})
    doc.Label = 'Splitting Board V2 - seven entrance HWPs (%d x %d in)' % PLATE_IN
    return doc, info


def example_baseplate(x=0, y=0, angle=0, drill=True):
    """Repository entry point (as for the other boards): build the board, return the info dict."""
    doc, info = build(x=x, y=y, angle=angle, drill=drill)
    return info


if __name__ == '__main__':
    example_baseplate()
    layout.redraw()
