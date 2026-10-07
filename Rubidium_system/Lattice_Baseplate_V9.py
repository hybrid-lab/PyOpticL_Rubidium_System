"""Lattice baseplate V9.5 (2026-10-06) - 24 x 15 in, f = 300 mm folded cat-eyes,
sliding Rb cell enclosure.

V9.5 against V9.4.2 (only the cell seat changes; no other hole or part moves):

* The Rb vapour cell gets its enclosure (optomech section 3b, SlidingCell*):
  a 76 x 40.4 x 48 mm aluminium body with a 30.4 mm through bore (cell 25.4 mm
  + 5 mm), a 12 mm hole from the top for the fill stem, two separate 10 mm end
  covers (four counterbored 8-32 screws each, eight 16 mm deep taps in the
  body; NO beam aperture yet - to be opened later), and a 6 mm wire hole in the
  side wall. The enclosure can slide across the beam by one cell radius
  (12.7 mm): a 25 x 10 mm shoulder along the +x (board) side carries two 8-32
  slots (17.1 mm long, 30 mm apart) and the plate carries two 8-32 taps instead
  of the old four corner taps. At slide 0 the beam runs through the cell
  centre, at 12.7 along the cell wall (the body moves toward -x on the board;
  the external-TA injection fold forbids the other direction).
* The seat pocket is now 10.3 mm deep (the bore axis sits 23 mm above the
  body's bottom) and shaped for the whole assembly plus the travel: 100 x 61.4 mm
  (board x 161.1..222.5, y 112..212; its +x edge takes in the external-TA
  injection fold's thumbscrew pocket, as the old pocket did, instead of leaving
  a 0.7 mm wall) with a 48 x 27 mm ear for the shoulder (board x 216.2..243.2,
  y 122..170); the old 104 x 56 x 19.05 pocket is gone. The two seat taps are
  at (223.35, 132) and (223.35, 162), through the 15.1 mm pocket floor. Hole
  count 106 -> 104 (100 x 8-32 + 4 table bolts).
* example_baseplate(cell_slide=...) builds the enclosure at any position of its
  travel; the dual configuration is additionally audited at cell_slide = 12.7.
  The cell glass (GC25075-RB envelope, stem up) is modelled inside the bore.

V9.4.2 against V9.4.1 (bolt pairs no more than 10 in apart):

* Both table-bolt pairs are now exactly 10 in apart and centred on the short
  edge (y = 50.8 and 304.8, i.e. 2.375 in from the top and bottom edges). The
  right-hand part of the plate between those two rows is full (0-order
  irises, the optional f = 75 set, the output heads), so the fiber-side pair
  moves inboard to 6.25 in (n = 5) from the right edge, x = 447.675: between
  the AOM housings (x <= 426) and the optional f = 75 lens holders (x >= 465).
  The TA-side pair stays 1.5 in from the left edge (x = 41.275), 16 in to the
  left of the other pair. Nominal units: (17.125, 1.5), (17.125, 11.5),
  (1.125, 1.5), (1.125, 11.5).
* The TA block moves 5 mm up (TA_XY (60, 140) -> (60, 145)) so that its
  adapter pocket clears the lower-left bolt by 5.3 mm; nothing else moves.
* The upper fiber-side bolt lies under the DP1 beam between the AOM and the
  f = 75 lens position (1.1 mm off the +1-order axis): install before aligning.

V9.4.1 against V9.4 (two changes, nothing else moves):

* Table bolts on the lab table's 1 in grid, whose first row is 1.5 in from
  the table edge. The plate's fiber-side (right, +x) edge sits 0.25 in inside
  the table edge, so a bolt (1.25 + n) in from that plate edge lands on row n.
  V9.4.1 had the two fiber-side bolts 3.25 in (n = 2) from the right edge,
  13 in apart and centred on the short edge, and the two TA-side bolts 19 in
  further left (1.5 in from the left edge), 11 in apart and also centred, so
  all four sat on 1 in grid points (superseded by V9.4.2 above).
* The optional f = 75 set (holes, QWP seat and the hardware of the two test
  configurations) sits on the 0-order / input axis y = DP_Y straight after each
  AOM - the V9.3 arrangement - instead of on the +1-order axis. The s-distances
  from the AOM are unchanged (DP1 lens 73 / QWP 91 / iris 113 / faces 123 and
  148; DP2 68 / 91 / 107 / 118 and 143); every element simply moves down by
  s*sin(1.0846 deg) (1.3 .. 3.1 mm) and turns to the board axes. In the
  test configurations the +1 order then passes the optics 1.4 mm off centre
  (f*2*theta_B after the lens; 1.4 mm at the lens itself) - nothing for 1/2 in
  optics - and the iris is centred on it with its slide.

What changed in V9.4 against V9.3:

* Cat-eye lens LA1618-B (1/2 in, f = 300 mm) instead of LA1612-B (f = 75): the
  focused spot on the retro mirror is 4x larger, 16x lower intensity. The plate
  was laid out with an estimated lens (R 154.5, tc 2.0); the catalogue lens
  (R 155.0, tc 2.2, te 2.1) wants both cat-eye legs ~1.1 mm longer. Accepted
  and documented (LA1618B_CATALOGUE, CAT_DEFOCUS_*): the cat-eye return stays
  antiparallel, the lateral walk is 9 um over 80-120 MHz and the mirror-side
  defocus adds a 45 m wavefront curvature. No hole moves.
* AOM -> lens -> mirror needs 605.5 mm of path, so each arm is folded into a U
  by two 45-degree fold mirrors. DP1 folds up to a return leg along the top
  edge; DP2 folds down to a return leg along the bottom edge.
    - Every mirror on the board - the four cat-eye folds F1..F4, both retro
      mirrors, the output steering mirrors and the common folds - is a Newport
      M05 with HKTS thumbscrews (the lab's only mirror mount). Fold bodies may
      overhang the plate edge; every 8-32 screw lands >= 6 mm inside it.
* The +1 order is modelled explicitly: after each AOM the nominal axis turns by
  2*theta_B = lambda*F/v = 1.0846 deg (100 MHz, TeO2 4.2 mm/us), so the four
  fold mirrors see the DIFFRACTED beam at exactly 45 deg and the return legs
  run 1.08 deg off the board axes. The AOM sits at the Bragg angle on its
  KM100PM; the undiffracted (0) order stays on the input axis.
* One IDA12 iris per arm on the vertical leg (L = 190-199 mm from the AOM: +1
  walk +-0.72 mm over 80-120 MHz, 0 order 3.6 mm off axis) blocks the 0 order
  before the second fold; set it to ~4.2 mm. The old irises next to the retro
  mirrors are gone. QWPs sit on the return legs (after both folds), so the
  folds only ever see pure s or pure p.
* DP2 is re-arranged: its output row (telescope, HWP, rotating PBS, iris, KA05T)
  is ABOVE the AOM row and the separation cube reflects the return upward
  (invert=True), so the down-going fold leg crosses nothing. Both AOMs are at
  angle 0 (KM100PM upstream, RF connector toward -y); the RF elbow zones are
  kept free of hardware and beams (DP1 tail toward -x, DP2 tail either way).
* The isolator lane (HWP, isolator, QWP, stations 1-3) moves 8 mm toward the
  TA (x 138 -> 130) and the PBS column 10 mm (273 -> 263), so the DP1 retro
  M05 clears the TA steering fold 2 thumbscrew and the common fold 1 knob
  pocket clears table bolt (3,0).
* Rows are compacted: DP2 return ~13 / DP2 AOM 82 / DP2 output 132.5 /
  external 173.5 / DP1 output 214.5 / main 274.5 / DP1 AOM 303 / DP1 return
  ~348. The common column (stations 5-6, cell pocket, shutter, fold 3) fixes
  MAIN_Y >= 274.5; above it the DP1 rows and fold F2 use the last 0.5 in.
  Plate 24 x 15 in (y_offset = -0.5 in keeps every old coordinate valid).
* All three fiber heads keep the V9.2/V9.3 rear tail-clamp offset (76 mm); the
  rows are 41 mm apart, so 30 mm wide clamps do not overlap. All irises are
  the standard IDA12 on the standard slotted slide mount; the DP2 output iris
  sits 36.5 mm (not 30) ahead of its lens tube so that its body stays out of
  the head's 28 mm front-access zone with the post toward -y.
* The external telescope has both lenses on the input lane (LA1560-B hole at
  x = 349, LA1213-B 75.6 mm upstream); the injection leg carries no lens, so
  no holder sits between the two output steering mirrors' thumbscrews.
* (V9.4) The four table bolts were the V9.2/V9.3 pattern; V9.4.1/V9.4.2
  replace them (see above).
* The V9.3 geometry (f = 75 cat-eyes on a 24 x 14 in plate) is in the git
  history of this file; its lens/QWP/iris/mirror positions live on as the
  optional hole set below.
* Optional f = 75 cat-eye (the V9.3 LA1612-B set) machined but not installed,
  straight after each AOM (V9.4.1: on the 0-order axis): L05G tap for the lens, the RSP05
  lip-adapter seat (pocket + two taps) for a QWP, slide-mount tap for an order
  iris (post toward -y) and two M05 taps for the retro mirror at lens->mirror
  50 and lens->mirror 75 (no thumbscrew pockets there: plain hex key). Distances
  from the AOM: DP1 lens 73 / QWP 91 / iris 113 / mirror faces 123 and 148;
  DP2 lens 68 / QWP 91 / iris 107 / faces 118 and 143 (DP2's straight run is
  15 mm shorter: AOM -> F3 is 165 mm against 179 mm for DP1). The lens sits a
  few mm short of the nominal 75 so that the "50" mirror thumbscrews and the
  "75" mirror tap clear the fold mount: with the "50" mirror every f = 300
  part may stay installed; the "75" mirror body sits where fold F1/F3 is, so
  that fold comes off for a 75/75 test. To make room, DP2's fold pair moved
  1 mm right (x 554 -> 555) and both 0-order irises moved further from their
  first fold (DP1 20 -> 28 mm above F1, DP2 L 190 -> 196 mm).

Original V9.2 description follows.

Lattice baseplate V9.2 - 24 x 14 in, 795 nm Rb-87 lattice light.

Beam order, read top to bottom in example_baseplate():

    TA -> two steering folds -> HWP -> isolator -> QWP
       -> six bare 8-32 conditioning stations (45/45 mm on the lane,
          60/100 mm along the beam after fold 2)
       -> Rb vapour cell in its sliding enclosure (V9.5) -> SR475 shutter
       -> power-division HWP -> main PBS
            transmitted -> DP1 arm: HWP, PBS, AOM on its integral seat,
                           folded f = 300 cat-eye (F1, iris, F2, lens, QWP, retro);
                           return -> HWP, telescope, rotating PBS, iris, KA05T
            reflected   -> DP2 arm: the same chain, output row above the AOM row

In mode='dual' a second KA05T feeds the DP2 arm from an external TA through a
two-lens telescope and an injection fold, and a blocking iris stops the
residual main-PBS beam.

Positions are millimetres in the board frame; z = 0 is the 12.7 mm optical
axis.

Run in FreeCAD (Macro > Macros..., or paste into the Python console):
    example_baseplate()                  single-TA configuration
    example_baseplate(mode='dual')       external-TA configuration
    example_baseplate(mode='dual', cell_slide=12.7)   enclosure slid by one cell radius
"""
import math

import FreeCAD as App
import Part

from PyOpticL import layout, optomech

# baseplate constants
base_dx = 24*layout.inch
TOP_EXTRA_IN = 0.5          # added above the old top edge (y = 352.425)
BOTTOM_EXTRA_IN = 0.5       # added below the old bottom edge (y = 3.175)
base_dy = (14 + TOP_EXTRA_IN + BOTTOM_EXTRA_IN)*layout.inch
PLATE_Y_OFFSET = -BOTTOM_EXTRA_IN*layout.inch   # keeps every old coordinate valid
base_dz = layout.inch
gap = layout.inch/8

# x-y coordinates of the table mount holes (in inches, nominal frame: centre at
# ((mx+0.5), (my+0.5)) in; the solid plate is inset 0.125 in from the nominal outline).
# The lab table has a 1 in grid whose first row is 1.5 in from the table edge.
# With the plate's fiber-side (right) edge 0.25 in inside the table edge, a
# bolt (1.25 + n) in from that plate edge lands on grid row n. V9.4.2: both
# pairs 10 in apart (the maximum allowed) and centred on the 14.75 in short
# edge, y = 50.8 / 304.8 (2.375 in from the top and bottom edges):
#   fiber-side pair  x = 606.425 - 6.25 in = 447.675 (n = 5): between the AOM
#                    housings (x <= 426) and the optional f = 75 lens holders (x >= 465).
#                    Nearer the fiber edge every centred 10 in pair hits the 0-order
#                    irises, the f = 75 option or the output heads.
#   TA-side pair     16 in further left: x = 41.275 (1.5 in from the left edge)
# All four are 1 in multiples apart, so they fall on the table grid together.
# The upper fiber-side bolt lies under the DP1 beam (AOM -> f = 75 lens position)
# 12.7 mm above the recessed bolt head - install the bolts before aligning.
mount_holes = [(17.125, 1.5), (17.125, 11.5), (1.125, 1.5), (1.125, 11.5)]

# --- common path ------------------------------------------------------------
TOP_RUN_Y = 338.        # the run the TA folds sit on, above the isolator lane
TA_XY = (60., 145.)     # TA emits +y (V9.4.2: 140 -> 145, the adapter pocket clears the lower-left bolt by 5.3 mm)
LANE_X = 130.           # isolator lane: HWP, isolator, QWP, stations 1-3 (V9.4: 138 -> 130, 8 mm nearer the TA)
CELL_X = LANE_X + 66.   # 196: fold 2, stations 5/6, cell, shutter, fold 3
MAIN_Y = 274.5          # top run: fold 3 -> power HWP -> main PBS (V9.4: 278.5 -> 274.5)
PBS_X = 263.            # main power PBS, and the column the DP2 feed turns on (V9.4: 273 -> 263 with the lane)
HWP_X = PBS_X - 31.4    # 231.6: power-division HWP
CELL_Y = 162.           # V9.4: 165 -> 162; V9.5 enclosure assembly 114..210, pocket 112..212 (station 6
                        # holder ends at 108, its bonded-lens slab at 111; shutter housing from 218.7)
CELL_SLIDE_MAX = 12.7   # V9.5: the enclosure's travel toward -x (one cell radius)
SHUTTER_Y = 238.        # V9.4: 240 -> 238 (housing 218.7..262.7, fold 3 body from 266)
TA_HWP_Y = 315.
ISO_Y = 245.
QWP_Y = 181.
LOWER_RUN_Y = 42.
STATION_LANE_Y = (160., 115., 70.)   # stations 1-3, 45 mm pitch down the lane
STATION_4_DX = 22.                   # station 4, 22 mm after fold 1 on the cross-run
STATION_5_Y = 58.                    # station 4 -> 5 along the beam: 44 + 16 = 60 mm
STATION_6_Y = 98.                    # station 4 -> 6 along the beam: 44 + 56 = 100 mm

# --- double-pass arms and output rows ---------------------------------------
DP1_Y = 303.            # DP1 AOM row (28.5 above MAIN_Y, as audited in V9.2/V9.3)
DP2_Y = 82.             # DP2 AOM row (RF elbow between it and the return leg at y = 10..17)
OUT1_Y = 214.5          # DP1 output row (M05 steering mirror clears the external lane; RSP05 tops at 237.7 clear the DP1 RF tail at 240)
OUT2_Y = 132.5          # DP2 output row, ABOVE its AOM row (V9.4); its rear tail clamp clears the F3 M05 thumbscrews
EXT_Y = 173.5           # external-TA input lane (V9.4: 165 -> 173.5, between the two output steering M05s; rows 41 mm apart)
PBS_TO_AOM = 79.        # separation PBS -> AOM: both AOMs at angle 0 (KM100PM upstream)
IRIS_TO_LENS_TUBE = {1: 30., 2: 36.5}   # output iris centre -> KA05T lens-tube front, per output row
LENS_TUBE_FRONT = 18.798        # KA05T lens-tube front ahead of the mount origin
REAR_CLAMP_OFFSET = 76.         # rear fiber tail-clamp pair behind every head (as V9.2/V9.3)
TAIL_CLAMP_WIDTH = 30.          # the user's tail clamps are narrower than the audit's 50 mm default:
                                # three heads 40/41 mm apart do not overlap (reserved 40 x 20 mm each)
OUTPUT_FRONT_ACCESS = 28.       # reserved axial access in front of an output head
EXTERNAL_FRONT_ACCESS = 50.
PORT_X = 273. + 70. + 125. + 30. + LENS_TUBE_FRONT    # 516.798: the V9.2 head position, kept
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
    # f = 300 cat-eye lens AS MODELLED AND AUDITED (R 154.5, tc 2.0 estimated
    # before the datasheet was available). The catalogue values are in
    # LA1618B_CATALOGUE below; the plate keeps this geometry on purpose.
    'LA1618-B': (300.0, 2.0, 1.8, 154.5/(1.51088-1.)),
}
# Thorlabs catalogue row (N-BK7 plano-convex, -B coating page, read 2026-09-30):
# LA1618-B  1/2"  f 300.0  R 155.0  tc 2.2  te 2.1  BFL 298.6 (587.6 nm).
# At 795 nm (f_d scaled by (n_d-1)/(n_795-1), as for the other rows): 303.48 mm.
LA1618B_CATALOGUE = {'f_587nm_mm': 300.0, 'R_mm': 155.0, 'tc_mm': 2.2, 'te_mm': 2.1,
                     'bfl_587nm_mm': 298.6, 'efl_795nm_mm': 300.0*(1.5168-1.)/(1.51088-1.)}
EXTERNAL_SPH_CENTER_SPACING = LENSES['LA1213-B'][3] + LENSES['LA1560-B'][3]

# --- f = 300 cat-eye, folded (V9.4) ----------------------------------------
# Plano-convex LA1618-B, curved face toward the AOM. n(N-BK7, 795 nm) = 1.51088.
N_BK7_795 = 1.51088
CAT_LENS = 'LA1618-B'
CAT_TC = LENSES[CAT_LENS][1]
CAT_EFL_795 = LENSES[CAT_LENS][3]                          # 302.42 mm (as modelled)
AOM_TO_CAT = CAT_EFL_795 + CAT_TC/2                        # 303.42: AOM centre -> lens centre
CAT_TO_MIRROR = CAT_EFL_795 - CAT_TC/N_BK7_795 + CAT_TC/2   # 302.10: lens centre -> mirror face
# With the catalogue lens (R 155.0, tc 2.2) the ideal distances are 304.58 and
# 303.12 mm, i.e. the drilled plate is 1.16 / 1.02 mm short on the two legs. The
# geometry is kept: a cat-eye returns the beam antiparallel for any AOM-side
# defocus (lateral walk 2*da*theta = 9 um at +-20 MHz), and a 1 mm mirror-side
# defocus only adds a f^2/(2*dm) = 45 m wavefront curvature (Rayleigh range of the
# focused spot 94 mm). Nothing on the plate moves.
_cat_tc, _cat_f = LA1618B_CATALOGUE['tc_mm'], LA1618B_CATALOGUE['efl_795nm_mm']
CAT_IDEAL_AOM_TO_CAT = _cat_f + _cat_tc/2                            # 304.58
CAT_IDEAL_CAT_TO_MIRROR = _cat_f - _cat_tc/N_BK7_795 + _cat_tc/2     # 303.12
CAT_DEFOCUS_AOM_SIDE = AOM_TO_CAT - CAT_IDEAL_AOM_TO_CAT             # -1.16 mm (accepted)
CAT_DEFOCUS_MIRROR_SIDE = CAT_TO_MIRROR - CAT_IDEAL_CAT_TO_MIRROR    # -1.02 mm (accepted)
# AOMO 3100-125 at 100 MHz, 795 nm, TeO2 longitudinal 4.2 mm/us: the +1 order
# leaves the input axis by 2*theta_B. The diffracted beam IS the design axis
# downstream of the AOM; the 0 order stays on the input axis.
AOM_RF_DESIGN_HZ = 100.e6
AOM_V_SOUND_MM_S = 4.2e6
DIFF_ANGLE_RAD = 0.795e-3*AOM_RF_DESIGN_HZ/AOM_V_SOUND_MM_S   # 0.018929 rad
DIFF_ANGLE_DEG = math.degrees(DIFF_ANGLE_RAD)                 # 1.0846 deg
DP1_FOLD_X = 591.        # DP1 fold pair at the right edge (M05 screws 6.2 mm inside the edge)
DP1_LEG2 = 41.5          # F1 -> F2 (F2 screw 8 mm inside the top edge; the QWP adapter stays inside it)
DP1_IRIS_ABOVE_F1 = 28.  # 0-order iris on the vertical leg, L = 207 mm from the AOM (clear of the optional f75 mirror knobs)
DP1_QWP_X = 235.         # on the return leg, between the retro M05 and the DP1 input steering M05
DP2_FOLD_X = 555.        # DP2 fold pair (555: one more mm would push the L300 holder onto bolt (19,0))
DP2_F4_Y = 20.           # F4 mirror point; the return leg then slopes down to the retro at y ~13 (R2 knob pocket 2.6 mm inside the edge)
DP2_IRIS_L = 196.        # 0-order iris on the vertical leg, L from the AOM (28 mm below F3, clear of the optional f75 mirror knobs)
DP2_QWP_X = 300.         # on the return leg, left of the AOM's RF tail zone
DP2_OUT_HWP_X = 419.     # DP2 output HWP and rotating PBS, right of the AOM/KM100PM footprint
DP2_OUT_ROT_X = 442.
DP1_OUT_ROT_X = 443.4    # DP1 rotating PBS, right of the DP1 RF neck zone
EXT_LENS2_HOLE_X = 349.  # external LA1560-B holder tap (its footprint clears the DP1 output steering M05 thumbscrew)
EXT_SPARE_DX = 125.      # spare external lens hole, PBS_X + 125
# --- optional f = 75 cat-eye hole set (V9.3 LA1612-B layout), bare holes only ---
# Distances along the 0-order (input) axis y = DP_Y from the AOM centre, per
# arm (V9.4.1; V9.4 had them on the +1-order axis). The lens sits short of the
# nominal 75 mm (DP1 73, DP2 68) so that the lens->mirror distances stay
# exactly 50 / 75 while the "50" mirror thumbscrews (35.7 mm behind its face)
# and the "75" mirror tap (12.96 mm behind) clear the fold mount F1 / F3.
# AOM-side defocus only walks the return beam sideways by 2*da*theta: 15 um
# (DP1) / 70 um (DP2) at the 80/120 MHz extremes. In the test configurations
# the +1 order runs 2*theta_B off this axis: 1.4 mm high at the lens, then
# parallel to the axis f*2*theta_B = 1.4 mm above it (AOM in the front focal
# plane) through the QWP, the iris and onto the retro mirror.
F75 = {1: {'lens': 73., 'qwp': 91., 'iris': 113., 'face': {'50': 123., '75': 148.}},
       2: {'lens': 68., 'qwp': 91., 'iris': 107., 'face': {'50': 118., '75': 143.}}}
F75_TAP_BEHIND_M05 = 12.96         # M05 tap behind a 6 mm mirror face
F75_PLUS1_OFFSET_AFTER_LENS = LENSES['LA1612-B'][3]*math.tan(DIFF_ANGLE_RAD)   # 1.44 mm: f*2*theta_B
RSP05_TAP_ALONG, RSP05_TAP_ACROSS = 0.9, 12.5     # (for reference: the seat is machined by the RSP05 adapter object itself)
IRIS_TAP_ALONG, IRIS_TAP_ACROSS = 1.956, -27.33   # slide-mount tap, post side

RED = (.85, .15, .1)
BLUE = (.1, .35, .95)
GREEN = (.05, .6, .3)
PURPLE = (.65, .15, .85)
UPSTREAM = ('Assumed upstream clearance radius 2.5 mm; TA measured q/M2 not supplied.')
DOWNSTREAM = ('Nominal 0.833 mm beam; conservative 1.2 mm diameter clearance envelope '
              'after telescope. Measured q/M2 and RF angle pending.')
KINKED = ('Nominal +1-order axis: 2*theta_B = %.4f deg from the input axis at %g MHz; '
          'the 0 order stays on the input axis and is stopped by the vertical-leg iris. '
          % (DIFF_ANGLE_DEG, AOM_RF_DESIGN_HZ/1e6)) + DOWNSTREAM
STATION_NOTE = ('Bare 8-32 hole (station %d of 6); holder and optic not yet selected. '
                'The audit reserves a 10 mm round envelope at the hole and checks a 16 mm '
                'along-beam holder footprint; a longer holder would need review.')


def _unit(v):
    n = math.hypot(v[0], v[1])
    return (v[0]/n, v[1]/n)


def _add(p, d, t):
    return (p[0] + d[0]*t, p[1] + d[1]*t)


def _rot90(d, ccw=True):
    return (-d[1], d[0]) if ccw else (d[1], -d[0])


def _dist(p, q):
    return math.hypot(q[0]-p[0], q[1]-p[1])


def example_baseplate(x=0, y=0, angle=0, mode='single', drill=True, cat_eye='300', cell_slide=0.):
    """Build the lattice board. mode: 'single' (one TA) or 'dual' (external TA).

    cat_eye: '300' (V9.4 as machined: f = 300 folded cat-eyes, the f = 75 set
    as bare holes) or the two test configurations on the SAME plate, '75-50'
    and '75-75' (LA1612-B set installed on its holes, lens->mirror 50 or 75;
    the f = 300 chain stays mounted except fold F1/F3 in '75-75'). The retro
    M05 of the f = 75 set carries no HKTS thumbscrews: those positions have no
    knob pocket, so the lower adjuster is driven with a plain 5/64 hex key.
    cell_slide: V9.5 position of the cell enclosure along its travel, 0 (beam
    through the cell centre) .. 12.7 mm (beam along the cell wall); the plate
    machining is the same for every value.
    """
    if mode not in ('single', 'dual'):
        raise ValueError("mode must be 'single' or 'dual'")
    if cat_eye not in ('300', '75-50', '75-75'):
        raise ValueError("cat_eye must be '300', '75-50' or '75-75'")
    if not 0. <= float(cell_slide) <= CELL_SLIDE_MAX + 1e-9:
        raise ValueError("cell_slide must be between 0 and %.1f mm" % CELL_SLIDE_MAX)
    f75_installed = cat_eye != '300'
    f75_mirror_key = cat_eye.split('-')[1] if f75_installed else None
    if App.ActiveDocument is None:
        App.newDocument('Lattice_V9_' + mode)
    doc = App.ActiveDocument

    baseplate = layout.baseplate(base_dx, base_dy, base_dz, x=x, y=y, angle=angle, gap=gap,
                                 drill=False, mount_holes=mount_holes, y_offset=PLATE_Y_OFFSET,
                                 name='Lattice plate 24 x 15 in')
    plate = doc.getObject(baseplate.active_baseplate)

    info = {'mode': mode, 'cat_eye': cat_eye, 'plate': plate, 'roots': {}, 'paths': [], 'arms': [],
            'reservations': [], 'extra_cuts': [], 'geometry_assertions': [],
            'alternate': False, 'service_regions': [], 'output_optical_routes': [],
            'layout_variant': 'Hand sketch V9',
            'plate_size_mm': [base_dx, base_dy, base_dz],
            'layout_status': 'V9.5 (2026-10-06): sliding Rb cell enclosure (10.3 mm pocket, two 8-32 slot taps, '
                             'travel 12.7 mm toward -x) on the V9.4.2 plate: f = 300 folded cat-eyes on the +1-order '
                             'axis, optional f = 75 hole set on the 0-order axis, table bolts on the 1 in grid (both '
                             'pairs 10 in apart and centred; fiber-side pair 6.25 in from the right edge, TA-side '
                             'pair 1.5 in from the left edge), all mirrors M05, DP2 output row above its AOM row, '
                             '24 x 15 in plate. Enclosure slide %.1f mm.' % cell_slide
                             + ('' if cat_eye == '300' else ' TEST CONFIGURATION cat_eye=%s on the same plate.' % cat_eye)}
    hidden = []
    # the hole audit checks the table bolts against this list (V9.4.2 pattern)
    info['mount_holes_mm'] = [((mx+.5)*layout.inch, (my+.5)*layout.inch) for mx, my in mount_holes]
    info['table_bolt_pattern'] = {
        'table_grid_in': 1.0, 'table_first_row_from_table_edge_in': 1.5,
        'plate_fiber_edge_inside_table_edge_in': 0.25, 'max_pair_spacing_in': 10,
        'fiber_side_pair': {'from_plate_right_edge_in': 6.25, 'n': 5, 'spacing_in': 10,
                            'centred_on_short_edge': True, 'xy_mm': [(447.675, 50.8), (447.675, 304.8)]},
        'ta_side_pair': {'from_plate_left_edge_in': 1.5, 'spacing_in': 10, 'centred_on_short_edge': True,
                         'xy_mm': [(41.275, 50.8), (41.275, 304.8)]},
        'plate_edges_mm': {'x': [3.175, 606.425], 'y': [-9.525, 365.125]}}

    # ---- placement helpers, so every optic below is a single readable line ----
    def put(name, cls, px, py, pangle=0, **kw):
        obj = baseplate.place_element(name, cls, x=px, y=py, angle=pangle, **kw)
        info['roots'][name] = obj
        return obj

    def mirror(name, px, py, pangle):
        return put(name, optomech.circular_mirror_union_optic, px, py, pangle, thickness=6,
                   mount_type=optomech.mirror_mount_M05, mount_args={'thumbscrews': True})

    def fold_angle(a, p, b):
        u = _unit((p[0]-a[0], p[1]-a[1]))
        v = _unit((b[0]-p[0], b[1]-p[1]))
        n = (v[0]-u[0], v[1]-u[1])
        return math.degrees(math.atan2(n[1], n[0]))

    # V9.4: every mirror on the board is an M05 with thumbscrews (the lab's
    # only mirror mount) - the folds, the retro mirrors and the output steering
    # mirrors included.
    def retro(name, px, py, pangle):
        return mirror(name, px, py, pangle)

    def bend(name, a, p, b):
        """A 45-degree M05 fold at p, turning the beam from a->p onto p->b."""
        return mirror(name, p[0], p[1], fold_angle(a, p, b))

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
        if part == CAT_LENS:
            obj.addProperty('App::PropertyString', 'CatalogueNote', 'Lens specification')
            obj.CatalogueNote = ('Thorlabs LA1618-B catalogue: R 155.0, tc 2.2, te 2.1, BFL 298.6 mm '
                                 '(587.6 nm); EFL 303.48 at 795 nm. Modelled with R 154.5 / tc 2.0: '
                                 'AOM->lens and lens->mirror are %.2f / %.2f mm short of the ideal '
                                 'cat-eye distances; accepted (return stays antiparallel, 9 um walk '
                                 'over 80-120 MHz).' % (-CAT_DEFOCUS_AOM_SIDE, -CAT_DEFOCUS_MIRROR_SIDE))
        return obj

    def hole(name, px, py, purpose):
        obj = put(name, optomech.BareTappedHole, px, py)
        obj.Purpose = purpose
        info['extra_cuts'].append(obj)
        info['reservations'].append({'object': obj.Name, 'reason': purpose})
        return obj

    def fiber(name, px, py, pangle, rear=REAR_CLAMP_OFFSET):
        # px is the KA05T mount origin; the lens-tube front sits LENS_TUBE_FRONT
        # ahead of it and the rear tail-clamp pair `rear` behind it.
        return put(name, optomech.fiberport_mount_KA05T_holes, px, py, pangle,
                   rear_hole_x_offset=rear, mount_args={'thumbscrews': True})

    def rotating_pbs(name, px, py, pangle):
        obj = put(name, optomech.rotation_stage_rsp05, px, py, pangle)
        obj.addProperty('App::PropertyString', 'Purpose').Purpose = (
            'Empty RSP05: user bonds PBS to rotating front face; no PBS or waveplate modeled.')
        return obj

    def path(name, points, color, envelope, assumption, kink_deg=None):
        obj = doc.addObject('Part::Feature', name)
        obj.Label = name + ' (nominal axis)'
        obj.Shape = Part.makePolygon([App.Vector(px, py, 0) for px, py in points])
        obj.ViewObject.LineColor = color
        obj.ViewObject.LineWidth = 2.5
        obj.addProperty('App::PropertyString', 'Scope').Scope = assumption
        obj.addProperty('App::PropertyBool', 'Bidirectional').Bidirectional = 'double pass' in name
        if isinstance(envelope, (float, int)):
            envelope = [envelope]*len(points)
        entry = {'name': name, 'points': points, 'object': obj.Name,
                 'envelope': envelope, 'assumption': assumption}
        if kink_deg is not None:
            # the audit's orthogonality rule exempts the diffracted axis downstream of an AOM
            entry['diffraction_kink_deg'] = kink_deg
            obj.addProperty('App::PropertyAngle', 'DiffractionKink').DiffractionKink = kink_deg
        info['paths'].append(entry)
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
    bend('TA steering fold 2', supply[1], supply[2], supply[3])      # (130, 338)
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
    bend('Common post-isolator fold 1', route[0], route[1], route[2])   # (130, 42)
    # the DP2 return leg (y ~ 14) passes under this M05's upper thumbscrew (knob at z = +9 mm)
    bend('Common post-isolator fold 2', route[1], route[2], route[3])         # (196, 42)
    bend('Common post-isolator fold 3', route[2], route[3], route[4])   # (196, 274.5)

    # V9.5: the sliding cell enclosure. The seat (a 10.3 mm pocket shaped for
    # the body, its covers, its shoulder and 12.7 mm of travel, plus two 8-32
    # taps through the floor) is placed with its local x along the beam
    # (angle 90: local +y = board -x, the sliding direction). The body, its two
    # covers and the cell glass stand on the seat `cell_slide` mm toward -x.
    cell = optomech.place_sliding_cell(baseplate, CELL_X, CELL_Y, angle=90, slide=cell_slide)
    info['cell'] = dict(cell)
    info['roots']['Rb cell seat (V9.5 pocket + 2 slot taps)'] = cell['root']
    info['roots']['Rb cell enclosure (V9.5 sliding body, covers, cell)'] = cell['cell']
    info['extra_cuts'].extend(o for o in cell['objects'] if hasattr(o, 'DrillPart'))
    cell_body = cell['cell']

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
    # angle 0: RF connector toward -y, KM100PM upstream of the AOM, so the
    # RF elbow sits between the DP1 and OUT1 rows and the top edge stays free
    # DiffractionAngle is the AOM object's record of the modelled downstream axis:
    # the +1 order (kinked) for the f = 300 chain, the input axis for the f = 75
    # test configurations (V9.3 convention); the body placement is the same.
    aom_axis_deg = 0. if f75_installed else DIFF_ANGLE_DEG
    dp1_aom = put('DP1 AOMO 3100-125', optomech.AOMO_3100_125, dp1_aom_x, DP1_Y, 0,
                  forward_direction=-1, backward_direction=1, diffraction_angle=aom_axis_deg,
                  surface_adapter_args={'adapter_height': 5})
    dp1_seat = optomech.integrate_aom(baseplate, dp1_aom)
    info['extra_cuts'].append(dp1_seat)
    # Folded f = 300 cat-eye on the +1-order axis d1 (2*theta_B toward +y, the
    # side away from the RF connector): +x-ish to F1 at the right edge, up the
    # vertical leg (iris, then F2), then back along the return leg to the lens,
    # the QWP and the retro mirror. All path lengths are measured along the beam.
    d1 = (math.cos(DIFF_ANGLE_RAD), math.sin(DIFF_ANGLE_RAD))
    u1 = _rot90(d1, ccw=True)                     # F1 turns the beam by +90 deg
    r1 = (-d1[0], -d1[1])                         # F2 turns it back, antiparallel to d1
    A1 = (dp1_aom_x, DP1_Y)
    dp1_leg1 = (DP1_FOLD_X - dp1_aom_x)/d1[0]     # F1 sits on x = DP1_FOLD_X
    F1 = _add(A1, d1, dp1_leg1)
    I1 = _add(F1, u1, DP1_IRIS_ABOVE_F1)
    F2 = _add(F1, u1, DP1_LEG2)
    dp1_d = AOM_TO_CAT - dp1_leg1 - DP1_LEG2
    LZ1 = _add(F2, r1, dp1_d)
    R1 = _add(LZ1, r1, CAT_TO_MIRROR)
    Q1 = _add(LZ1, r1, (LZ1[0] - DP1_QWP_X)/(-r1[0]))
    dp1_f1 = bend('DP1 cat-eye fold 1', A1, F1, F2)
    put('DP1 order selection iris', optomech.pinhole_ida12, I1[0], I1[1], -90.+DIFF_ANGLE_DEG)
    bend('DP1 cat-eye fold 2', F1, F2, LZ1)
    dp1_lens = lens('DP1 L300 ' + CAT_LENS, CAT_LENS, LZ1[0], LZ1[1], DIFF_ANGLE_DEG)
    wp('DP1 cat eye QWP', Q1[0], Q1[1], 180.+DIFF_ANGLE_DEG)
    dp1_retro = retro('DP1 retro mirror', R1[0], R1[1], DIFF_ANGLE_DEG)

    # =========================================================================
    # 5. DP2 arm (reflected): one fold down to its AOM row, then the double pass
    # =========================================================================
    dp2_sep_x = X0 + 48.
    dp2_aom_x = dp2_sep_x + PBS_TO_AOM
    dp2_in = bend('DP2 input steering mirror', (X0, MAIN_Y), (X0, DP2_Y), (dp2_sep_x, DP2_Y))
    wp('DP2 input HWP', X0+25, DP2_Y, 0)
    # V9.4: the DP2 output row is ABOVE its AOM row, so this cube reflects the
    # returning beam toward +y (invert=True)
    pbs('DP2 separation PBS', dp2_sep_x, DP2_Y, 0, invert=True)
    dp2_aom = put('DP2 AOMO 3100-125', optomech.AOMO_3100_125, dp2_aom_x, DP2_Y, 0,
                  forward_direction=-1, backward_direction=1, diffraction_angle=aom_axis_deg,
                  surface_adapter_args={'adapter_height': 5})
    dp2_seat = optomech.integrate_aom(baseplate, dp2_aom)
    info['extra_cuts'].append(dp2_seat)
    # Folded f = 300 cat-eye: +x-ish to F3, DOWN the vertical leg (iris, then F4
    # near the bottom edge), then back along the return leg (sloping 1.08 deg
    # down toward -x) to the lens, the QWP and the retro mirror.
    d2 = d1
    u2 = _rot90(d2, ccw=False)                    # F3 turns the beam by -90 deg
    r2 = (-d2[0], -d2[1])
    A2 = (dp2_aom_x, DP2_Y)
    dp2_leg1 = (DP2_FOLD_X - dp2_aom_x)/d2[0]
    F3 = _add(A2, d2, dp2_leg1)
    dp2_leg2 = (F3[1] - DP2_F4_Y)/(-u2[1])
    F4 = _add(F3, u2, dp2_leg2)
    I2 = _add(F3, u2, DP2_IRIS_L - dp2_leg1)
    dp2_d = AOM_TO_CAT - dp2_leg1 - dp2_leg2
    LZ2 = _add(F4, r2, dp2_d)
    R2 = _add(LZ2, r2, CAT_TO_MIRROR)
    Q2 = _add(LZ2, r2, (LZ2[0] - DP2_QWP_X)/(-r2[0]))
    dp2_f3 = bend('DP2 cat-eye fold 1', A2, F3, F4)
    put('DP2 order selection iris', optomech.pinhole_ida12, I2[0], I2[1], -90.+DIFF_ANGLE_DEG)
    bend('DP2 cat-eye fold 2', F3, F4, LZ2)
    dp2_lens = lens('DP2 L300 ' + CAT_LENS, CAT_LENS, LZ2[0], LZ2[1], DIFF_ANGLE_DEG)
    wp('DP2 cat eye QWP', Q2[0], Q2[1], 180.+DIFF_ANGLE_DEG)
    dp2_retro = retro('DP2 retro mirror', R2[0], R2[1], DIFF_ANGLE_DEG)

    # =========================================================================
    # 5b. Optional f = 75 cat-eye hole sets (bare 8-32 taps, nothing installed)
    # =========================================================================
    # V9.4.1: the set lies on the 0-order (input) axis y = DP_Y, elements at
    # angle 0 (lens, QWP, iris) and 180 (retro mirror), as in V9.3.
    f75_holes, f75_lens_holes, f75_parts, f75_seats = [], [], {}, []
    f75_note = ('Bare 8-32 hole of the OPTIONAL f = 75 cat-eye (V9.3 LA1612-B set) on the 0-order '
                '(input) axis straight after the AOM; nothing is installed in V9.4. ')

    def f75_set(index, A):
        tag, geo = 'DP%d ' % index, F75[index]
        def at(s, t=0.):
            return (A[0] + s, A[1] + t)
        # The RSP05 lip adapter needs its 23 x 48 x 9.3 mm pocket, not just two
        # taps, so the QWP seat is always machined: the RSP05 object is placed in
        # every configuration and marked not-installed (hidden, excluded from the
        # audits) when the f = 75 set is absent - like the single-TA blocker seat.
        f_qwp = wp(tag+'f75 cat eye QWP', *at(geo['qwp']), 0.)
        f_qwp.addProperty('App::PropertyBool', 'InstalledInThisMode', 'Installation')
        f_qwp.InstalledInThisMode = f75_installed
        if not f75_installed:
            f_qwp.Label = tag+'f75 cat eye QWP - NOT INSTALLED (seat machined for the f = 75 option)'
            hidden.append(f_qwp)
            f75_seats.append(tag+'f75 cat eye QWP')
        if f75_installed:
            # test configuration: the set is mounted on exactly the holes drilled
            # for it (each part's own DrillPart lands on the bare-hole position)
            f_lens = lens(tag+'f75 LA1612-B', 'LA1612-B', *at(geo['lens']), 0.)
            f_iris = put(tag+'f75 order iris', optomech.pinhole_ida12, *at(geo['iris']), 0.)
            face_s = geo['face'][f75_mirror_key]
            f_retro = put(tag+'f75 retro mirror (lens->mirror %s)' % f75_mirror_key,
                          optomech.circular_mirror_union_optic, *at(face_s), 180.,
                          thickness=6, mount_type=optomech.mirror_mount_M05, mount_args={'thumbscrews': False})
            f75_parts[index] = {'lens': f_lens, 'qwp': f_qwp, 'iris': f_iris, 'retro': f_retro,
                                'A': A, 'lens_xy': at(geo['lens']), 'qwp_xy': at(geo['qwp']),
                                'iris_xy': at(geo['iris']), 'retro_xy': at(face_s),
                                'lens_s': geo['lens'], 'mirror_s': face_s}
        else:
            lens_hole = hole(tag+'f75 lens 8-32', *at(geo['lens'] - holder_tap_offset('LA1612-B')),
                             f75_note + 'L05G tap for the LA1612-B %g mm after the AOM (holder body upstream).' % geo['lens'])
            f75_lens_holes.append(lens_hole)
            f75_holes.append(lens_hole)
            f75_holes.append(hole(tag+'f75 order iris 8-32', *at(geo['iris'] + IRIS_TAP_ALONG, IRIS_TAP_ACROSS),
                                  f75_note + 'Slide-mount tap for the IDA12 order iris %g mm after the AOM, post toward -y.' % geo['iris']))
        for key, face_s in geo['face'].items():
            if f75_installed and key == f75_mirror_key:
                continue
            f75_holes.append(hole(tag+'f75 retro mirror 8-32 (lens->mirror %s)' % key, *at(face_s + F75_TAP_BEHIND_M05),
                                  f75_note + 'M05 tap for a retro mirror facing the AOM, mirror face %g mm after the AOM '
                                  '(lens -> mirror %s mm).' % (face_s, key)))
    f75_set(1, A1)
    f75_set(2, A2)
    inactive = list(f75_seats)
    if cat_eye == '75-75':
        # the 75/75 mirror body stands where the first fold is: that fold is off the plate
        for obj in (dp1_f1, dp2_f3):
            obj.Label = obj.Label + ' - NOT INSTALLED (f75-75 test)'
            hidden.append(obj)
        inactive += ['DP1 cat-eye fold 1', 'DP2 cat-eye fold 1']
    if inactive:
        for key in ('fiber_clearance', 'service_clearance'):
            info.setdefault(key, {})['inactive_roots'] = inactive

    # =========================================================================
    # 6. The two output rows: telescope, HWP, rotating PBS, iris, fiber head
    # =========================================================================
    iris_x = {k: PORT_X - LENS_TUBE_FRONT - v for k, v in IRIS_TO_LENS_TUBE.items()}   # 468.0 / 461.5
    outputs = []
    # DP1 row (below its AOM row): HWP right after the mirror, then the telescope,
    # then the rotating PBS - the two RSP05 adapters stay clear of the DP1 RF
    # elbow zones (tail x 361..412, neck x 402..422, both at y >= 240).
    # DP2 row (above its AOM row): telescope first, HWP and rotating PBS beyond
    # x = 401 where the AOM/KM100PM footprint (y up to 104) ends.
    for index, row_y, source_y, sep_x, aom_x, hwp_x, lens1_x, rot_x in (
            (1, OUT1_Y, DP1_Y, dp1_sep_x, dp1_aom_x, dp1_sep_x + 24.6, dp1_sep_x + 38.1, DP1_OUT_ROT_X),
            (2, OUT2_Y, DP2_Y, dp2_sep_x, dp2_aom_x, DP2_OUT_HWP_X, dp2_sep_x + 16., DP2_OUT_ROT_X)):
        tag = 'DP%d ' % index
        lens2_x = lens1_x + 45.319348
        out_mirror = bend(tag+'output steering mirror',
                          (sep_x, source_y), (sep_x, row_y), (PORT_X, row_y))
        l1 = lens(tag+'output first LA1289-B', 'LA1289-B', lens1_x, row_y, 180)
        l2 = lens(tag+'output second LA1540-B', 'LA1540-B', lens2_x, row_y, 0)
        wp(tag+'output HWP', hwp_x, row_y, 0)
        rotating_pbs(tag+'empty rotating PBS RSP05', rot_x, row_y, 0)
        # standard slotted slide mounts on both rows. DP1: post toward +y (ends
        # at 252, 40 mm left of the RF tail zone). DP2: post toward -y (ends at
        # 95, 11 mm above the DP2 AOM-row beam), clear of the external head's
        # 50 mm front-access zone above; with the post at -y the iris body faces
        # the head, so it sits 36.5 mm ahead of the lens tube (28 mm access zone).
        out_iris = put(tag+'output filtering iris', optomech.pinhole_ida12, iris_x[index], row_y,
                       180 if index == 1 else 0)
        head = fiber(tag+'output KA05T', PORT_X, row_y, 180)
        outputs.append(dict(index=index, row_y=row_y, source_y=source_y, sep_x=sep_x, aom_x=aom_x,
                            mirror=out_mirror, l1=l1, l2=l2, hwp_x=hwp_x, rot_x=rot_x,
                            iris=out_iris, head=head, lens1_x=lens1_x, lens2_x=lens2_x))

    # =========================================================================
    # 7. External-TA input (installed in mode='dual' only)
    # =========================================================================
    external_head = fiber('External TA input KA05T', PORT_X, EXT_Y, 180)
    # V9.4: both telescope lenses on the input lane (the L05G footprint of a lens
    # on the injection leg, or anywhere between x 285 and 336 on the lane, would
    # sit inside one of the two output steering M05s' thumbscrew envelopes).
    external_lens2_x = EXT_LENS2_HOLE_X - holder_tap_offset('LA1560-B')       # 339.25: lens 2 plane
    external_lens1_x = external_lens2_x + EXTERNAL_SPH_CENTER_SPACING          # 414.82: lens 1 plane
    e1 = hole('External spherical first lens 8-32',
              external_lens1_x + holder_tap_offset('LA1213-B'), EXT_Y,
              'Bare 8-32 hole for the external telescope lens 1 (LA1213-B planned); '
              'L05G tap position, lens plane %g mm downstream.' % holder_tap_offset('LA1213-B'))
    e2 = hole('External spherical second 8-32', EXT_LENS2_HOLE_X, EXT_Y,
              'Bare 8-32 hole for the external telescope lens 2 (LA1560-B planned); '
              'L05G tap position, lens plane %g mm downstream.' % holder_tap_offset('LA1560-B'))
    spare = hole('External spherical spare 8-32', X0+EXT_SPARE_DX, EXT_Y,
                 'One optional 8-32 lens position in the external input lane.')
    external_holes = [e1, e2, spare]
    # beam direction at each: all three sit on the -x lane
    external_beam_dirs = [(-1., 0.), (-1., 0.), (-1., 0.)]
    injection = bend('Optional external TA injection mirror',
                     (external_lens2_x, EXT_Y), (X0, EXT_Y), (X0, DP2_Y))
    BLOCKER_Y = MAIN_Y - 49.       # 225.5: 10 mm off the residual axis, ring metal on it
    blocker = put('Optional PBS leakage blocking iris', optomech.pinhole_ida12, X0+10., BLOCKER_Y, 90)
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
    w_focus = .000795*CAT_EFL_795/(math.pi*.6)          # 0.127 mm at the retro mirror
    if not f75_installed:
        path('DP1 double pass',
             [(dp1_sep_x, DP1_Y), A1, F1, I1, F2, LZ1, Q1, R1], BLUE,
             [.6, .6, .6, .6, .6, .6, .6*(1. - (LZ1[0]-Q1[0])/CAT_EFL_795), w_focus],
             KINKED, kink_deg=DIFF_ANGLE_DEG)
        path('DP2 double pass',
             [(dp2_sep_x, DP2_Y), A2, F3, I2, F4, LZ2, Q2, R2], GREEN,
             [.6, .6, .6, .6, .6, .6, .6*(1. - (LZ2[0]-Q2[0])/CAT_EFL_795), w_focus],
             KINKED, kink_deg=DIFF_ANGLE_DEG)
    else:
        # f = 75 test (V9.4.1): AOM -> LA1612-B -> QWP -> iris -> retro on the
        # 0-order (input) axis, as in V9.3. The +1 order leaves the AOM 2*theta_B
        # above that axis and, the AOM being in the lens's front focal plane,
        # runs parallel to it f*2*theta_B = 1.4 mm above after the lens, where
        # it converges toward its focus (EFL 75.87 behind the lens, spot
        # 0.038 mm). The envelope radius below covers BOTH orders: the nominal
        # 0.6 mm about the +1 order plus its offset from the modelled axis.
        f75_efl = LENSES['LA1612-B'][3]
        f75_offset_after_lens = F75_PLUS1_OFFSET_AFTER_LENS             # 1.44 mm
        for index, sep_x, row_y, color in ((1, dp1_sep_x, DP1_Y, BLUE), (2, dp2_sep_x, DP2_Y, GREEN)):
            pr = f75_parts[index]
            def env(s):
                return max(.6*(1. - (s - pr['lens_s'])/f75_efl), .038) + f75_offset_after_lens
            path('DP%d double pass' % index,
                 [(sep_x, row_y), pr['A'], pr['lens_xy'], pr['qwp_xy'], pr['iris_xy'], pr['retro_xy']], color,
                 [.6, .6, .6 + pr['lens_s']*math.tan(DIFF_ANGLE_RAD),
                  env(F75[index]['qwp']), env(F75[index]['iris']), env(pr['mirror_s'])],
                 'f = 75 test configuration (%s) on the 0-order axis; the envelope includes the +1 order, '
                 '2*theta_B = %.4f deg off the input axis at %g MHz (1.4 mm above the axis after the lens). '
                 % (cat_eye, DIFF_ANGLE_DEG, AOM_RF_DESIGN_HZ/1e6) + DOWNSTREAM)
    for out in outputs:
        path('DP%d output' % out['index'],
             [(out['sep_x'], out['source_y']), (out['sep_x'], out['row_y']),
              (out['lens1_x'], out['row_y']), (out['lens1_x']+30.2466184, out['row_y']),
              (out['lens2_x'], out['row_y']), (PORT_X-LENS_TUBE_FRONT, out['row_y'])],
             BLUE if out['index'] == 1 else GREEN, [.6, .6, .6, .035, .6, .6], DOWNSTREAM)
    if mode == 'single':
        path('DP2 feed', [(X0, MAIN_Y), (X0, DP2_Y), (dp2_sep_x, DP2_Y)], GREEN, .6, DOWNSTREAM)
    else:
        external_focus_x = external_lens1_x - LENSES['LA1213-B'][3]
        path('External TA telescope',
             [(PORT_X-LENS_TUBE_FRONT, EXT_Y), (external_lens1_x, EXT_Y), (external_focus_x, EXT_Y),
              (external_lens2_x, EXT_Y), (X0, EXT_Y), (X0, DP2_Y), (dp2_sep_x, DP2_Y)],
             PURPLE, [.9, .9, .035, .6, .6, .6, .6], DOWNSTREAM)
        # Stop the displayed beam at the deliberately offset iris metal, but keep
        # a separate full-length probe for the physical contact audit; drawing
        # that probe as a beam would look as though light passed the blocker.
        residual = doc.addObject('Part::Feature', 'PBSResidualBlocked')
        residual.Label = 'PBS residual - stops at offset iris metal'
        residual.Shape = Part.makePolygon([App.Vector(PBS_X, MAIN_Y, 0), App.Vector(PBS_X, BLOCKER_Y+5., 0)])
        residual.ViewObject.LineColor = (.6, .45, .15)
        residual.addProperty('App::PropertyLength', 'VisibleStopY', 'Beam display').VisibleStopY = BLOCKER_Y+5.
        residual.addProperty('App::PropertyLength', 'AuditProbeEndY', 'Beam display').AuditProbeEndY = BLOCKER_Y-12.
        info['paths'].append({'name': 'PBS residual blocked', 'points': [(PBS_X, MAIN_Y), (PBS_X, BLOCKER_Y-12.)],
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
            {'type': 'iris', 'name': out['iris'].Label, 'xy': (iris_x[out['index']], out['row_y'])},
            {'type': 'fiber', 'name': out['head'].Label, 'xy': (PORT_X-LENS_TUBE_FRONT, out['row_y'])}]})
        info['geometry_assertions'].append(
            {'name': tag+'output iris centre -> KA05T lens-tube front',
             'measured': (PORT_X-LENS_TUBE_FRONT)-iris_x[out['index']],
             'expected': IRIS_TO_LENS_TUBE[out['index']], 'tolerance': 1e-7})
        info['geometry_assertions'].append(
            {'name': tag+'rotating PBS -> output iris', 'measured': iris_x[out['index']]-out['rot_x'],
             'expected': iris_x[out['index']]-out['rot_x'], 'tolerance': 1e-7})

    for index, aom, seat, cat, retro, arm_y, aom_x, tail_sgn in (
            (1, dp1_aom, dp1_seat, dp1_lens, dp1_retro, DP1_Y, dp1_aom_x, -1.),
            (2, dp2_aom, dp2_seat, dp2_lens, dp2_retro, DP2_Y, dp2_aom_x, -1.)):
        tag = 'DP%d ' % index
        if f75_installed:
            pr = f75_parts[index]
            info['arms'].append({'id': index, 'aom': aom.Name, 'lens': pr['lens'].Name, 'retro': pr['retro'].Name,
                                 'integral_seat': seat.Name, 'aom_to_cat': pr['lens_s'],
                                 'cat_to_mirror': pr['mirror_s'] - pr['lens_s'], 'folded': False,
                                 'axis': '0-order (input) axis; +1 order %.2f mm above it after the lens'
                                         % F75_PLUS1_OFFSET_AFTER_LENS,
                                 'diffraction_kink_deg': 0., 'configuration': cat_eye,
                                 'idle_f300_chain': [cat.Name, retro.Name]})
            info['geometry_assertions'].extend([
                {'name': tag+'f75 AOM -> LA1612-B plane', 'measured': _dist(pr['A'], pr['lens_xy']),
                 'expected': pr['lens_s'], 'tolerance': 1e-7},
                {'name': tag+'f75 LA1612-B -> retro face', 'measured': _dist(pr['lens_xy'], pr['retro_xy']),
                 'expected': float(f75_mirror_key), 'tolerance': 1e-7}])
        else:
            info['arms'].append({'id': index, 'aom': aom.Name, 'lens': cat.Name, 'retro': retro.Name,
                                 'integral_seat': seat.Name, 'aom_to_cat': AOM_TO_CAT,
                                 'cat_to_mirror': CAT_TO_MIRROR, 'folded': True,
                                 'diffraction_kink_deg': DIFF_ANGLE_DEG})
        # both AOMs at angle 0: connector toward -y. Both tails are clocked toward
        # -x: DP1's because the OUT1 rotating PBS sits under a +x tail, DP2's
        # because its return leg (y ~ 18 at x 440) would graze a +x tail zone.
        info['service_regions'].append(
            {'name': tag+'RF elbow neck candidate', 'kind': 'aom_connector', 'owner': aom.Name,
             'origin_xy_mm': [aom_x, arm_y-33.02], 'direction_xy': [0, -1.], 'length_mm': 20., 'width_mm': 20.,
             'allowed_paths': [], 'dimensions_verified': False,
             'assumptions': ['Unconfirmed 20 mm outward neck envelope.']})
        info['service_regions'].append(
            {'name': tag+'RF elbow tail candidate', 'kind': 'aom_sma', 'owner': aom.Name,
             'origin_xy_mm': [aom_x, arm_y-53.02], 'direction_xy': [tail_sgn, 0], 'length_mm': 50.8, 'width_mm': 20.,
             'allowed_paths': [], 'dimensions_verified': False,
             'assumptions': ['Provisional planar elbow, clocking not confirmed.']})

    info['service_regions'].append(
        {'name': 'TA thick bottom cable', 'kind': 'ta_cable', 'owner': ta.Name,
         'origin_xy_mm': [9.844387, TA_XY[1] - 29.925], 'direction_xy': [-1., 0.], 'length_mm': 101.6,
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
    # the rear tail-clamp pairs sit REAR_CLAMP_OFFSET behind every head; the user's
    # clamps are TAIL_CLAMP_WIDTH wide (audit default 50), so rows 40 mm apart do not overlap
    info.setdefault('fiber_clearance', {}).update({'rear_offsets_mm': [REAR_CLAMP_OFFSET],
                                                   'clamp_width_mm': TAIL_CLAMP_WIDTH})
    # the upper fiber-side bolt (17.125, 11.5) lies under the DP1 beam between
    # the AOM and the f = 75 lens position: install before aligning
    info.setdefault('hole_clearance', {})['platform_beam_crossings_allowed'] = True
    # the optional f75 lens and mirror taps sit on the 0-order axis by design:
    # empty holes 12.7 mm below the input beam, usable only with the f = 300
    # chain's first fold removed or the beam absent
    info['hole_clearance']['empty_holes_under_beam_allowed'] = [
        o.Label for o in f75_holes if 'lens' in o.Label or 'retro mirror' in o.Label]

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
    spherical_groups.append({'name': 'f75 option', 'active_lenses': [],
                             'spare_holes': [o.Name for o in f75_holes],
                             'stations_only': True, 'spare_required': len(f75_holes)})
    if mode == 'dual':
        info['geometry_assertions'].append(
            {'name': 'External f1+f2 separation (design lens planes, both on the lane)',
             'measured': external_lens1_x-external_lens2_x,
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
            + list(zip(external_holes, external_beam_dirs))
            # the two optional f75 lens taps are audited with the L05G footprint
            # (beam along +x, the 0-order axis); the QWP and iris taps with a 10 mm disk
            + [(o, (1., 0.)) for o in f75_lens_holes]]
            + [{'object': o.Name, 'center_xy_mm': [o.BasePlacement.Base.x, o.BasePlacement.Base.y],
                'diameter_mm': 10.0}
               for o in f75_holes if o not in f75_lens_holes and 'retro mirror' not in o.Label]}
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

    def dist(p, q):
        return math.hypot(q[0]-p[0], q[1]-p[1])

    def seat_tap_xy(index):
        # a seat tap (seat frame) carried into the board frame by the seat's placement
        lx, ly = cell['dimensions']['tap_holes_local_xy_mm'][index]
        seat = cell['root']
        v = seat.BasePlacement.Rotation.multVec(App.Vector(lx, ly, 0))
        return (seat.BasePlacement.Base.x + v.x, seat.BasePlacement.Base.y + v.y)

    info['geometry_assertions'].extend([
        {'name': 'DP1 AOM -> cat-eye lens along the folded beam',
         'measured': dist(A1, F1) + dist(F1, F2) + dist(F2, LZ1), 'expected': AOM_TO_CAT, 'tolerance': 1e-7},
        {'name': 'DP1 cat-eye lens -> retro mirror', 'measured': dist(LZ1, R1),
         'expected': CAT_TO_MIRROR, 'tolerance': 1e-7},
        {'name': 'DP1 fold 1 turns the beam by 90 deg',
         'measured': math.degrees(math.acos(d1[0]*u1[0] + d1[1]*u1[1])), 'expected': 90., 'tolerance': 1e-7},
        {'name': 'DP1 return leg antiparallel to the +1 order',
         'measured': math.degrees(math.acos(-(d1[0]*r1[0] + d1[1]*r1[1]))), 'expected': 0., 'tolerance': 1e-7},
        {'name': 'DP1 0-order iris distance from the AOM along the beam',
         'measured': dist(A1, F1) + dist(F1, I1), 'expected': dp1_leg1 + DP1_IRIS_ABOVE_F1, 'tolerance': 1e-7},
        {'name': 'DP2 AOM -> cat-eye lens along the folded beam',
         'measured': dist(A2, F3) + dist(F3, F4) + dist(F4, LZ2), 'expected': AOM_TO_CAT, 'tolerance': 1e-7},
        {'name': 'DP2 cat-eye lens -> retro mirror', 'measured': dist(LZ2, R2),
         'expected': CAT_TO_MIRROR, 'tolerance': 1e-7},
        {'name': 'DP2 fold 1 turns the beam by 90 deg',
         'measured': math.degrees(math.acos(d2[0]*u2[0] + d2[1]*u2[1])), 'expected': 90., 'tolerance': 1e-7},
        {'name': 'DP2 0-order iris distance from the AOM along the beam',
         'measured': dist(A2, F3) + dist(F3, I2), 'expected': DP2_IRIS_L, 'tolerance': 1e-7},
        {'name': 'Stations 1-2 pitch', 'measured': station_pitch(lane_stations[0], lane_stations[1]),
         'expected': 45., 'tolerance': 1e-7},
        {'name': 'Stations 2-3 pitch', 'measured': station_pitch(lane_stations[1], lane_stations[2]),
         'expected': 45., 'tolerance': 1e-7},
        {'name': 'Station 4->5 along beam via fold 2',
         'measured': along_beam(sphere_stations[0], sphere_stations[1], (CELL_X, LOWER_RUN_Y)),
         'expected': 60., 'tolerance': 1e-7},
        {'name': 'Station 4->6 along beam via fold 2',
         'measured': along_beam(sphere_stations[0], sphere_stations[2], (CELL_X, LOWER_RUN_Y)),
         'expected': 100., 'tolerance': 1e-7},
        # V9.5: the enclosure slides toward -x; the seat (pocket + taps) never moves
        {'name': 'Cell enclosure bore axis offset from the beam (toward -x) = cell_slide',
         'measured': CELL_X - cell_body.BasePlacement.Base.x, 'expected': float(cell_slide), 'tolerance': 1e-7},
        {'name': 'Cell enclosure stays on the beam axis along y',
         'measured': cell_body.BasePlacement.Base.y, 'expected': CELL_Y, 'tolerance': 1e-7},
        {'name': 'Cell seat tap 1 on the board at (CELL_X + 27.35, CELL_Y - 30)',
         'measured': dist(seat_tap_xy(0), (CELL_X + 27.35, CELL_Y - 30.)), 'expected': 0., 'tolerance': 1e-7},
        {'name': 'Cell seat tap 2 on the board at (CELL_X + 27.35, CELL_Y)',
         'measured': dist(seat_tap_xy(1), (CELL_X + 27.35, CELL_Y)), 'expected': 0., 'tolerance': 1e-7}])
    info['cell_enclosure'] = {
        'slide_mm': float(cell_slide), 'travel_mm': CELL_SLIDE_MAX, 'slide_direction_board': '-x',
        'seat_taps_board_xy_mm': [[CELL_X + 27.35, CELL_Y - 30.], [CELL_X + 27.35, CELL_Y]],
        'pocket_main_board_mm': [CELL_X - 34.9, CELL_Y - 50., CELL_X + 26.5, CELL_Y + 50.],
        'pocket_ear_board_mm': [CELL_X + 20.2, CELL_Y - 40., CELL_X + 47.2, CELL_Y + 8.],
        'assembly_board_mm': [CELL_X - 20.2 - cell_slide, CELL_Y - 48., CELL_X + 45.2 - cell_slide, CELL_Y + 48.],
        'shoulder_board_mm': [CELL_X + 20.2 - cell_slide, CELL_Y - 38., CELL_X + 45.2 - cell_slide, CELL_Y + 6.],
        'dimensions': cell['dimensions']}
    info['fold_geometry'] = {
        'diffraction_kink_deg': DIFF_ANGLE_DEG,
        'cat_eye_lens_catalogue': dict(LA1618B_CATALOGUE),
        'cat_eye_defocus_mm': {'aom_side': CAT_DEFOCUS_AOM_SIDE, 'mirror_side': CAT_DEFOCUS_MIRROR_SIDE,
                               'accepted': True},
        'f75_option': {'distances_from_aom_mm': {'DP%d' % k: v for k, v in F75.items()},
                       'axis': '0-order (input) axis y = DP_Y (V9.4.1; V9.4 used the +1-order axis)',
                       'plus1_offset_after_lens_mm': F75_PLUS1_OFFSET_AFTER_LENS,
                       'installed': f75_installed, 'configuration': cat_eye,
                       'bare_holes': [o.Name for o in f75_holes],
                       'note': 'With the lens->mirror 50 position every f = 300 part may stay installed; '
                               'the lens->mirror 75 mirror body overlaps fold F1 (DP1) / F3 (DP2), which '
                               'must be removed for that test.'},
        'DP1': {'AOM': A1, 'F1': F1, 'iris': I1, 'F2': F2, 'lens': LZ1, 'QWP': Q1, 'retro': R1,
                'leg1': dp1_leg1, 'leg2': DP1_LEG2, 'fold2_to_lens': dp1_d},
        'DP2': {'AOM': A2, 'F3': F3, 'iris': I2, 'F4': F4, 'lens': LZ2, 'QWP': Q2, 'retro': R2,
                'leg1': dp2_leg1, 'leg2': dp2_leg2, 'fold2_to_lens': dp2_d}}

    # ---- cut the plate once every element and machining volume is in place ----
    doc.recompute()
    layout.redraw()
    for obj in hidden:
        for child in optomech.descendants(obj):
            child.ViewObject.hide()
    plate.Drill = drill
    plate.touch()
    doc.recompute()
    doc.Label = ('Lattice V9.5 - ' + ('single TA' if mode == 'single' else 'external TA')
                 + ('' if cat_eye == '300' else ' - f75 test ' + cat_eye)
                 + ('' if not cell_slide else ' - cell slid %.1f mm' % cell_slide))
    return info


if __name__ == "__main__":
    example_baseplate()
    layout.redraw()
