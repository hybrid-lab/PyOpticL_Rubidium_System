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
