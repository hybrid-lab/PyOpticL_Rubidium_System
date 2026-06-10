from PyOpticL import layout, optomech

# baseplate constants
base_dx = 14*layout.inch
base_dy = 8*layout.inch
base_dz = 1*layout.inch
gap = layout.inch/8

mount_holes = [(2, 0), (3, 7), (13, 0), (10, 7)]

input_y = 6.75*layout.inch

def example_baseplate(x=0, y=0, angle=0):

    baseplate = layout.baseplate(base_dx, base_dy, base_dz, x=x, y=y, angle=angle, gap=gap, mount_holes=mount_holes)

    beam = baseplate.add_beam_path(x=5*layout.inch, y=input_y, angle=layout.cardinal['left'])

    #baseplate.place_element("Input Fiberport", optomech.fiberport_mount_km05T, x=5.5*layout.inch, y=input_y, angle=layout.cardinal['left'], mount_args=dict(thumbscrews=True))
    baseplate.place_element("Input Fiberport", optomech.fiberport_mount_KA05T, x=5.5*layout.inch, y=input_y, angle=layout.cardinal['left'], mount_args=dict(thumbscrews=True))

    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, beam, beam_index=0b1, x=1.75*layout.inch, angle=layout.turn['up-right'],
                                        mount_type=optomech.mirror_mount_M05, mount_args=dict(thumbscrews=True))

    baseplate.place_element_along_beam("1/4 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b1, distance=1*layout.inch, angle=layout.cardinal['up'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b1, distance=1*layout.inch, angle=layout.cardinal['up'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Beam Splitter Cube", optomech.cube_splitter, beam,
                                       beam_index=0b1, distance=1*layout.inch, angle=layout.cardinal['down'],
                                       mount_type=optomech.cube_mount_halfinch)
    
    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, beam,
                                       beam_index=0b10, distance=2.15*layout.inch, angle=layout.turn['down-right'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))

    baseplate.place_element_along_beam("1/4 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b10, distance=3*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, beam,
                                       beam_index=0b10, distance=3.5*layout.inch, angle=layout.turn['down-left'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))
    
    baseplate.place_element_along_beam("Beam Splitter Cube", optomech.cube_splitter, beam, beam_index=0b10, distance=2.15*layout.inch, angle=layout.cardinal['right'], mount_type=optomech.cube_mount_halfinch, invert=True)

    baseplate.place_element_along_beam("Vapor Cell", optomech.Vapor_Ref_Cell, beam, beam_index=0b11, distance=3.25*layout.inch, angle=layout.cardinal['right'])

    baseplate.place_element("1/2 Waveplate", optomech.waveplate, x=9.5*layout.inch, y=3.75*layout.inch, angle=layout.cardinal['right'], mount_type=optomech.rotation_stage_rsp05)

    baseplate.place_element("Beam Splitter Cube", optomech.cube_splitter, x=11*layout.inch, y=3.75*layout.inch, angle=layout.cardinal['right'], mount_type=optomech.cube_mount_halfinch)

    baseplate.place_element("Mirror", optomech.circular_mirror, x=11*layout.inch, y=5.75*layout.inch, angle=layout.turn['up-right'],
                            mount_type=optomech.mirror_mount_M05, mount_args=dict(thumbscrews=True))
    
    # For the photodiode, we can choose different models in optomech.py like optomech.photodetector_pdb250a or optomech.photodetector_pdb210a.
    baseplate.place_element("PD", optomech.photodetector_pdb250aa, x=12*layout.inch, y=4.75*layout.inch, angle=layout.cardinal['left'])

    
if __name__ == "__main__":
    example_baseplate()
    layout.redraw()
