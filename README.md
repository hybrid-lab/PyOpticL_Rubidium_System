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
Haotian Xu with GPT (Codex) and Claude:

| Board | Script | Size | Production folder |
|---|---|---|---|
| Lattice board | `Rubidium_system/Lattice_Baseplate_V9.py` | 24 × 14 in | `Production/LatticeBoardV9/` |
| TA board | `Rubidium_system/TA_Baseplate_V9.py` | 25 × 14 in | `Production/TABoardV9/` |
| Double-pass AOM board | `Rubidium_system/AOM_DoublePass_Baseplate_V9.py` | 17 × 6 in | `Production/AOMDoublePassV9/` |

Each script is self-contained: constants at the top, then every optic placed in
beam order inside `example_baseplate()`. Run one in FreeCAD (Macro > Macros…, or
paste into the Python console) and the board is built.

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
- `BareTappedHole` — an 8-32 tap-drill location with no mount, optic or
  counterbore, used for every position whose holder is not yet chosen.
- `CellPocketMachining` / `place_cell_pocket` — the Rb cell seat: a 104 × 56 mm
  pocket, 3/4 in deep, with four corner 8-32 taps. Nothing is modelled above the
  plate, because the enclosure has not been designed yet.
- `IntegralAOMSeat` / `integrate_aom` / `_make_IntegralAOMBaseplate` — the AOM
  seat machined directly into the baseplate (no lower surface adapter), with a
  flat screw-bearing face at z = −1.231 mm.
- `PersistentDrillVolume`, `keep_machining_hidden`, `deepen_isolator_pocket`,
  `add_fiber_tail_alternative`, `descendants` — supporting machining helpers.

The two variants are new classes rather than edits to the existing ones, so the
other boards on this branch keep the exact geometry they had.

**Added — three board scripts** in `Rubidium_system/`, listed in the table above.

**Added — three `Production/` folders**, each holding the top and 3D renders,
the audit report (`*_validation.json`), a BOM spreadsheet in the same
Adaptors/Elements layout as the other branches, and `StepFile/` with the
machined baseplate STEP. The three baseplate STEPs are also collected in
`Production/Baseplate/`.

**Unchanged:** `stl/` (all 22 meshes these boards need, plus the cell glass, are
already present and identical), every other script in `Rubidium_system/`, and
every other `Production/` folder.

## Boards

**Lattice board (24 × 14 in).** TA → two steering folds → HWP → isolator → QWP →
six bare 8-32 conditioning stations (45/45 mm down the lane, then 60 mm and
100 mm along the beam) → Rb cell seat → SR475 shutter → power HWP/PBS. The
transmitted and reflected beams feed two double-pass AOM arms: G&H AOMO 3100-125
on an integral seat, LA1612-B cat-eye lens 75 mm from the AOM and 75 mm from the
retro mirror, order-selection iris 10 mm before the mirror. Each return is
separated by its PBS and passes an LA1289-B/LA1540-B telescope, HWP, rotating
PBS and iris into a KA05T. `example_baseplate(mode='dual')` adds a second KA05T
input for an external TA, its injection fold and a blocking iris.

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

Nine positions are drilled as bare 8-32 holes because the optic has not been
chosen: the six conditioning stations on the lattice and TA boards, and the
three external-TA telescope positions on the lattice board. Each hole is placed
where a POLARIS-L05G holder's own tap would land, so fitting the holder later
puts the lens on the design plane.

They are sized for an L05G with a 10 mm cylindrical lens bonded to its front
face. Measured against the real part outlines in the plate plane, the clearance
to the nearest neighbouring part is:

| Position | Clearance |
|---|---|
| Station 1 | 2.40 mm |
| Station 2 | 8.00 mm |
| Station 3 | 6.61 mm |
| Station 4 | 7.00 mm |
| Station 5 | 2.31 mm |
| Station 6 | 25.74 mm |
| External lens 1 | 20.58 mm |
| External lens 2 | 10.35 mm |
| External spare | 19.38 mm |

The Rb cell seat is likewise a pocket only: the enclosure is a later design, so
no cell part is modelled or listed in the BOM.

## Machining

`Production/Baseplate/` holds the three machined baseplate STEPs — one solid
each, with all pockets, 8-32 tap-drill bores, the integral AOM seats, the cell
pocket and the 1/4-20 table-bolt counterbores included. The solid is inset
3.175 mm from the nominal outline on every side, as in every PyOpticL plate.
Threads are specified, not modelled.

## Audits

The boards were checked with a set of read-only audits (mesh contacts, beam and
hardware crossings, fiber tail clamps, service clearances for the TA cable and
the AOM RF elbows, hole access, AOM seat machining probes). The saved reports
are the `*_validation.json` files in `Production/`. All three boards report no
issue apart from six accepted items on the lattice and TA boards: the two TA
steering mirrors sit at the top of the plate, so their M05 bodies extend about
3.6 mm past the outline and their thumbscrews about 21 mm — above the plate, not
through it. The audit scripts themselves are development tooling and are not
part of this branch.
