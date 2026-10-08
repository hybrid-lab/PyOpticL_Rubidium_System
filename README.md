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
Haotian Xu with GPT (Codex) and Claude. Current revision **V9.6** (2026-10-08,
lattice board: split sliding Rb cell enclosure; the TA and double-pass boards
are unchanged since V9.3); the change log is at the end of this section.

| Board | Script | Size | Production folder |
|---|---|---|---|
| Lattice board | `Rubidium_system/Lattice_Baseplate_V9.py` | 24 × 15 in | `Production/LatticeBoardV9/` |
| TA board | `Rubidium_system/TA_Baseplate_V9.py` | 25 × 14 in | `Production/TABoardV9/` |
| Double-pass AOM board | `Rubidium_system/AOM_DoublePass_Baseplate_V9.py` | 17 × 6 in | `Production/AOMDoublePassV9/` |

Each script is self-contained: constants at the top, then every optic placed in
beam order inside `example_baseplate()`. Run one in FreeCAD (Macro > Macros…, or
paste into the Python console) and the board is built. The lattice script also
takes `cat_eye='75-50'` / `'75-75'` to build the two f = 75 test configurations
on the same plate, and `cell_slide=0 .. 10.5` to put the cell enclosure anywhere
along its travel (see the lattice board below).

## What this branch changes

This branch starts from **`yajur-branch`**, not from `main`. The boards are built
on the yajur-branch component library: its `optomech.py` is the file these
boards were designed and audited against, and `main`'s version differs in 7 of
the 17 classes they use — `fiberport_mount_KA05T_holes`, which carries the rear
fiber tail-clamp holes used by all three boards, does not exist in `main` at all.

Relative to `yajur-branch`, exactly these files are touched:

**Modified — `optomech.py`** (everything above the banner
`Rb-87 795 nm lattice laser system - components added on this branch` is the
yajur-branch file, unchanged):

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
  counterbore, used for every position whose holder is not yet chosen.
- `SlidingCellEnclosure` / `SlidingCellLid` / `SlidingCellCover` /
  `SlidingCellGlass` / `SlidingCellSeat` / `place_sliding_cell` (V9.5, split in
  V9.6) — the Rb cell enclosure and its seat: a plain block cut into a lower
  half and a lid, 82 × 43.9 × 24 mm each, parted on the bore axis, with the
  30.4 mm bore, a 12 × 10 mm stem channel split between them, one through slot
  in the bore's end region, eight 16 mm deep cover taps and a 6 × 6 mm cable
  notch; two 8 mm end covers with counterbored 8-32 holes (no beam aperture
  yet); the GC25075-RB envelope; and the plate machining (an 11.3 mm pocket
  shaped for the assembly plus 10.5 mm of travel, one 8-32 tap through its
  floor). `place_sliding_cell(bp, x, y,
  angle, slide)` places the seat and the enclosure `slide` mm along the slot
  direction. All dimensions live in the `SLIDING_CELL` dict and are exported
  with the parts (`Production/CellEnclosure/`). The V9.2–V9.4 pocket-only seat
  (`CellPocketMachining` / `place_cell_pocket`) stays in the file for the TA
  board, which still uses it.
- `IntegralAOMSeat` / `integrate_aom` / `_make_IntegralAOMBaseplate` — the AOM
  seat machined directly into the baseplate (no lower surface adapter), with a
  flat screw-bearing face at z = −1.231 mm.
- `PersistentDrillVolume`, `keep_machining_hidden`, `deepen_isolator_pocket`,
  `add_fiber_tail_alternative`, `descendants` — supporting machining helpers.

The three variants are new classes rather than edits to the existing ones, so
the other boards on this branch keep the exact geometry they had.

**Added — three board scripts** in `Rubidium_system/`, listed in the table above.

**Added — three `Production/` folders**, each holding the top and 3D renders,
the audit report (`*_validation.json`), a BOM spreadsheet in the same
Adaptors/Elements layout as the other branches, `StepFile/` with the machined
baseplate STEP, and a `*_TAP_or_NOT` sheet (PDF + PNG) that marks which holes
of that plate are tapped. The three baseplate STEPs are also collected in
`Production/Baseplate/`, and the same sheets for the two adapters are in
`Production/Adapters/`. **`Production/CellEnclosure/`** (since V9.5) holds the
Rb cell enclosure: lower half, lid, cover and assembly STEPs, the four-sheet
dimensioned drawing (PDF + PNG) and the dimension JSON.

**Unchanged:** `stl/` (all 22 meshes these boards need, plus the cell glass, are
already present and identical), every other script in `Rubidium_system/`, and
every other `Production/` folder.

## Boards

**Lattice board (24 × 15 in, V9.6).** TA → two steering folds → HWP → isolator →
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

**Rb cell enclosure (V9.6).** The GC25075-RB cell (Ø25.4 × 71.84 mm) sits in a
plain machined aluminium block, 82 × 43.9 × 48 mm, that is cut in two along
the bore axis — a lower half and a lid, 24 mm each — so the cell is simply
laid in. Nothing sticks out of the block. The parting plane is the plate's
12.7 mm optical axis, so the beam runs along the split. The bore is Ø30.4 mm
(cell diameter + 5 mm), through the whole length, bored with the two halves
clamped together. The fill stem lies in the parting plane and points toward
−x on the board (away from the side the beam moves to), in a 12 × 10 mm
channel split 5/5 between the halves and open at the outer face (the stem tip
ends 1 mm inside it; a longer stem simply protrudes). A 6 × 6 mm cable notch
in the lower half's parting face leaves through the same wall. Two separate
8 mm end covers are each held by four 8-32 × 5/8 in socket head screws in
counterbored holes — eight 16 mm deep taps, two in each half, so the covers
also tie the halves together. The covers carry **no beam aperture yet** — it
is to be opened later on the bore axis.

The enclosure slides across the beam and is held by a single screw. The block
is 6 mm longer than the cell needs at its +y end (board), and in that end
region of the bore — beyond the cell, 1.2 mm from its end — one through slot
(4.37 wide, 14.9 long, running through both halves) sits on the −x half of the
bore while the beam uses the centre and the +x half; one 8-32 × 2 in screw
goes from the lid top through the slot into an 8-32 tap in the plate at
(185, 201.3). It clamps the halves together and fixes the position, its head
riding in an 8.5 × 5 mm counter-slot below the lid top, so the position is
set from above with everything assembled; the screw never meets the cell or
the beam (≥ 8.9 mm from the beam at any position). The pocket's end walls
keep the block square and the eight cover screws tie the halves at both ends.
With the screw at the slot's outer end the beam passes through the cell
centre; pushed to the other end (the block moving 10.5 mm toward −x) the beam
runs 2.2 mm inside the cell wall on the +x side — further than that the beam
would be in the glass, and the pocket would merge with the isolator's. The
plate pocket is 11.3 mm deep (the bore axis is 24 mm above the block's bottom,
so this puts it at the 12.7 mm optical height) and shaped for both halves, the
covers and the travel: 102 × 61.7 mm (board x 160.8–222.5, y 114–216; its +x
edge runs into the injection fold's thumbscrew pocket, as the old pocket did);
the pocket wall on the −x side is the travel stop, and the 98 mm assembly
keeps 3 mm to the station-6 holder slab and 2.7 mm of plate to the shutter
housing pocket. Both ends of the travel were built and audited
(`example_baseplate(mode='dual', cell_slide=10.5)` is the second report in
`Production/LatticeBoardV9/`): the two halves are never exempted — the beam
has to pass the bore geometrically — while the aperture-less covers and the
cell envelope are exempted explicitly for a beam running along the bore. The
enclosure parts are in `Production/CellEnclosure/`
(`Rb_Cell_Enclosure_LowerHalf_V9_6.step`, `..._Lid_V9_6.step`,
`..._Cover_V9_6.step`, `..._Assembly_V9_6.step`, the drawing
`Rb_Cell_Enclosure_V9_6_drawing.pdf` and `..._dimensions.json`); the cell is
centred in the bore by its heater/insulation, which is not part of this
design.

**Table bolts (V9.4.2).** The lab table has a 1 in hole grid whose first row
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

**TA board (25 × 14 in).** The same TA section, isolator lane, six stations and
cell seat; after the cell the beam is folded up a column to the power HWP/PBS.
The transmitted arm carries the AOM and the shutter, then a fold and the output
chain; the reflected arm reaches the short edge through two folds and the same
chain without an iris.

**Double-pass AOM board (17 × 6 in).** Standalone double pass: KA05T, HWP, PBS,
AOM on an integral seat, f = 75 mm cat-eye (LA1612-B, 795 nm EFL 75.95 mm), QWP,
iris, retro mirror; the return line runs 74 mm above the input line through a
steering mirror, HWP, rotating PBS and iris into a KA05T.

## Positions with nothing installed yet

On both boards the six conditioning stations and, on the lattice board, the
three external-TA telescope positions are drilled as bare 8-32 holes because
the optic has not been chosen. Each hole is placed where a POLARIS-L05G holder's
own tap would land, so fitting the holder later puts the lens on the design
plane. They are sized for an L05G with a 10 mm cylindrical lens bonded to its
front face, and the audit checks that holder footprint against every installed
part (no conflict on either board; on the TA board the V9.3 clearances still
apply: station 1 2.40 mm, station 2 8.00 mm, station 3 6.61 mm, station 4
7.00 mm, station 5 2.31 mm, station 6 25.74 mm).

The lattice board additionally carries the twelve bare holes of the optional
f = 75 cat-eye described above (six per AOM arm). The lens and mirror taps of
that set lie on the input beam axis by design — empty holes 12.7 mm below the
beam, usable only with that beam absent or the f = 300 chain's first fold
removed.

The Rb cell seat carries the V9.6 enclosure described above; the covers' beam
apertures are the one feature of it still to be machined.

## Machining

`Production/Baseplate/` holds the three machined baseplate STEPs — one solid
each, with all pockets, 8-32 tap-drill bores, the integral AOM seats, the cell
pocket and the 1/4-20 table-bolt counterbores included (the lattice plate is
`Lattice_V9_6_baseplate_24x15in.step`; the superseded V9.4–V9.5 and
24 × 14 in V9.2/V9.3 plates are removed). The solid is inset
3.175 mm from the nominal outline on every side, as in every PyOpticL plate.
Threads are specified, not modelled — a STEP file shows every bore's diameter,
position and depth but cannot say whether it is threaded, so each plate and
each adapter has a **`*_TAP_or_NOT` sheet** next to its STEP that marks exactly
that and nothing else (red ring = tap, blue crossed circle = do not tap; drill
sizes, tolerances, material and finish are left to the shop):

| Part | Sheet | Tapped | Not tapped |
|---|---|---|---|
| Lattice baseplate (V9.6) | `Production/LatticeBoardV9/Lattice_V9_6_baseplate_TAP_or_NOT.pdf` | 99 × #8-32 | 4 × 1/4-20 table-bolt clearance |
| TA baseplate | `Production/TABoardV9/TA_Board_V9_baseplate_TAP_or_NOT.pdf` | 57 × #8-32 | 4 × 1/4-20 clearance |
| Double-pass AOM baseplate | `Production/AOMDoublePassV9/AOM_DoublePass_V9_baseplate_TAP_or_NOT.pdf` | 22 × #8-32 | 3 × 1/4-20 clearance |
| TA adapter (`stl/TA_adapter.stl`) | `Production/Adapters/TA_adapter_TAP_or_NOT.pdf` | 4 × M2.5 × 0.45 (board screws) | 4 × 8-32 clearance (to the plate taps) |
| AOM adapter (`stl/aom_adapter.stl`) | `Production/Adapters/AOM_adapter_TAP_or_NOT.pdf` | 2 × M4 × 0.7 | 4 × clearance, in a row |

Every hole in the part is marked on its sheet; the rounded corners inside the
milled pockets are R3.175 end-mill fillets, not holes. `Production/Adapters/`
also holds `V9_6_tapping_sheets_all.pdf`, the five sheets in one file (the
V9.6 lattice sheet and the four unchanged V9.3 sheets), and the hole
coordinates of every sheet are listed on it (plates: STEP-file coordinates;
adapters: from the part's lower-left corner).

## Audits

The boards were checked with a set of read-only audits (mesh contacts, beam and
hardware crossings, fiber tail clamps, service clearances for the TA cable and
the AOM RF elbows, hole access, AOM seat machining probes). The saved reports
are the `*_validation.json` files in `Production/`. All three boards report no
issue apart from accepted overhangs: on the TA board the two TA steering
mirrors sit at the top of the plate, so their M05 bodies extend about 3.6 mm
past the outline and their thumbscrews about 21 mm — above the plate, not
through it; on the V9.6 lattice board the same two mirrors plus the three
fold mirrors at the plate corners (F1, F2, F4) and the DP1 0-order iris ring
overhang the edge the same way (ten items), every screw of theirs landing at
least 6.1 mm inside the edge. The upper fiber-side table bolt lies under the
DP1 beam (AOM → f = 75 lens position) 12.7 mm above the recessed bolt head:
install the bolts before aligning. The audit scripts themselves are development tooling and are
not part of this branch.

## Change log

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
