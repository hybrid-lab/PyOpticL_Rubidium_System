from PyOpticL import layout, optomech

def polaris_k05s1_with_thumbscrews(obj):
    return optomech.mirror_mount_k05s1(obj, thumbscrews=True)

# baseplate constants
base_dx = 12*layout.inch
base_dy = 13*layout.inch
base_dz = layout.inch
gap = layout.inch/8

# x-y coordinates of mount holes (in inches) (x,y)
mount_holes = [(0, 0), (0, 12), (11, 0), (11, 12)]


# function so baseplate can be added to other layouts
def example_baseplate(x=0, y=0, angle=0):

    # define and place baseplate object
    baseplate = layout.baseplate(base_dx, base_dy, base_dz, x=x, y=y, angle=angle,
                                 gap=gap, mount_holes=mount_holes)

    # add beam
    beam1 = baseplate.add_beam_path(x=3.6*layout.inch, y=1.5*layout.inch, angle=layout.cardinal['right'])

    beam2 = baseplate.add_beam_path(x=3.6*layout.inch, y=3.5*layout.inch, angle=layout.cardinal['right'])

    beam3 = baseplate.add_beam_path(x=3.6*layout.inch, y=5.5*layout.inch, angle=layout.cardinal['right'])

    beam4 = baseplate.add_beam_path(x=3.6*layout.inch, y=7.5*layout.inch, angle=layout.cardinal['right'])

    beam5 = baseplate.add_beam_path(x=3.6*layout.inch, y=9.5*layout.inch, angle=layout.cardinal['right'])

    beam6 = baseplate.add_beam_path(x=3.6*layout.inch, y=11.5*layout.inch, angle=layout.cardinal['right'])


    
    #beam 1
    baseplate.place_element("beam1 Input Fiberport", optomech.fiberport_mount_KA05T, mount_args=dict(thumbscrews=True), 
        x=3.5*layout.inch, y = 1.5*layout.inch, angle=layout.cardinal['right'])

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam1,
                                       beam_index=0b1, distance=1.5*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam1,
                                       beam_index=0b1, distance=1*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    baseplate.place_element_along_beam("beam1 Output Fiberport", optomech.fiberport_mount_KA05T, beam1,
                                       beam_index=0b1, distance=2.5*layout.inch, angle=layout.cardinal['left'], mount_args=dict(thumbscrews=True))




    #beam 2
    baseplate.place_element("beam2 Input Fiberport", optomech.fiberport_mount_KA05T, mount_args=dict(thumbscrews=True), 
        x=3.5*layout.inch, y = 3.5*layout.inch, angle=layout.cardinal['right'])

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam2,
                                       beam_index=0b1, distance=1.5*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam2,
                                       beam_index=0b1, distance=1*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    baseplate.place_element_along_beam("beam2 Output Fiberport", optomech.fiberport_mount_KA05T, beam2,
                                       beam_index=0b1, distance=2.5*layout.inch, angle=layout.cardinal['left'], mount_args=dict(thumbscrews=True))


    #beam 3
    baseplate.place_element("beam3 Input Fiberport", optomech.fiberport_mount_KA05T, mount_args=dict(thumbscrews=True), 
        x=3.5*layout.inch, y = 5.5*layout.inch, angle=layout.cardinal['right'])

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam3,
                                       beam_index=0b1, distance=1.5*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam3,
                                       beam_index=0b1, distance=1*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    baseplate.place_element_along_beam("beam3 Output Fiberport", optomech.fiberport_mount_KA05T, beam3,
                                       beam_index=0b1, distance=2.5*layout.inch, angle=layout.cardinal['left'], mount_args=dict(thumbscrews=True))


    #beam 4
    baseplate.place_element("beam4 Input Fiberport", optomech.fiberport_mount_KA05T, mount_args=dict(thumbscrews=True), 
        x=3.5*layout.inch, y = 7.5*layout.inch, angle=layout.cardinal['right'])

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam4,
                                       beam_index=0b1, distance=1.5*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam4,
                                       beam_index=0b1, distance=1*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    baseplate.place_element_along_beam("beam4 Output Fiberport", optomech.fiberport_mount_KA05T, beam4,
                                       beam_index=0b1, distance=2.5*layout.inch, angle=layout.cardinal['left'], mount_args=dict(thumbscrews=True))


#beam 5
    baseplate.place_element("beam5 Input Fiberport", optomech.fiberport_mount_KA05T, mount_args=dict(thumbscrews=True), 
        x=3.5*layout.inch, y = 9.5*layout.inch, angle=layout.cardinal['right'])

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam5,
                                       beam_index=0b1, distance=1.5*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam5,
                                       beam_index=0b1, distance=1*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    baseplate.place_element_along_beam("beam5 Output Fiberport", optomech.fiberport_mount_KA05T, beam5,
                                       beam_index=0b1, distance=2.5*layout.inch, angle=layout.cardinal['left'], mount_args=dict(thumbscrews=True))



#beam 6
    baseplate.place_element("beam6 Input Fiberport", optomech.fiberport_mount_KA05T, mount_args=dict(thumbscrews=True), 
        x=3.5*layout.inch, y = 11.5*layout.inch, angle=layout.cardinal['right'])

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam6,
                                       beam_index=0b1, distance=1.5*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam6,
                                       beam_index=0b1, distance=1*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    baseplate.place_element_along_beam("beam6 Output Fiberport", optomech.fiberport_mount_KA05T, beam6,
                                       beam_index=0b1, distance=2.5*layout.inch, angle=layout.cardinal['left'], mount_args=dict(thumbscrews=True))










# this allows the file to be run as a macro or imported into other files
if __name__ == "__main__":
    example_baseplate()
    layout.redraw()
