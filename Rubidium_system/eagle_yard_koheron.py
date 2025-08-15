import time
start_time=time.time()
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Module')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Subsystem')))
from PyOpticL import layout, optomech
import numpy as np


wavelength = 780e-6   #wavelength in mm

label = "               "  + str(wavelength*1e6) + "nm"

# Define the dimension of the baseplet
base_dx = 6*layout.inch 
base_dy = 4*layout.inch 
base_dz = layout.inch
gap = layout.inch/4

# # Define the position from where the beam will enter into the baseplate
input_x = 0*layout.inch 
input_y = 0.5*layout.inch
input_y = base_dy - input_y

# Adding mount holes to bolt the baseplate to the optical table
mount_holes=[[3,0],[0,2],[0,4],[4,2]]

def koheron_eagleyard(x=0, y=0, angle=0):
    baseplate = layout.baseplate(base_dx, base_dy, base_dz, x=x, y=y, angle=angle,
                                 gap=gap, mount_holes=[(1,1),(5,3),(0,3), (4,3),(4,2)], y_offset  = 9, label=label)
    layout.place_element_on_table("ecdl",  optomech.ECDL, x = 0 + x, y = 0 + y, angle= angle)

if __name__ == "__main__":
    koheron_eagleyard()
    layout.redraw()