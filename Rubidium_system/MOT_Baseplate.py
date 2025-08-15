from PyOpticL import layout, optomech

# baseplate constants
base_dx = 14*layout.inch
base_dy = 8*layout.inch
base_dz = layout.inch
gap = layout.inch/8

# x-y coordinates of mount holes (in inches) (x,y)
mount_holes = [(3, 0), (0, 7), (12, 0), (13, 7)]

# y coordinate of beam input
input_y = 4*layout.inch

# function so baseplate can be added to other layouts
def example_baseplate(x=0, y=0, angle=0):

    # define and place baseplate object
    baseplate = layout.baseplate(base_dx, base_dy, base_dz, x=x, y=y, angle=angle,
                                 gap=gap, mount_holes=mount_holes)

    # add beam
    beam = baseplate.add_beam_path(x=3*layout.inch, y=input_y, angle=layout.cardinal['right'])

    baseplate.place_element("DFB", optomech.Koheron_DFB_Laser, x=3.125*layout.inch, y=input_y, angle=0)

    # add waveplate along the transmitted beam, 1" after the DFB laser, mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b1, distance=1.25*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    #Adding the isolator to make sure there is no unwanted beam going back as feedback
    baseplate.place_element_along_beam("Optical_Isolator", optomech.isolator_780, beam,
                                       beam_index=0b1, distance=2.5*layout.inch, angle=layout.cardinal['left'])

    baseplate.place_element_along_beam("1/4 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b1, distance=2.5*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # add waveplate along the beam, mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b1, distance=1.25*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # add splitter component along beam
    baseplate.place_element_along_beam("Beam Splitter Cube", optomech.cube_splitter, beam,
                                       beam_index=0b1, distance=1*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.skate_mount)


    # add mirror along the reflected beam, 1 inch from the splitter cube, mounted in a m05 mount
    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, beam,
                                       beam_index=0b11, distance=2.5*layout.inch, angle=layout.turn['up-left'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))

    # add waveplate along the reflected beam, mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b11, distance=1.75*layout.inch, angle=layout.cardinal['left'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # add output fiberport along the second beam
    baseplate.place_element_along_beam("Beat Output Fiberport", optomech.fiberport_mount_km05T, beam,
                                       beam_index=0b11, distance = 2.5*layout.inch, angle=layout.cardinal['right'],
                                       mount_args=dict(thumbscrews=True))




    # add mirror along the transmitted beam, mounted in a m05 mount
    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, beam,
                                       beam_index=0b10, distance=1*layout.inch, angle=layout.turn['up-left'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))

    # add mirror along the transmitted beam, mounted in a m05 mount
    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, beam,
                                       beam_index=0b10, distance=2.25*layout.inch, angle=layout.turn['down-left'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))

    # add waveplate along the transmitted beam, mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b10, distance=1.75*layout.inch, angle=layout.cardinal['left'],
                                       mount_type=optomech.rotation_stage_rsp05)

    baseplate.place_element_along_beam("Beam Splitter Cube", optomech.cube_splitter, beam,
                                       beam_index=0b10, distance=layout.inch, angle=layout.cardinal['left'],
                                       mount_type=optomech.skate_mount)
    
    # add output fiberport along the transmitted beam
    baseplate.place_element_along_beam("MOT Output Fiberport", optomech.fiberport_mount_km05T, beam,
                                       beam_index=0b100, distance=2.5*layout.inch, angle=layout.cardinal['right'],
                                       mount_args=dict(thumbscrews=True))

# this allows the file to be run as a macro or imported into other files
if __name__ == "__main__":
    example_baseplate()
    layout.redraw()
