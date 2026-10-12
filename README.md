# Rb87 Neutral Atom Optical Platform (PyOpticL + FreeCAD)

This repository contains a PyOpticL-based optical/mechanical layout for building an optical platform targeting Rb-87 neutral atom experiments. It assembles a complete, code-driven CAD model in FreeCAD, organizing the setup into modular boards.

The project originates from (and depends on) PyOpticL, a code-to-CAD tooling framework for modular optics systems engineering, and uses FreeCAD as the CAD backend.

- Project webpage (origin): https://github.com/UMassIonTrappers/PyOpticL
- Affiliation: UC Berkeley, Department of Physics — Prof. Sulyemanzade’s research group
- Lab website: https://suleymanzadelab.com/
- Collaborators:
  - University of Wisconsin-Madison - Prof. Sinclair's research group - https://sinclair.physics.wisc.edu/
  - Dr. Brandon Grinkemeyer, Harvard University (Postdoctoral Researcher) — https://lukin.physics.harvard.edu/people/brandon-grinkemeyer

---
## Overview

- Purpose: Build a modular optical platform for Rb-87 neutral atom quantum computing.
- CAD Backend: FreeCAD
- Optical/CAD Tooling: PyOpticL
- Project Structure: The system is organized into these main boards:
  - Reference_board
  - Laser_board
  - Repumper_board
  - Spectroscopy_board
  - TA_board
  - AOM_board

## Prerequisites

- FreeCAD (latest stable recommended)
- PyOpticL module installed in FreeCAD

---

## Installation

1. Install FreeCAD on your system.
2. Install PyOpticL in FreeCAD, following the official instructions at https://github.com/UMassIonTrappers/PyOpticL.
3. Update the PyOpticL module directory with this project’s assets:
   - Copy the `stl` folder from this repository into the PyOpticL module’s directory.
   - Copy `optomech.py` from this repository into the PyOpticL module’s directory, replacing the existing file if present.

Note: The exact PyOpticL module path depends on your OS and FreeCAD configuration (e.g., on macOS it may be under `~/Library/Application Support/FreeCAD/Mod/PyOpticL/PyOpticL`).

## Project Files

- `stl/` — Mechanical part models used by the layout (mounts, adapters, etc.) in stl format.
- `optomech.py` — Project-specific mechanical and optical component definitions/overrides for PyOpticL.
- `Adapters/` - 3D\-printable files(most of them are in step format) for the adapters on the boards, along with the Rb cell holders.
- Main script: See the provided Python script (e.g., “PyOpticL_Rubidium_System”) that constructs all boards in FreeCAD using PyOpticL.

---

## Boards

- Reference_board:
![The schematic of reference board in FreeCAD(front view))](<Production/ReferenceBoard/ReferenceBoard1.png>)
![The schematic of reference board in FreeCAD(top view)](<Production/ReferenceBoard/ReferenceBoard2.png>)
  After exiting the laser, the main beam passes through polarizing elements and isolators, then through several PBSs before entering the fiber, which leads to the Spectroscopy board for frequency locking. Three beams, including the MOT light and Repump light, are each combined with side beams split from the main beam by PBSs, using beatnote technology to achieve frequency locking of these beams.<br><br>

---

- Laser_board:
![The schematic of Laser board1 in FreeCAD(front view)](<Production/LaserBoard/LaserBoard1a.png>) 
![The schematic of Laser board1 in FreeCAD(top view)](<Production/LaserBoard/LaserBoard1b.png>) 
![The schematic of Laser board2 in FreeCAD(front view)](<Production/LaserBoard2/Laser_Board2a.png>) 
![The schematic of Laser board2 in FreeCAD(top view)](<Production/LaserBoard2/Laser_Board2b.png>) 
The Laser board’s beam splits into two paths: one for various operations (Like MOT and Repumper) and one to the Reference board for frequency locking. 
Because of different types of isolators we may using, there are two versions of the Laser board.<br><br>

---

- Repumper_board:
![The schematic of repumper board in FreeCAD(front view)](<Production/RepumperBoard/RepumperBoard1.png>)
![The schematic of repumper board in FreeCAD(top view)](<Production/RepumperBoard/RepumperBoard2.png>)
The laser board output is sent via fiber to the repumper board (lower left), where a PBS splits it into two beams: one directed to the AOM board (which we likely won’t use for repumping), and the other passing through an AOM and shutter into a fiber.<br><br>

---

- Spectroscopy_board:
![The schematic of spectroscopy board in FreeCAD(front view)](<Production/SASBoard/SASBoard1.png>)
![The schematic of spectroscopy board in FreeCAD(top view)](<Production/SASBoard/SASBoard2.png>)
After going through the reference board, the main beam splits into two beams, one strong(pump) and one weak(probe), which counterpropagate through the Rb atomic vapor at this board. The stronger beam finally goes to the photodetector. Here we use the Saturation absorption spectroscopy method, which will selectively saturate zero-velocity atoms in a vapor, producing a narrow Lamb dip that overcomes Doppler broadening and provides a stable reference for high-precision laser frequency locking.<br><br>

---

- TA_board: 
![The schematic of TA board in FreeCAD(front view)](<Production/TABoard/TABoard1.png>)
![The schematic of TA board in FreeCAD(top view)](<Production/TABoard/TABoard2.png>)
On this board, a tapered amplifier boosts the laser power before passing it through a -60 dB isolator. The beam is then split into two paths: one leads directly to a fiber for possible coarse locking, while the other passes through an AOM and a shutter before entering a fiber for operations.

---

- AOM_board:
![The schematic of AOM board in FreeCAD(front view)](<Production/AOMBoard/AOMBoard1.png>)
![The schematic of AOM board in FreeCAD(top view)](<Production/AOMBoard/AOMBoard2.png>)
After the TA board, we split the beam into multiple paths, couple each into an optical fiber, and equip each path with an AOM and shutter for switching. This is achieved by combining the Repumper board and AOM board. The TA output is sent via fiber to the repumper board, where a PBS divides it into two beams: one is routed to the appropriately positioned AOM board, and the other passes through an AOM and shutter into a fiber. The beam entering the AOM board is split again: one branch feeds the next AOM board, and the other is coupled into a fiber. This way, we can control the number of beams by adjusting the number of AOM boards.

---
## How to Use

Please see the Quickstart Guide in the PyOpticL wiki:
https://github.com/UMassIonTrappers/PyOpticL/wiki#quickstart-guide

---

## Acknowledgments

**Developed through a collaborative effort between the Department of Physics at the [University of California, Berkeley](https://suleymanzadelab.com/) (Prof. Sulyemanzade’s group) and the [University of Wisconsin–Madison](https://sinclair.physics.wisc.edu/) (Prof. Sinclair’s research group).**  
Additional contributions were provided by [Dr. Brandon Grinkemeyer](https://lukin.physics.harvard.edu/people/brandon-grinkemeyer) (Harvard University, Lukin Group).

The project builds on **PyOpticL**, a code-to-CAD optical layout tool enabling parametric and modular optics design within **FreeCAD**, an open-source parametric 3D CAD modeler used to render and manipulate the generated assemblies.

## Citation

If you use this work in academic settings, please also cite:
- PyOpticL and its associated publications.
- This repository (include commit or release tags).
- UC Berkeley Physics — Sulyemanzade Lab; UW–Madison — Prof. Josiah Sinclair; Harvard University — Dr. Brandon Grinkemeyer.

---

---

# Rb-87 795 nm lattice laser system — branch `gpt+claude+Haotian`

Three baseplates for the 795 nm lattice light, designed in September 2026 by
Haotian Xu with GPT (Codex) and Claude. The current TA revision is **V9.13**
(2026-10-12): an **11.625 × 11 in plate with one fiber output**. The compact
route retains the non-mirror optical order, with four bare conditioning
positions: two cylindrical-lens and two spherical-lens provisions.
After the cell, two steering folds and a folded two-lens telescope lead to an
HWP, a real 12.7 mm PBS bonded to an RSP05, and one KA05T. This revision has
six mirrors and no AOM or shutter. The TA cable leaves the upper long edge;
every physical part and the full 4 in cable allowance beyond that nominal
edge fit inside the 28 × 15 in platform at a verified mounting-grid position.
The measured occupied envelope is 310.985 × 377.825 mm. The full V9.7 sliding
cell enclosure remains, including its end covers that still need beam
apertures before optical operation. The lattice board remains at V9.7 and
the double-pass board at V9.3; earlier TA designs remain in the change log.
Since 2026-10-09 the branch also carries a fourth, independent board, the
**Splitting Board V2** (24 × 14 in): one fiber in, HWP → PBS splits 1 → 2 → 4
with a single-pass AOM after every stage (1 + 2 + 4 AOMs), four fibers out on
one short edge. The current 2026-10-12 design uses five KM05T assemblies on
lip adapters, two output steering mirrors per final lane, and four modelled
12.7 mm PBS cubes bonded to their rotating stages. It is an **AOM RF-off,
zero-order reference layout**: every beam leg follows a board axis, and all
23 mirrors have 45° incidence. The RF-on first-order paths are not validated.
The subsequent Splitting mounting update moves only its four platform-fixing
holes onto a relative 1 in grid; its plate size, optical parts and placements
remain unchanged. With the confirmed 25.4 mm platform-edge hole offset, all
four bolts align after a (+53.975, +22.225) mm board-frame translation. The
user has accepted the resulting maximum 5.451278 mm hardware/RF overhang.

| Board | Script | Size | Production folder |
|---|---|---|---|
| Lattice board | `Rubidium_system/Lattice_Baseplate_V9.py` | 24 × 15 in | `Production/LatticeBoardV9/` |
| TA board (V9.13) | `Rubidium_system/TA_Baseplate_V9.py` | 11.625 × 11 in | `Production/TABoardV9/` |
| Double-pass AOM board | `Rubidium_system/AOM_DoublePass_Baseplate_V9.py` | 17 × 6 in | `Production/AOMDoublePassV9/` |
| Splitting board (1 → 2 → 4 AOMs) | `Rubidium_system/Splitting_Board_V2.py` | 24 × 14 in | `Production/SplittingBoardV2/` |

Each script is self-contained: constants at the top, then every optic placed in
beam order inside `example_baseplate()`. Run one in FreeCAD (Macro > Macros…, or
paste into the Python console) and the board is built. The lattice script also
takes `cat_eye='75-50'` / `'75-75'` to build the two f = 75 test configurations
on the same plate, and `cell_slide=0 .. 10.5` to put the cell enclosure anywhere
along its travel (see the lattice board below). The TA script also accepts
`cell_slide=0 .. 10.5` for the same enclosure.

## What this branch changes

This branch starts from **`yajur-branch`**, not from `main`. The boards are built
on the yajur-branch component library: its `optomech.py` is the file the
original three boards were designed and audited against, and `main`'s version
differs in 7 of the 17 classes they use — `fiberport_mount_KA05T_holes`, which
carries their rear fiber tail-clamp holes, does not exist in `main` at all.
The revised Splitting board instead uses yajur's existing
`fiberport_mount_km05T`, `mirror_mount_km05T` and
`surface_adapter_fiberport_lip`, with explicit board-level tail-clamp taps.

The changes relative to `yajur-branch` are described below:

**Modified — `optomech.py`**: the code above the banner
`Rb-87 795 nm lattice laser system - components added on this branch` is
inherited from yajur-branch, with two narrow changes added on 2026-10-12.
`surface_adapter_fiberport_lip` accepts `hole_config='mount_only'`, which omits
the optional Y-shape pattern while retaining the two adapter mounting taps
and the separately controlled rear-pair flags. Splitting turns all three
rear-pair flags off. The adapter mesh, all existing hole modes and their
defaults are unchanged. `ViewProvider` also binds its owning object before
proxy assignment and again in `attach`, so reopening an FCStd restores the
component tree; this changes no part geometry. The classes and helpers added
below the banner are:

- `lens_holder_l05g_no_pin_slots` — POLARIS-L05G without the two 5 × 2 × 2.2 mm
  alignment-pin slots, so the holder can sit anywhere without extra plate
  features. Same mesh and same central 8-32 bore as `lens_holder_l05g`.
- `isolator_850_long_pocket` — IOT-5-850-VLP with the pocket spanning the whole
  body (dx 80 → 113.5 mm), as on the hana-branch boards.
- `TA_butterfly_on_adapter` — the TA evaluation board screwed to the TA adapter
  instead of straight to the plate. Same mesh and the same linked `TA_adapter`
  as `TA_butterfly`, but it drills nothing itself: the board's four M2.5 screws
  go into the adapter's own tapped holes and the adapter is held by four 8-32
  into the plate, so the plate under the TA has no M2.5 holes (V9.3).
- `BareTappedHole` — an 8-32 tap-drill location with no mount, optic or
  counterbore, used for positions whose holder is not yet chosen and for the
  revised Splitting board's ten explicit fiber tail-clamp taps.
- `rotation_stage_rsp05_bonded_cube` / `RSP05CubeAdhesive` /
  `audit_rsp05_bonded_cube` — the inherited RSP05 mesh and lip adapter with a
  real 12.7 mm PBS cube on its engraved rotating face. Four corner adhesive
  pads per cube model a 0.2 mm bond layer. The audit checks the actual bond
  contacts and the cube's full rotation envelope against supplied physical
  parts. It does not certify adhesive strength or optical-coating compatibility.
- `SlidingCellEnclosure` / `SlidingCellLid` / `SlidingCellCover` /
  `SlidingCellGlass` / `SlidingCellSeat` / `place_sliding_cell` (V9.5, split in
  V9.6, two end screws and closed stem pocket in V9.7) — the Rb cell enclosure
  and its seat: a plain block cut into a lower half and a lid, 88 × 46.9 × 24 mm
  each, parted on the bore axis, with the 30.4 mm bore, a closed 12 × 10 mm
  stem pocket split between them, a through slot in each bore end region,
  eight 16 mm deep cover taps and a 6 × 6 mm cable notch; two 7 mm end covers
  with counterbored 8-32 holes (no beam aperture yet); the GC25075-RB envelope;
  and the plate machining (an 11.3 mm pocket shaped for the assembly plus
  10.5 mm of travel, two 8-32 taps through its floor). `place_sliding_cell(bp, x, y,
  angle, slide)` places the seat and the enclosure `slide` mm along the slot
  direction. All dimensions live in the `SLIDING_CELL` dict and are exported
  with the parts (`Production/CellEnclosure/`). The V9.2–V9.4 pocket-only seat
  (`CellPocketMachining` / `place_cell_pocket`) stays in the library for legacy
  layouts. The V9.13 TA board uses the full, unchanged V9.7 enclosure and
  sliding seat, including the unfinished end covers.
- `IntegralAOMSeat` / `integrate_aom` / `_make_IntegralAOMBaseplate` — the AOM
  seat machined directly into the baseplate (no lower surface adapter), with a
  flat screw-bearing face at z = −1.231 mm.
- `PersistentDrillVolume`, `keep_machining_hidden`, `deepen_isolator_pocket`,
  `add_fiber_tail_alternative`, `descendants` — supporting machining helpers.

The component variants are new classes. The adapter's additional
`mount_only` mode is selected only by the revised Splitting board, so the
other boards retain their existing geometry and default drilling patterns.

**Added — four board scripts** in `Rubidium_system/`, listed in the table above
(`Splitting_Board_V2.py` since 2026-10-09; its KM05T heads use the inherited
classes and its bonded output cubes use the new RSP05 subclass above).

**Added — four `Production/` folders** (`Production/SplittingBoardV2/` since
2026-10-09), each holding the top and 3D renders,
the audit report (`*_validation.json`), a BOM spreadsheet in the same
Adaptors/Elements layout as the other branches, `StepFile/` with the machined
baseplate STEP, and a `*_TAP_or_NOT` sheet (PDF + PNG) that marks which holes
of that plate are tapped. The baseplate STEPs are also collected in
`Production/Baseplate/`, and the same sheets for the two adapters are in
`Production/Adapters/`. **`Production/CellEnclosure/`** (since V9.5) holds the
Rb cell enclosure: lower half, lid, cover and assembly STEPs, the four-sheet
dimensioned drawing (PDF + PNG) and the dimension JSON.

**Added — board export and projection tools** in `tools/`:
`ta_projection_audit.py` checks beam crossings and projected hardware,
including thumbscrews regardless of their height; `export_ta_board.py` exports
the machined STEP, top/3D views, validation report, hole inventory and plate
edges from FreeCAD; `render_ta_documents.py` creates the BOM and tapping sheets
from those exports. The existing full 3D, aperture, service and machining
audits remain local development tooling. The export helper consumes their
report together with the projection result; the new projection check does not
replace them. Run the board with this repository's `optomech.py` loaded as
`PyOpticL.optomech`, as described in the installation instructions above.
The export and document helpers also accept the Splitting board's source and
filename stem. `tools/km05t_audit.py` adds its KM05T installation and tail-access
checks; these are required by the exporter whenever KM05T heads are present.
`tools/refine_mesh_candidates.py` can resolve an otherwise inconclusive mesh
pair only when its actual XY convex hulls are strictly separated beyond the
tessellation uncertainties; the original checks and counts remain in the report.
`tools/bonded_cube_audit.py` checks registered bonded cubes and resolves only
their intended axial glass traversal when the actual placement, aperture and
bond/rotation checks supply the matching evidence. `tools/single_output_audit.py`
checks the TA's one actual post-cell route, folded lens spacing and single
fiber head, with no AOM or shutter. Its saved legacy AOM-order calculation is
inapplicable, not evidence of coupling efficiency. `tools/table_envelope_audit.py`
includes all actual TA geometry, cable and fiber service envelopes, and searches
the confirmed table grid using the finished plate edges.
`tools/zero_order_reference_audit.py`
requires the explicit RF-off model, verifies zero deflection through all seven
AOMs and checks every mirror's 45° incidence and axis-aligned beam legs. It
archives the older RF-on optical calculation as inapplicable to this reference
model; mechanical, aperture and projection checks remain active. It does not
claim RF-on first-order feasibility. `tools/splitting_table_envelope_audit.py`
checks the physical assembly and its service reservations against a 28 × 15 in
platform by continuous translation. `tools/table_mount_audit.py` separately
checks the four fixing holes against the machined plate and their relative
1 in grid. The saved `table_grid_installation` then records the confirmed
25.4 mm platform-edge hole offset, aligned installation and approved overhang.

**Unchanged:** the inherited `stl/` meshes, including the existing KM05T and
fiberport lip-adapter meshes; every other script in `Rubidium_system/`; and
every other `Production/` folder.

## Boards

**Lattice board (24 × 15 in, V9.7).** TA → two steering folds → HWP → isolator →
QWP → six bare 8-32 conditioning stations (45/45 mm down the lane, then 60 mm
and 100 mm along the beam) → Rb cell in its sliding enclosure → SR475 shutter →
power HWP/PBS. The
transmitted and reflected beams feed two double-pass AOM arms: G&H AOMO
3100-125 on an integral seat at the Bragg angle, then an **f = 300 mm cat-eye
(LA1618-B) folded into a U by two 45° M05 fold mirrors** — the +1 order is the
design axis downstream of the AOM (2θ_B = 1.08° at 100 MHz, so the folds see
the diffracted beam at exactly 45° and the return legs run along the top and
bottom plate edges 1.08° off the board axes), an IDA12 on the vertical leg
blocks the 0 order (190–207 mm from the AOM, where the two orders are 3.6–3.9 mm
apart), and the QWP sits on the return leg before the retro mirror. Each return
is separated by its PBS and passes an LA1289-B/LA1540-B telescope, HWP, rotating
PBS and iris into a KA05T; the DP2 output row lies above its AOM row, so no
beams cross. Every mirror on the board is a Newport M05 with HKTS adjusters.
`example_baseplate(mode='dual')` adds a second KA05T input for an external TA
(both telescope lenses on the input lane), its injection fold and a blocking
iris.

The V9.3 **f = 75 mm cat-eye (LA1612-B) is kept as an option**: straight after
each AOM, on the 0-order (input) axis as in V9.3, the plate carries the bare
holes for a POLARIS-L05G lens holder (DP1 73 mm / DP2 68 mm from the AOM), an
RSP05 QWP mount (91 mm), an IDA12 slide mount (113 / 107 mm, post toward −y)
and two M05 retro-mirror positions, lens → mirror 50 mm and 75 mm. Nothing is
installed there. In that configuration the +1 order leaves the input axis by
2θ_B and, the AOM being in the lens's front focal plane, runs parallel to it
1.4 mm above after the lens — well inside the 1/2 in optics; the iris is
centred on it with its slide. With the 50 mm mirror every f = 300 part can
stay on the plate; the 75 mm mirror body stands where fold F1 (DP1) / F3 (DP2)
is, so that fold comes off for a 75/75 test. Those two mirror positions have
no thumbscrew pocket: the lower M05 adjuster is driven with a plain 5/64 hex
key there. Both test configurations were built on the same plate and audited
(`example_baseplate(mode='dual', cat_eye='75-50')` / `'75-75'`; reports in
`Production/LatticeBoardV9/`).

**Rb cell enclosure (V9.7).** The GC25075-RB cell (Ø25.4 × 71.8 mm per the
Thorlabs drawing 24088-E0W, length tolerance 0.8, fill stem at mid-length and
< 10 mm high) sits in a plain machined aluminium block, 88 × 46.9 × 48 mm, that
is cut in two along the bore axis — a lower half and a lid, 24 mm each — so
the cell is simply laid in. Nothing sticks out of the block. The parting plane
is the plate's 12.7 mm optical axis, so the beam runs along the split. The
bore is Ø30.4 mm (cell diameter + 5 mm), through the whole length, bored with
the two halves clamped together. The fill stem lies in the parting plane and
points toward −x on the board (away from the side the beam moves to), in a
12 × 10 mm pocket split 5/5 between the halves; the pocket is **closed**: it
runs from the bore to 24.2 mm from the axis (1.5 mm beyond the longest stem
Thorlabs allows) and leaves 2.5 mm of wall to the outer face, so nothing
connects the cell space to the outside there. A 6 × 6 mm cable notch in the
lower half's parting face leaves through the same wall. Two separate 7 mm end
covers are each held by four 8-32 × 5/8 in socket head screws in 3.5 mm
counterbores (the heads stand 0.9 mm proud) — eight 16 mm deep taps, two in
each half, so the covers also tie the halves together. The covers carry **no
beam aperture yet** — it is to be opened later on the bore axis.

The placement coordinates and board directions in this enclosure description
refer to the lattice board. The V9.13 TA board reuses these parts at its own
placement, recorded in its script and validation report.

The enclosure slides across the beam and is held by a screw at each end. The
block is 8.1 mm longer than the cell at both ends, and in each bore end region
— beyond the cell, 1 mm from its end even at the +0.8 length tolerance — a
through slot (4.37 wide, 14.9 long, running through both halves) sits on the
−x half of the bore while the beam uses the centre and the +x half; two 8-32 ×
2 in screws go from the lid top through the slots into two 8-32 taps in the
plate at (185, 123.6) and (185, 203.4). They clamp the halves together and fix
the position, their heads riding in 8.5 × 5 mm counter-slots below the lid
top, so the position is set from above with everything assembled; the screws
never meet the cell or the beam (≥ 8.9 mm from the beam at any position). With
the screws at the slots' outer ends the beam passes through the cell centre;
pushed to the other end (the block moving 10.5 mm toward −x) the beam runs
2.2 mm inside the cell wall on the +x side — further than that the beam would
be in the glass. The plate pocket is 11.3 mm deep (the bore axis is 24 mm
above the block's bottom, so this puts it at the 12.7 mm optical height) and
shaped for both halves, the covers and the travel: 104.4 × 64.7 mm (board
x 157.8–222.5, y 111.3–215.7; its +x edge runs into the injection fold's
thumbscrew pocket, as the old pocket did, and its −x edge keeps 3.8 mm of
plate to the isolator and output-QWP pockets); the pocket wall on the −x side
is the travel stop. To fit the longer block between the station-6 lens slab
(y 111) and the shutter housing pocket (y 217.7) the seat moved 1.5 mm along
the beam to y = 163.5. Both ends of the travel were built and audited
(`example_baseplate(mode='dual', cell_slide=10.5)` is the second report in
`Production/LatticeBoardV9/`): the two halves are never exempted — the beam
has to pass the bore geometrically — while the aperture-less covers and the
cell envelope are exempted explicitly for a beam running along the bore. The
enclosure parts are in `Production/CellEnclosure/`
(`Rb_Cell_Enclosure_LowerHalf_V9_7.step`, `..._Lid_V9_7.step`,
`..._Cover_V9_7.step`, `..._Assembly_V9_7.step`, the drawing
`Rb_Cell_Enclosure_V9_7_drawing.pdf` and `..._dimensions.json`); the cell is
centred in the bore, and kept from sliding along it, by its heater/insulation,
which is not part of this design.

**Lattice table bolts (V9.4.2).** The lab table has a 1 in hole grid whose first row
is 1.5 in from the table edge. The plate is meant to sit with its fiber-side
(right) edge 0.25 in inside the table edge, so a bolt (1.25 + n) in from that
plate edge lands on grid row n. Both bolt pairs are 10 in apart (the maximum
allowed) and centred on the short edge (2.375 in from the top and bottom
edges). The right-hand part of the plate between those two rows is occupied
(0-order irises, the optional f = 75 set, the output heads), so the fiber-side
pair sits 6.25 in (n = 5) from the right plate edge, between the AOM housings
and the optional f = 75 lens holders; the TA-side pair is 16 in further left
(1.5 in from the left edge). All four fall on grid points together. STEP-file
coordinates (mm): (447.675, 50.8), (447.675, 304.8), (41.275, 50.8),
(41.275, 304.8). The TA block sits 5 mm higher than in V9.4.1 so that its
adapter pocket clears the lower-left bolt by 5.3 mm.

The 10 in bolt-pair limit above applies to the lattice board. The compact TA
board has its own table-grid mounting pattern in `TA_Baseplate_V9.py` and the
current tapping sheet.

**TA board (11.625 × 11 in, V9.13, 2026-10-12).** The nominal outline is
295.275 × 279.4 mm; the machined plate is 288.925 × 273.05 × 25.4 mm after
the standard 3.175 mm edge inset. Its nominal area is 16.96% smaller than
V9.12. The TA emits right from (132, 226) mm through the HWP at (230, 226),
then folds at (266, 226) and (266, 182) toward the isolator at (205, 182).
The next fold at (27.8, 182) sends the beam down through the QWP at
(27.8, 157) and the first cylindrical-lens provision at (27.8, 138).
It folds right at (27.8, 115), through the second cylindrical provision at
(50, 115), spherical provisions at (75, 115) and (115, 115), and the cell
at (180, 115). The non-mirror optical sequence is unchanged. The two
cylindrical provisions span **45.2 mm along the folded beam** (23 + 22.2 mm);
the spherical provisions are 40 mm apart. These are four reserved mounting
holes for optics that have not been selected, not a focal-length prescription.
The full lattice V9.7 enclosure, seat, lid and covers are retained. The TA
adapter retains its previous geometry; native comparison verifies its rigid
27 mm translation in +X against V9.12.

There is one post-cell output, in this order:
cell → mirror at (265, 115) → LA1289-B at (265, 97) → mirror at (265, 68)
→ LA1540-B at (248.680652, 68) → HWP at (223.680652, 68)
→ bonded PBS cube at (205.977652, 68) → fiber face at (141.680652, 68) mm.
Both output mirrors have 45° incidence. The second mirror lies between the
two lenses, so their retained **45.319348 mm spacing is measured along the
folded beam**: 29 + 16.319348 mm. Their direct centre-to-centre chord is not
the telescope spacing. The first lens mount has 90° yaw and the second 0°.
The RSP05 reference is at (191.680652, 68) mm,
32 mm after the HWP; its bonded 12.7 mm PBS lies 14.297 mm upstream of that
reference. Only its axial transmitted route is modelled. There are six mirrors
in total, one KA05T and no AOM, shutter, branch-splitting PBS or output iris.

The KA05T reference is (122.882652, 68) mm, with its tail-clamp pair centred
at (56.182652, 68) mm: the 66.7 mm rear offset is retained. The audit reserves
the full 60 × 20 mm clamp footprint and the 20 mm-wide fiber corridor to the
left edge. RF clearance is explicitly not applicable because the actual
object and service inventories contain no AOM.

The TA cable exits the upper **long edge** in +Y. A full 101.6 mm (4 in)
reservation starts at the nominal Y = 279.4 mm edge, in addition to the
connector service region. Including actual hardware, knobs, fiber services
and cable, the occupied envelope is 310.984956 × 377.825 mm. The selected
translation onto the **28 × 15 in platform** is **(+215.9, −3.175) mm**.
The confirmed table hole grid has 25.4 mm pitch and its outermost holes are
25.4 mm from each edge. All four fixing holes align:

| Fixing-hole centre in board frame (mm) | Centre on platform (mm) | Grid indices from platform edges |
|---|---|---|
| (266.7, 28.575) | (482.6, 25.4) | (19, 1) |
| (38.1, 28.575) | (254, 25.4) | (10, 1) |
| (38.1, 257.175) | (254, 254) | (10, 10) |
| (190.5, 257.175) | (406.4, 254) | (16, 10) |

The lower-right anchor is 25.4 mm from the finished right and lower plate
edges. At this installation position the actual plate's lower edge lands at
platform Y = 0; the empty 3.175 mm nominal border is not physical stock.
The plate, all hardware and all reserved services are fully inside the
platform, with 3.175 mm remaining above the cable envelope. Six knobs extend
beyond the plate sides, but remain within the platform. The reused V9.7 end
covers are still opaque: their beam apertures must be designed and machined
before optical operation.

Current V9.13 machining model:
[TA_Board_V9_baseplate_11p625x11in.step](Production/TABoardV9/StepFile/TA_Board_V9_baseplate_11p625x11in.step).
The earlier single-output
[14 × 11 in V9.12 STEP](Production/TABoardV9/StepFile/TA_Board_V9_baseplate_14x11in.step),
and the dual-output
[14 × 16.5 in V9.11 STEP](Production/TABoardV9/StepFile/TA_Board_V9_baseplate_14x16p5in.step),
[14 × 21.5 in V9.9 STEP](Production/TABoardV9/StepFile/TA_Board_V9_baseplate_14x21p5in.step),
[14 × 17.5 in V9.8 STEP](Production/TABoardV9/StepFile/TA_Board_V9_baseplate_14x17p5in.step)
and
[25 × 14 in STEP](Production/TABoardV9/StepFile/TA_Board_V9_baseplate_25x14in.step)
are retained as legacy models. The top/3D renders, BOM, tapping sheet,
hole inventory and validation report in `Production/TABoardV9/` describe V9.13.
The [installation-clearance plan](Production/TABoardV9/TA_Board_V9_table_clearance.png)
shows the beam routes, cable reservations and measured platform envelope.

**Double-pass AOM board (17 × 6 in).** Standalone double pass: KA05T, HWP, PBS,
AOM on an integral seat, f = 75 mm cat-eye (LA1612-B, 795 nm EFL 75.95 mm), QWP,
iris, retro mirror; the return line runs 74 mm above the input line through a
steering mirror, HWP, rotating PBS and iris into a KA05T.

**Splitting board (24 × 14 in, V2, revised 2026-10-12).** One KM05T input on the left
short edge, seven G&H AOMO 3100-125 on integral seats, three HWP → PBS splits
and four KM05T outputs, all four pointing +X through the right short edge
(output 1 at the top). The model has **RF off and follows the straight-through
zero order** at every AOM:

    input KM05T -> A:  M1, AOM, iris, HWP, PBS
        A transmitted -> B1: M1, M2, AOM, iris, HWP, PBS
            B1 transmitted -> C1: FR, M1, M2, AOM, HWP, bonded PBS, output fold, iris, output fold -> output 4
            B1 reflected   -> C2:     M1, M2, AOM, output fold, output fold, HWP, bonded PBS, iris -> output 3
        A reflected   -> B2: M1, M2, AOM, iris, HWP, PBS
            B2 transmitted -> C3:     M1, M2, AOM, output fold, output fold, HWP, bonded PBS, iris -> output 2
            B2 reflected   -> C4: FR, M1, M2, AOM, output fold, output fold, HWP, bonded PBS, iris -> output 1

All 23 steering mirrors use Newport M05 mounts at exactly 45° incidence,
giving 90° folds and horizontal or vertical beam legs. This includes the
mirrors immediately before the AOMs; there is no Bragg-compensation angle in
this RF-off layout. A has one input steering mirror (the input head itself
is adjustable); B1, B2, C2 and C3 have two, while C1 and C4 also have an FR
feed fold. Each C lane adds two output steering mirrors. C1 keeps its HWP and
bonded PBS on the AOM row, then folds through an iris on the vertical leg
before the second fold sends the beam to its fiber. C2–C4 put both added folds
before the HWP and bonded PBS. No beam may pass beneath a knob, even when the
parts are separated in height; the final geometry must satisfy the full
mechanical and XY-projection checks.

The layout includes edge overhangs from eight knobs and the C1 FR/M1 mount
bodies. Their conservative body bounding boxes extend about 6.44 mm beyond
the plate, while their actual bottom support surfaces protrude about 1.60 mm.
About 98.4% of each bottom footprint remains supported and the mounting-tap
centres are about 8.93 mm inside the edge. These are geometric support
measurements, not a certification of mount strength or stiffness; the final
report records the accepted overhangs separately from collisions.

The A and B lanes keep AOM → iris 81 mm, → HWP 98 mm and → PBS 121 mm.
The output HWP and second RSP05 **stage references** are 32 mm apart. Each
second stage is turned 180° so that the cube bonds to the supported engraved
rotating face on the upstream side. With the 0.2 mm adhesive layer, the cube
centre is 14.297 mm upstream of that stage reference; it is an actual optical
solid rather than an empty mount. The four 12.7 mm cubes each have four
modelled corner adhesive pads. Bond strength, cure behaviour and coating
compatibility still require assembly engineering. The model does not validate
RF-on first-order propagation, diffraction efficiency, order rejection or
fiber-coupling performance. In particular, the iris is centred on the zero
order here and does not reject it.

AOMs A, B1, B2, C2 and C4 are in orientation D (KM100PM downstream); C1 and
C3 are in U. Each AOM retains its 40 × 20 mm RF-elbow reservation, exceeding
the 1.5 in (38.1 mm) axial requirement. The four output tail clamps end at
the right plate edge. The four table bolts now use the staggered relative
1 in grid below, replacing the original centred pairs spaced 7 in apart.
The original V2 layout was found with a 2-D footprint model
of its then-current parts (their FreeCAD bounding boxes) and a sequential-LP
compactor, then built and audited in FreeCAD. (V2 is the second layout of this board; the first one
had crossing beams and outputs on three edges and was not published.)

**Splitting table bolts (2026-10-12 mounting update).** Only the four
1/4-20 platform-fixing clearance holes and their counterbores move. The
24 × 14 in plate, all optical parts and placements, component taps and
fiber-tail clamp holes remain unchanged. The lower-right fixing-hole centre is
25.4 mm from both the **actual machined right and lower edges**. Those edges
are inset 3.175 mm from the nominal outline; the nominal X/Y = 0 lines are not
the edge datum. Coordinates below use the script's board frame, in millimetres.

| Fixing hole | Centre (mm) | Offset from lower-right anchor (in) |
|---|---|---|
| Lower-right anchor | (581.025, 28.575) | (0, 0) |
| Lower-left | (22.225, 79.375) | (−22, 2) |
| Upper-left | (22.225, 333.375) | (−22, 12) |
| Upper-right | (581.025, 282.575) | (0, 10) |

This pattern is defined by `TABLE_MOUNT_ANCHOR_MM` and
`TABLE_MOUNT_OFFSETS_IN` in `Splitting_Board_V2.py`. Every relative X and Y
separation is an integer multiple of 25.4 mm. The user confirmed that the
28 × 15 in platform's outermost holes are 25.4 mm from its edges. Translating
the board frame by **(+53.975, +22.225) mm** places the four holes at table
coordinates (635, 50.8), (76.2, 101.6), (76.2, 355.6), and (635, 304.8) mm:
all four align with the 1 in grid. The actual machined plate lies fully within
the platform. Its hardware and RF reservations extend beyond the upper edge;
the maximum is **5.4512777506515 mm**, at `Lower_Thumbscrew023`, and the user
explicitly accepted retaining this layout with that overhang. The B2 and C4
RF reservations extend 4.566 and 5.3155 mm beyond the upper edge, respectively.
The machining inventory remains 85 tapped plus four clearance holes.

The lower-right counterbore clears the actual hardware and the fiber-tail
clamp taps, but the C1 / Output 4 fiber-tail corridor passes above it.
Fasten the plate to the platform before installing that tail clamp and
routing its fiber; remove the fiber and clamp before undoing the plate bolt.

All five heads use the existing `fiberport_mount_km05T` assembly and the
unchanged [Surface_Adapter_fiberport_lip.step](Production/Adapters/Stepfile/Surface_Adapter_fiberport_lip.step).
The lens tube, fiber adapter, lens adapter and lens-envelope positions match
the former KA05T assembly. Each lip adapter drills only its two mounting taps;
two separate `BareTappedHole` features place each tail-clamp pair, spaced
18.328 mm apart. The input and C1–C3 heads keep a 76 mm rear offset. The C4
head moves 32 mm right toward its existing pair, reducing its offset to
44 mm while keeping the pair centre at board coordinates (596.415072, 325) mm.
C3's output row moves to Y = 207 mm, including its head and tail-clamp pair;
its rear offset remains 76 mm. No additional rear extension is introduced.
The optional Y-shape and
52.7/72.7/82.7 mm rear-pair patterns are disabled. The board still reserves a
20 × 40 mm tail-clamp area and a 20 mm straight fiber corridor. Clamps are not
modelled parts. The BOM counts five KM05T mounts, five separate lip adapters,
their optical subparts, seven actual PBS cubes (three splitting cubes and four
bonded output cubes), and eleven RSP05 stages (seven for waveplates and four
for the bonded cubes). The four modelled output cubes replace the former
manual allowance for four unmodelled cubes; they are not counted twice.
C220TMD-A remains a CAD envelope; the optical design assumes an
f ≈ 4.5 mm fiber collimation lens.

The [layout illustration](Production/SplittingBoardV2/Splitting_Board_V2_layout_model.png),
top/3D renders, STEP, BOM, tapping sheet and validation report all describe
the current RF-off reference layout. The illustration shows conservative XY
envelopes and service reservations; overlapping rectangles are not evidence
of a physical collision. The final STEP is a valid single solid measuring
603.25 × 349.25 × 25.4 mm.

## Positions with nothing installed yet

The lattice board's six conditioning stations, the TA board's four stations
(two cylindrical and two spherical), and the lattice board's three
external-TA telescope positions are drilled as bare 8-32 holes because
the optic has not been chosen. Each hole is placed where a POLARIS-L05G holder's
own tap would land, so fitting the holder later puts the lens on the design
plane. They are sized for an L05G with a 10 mm cylindrical lens bonded to its
front face, and the audit checks that holder footprint against every installed
part. For TA, `tools/conditioning_station_audit.py` independently verifies
the four actual drilled holes and both the 16 mm circular reservations and
the complete planned L05G/lens footprints, including mutual station clearance.
It preserves the legacy audit evidence and replaces only the obsolete
three-cylindrical/six-total-station count assumptions. The results are in the current
[TA validation report](Production/TABoardV9/TA_Board_V9_validation.json).

The lattice board additionally carries the twelve bare holes of the optional
f = 75 cat-eye described above (six per AOM arm). The lens and mirror taps of
that set lie on the input beam axis by design — empty holes 12.7 mm below the
beam, usable only with that beam absent or the f = 300 chain's first fold
removed.

Both the lattice and V9.13 TA boards carry the V9.7 enclosure described above.
Its end covers have no beam apertures yet and currently block the optical
axis. Heater/insulation and the glass retention they provide are not modelled.

## Machining

`Production/Baseplate/` holds the machined baseplate STEPs — one solid
each, with all pockets, 8-32 tap-drill bores, integral AOM seats where applicable, the cell
pocket and the 1/4-20 table-bolt counterbores included (the lattice plate is
`Lattice_V9_7_baseplate_24x15in.step`; the superseded V9.4–V9.5 and
24 × 14 in V9.2/V9.3 plates are removed; the splitting plate is
`Splitting_Board_V2_baseplate_24x14in.step`). The current TA plate is
`TA_Board_V9_baseplate_11p625x11in.step`; the 14 × 11 in V9.12,
14 × 16.5 in V9.11, 14 × 21.5 in V9.9,
14 × 17.5 in V9.8 and 25 × 14 in predecessors are retained as legacy STEPs. The solid is inset
3.175 mm from the nominal outline on every side, as in every PyOpticL plate.
Threads are specified, not modelled — a STEP file shows every bore's diameter,
position and depth but cannot say whether it is threaded, so each plate and
each adapter has a **`*_TAP_or_NOT` sheet** next to its STEP that marks exactly
that and nothing else (red ring = tap, blue crossed circle = do not tap; drill
sizes, tolerances, material and finish are left to the shop):

| Part | Sheet | Tapped | Not tapped |
|---|---|---|---|
| Lattice baseplate (V9.7) | `Production/LatticeBoardV9/Lattice_V9_7_baseplate_TAP_or_NOT.pdf` | 100 × #8-32 | 4 × 1/4-20 table-bolt clearance |
| TA baseplate (V9.13) | `Production/TABoardV9/TA_Board_V9_baseplate_TAP_or_NOT.pdf` | 31 × #8-32 | 4 × 1/4-20 table-bolt clearance |
| Double-pass AOM baseplate | `Production/AOMDoublePassV9/AOM_DoublePass_V9_baseplate_TAP_or_NOT.pdf` | 22 × #8-32 | 3 × 1/4-20 clearance |
| Splitting baseplate (V2, RF-off reference) | `Production/SplittingBoardV2/Splitting_Board_V2_baseplate_TAP_or_NOT.pdf` | 85 × #8-32 | 4 × 1/4-20 table-bolt clearance |
| TA adapter (`stl/TA_adapter.stl`) | `Production/Adapters/TA_adapter_TAP_or_NOT.pdf` | 4 × M2.5 × 0.45 (board screws) | 4 × 8-32 clearance (to the plate taps) |
| AOM adapter (`stl/aom_adapter.stl`) | `Production/Adapters/AOM_adapter_TAP_or_NOT.pdf` | 2 × M4 × 0.7 | 4 × clearance, in a row |

The standalone TA adapter matching the **current TA V9.13 and lattice V9.7
board models** is
[`TA_adapter_board_model.step`](Production/Adapters/Stepfile/TA_adapter_board_model.step).
Use it with `Production/Adapters/TA_adapter_TAP_or_NOT.pdf`. Its analytic
100 × 108 × 11.3 mm slab and eight through holes were recovered from the
pre-`c7e6eb8` STEP geometry and checked against the actual placed adapter
meshes. The four clearance holes are analytic Ø4.50 mm circles; the sheet's
Ø4.48 label is the tessellated STL measurement. The separate existing
`Production/Adapters/Stepfile/TA_adapter.step` has different hole groups and
counterbores and does **not** match these board models or this tapping sheet.
Neither board nor its component meshes were changed for this export.
The actual TA-body mesh has short mounting slots around the four M2.5 axes;
the model leaves at least 0.066 mm radial clearance for a Ø2.5 mm screw.
The adapter's four outer holes also align with the holes in both machined
baseplate solids. Checks and source hashes are recorded in
[`TA_adapter_board_model_validation.json`](Production/Adapters/TA_adapter_board_model_validation.json).

The final machined-solid inventories contain 35 hole axes on TA V9.13 and
89 on the RF-off Splitting board. Splitting has eight more tapped holes than
the preceding KM05T export, one for each added output steering mirror.

Every hole in the part is marked on its sheet; the rounded corners inside the
milled pockets are R3.175 end-mill fillets, not holes. `Production/Adapters/`
also holds the historical `V9_7_tapping_sheets_all.pdf`, the five sheets in one
file (the V9.7 lattice sheet and the four V9.3 sheets). Its TA page describes
the legacy plate; use the current V9.13 TA sheet linked above. The hole
coordinates of every sheet are listed on it (plates: STEP-file coordinates;
adapters: from the part's lower-left corner).

## Audits

The boards were checked with a set of read-only audits (mesh contacts, beam and
hardware crossings, fiber tail clamps, service clearances for the TA cable and
the AOM RF elbows, hole access, AOM seat machining probes). The saved reports
are the `*_validation.json` files in `Production/`.

The compact TA report combines these checks with
`tools/ta_projection_audit.py`. It checks crossings between beam segments and
the XY projections of actual placed hardware, including mirror knobs;
vertical separation never excuses a beam beneath a knob. Any accepted
overhang, optical exception or unresolved candidate is listed in that report,
along with the current station, clamp and service clearances.
The exported V9.13 assembly, with the cell at slide = 0 mm, has zero detected
beam crossings, knob projection hits, foreign-hardware projection conflicts,
part contacts, unresolved candidates, clamp/service conflicts or hole-access
issues. Its projection check covers 18 beam segments, 55 physical objects and
923 object/segment pairs. The minimum beam-edge/knob projection margin is
17.839503 mm. The single-output audit verifies the actual route, two 45° output
folds and 45.319348 mm lens-to-lens distance along the folded path. The real
bonded cube passes its face-contact, adhesive and rotation-envelope checks.
The old RF/order-separation calculation is retained as inapplicable because
there is no AOM; no Gaussian mode-matching or coupling-efficiency claim follows.

The actual-vertex table audit records six protruding knobs, at most
11.767478 mm beyond the machined plate edge, and no body overhang. Every
protrusion, the full 101.6 mm cable extension, fiber clamp and service region
is included in the 310.984956 × 377.825 mm occupied envelope. A search finds
16 placements on the confirmed 1 in platform grid. The selected
(+215.9, −3.175) mm translation aligns all four actual drilled fixing holes
and contains the complete assembly and services within the 711.2 × 381 mm
platform. The actual finished plate determines the lower support edge; its
empty nominal border is excluded from physical containment.
The negative regression probe in `tools/test_ta_projection.py` is correctly
rejected beneath an elevated M05 knob, with the model unchanged. The saved
FCStd reopens with all 72 objects and names preserved, no invalid/error object
states, and unchanged single-solid plate volume. The STEP round trip also
preserves one valid solid and its volume. A separately rebuilt slide = 10.5 mm
assembly also passes the full mechanical, hole, service and projection checks;
its complete report is
[TA_Board_V9_cell_endpoint_validation.json](Production/TABoardV9/TA_Board_V9_cell_endpoint_validation.json).
The moving cell assembly's swept bounding box stays 1.8 mm clear of the fixed
isolator adapter throughout the 0–10.5 mm linear travel. The production model
is saved at slide = 0 mm.
`mechanical_projection_passed` describes mechanical routing only. The reused
V9.7 end covers remain solid and opaque, so `optical_path_readiness` is
`blocked_by_unmachined_cell_covers`; the required follow-up is to machine their
beam apertures and rerun the optical-path audit. A mechanical pass does not
mean the current assembly is ready to transmit light through those covers.

On the V9.7 lattice board the two TA steering mirrors plus the three
fold mirrors at the plate corners (F1, F2, F4) and the DP1 0-order iris ring
have ten recorded edge-overhang entries, every screw of theirs landing at
least 6.1 mm inside the edge. The upper fiber-side table bolt lies under the
DP1 beam (AOM → f = 75 lens position) 12.7 mm above the recessed bolt head:
install the bolts before aligning.

The 2026-10-12 Splitting revision uses `tools/km05t_audit.py` in addition to
the full engineering and XY-projection checks. During one synchronous call,
it adapts only the older fiber audit's selection of registered KM05T roots,
and extends the service audit's owner registry for those heads, then restores
both functions/settings. The checked meshes, placements,
tail-clamp regions and cable corridors remain the real KM05T geometry.
An independent installation check requires five heads, five lip adapters,
ten explicit tail taps and ten adapter mounting taps. It checks each drilling
feature against the final plate's cylindrical faces and empty cut volume;
metadata alone cannot establish that a hole exists. Self-cutter notifications
are archived only when that independent hole check supplies matching evidence.
Its results appear as `fiber_clearance`, `fiber_installation`,
`service_clearance`, `hole_clearance` and the combined `km05t_audit` gate in
[the Splitting validation report](Production/SplittingBoardV2/Splitting_Board_V2_validation.json).
The current RF-off design also requires the explicit zero-order/45° checks,
the four actual bonded-cube contact and rotation-envelope audits, and the
platform-envelope check described above. These checks pass for all seven
AOMs, all 23 mirrors and all four bonded cubes. The full report has zero
detected mechanical, aperture, fiber-installation, service, hole-access or
unresolved-candidate issues. Projection checks cover 55 beam segments,
198 physical objects and 12,187 object/segment pairs, with zero ray crossings,
knob hits or foreign-hardware conflicts. The minimum beam-edge/knob projection
margin is 0.520322 mm, between the C4 route and C3 M1's lower knob. A deliberate
beam beneath an elevated KM100PM knob is correctly rejected without changing
the model. RF-on first-order readiness remains unevaluated; a mechanical and
zero-order reference pass does not establish RF-on optical performance.

Ten conservative edge-overhang entries are retained: eight knobs and the
two C1 mirror bodies described above. The occupied assembly and service
envelope is 609.6 × 379.354756 mm (24 × 14.935227 in). It fits the 28 × 15 in
platform under continuous translation, leaving 101.6 mm in length and only
1.645244 mm in total width. The selected grid-aligned installation instead
uses the confirmed (+53.975, +22.225) mm translation: all four fixing holes
align and the machined plate stays inside, while the uppermost actual knob
extends 5.451278 mm beyond the platform. The user accepts this hardware/RF
overhang. It is recorded separately in `table_grid_installation`; the earlier
free-translation envelope pass is not a claim that this selected installation
contains every protrusion. Outside-plate fiber routing and overhang strength
are not certified by the envelope check.

The saved FCStd reopens with 244 objects, unchanged placements and object
names, no object error states, and a valid single-solid plate with unchanged
volume. Its external `PyOpticL.layout.ViewProvider` raises an `Object`
attribute error when restoring the plate's tree view. This is a remaining
runtime tree-view limitation; the stored plate geometry and placements pass
their independent checks. The STEP round trip also preserves a valid single
solid and its volume.

The preceding KM05T-only revision passed all four fiber-related checks for
five heads, five lip adapters, ten tail holes and ten adapter mounting holes.
Its projection report had zero ray crossings, knob hits or foreign-hardware
conflicts. Three formerly unresolved mesh pairs were proven separated by
actual XY convex-hull gaps of 5.498833, 8.681311 and 7.079230 mm; the original
records remain archived under `mesh_candidate_refinement`. Its engineering
issue counts were zero, with eleven resolved bounding-box candidates and
twelve recorded overhang entries. These are historical results and do not
establish clearance for the new mirrors and bonded cubes.

For historical reference, the 2026-10-09 KA05T report recorded no contact,
intersection, beam-crossing or clearance issue. Its accepted items were
twelve overhang entries — the four mirrors on the long edges (C1 FR and
C1 M1 at the bottom, C4 FR and C4 M1 at the top) stand up to 8.4 mm (M05 body)
and 21 mm (thumbscrew) past the outline, their thumbscrew-relief pockets open
to the plate edge, and every screw lands at least 6.9 mm inside it — and
three mirror-mount pairs whose triangle-level mesh test ran out of time (the
M05 mesh has 319 k triangles); the XY convex hulls of those meshes are 5.5,
7.1 and 8.7 mm apart, so they cannot touch. The older full audit suite remains
local development tooling. The TA projection, export and document-generation
helpers and the Splitting KM05T audit are included in `tools/`.

## Change log

**V9.13 (2026-10-12, compact TA with four conditioning provisions)** — reduces
the single-output plate from 14 × 11 to 11.625 × 11 in. The non-mirror optical
order is preserved; the TA HWP moves onto its first straight leg and the QWP
onto the left vertical leg. Two cylindrical provisions straddle a fold with
45.2 mm of beam travel between them; two spherical provisions are 40 mm apart.
No conditioning lenses or focal lengths have been selected. The output
telescope retains 45.319348 mm of folded travel (29 + 16.319348 mm), and the
32 mm HWP/stage, 50 mm stage/fiber-face and 66.7 mm tail-clamp spacings remain.
The 72-object assembly has 31 tapped plus four platform-clearance holes. Its
four actual fixing holes align at (+215.9, −3.175) mm on the confirmed table
grid, with all hardware and the full 4 in cable reservation contained inside
the 28 × 15 in platform. Both cell-travel endpoints pass mechanical checks;
the full linear sweep clears the isolator adapter by 1.8 mm. The unchanged
cell covers still need beam apertures. V9.12 and earlier STEPs remain historical.

**V9.12 (2026-10-12, TA single output)** — replaces the two post-cell branches
with one route and reduces the plate from 14 × 16.5 to 14 × 11 in. All
pre-cell parts, including the complete V9.7 cell enclosure, retain their
relative geometry and move 138 mm in −Y, verified by native object/mesh
comparison. The output order is cell → mirror → LA1289-B → mirror → LA1540-B
→ HWP → real 12.7 mm PBS bonded to RSP05 → KA05T. The mirror between the lenses
preserves 45.319348 mm of along-beam spacing. The output has a 66.7 mm rear
clamp offset; there are six mirrors in total and no AOM, shutter or output iris.
Four fixing holes align on the confirmed platform grid at
(+180.975, −3.175) mm translation. All actual hardware, fiber services and the
full 4 in TA cable allowance fit inside the 28 × 15 in platform. Four knobs
extend beyond the plate, with no platform overhang. The final machining
inventory is 33 tapped plus four clearance holes. The 74-object native model,
STEP, views, BOM, tapping sheets and audits describe this revision; V9.11's
14 × 16.5 in STEP and prior versions remain historical. The inherited cell
end covers still require beam apertures before optical operation.

**Splitting V2 (2026-10-12, platform-fixing holes only)** — relocates the four
fixing holes onto the relative 1 in pattern listed above. The lower-right
anchor is exactly 25.4 mm from the finished right and lower plate edges,
including the standard 3.175 mm outline inset. Plate dimensions, all optical
components and placements, and every component and tail-clamp tap stay as in
the preceding revision. The hole count remains 85 tapped + 4 clearance. With
the confirmed 25.4 mm table-edge hole offset, the (+53.975, +22.225) mm
translation aligns all four bolts on the 28 × 15 in platform. The plate is
fully inside; the user accepts the maximum 5.451278 mm top hardware/RF
overhang. Splitting's lower-right plate bolt must be installed before
the C1 / Output 4 tail clamp and fiber, with the sequence reversed for removal.

The entries below describe earlier revisions; their statements about retained
table bolts or unverified relative spacing describe those historical states.

**Splitting board V2 (2026-10-12, RF-off reference and output steering)** —
adds two steering mirrors to each of the four output lanes, bringing the total
to 23. Every mirror now has exactly 45° incidence, and all beam legs follow
the board axes with each AOM modelled off in straight-through order zero.
Four actual 12.7 mm PBS cubes replace the empty output RSP05 positions; each
is bonded to the engraved rotor using four modelled 0.2 mm adhesive pads.
The HWP and second-stage references are 32 mm apart. C1's added folds straddle
its iris after the HWP/PBS; C2–C4 put both folds before their HWP/PBS.
The 24 × 14 in plate, five KM05T heads and lip adapters are retained. Four
heads keep their 76 mm tail-clamp offset; the C4 head moves 32 mm right toward
its unchanged pair, giving a 44 mm offset. C3's output row and its pair move
to Y = 207 mm without increasing that head's rear offset. New scoped audits
verify the zero-order reference,
bonded-cube geometry and platform envelope; RF-on first-order behaviour is
not validated. All mechanical and reference-path checks pass, including a
negative beam-under-knob test; the minimum beam-edge/knob margin is 0.520322 mm.
The 24 × 14.935227 in occupied envelope fits the 28 × 15 in platform by
continuous translation with 1.645244 mm total width spare. The final machining
inventory is 85 tapped and four clearance holes. STEP, top/3D views, layout
illustration, BOM and tapping sheets are regenerated. FCStd geometry and
placements survive reopening, with the external plate tree-view limitation
recorded above.

**V9.11 (2026-10-12, TA tail-clamp spacing)** — moves both rear fiber-clamp
hole pairs 12.7 mm farther behind the heads: 66.7 mm for the direct output
and 58.7 mm for the AOM output. The four clamp-hole positions change; the
14 × 16.5 in outline, every optic and its placement, all other mounting holes,
and optical order remain as in V9.10. The full 60 × 20 mm clamp footprints and
20 mm fiber corridors remain clear in the rebuilt mechanical audit. The
cell-slide checks pass at both 0 and 10.5 mm, and the deliberately injected
beam-under-knob case is correctly rejected. The
occupied hardware-plus-cable envelope is unchanged at
367.784956 × 523.592478 mm, including the full 101.6 mm TA cable allowance.
The reused opaque cell covers still require beam apertures before operation.

**V9.10 (2026-10-12, folded TA output)** — adds one steering mirror on a
Newport M05 mount at
(40, 33.5) mm before the AOM output's first telescope lens, turning the long
downward leg right across the bottom. The AOM branch now has two output folds;
the direct-fiber branch keeps its single fold and left exit. The plate shrinks
from 14 × 21.5 in to 14 × 16.5 in, 5 in shorter and 23.26% smaller in area.
The nominal outline is 355.6 × 419.1 mm and the machined STEP is
349.25 × 412.75 × 25.4 mm. The common train moves 127 mm in −Y while preserving
every existing optic's order, all conditioning station pitches, both telescope
spacings and the full V9.7 sliding cell. Rear clamp offsets remain 46 mm (AOM)
and 54 mm (direct); the 40 mm RF space and 101.6 mm TA cable allowance remain.
The actual hardware-plus-cable envelope is 367.784956 × 523.592478 mm
(14.480 × 20.614 in), fitting the 15 × 28 in platform by continuous translation;
mounting-grid alignment is unverified. Both cell-slide endpoints pass the
mechanical checks. Across 26 beam segments and 90 physical objects, there are
no crossings, knob projection hits or foreign-hardware projection conflicts;
the minimum beam-edge/knob margin is 7.039884 mm. Seven knobs protrude beyond
the plate, with no body overhang. The new STEP is
`TA_Board_V9_baseplate_14x16p5in.step`; V9.9 and earlier STEPs remain legacy
models. STEP, top/3D views, BOM, tapping sheets, clearance plan and reports are
regenerated, with nine mirrors and 55 tapped plus four clearance holes.
The unchanged opaque cell covers still require beam apertures before operation.

**V9.9 (2026-10-12, TA short-edge cable)** — the TA plate becomes 14 × 21.5 in
(355.6 × 546.1 mm nominal; 349.25 × 539.75 × 25.4 mm machined outline).
The TA cable exits the upper short edge in +Y with 4 in reserved for it,
giving a nominal 14 × 25.5 in envelope within the 15 × 28 in platform.
Including all hardware protrusions, the verified envelope is
367.784956 × 647.7 mm (14.480 × 25.5 in), leaving 13.215044 × 63.5 mm within
the platform under continuous translation; mounting-grid alignment remains
unverified. Both cell-slide endpoints pass the mechanical checks, with no
beam crossing or knob underpass. The common optical sequence, all six
conditioning pitches, both output telescope spacings and the full V9.7
sliding cell are retained.
The AOM output runs down the left side to the bottom edge; the direct branch
uses one mirror and runs left to the left edge. Rear clamp offsets are 46 mm
(AOM) and 54 mm (direct); RF space remains 40 mm, above the 38.1 mm requirement.
The new STEP filename is `TA_Board_V9_baseplate_14x21p5in.step`; the 14 × 17.5 in
and 25 × 14 in STEPs remain legacy models. STEP, top/3D views, BOM, tapping
sheets and validation report are regenerated; the final plate has 54 tapped
and four clearance holes. The reused opaque cell covers still need beam apertures.

**Splitting board V2 (2026-10-12, KM05T adapters)** — replaces the input and
all four output KA05T heads with the existing KM05T assemblies and lip
adapters. Every optical coordinate and path, the 24 × 14 in plate, table
bolts, 76 mm tail-clamp pairs and 40 mm RF reservations are preserved. The
only addition to the inherited part of `optomech.py` is the opt-in
`mount_only` adapter drilling mode; existing defaults are unchanged. Explicit
tail-tap features and `tools/km05t_audit.py` make the new mounting geometry
auditable. Installation, tail/service/hole clearances and projection checks
pass; three old mesh candidates are resolved by strictly positive actual-hull
separation. All production files and the layout illustration are regenerated.
The final plate has 77 tapped and four clearance holes, 81 hole axes in total.

**V9.8 (2026-10-11, TA board)** — the TA plate shrinks from 25 × 14 in to
14 × 17.5 in, reducing nominal area by 30%. Optical order, the six conditioning
station pitches and both output telescope spacings are preserved. The direct
PBS branch uses one steering mirror and exits at the bottom; the AOM output
exits at the left. Rear clamp offsets become 54 mm (direct) and 64 mm (AOM),
with full clamp and cable reservations. The TA now reuses the complete V9.7
sliding cell enclosure and seat without altering those parts. Its unfinished
opaque end covers are explicitly recorded as blocking optical operation
until beam apertures are machined. The 10 in bolt-pair limit remains specific
to the lattice board.

That revision exported `TA_Board_V9_baseplate_14x17p5in.step`, now retained as
a legacy model alongside the prior 25 × 14 in STEP. Its top/3D renders, BOM,
hole inventory, validation report and tapping sheets described V9.8.
The branch added `tools/ta_projection_audit.py`,
`tools/export_ta_board.py` and `tools/render_ta_documents.py` for projection
checks and reproducible exports. Mechanical routing and the unfinished
cell-cover optical obstruction are reported separately.

**Splitting board V2 (2026-10-09, new board)** — `Rubidium_system/Splitting_Board_V2.py`
and `Production/SplittingBoardV2/` (top and 3D renders, layout figure, audit
report, BOM, tapping sheet, `StepFile/Splitting_Board_V2_baseplate_24x14in.step`;
the STEP is also in `Production/Baseplate/`). Nothing else on the branch
changes.

**V9.7 (2026-10-08, lattice board only)** — the cell enclosure gets a
screw at each end and a closed stem pocket: the plain block grows to 88 ×
46.9 × 48 (x = ±44 about the cell) with a through slot in each bore end
region and two 8-32 × 2 in screws into plate taps at (185, 123.6) and
(185, 203.4); the stem pocket stops 2.5 mm before the −x face (the Thorlabs
drawing gives the stem as < 10 mm high at mid-length); covers 7 mm; the seat
moves to y = 163.5 so that the 102 mm assembly fits between the station-6
slab and the shutter pocket. Plate: pocket 104.4 × 61.7 at x 157.8–222.5,
y 111.3–215.7, two taps; hole count 103 → 104. Five configurations rebuilt
and audited — no contact, intersection or clearance conflict, the same ten
accepted overhangs. New STEP (`Lattice_V9_7_baseplate_24x15in.step`),
renders, audit reports, BOM and tapping sheets replace the V9.6 ones;
`Production/CellEnclosure/` holds the V9_7 lower half, lid, cover and
assembly STEPs, drawing and dimension JSON (V9.6 files removed).

**V9.6 (2026-10-08, lattice board only)** — the cell enclosure is redesigned
after review of V9.5 as a plain block cut in two along the bore axis (lower
half + lid, 82 × 43.9 × 24 each): the bottom shoulder is gone, one slot in the
bore's end region beyond the cell runs through both halves and a single 8-32 ×
2 in screw from the lid top clamps the halves and fixes the position; the fill
stem lies in the parting plane in a 12 × 10 channel toward −x; the Ø6 wire
hole becomes a 6 × 6 notch at the parting line; the covers are 8 mm (5/8 in
screws); travel 10.5 mm (the glass wall and the isolator pocket limit it).
Plate: the pocket becomes 11.3 mm deep, 102 × 61.7, with one tap at (185,
201.3) instead of two; hole count 104 → 103. Five configurations rebuilt and
audited — no contact, intersection or clearance conflict, the same ten
accepted overhangs. New STEP (`Lattice_V9_6_baseplate_24x15in.step`),
renders, audit reports, BOM and tapping sheets replace the V9.5 ones;
`Production/CellEnclosure/` now holds the lower half, lid, cover and assembly
STEPs, a four-sheet drawing and the dimension JSON (the V9.5 body/cover files
are removed).

**V9.5 (2026-10-06, lattice board only)** — the Rb cell gets its enclosure and
the seat becomes a sliding one; nothing else on the plate moves. New library
classes `SlidingCellEnclosure`, `SlidingCellCover`, `SlidingCellGlass`,
`SlidingCellSeat` and `place_sliding_cell` (optomech section 3b): body
76 × 40.4 × 48 with the Ø30.4 bore, Ø12 stem hole, 25 × 10 slot shoulder (two
8-32 slots, 12.7 mm of travel), eight 16 mm cover taps and the Ø6 wire hole;
two 10 mm counterbored covers without apertures; the GC25075-RB envelope. The
plate's 104 × 56 × 19.05 pocket and four corner taps are replaced by a 10.3 mm
pocket (100 × 61.4 plus a 48 × 27 ear) with two 8-32 taps through its floor at
(223.35, 132) and (223.35, 162); hole count 106 → 104 (100 × 8-32 + 4 bolts).
`example_baseplate(cell_slide=…)` builds the enclosure anywhere along its
travel; five configurations (single, dual, 75-50, 75-75, dual + cell slid
12.7 mm) were rebuilt and audited — no contact, intersection or clearance
conflict, the same ten accepted overhangs. The audits learned the enclosure:
the body is checked geometrically, the aperture-less covers and the cell are
exempted only for a beam along the bore, and the seat taps are owned by the
body (hole_clearance). New STEP (`Lattice_V9_5_baseplate_24x15in.step`),
renders, audit reports, BOM (enclosure body, covers, cell and screws added)
and tapping sheets replace the V9.4.2 ones; `Production/CellEnclosure/` is
new (body / cover / assembly STEPs, three-sheet drawing, dimension JSON).
`optomech.py` on the branch now also carries the pin-free
`mirror_mount_k05s1_no_pins` variant mentioned under V9.4, which had not been
pushed with that revision.

**V9.4.2 (2026-10-04, lattice board only)** — both table-bolt pairs are
limited to 10 in spacing while staying centred on the short edge. Nearer the
fiber edge every such pair collides with the 0-order irises, the optional
f = 75 set or the output heads, so the fiber-side pair moves inboard to
6.25 in (n = 5) from the right edge, between the AOM housings and the f = 75
lens holders; the TA-side pair stays 1.5 in from the left edge (16 in to the
left of the other pair). Nominal units (17.125, 1.5), (17.125, 11.5),
(1.125, 1.5), (1.125, 11.5). The TA block moves 5 mm up so that its adapter
pocket clears the lower-left bolt by 5.3 mm; nothing else moves. All four
configurations rebuilt and audited: no contact, intersection or clearance
conflict; the ten accepted overhangs are unchanged. New STEP
(`Lattice_V9_4_2_baseplate_24x15in.step`), renders, audit reports, BOM and
tapping sheets replace the V9.4.1 ones.

**V9.4.1 (2026-10-04, lattice board only)** — two changes, nothing else
moves. (1) The four table bolts are re-laid on the lab table's 1 in grid
(first row 1.5 in from the table edge): with the plate's fiber-side edge
0.25 in inside the table edge, the fiber-side pair sits 3.25 in from that
plate edge, 13 in apart and centred on the short edge, and the TA-side pair
19 in further left (1.5 in from the left edge), 11 in apart and centred —
(20.125, 0), (20.125, 13), (1.125, 1), (1.125, 12) in the script's nominal
inch units. (2) The optional f = 75 set (its bare holes, the machined RSP05
seat and the hardware of the two test configurations) moves from the
+1-order axis onto the 0-order/input axis straight after each AOM, as in
V9.3; the distances from the AOM are unchanged, so every element moves down by
1.3–3.1 mm and turns to the board axes. All four configurations (single, dual,
75-50, 75-75) were rebuilt and audited on the new plate: no contact,
intersection or clearance conflict; the ten accepted edge overhangs are the
same. New STEP (`Lattice_V9_4_1_baseplate_24x15in.step`), renders, audit
reports, BOM and tapping sheet (`Lattice_V9_4_1_baseplate_TAP_or_NOT`,
`V9_4_1_tapping_sheets_all.pdf`); the V9.4 STEP and sheets were removed
(and the V9.4.1 ones in turn by V9.4.2).

**V9.4 (2026-10-01, lattice board only)** — the double-pass cat-eyes change
from f = 75 mm (LA1612-B) to f = 300 mm (LA1618-B): the focused spot on the
retro mirror is 4× larger. Each AOM → lens → mirror path (605.5 mm) is folded
into a U by two 45° M05 fold mirrors on the +1-order axis; one IDA12 on the
vertical leg blocks the 0 order; the QWP moves to the return leg. The plate
grows to 24 × 15 in (0.5 in added at the top and bottom; every V9.3 coordinate
is kept, the four table bolts are the V9.2/V9.3 pattern unchanged); the
isolator lane moves 8 mm toward the TA and the PBS column 10 mm; the DP2 output
row moves above its AOM row so the fold leg crosses nothing; the external-TA
telescope has both lenses on the input lane; every mirror is a Newport M05; all
three fiber heads keep the 76 mm rear tail-clamp pair. The LA1612-B set is kept
as an option on bare holes after each AOM (lens → mirror 50 or 75 mm), and both
f = 75 test configurations were built on the same plate and audited. The
LA1618-B catalogue values (R 155.0, tc 2.2 mm) were read after the layout was
drilled with R 154.5 / tc 2.0: the resulting 1.2 / 1.0 mm cat-eye defocus is
documented in the script and accepted (the return stays antiparallel; the
lateral walk over 80–120 MHz is 9 µm). New STEP, renders, audit reports, BOM
and tapping sheet in `Production/LatticeBoardV9/` and `Production/Baseplate/`;
the 24 × 14 in STEP, its sheet and `V9_3_tapping_sheets_all.pdf` are removed
(replaced by `V9_4_tapping_sheets_all.pdf`). Audit tooling gained the
`diffraction_kink_deg` exemption from the orthogonality rule and a note class
for empty optional taps under a beam; `optomech.py` is unchanged except for a
pin-free `mirror_mount_k05s1_no_pins` variant that the final board does not
use.

**V9.3 (2026-09-28)** — the four M2.5 tapped holes the plate used to carry under
the TA butterfly board are removed from the lattice and TA baseplates; the TA
adapter is unchanged and keeps its own four M2.5 threads, and the plate keeps
the adapter's four 8-32 taps. The boards now place `TA_butterfly_on_adapter`
(new class, see above). Plate volume of the lattice and TA boards rises by
exactly the four 2.05 mm × 13.8 mm bores (182.195 mm³); nothing else in any
board moved, and the audits report the same six accepted items as before. Both
STEPs (`Production/Baseplate/`, `Production/*/StepFile/`) were re-exported, the
renders, audit reports and BOMs regenerated, and the `*_TAP_or_NOT` sheets for
the three plates and the two adapters added.

**V9.2 (2026-09-25)** — first publication of the three boards on this branch.
