from PyOpticL import layout, optomech

def polaris_k05s1_with_thumbscrews(obj):
    return optomech.mirror_mount_k05s1(obj, thumbscrews=True)

# baseplate constants
base_dx = 20*layout.inch
base_dy = 14*layout.inch
base_dz = layout.inch
gap = layout.inch/8

# x-y coordinates of mount holes (in inches) (x,y)
mount_holes = [(1, 1), (1, 13), (14, 13), (19,1)]

# y coordinate of beam input
input_y = 7*layout.inch

# function so baseplate can be added to other layouts
def example_baseplate(x=0, y=0, angle=0):

    # define and place baseplate object
    baseplate = layout.baseplate(base_dx, base_dy, base_dz, x=x, y=y, angle=angle,
                                 gap=gap, mount_holes=mount_holes)

    # add beam
    ref_beam = baseplate.add_beam_path(x=3*layout.inch, y=input_y, angle=layout.cardinal['right'])

    mot_beam = baseplate.add_beam_path(x=8.5*layout.inch, y=input_y+2.5*layout.inch, angle=layout.cardinal['right'])

    repump_beam = baseplate.add_beam_path(x=10*layout.inch, y=input_y+4.*layout.inch, angle=layout.cardinal['right'])

    spare_beam = baseplate.add_beam_path(x=11.5*layout.inch, y=input_y+5.5*layout.inch, angle=layout.cardinal['right'])

    #option for laser on reference board
    ref_beam1 = baseplate.add_beam_path(x=3.125*layout.inch, y=input_y+4.5*layout.inch, angle=layout.cardinal['left'])
    #option for laser on different board
    ref_beam2 = baseplate.add_beam_path(x=2*layout.inch, y=input_y-3.5*layout.inch, angle=layout.cardinal['up'])


    # #Place reference laser
    # baseplate.place_element("DFB", optomech.Koheron_DFB_Laser, x=3.125*layout.inch, y=input_y, angle=0)
    baseplate.place_element("DFB", optomech.Koheron_DFB_Laser, x=3*layout.inch, y=input_y+4.5*layout.inch, angle=180)
    #add mirror
    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, ref_beam1,
                                       beam_index=0b1, x=2*layout.inch, angle=layout.turn['up-right'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))

    #add mirror
    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, ref_beam1,
                                       beam_index=0b1, distance=4.5*layout.inch, angle=layout.turn['down-right'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))

    #set up path if we want to use a fiber port instead of laser
    baseplate.place_element("reference Input Fiberport", optomech.fiberport_mount_km05T, mount_args=dict(thumbscrews=True), adapter_args=dict(
        rear_pair_43=True,
        rear_pair_63=False,
        rear_pair_73=False,),
        x=2*layout.inch, y = input_y-4.5*layout.inch, angle=layout.cardinal['up'])

    #add mirror
    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, ref_beam2,
                                       beam_index=0b1, distance=3.5*layout.inch, angle=layout.turn['up-right'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))




    #set up center line of reference beam optics
    # add waveplate along the transmitted beam, 1" after the DFB laser, mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, ref_beam,
                                       beam_index=0b1, distance=1.25*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    #Adding the isolator to make sure there is no unwanted beam going back as feedback
    baseplate.place_element_along_beam("Optical_Isolator", optomech.isolator_780, ref_beam,
                                       beam_index=0b1, distance=1.375*layout.inch, angle=layout.cardinal['left'])
    
    baseplate.place_element_along_beam("Optical_Isolator", optomech.isolator_780, ref_beam,
                                       beam_index=0b1, distance=1.875*layout.inch, angle=layout.cardinal['left'])

    baseplate.place_element_along_beam("1/4 Waveplate", optomech.waveplate, ref_beam,
                                       beam_index=0b1, distance=1.25*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, ref_beam,
                                       beam_index=0b1, distance=1*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # add splitter component along beam
    baseplate.place_element_along_beam("Beam Splitter Cube", optomech.cube_splitter, ref_beam,
                                       beam_index=0b1, x=10.75*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.skate_mount, cube_size=0.5*layout.inch, mount_args=dict(
                                        cube_dx=0.5*layout.inch,
                                        cube_dy=0.5*layout.inch,
                                        cube_dz=0.5*layout.inch,), invert=True)


    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, ref_beam,
                                       beam_index=0b10, x=13.05*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # add splitter component along beam
    baseplate.place_element_along_beam("Beam Splitter Cube", optomech.cube_splitter, ref_beam,
                                       beam_index=0b10, x=14.05*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.skate_mount, cube_size=0.5*layout.inch,mount_args=dict(
                                        cube_dx=0.5*layout.inch,
                                        cube_dy=0.5*layout.inch,
                                        cube_dz=0.5*layout.inch,),invert=True)

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, ref_beam,
                                       beam_index=0b100, distance=2.125*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # add splitter component along beam
    baseplate.place_element_along_beam("Beam Splitter Cube", optomech.cube_splitter, ref_beam,
                                       beam_index=0b100, x=17.3*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.skate_mount, cube_size=0.5*layout.inch,mount_args=dict(
                                        cube_dx=0.5*layout.inch,
                                        cube_dy=0.5*layout.inch,
                                        cube_dz=0.5*layout.inch,), invert=True)

    # add mirror along the MOT beam, mounted in a m05 mount
    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, ref_beam,
                                       beam_index=0b1000, distance=1.4*layout.inch, angle=layout.turn['up-left'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True),
                                       adapter_type=optomech.surface_adapter)

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, ref_beam,
                                       beam_index=0b1000, distance=layout.inch, angle=layout.cardinal['up'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # add output fiberport along the transmitted beam
    baseplate.place_element_along_beam("Ref Output Fiberport", optomech.fiberport_mount_km05T, ref_beam,
                                       beam_index=0b1000, distance=3*layout.inch -5.136, angle=layout.cardinal['up'],
                                       mount_args=dict(thumbscrews=True), adapter_args=dict(
        rear_pair_43=False,
        rear_pair_63=True,
        rear_pair_73=False,))







    # add input fiberport along the MOT beam
    baseplate.place_element("MOT Input Fiberport", optomech.fiberport_mount_km05T, mount_args=dict(thumbscrews=True), 
        x=8*layout.inch, y = input_y+2.5*layout.inch, angle=layout.cardinal['right'], adapter_args=dict(
        rear_pair_43=False,
        rear_pair_63=False,
        rear_pair_73=True,))

    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, mot_beam,
                                       beam_index=0b1, x=10.75*layout.inch, angle=layout.turn['up-left'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, mot_beam,
                                       beam_index=0b1, distance=0.75*layout.inch, angle=layout.cardinal['down'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # Place the mirror on ref_beam
    baseplate.place_element_along_beam("Shared Mirror", optomech.circular_mirror, ref_beam,
                                       beam_index=0b11, distance=2.75*layout.inch, angle=layout.turn['down-left'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))


    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, ref_beam,
                                       beam_index=0b11, distance=2*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, ref_beam,
                                       beam_index=0b11, distance=1.25*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # add output fiberport along the transmitted beam
    baseplate.place_element_along_beam("MOT Output Fiberport", optomech.fiberport_mount_km05T, ref_beam,
                                       beam_index=0b11, distance=3.5*layout.inch, angle=layout.cardinal['right'],  adapter_args=dict(
        rear_pair_43=False,
        rear_pair_63=False,
        rear_pair_73=True,), mount_args=dict(thumbscrews=True))


#####################################################################################################


    # add output fiberport along the repump beam
    baseplate.place_element("Repumper Input Fiberport", optomech.fiberport_mount_km05T, mount_args=dict(thumbscrews=True), 
        x=9.5*layout.inch, y = input_y+4.0*layout.inch, angle=layout.cardinal['right'],  adapter_args=dict(
        rear_pair_43=False,
        rear_pair_63=True,
        rear_pair_73=False,))

    # add mirror along the repump beam, mounted in a m05 mount
    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, repump_beam,
                                   beam_index=0b1, x=14.05*layout.inch, angle=layout.turn['up-left'],
                                   mount_type=optomech.mirror_mount_M05,
                                   mount_args=dict(thumbscrews=True))

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, repump_beam,
                                       beam_index=0b1, distance=1.375*layout.inch, angle=layout.cardinal['down'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # Place the mirror on ref_beam
    baseplate.place_element_along_beam("Shared Mirror", optomech.circular_mirror, ref_beam,
                                       beam_index=0b101, distance=4.25*layout.inch, angle=layout.turn['down-left'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, ref_beam,
                                       beam_index=0b101, distance=1.2*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, ref_beam,
                                       beam_index=0b101, distance=3*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    baseplate.place_element_along_beam("Repumper Output Fiberport", optomech.fiberport_mount_km05T, ref_beam,
                                       beam_index=0b101, distance=3.5*layout.inch, angle=layout.cardinal['right'],  adapter_args=dict(
        rear_pair_43=False,
        rear_pair_63=True,
        rear_pair_73=False,), mount_args=dict(thumbscrews=True))








    # add output fiberport along the spare beam
    baseplate.place_element("Spare Input Fiberport", optomech.fiberport_mount_km05T, mount_args=dict(thumbscrews=True), 
        x=11*layout.inch, y = input_y+5.5*layout.inch, angle=layout.cardinal['right'],  adapter_args=dict(
        rear_pair_43=False,
        rear_pair_63=False,
        rear_pair_73=True,))

    # add mirror along the repump beam, mounted in a m05 mount
    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, spare_beam,
                                   beam_index=0b1, x=17.3*layout.inch, angle=layout.turn['up-left'],
                                   mount_type=optomech.mirror_mount_M05,
                                   mount_args=dict(thumbscrews=True))

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, spare_beam,
                                       beam_index=0b1, distance=1.375*layout.inch, angle=layout.cardinal['down'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # Place the mirror on ref_beam
    baseplate.place_element_along_beam("Shared Mirror", optomech.circular_mirror, ref_beam,
                                       beam_index=0b1001, distance=5.75*layout.inch, angle=layout.turn['down-left'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, ref_beam,
                                       beam_index=0b1001, distance=1.2*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, ref_beam,
                                       beam_index=0b1001, distance=4.5*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # add output fiberport along the transmitted beam
    baseplate.place_element_along_beam("Spare Output Fiberport", optomech.fiberport_mount_km05T, ref_beam,
                                       beam_index=0b1001, distance=3*layout.inch, angle=layout.cardinal['right'],  adapter_args=dict(
        rear_pair_43=False,
        rear_pair_63=False,
        rear_pair_73=True,),mount_args=dict(thumbscrews=True))


# this allows the file to be run as a macro or imported into other files
if __name__ == "__main__":
    example_baseplate()
    layout.redraw()
