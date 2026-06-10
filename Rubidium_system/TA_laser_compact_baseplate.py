from PyOpticL import layout, optomech

# baseplate constants
base_dx = 15*layout.inch
base_dy = 11.25*layout.inch
base_dz = layout.inch
gap = layout.inch/8

# x-y coordinates of mount holes (in inches) (x,y)
mount_holes = [(0, 0), (5, 10), (14, 0), (14, 10)]

# y coordinate of beam input
# input_y = 6.00*layout.inch
# input_x = 3.385*layout.inch
input_y = 7.75*layout.inch
input_x = 2.75*layout.inch

# function so baseplate can be added to other layouts
def example_baseplate(x=0, y=0, angle=0):

    # define and place baseplate object
    baseplate = layout.baseplate(base_dx, base_dy, base_dz, x=x, y=y, angle=angle,
                                 gap=gap, mount_holes=mount_holes)

    # add beam
    beam = baseplate.add_beam_path(x=input_x, y=input_y, angle=layout.cardinal['down'])

    baseplate.place_element("TA", optomech.TA_butterfly, x=input_x, y=input_y, angle=270)

    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror_union_optic, beam,
                                   beam_index=0b1, distance=2*layout.inch, angle=layout.turn['down-right'],
                                   mount_type=optomech.mirror_mount_M05X,
                                   mount_args=dict(thumbscrews=True))

    # # add waveplate along the transmitted beam, 1" after the laser, mounted in a rotation stage
    # baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam,
    #                                    beam_index=0b1, distance=1*layout.inch, angle=layout.cardinal['right'],
    #                                    mount_type=optomech.rotation_stage_rsp05)

    #Adding the isolator to make sure there is no unwanted beam going back as feedback
    baseplate.place_element_along_beam("Optical_Isolator", optomech.isolator_780_mp, beam,
                                       beam_index=0b1, distance=2.95*layout.inch, angle=layout.cardinal['left'])


    # baseplate.place_element_along_beam("1/4 Waveplate", optomech.waveplate, beam,
    #                                    beam_index=0b1, distance=2.9*layout.inch, angle=layout.cardinal['right'],
    #                                    mount_type=optomech.rotation_stage_rsp05)

    # add waveplate along the beam, 1/2" before the PBS , mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b1, distance=2.9*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # add splitter component along beam
    baseplate.place_element_along_beam("Beam Splitter Cube", optomech.cube_splitter, beam,
                                       beam_index=0b1, distance=1*layout.inch, angle=layout.cardinal['right'],
                                       invert = True, mount_type=optomech.cube_mount_halfinch)




    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror_union_optic, beam,
                                       beam_index=0b11, distance=2*layout.inch, angle=layout.turn['down-left'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))

        # add waveplate along the reflected beam, mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b11, distance=0.9*layout.inch, angle=layout.cardinal['left'],
                                       mount_type=optomech.rotation_stage_rsp05)

    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b11, distance=1.0*layout.inch, angle=layout.cardinal['left'],
                                       mount_type=optomech.rotation_stage_rsp05)

    # # add output fiberport along the second beam (replaced km05T by KA05T)
    #baseplate.place_element_along_beam("Output Fiberport", optomech.fiberport_mount_km05T, beam,
    #                                   beam_index=0b11, distance=2.5*layout.inch, angle=layout.cardinal['right'],
    #                                   mount_args=dict(thumbscrews=True))
    baseplate.place_element_along_beam("Output Fiberport", optomech.fiberport_mount_KA05T, beam,
                                       beam_index=0b11, distance=4.4*layout.inch, angle=layout.cardinal['right'],
                                       mount_args=dict(thumbscrews=True))

    # # Adding lens pair make collimated beam. Lens 1
    # baseplate.place_element_along_beam("Lens f212mm B coat", optomech.circular_lens, beam,
    #                                      beam_index=0b10, distance=0.5*layout.inch, angle=layout.cardinal['left'],
    #                                      focal_length=150, part_number='AC127-050-B', mount_type=optomech.lens_holder_l05g)

    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror_union_optic, beam,
                                       beam_index=0b10, distance=2.5*layout.inch, angle=layout.turn['up-left'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))

    # Adding AOM
    surface_adapter_args= dict(adapter_height=5)
    aom = baseplate.place_element_along_beam("AOM", optomech.AOMO_3100_125, beam,
                                       beam_index=0b10, distance=1*layout.inch, angle=layout.cardinal['up'],
                                       forward_direction=-1, backward_direction=1, diffraction_angle = 0, surface_adapter_args=surface_adapter_args) #422*1e-9 / 0.0002) 0.01
    # diffraction angle is roughtly wavelength_of_light/wavelength_of_sound
    # wavelength of sound is estimated in 20c in quartz
    # but it is usually quite small

    # add mirror along the transmitted beam, mounted in a m05 mount
    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror_union_optic, beam,
                                       beam_index=0b101, distance=3*layout.inch, angle=layout.turn['down-left'] + aom.DiffractionAngle.Value,
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))
    
    # Lens 2
    # add mirror along the transmitted beam, mounted in a m05 mount
    # lens = baseplate.place_element_along_beam("Lens f212mm B coat", optomech.circular_lens, beam,
    #                                      beam_index=0b101, distance=150-3*layout.inch, angle=layout.cardinal['left'] + aom.DiffractionAngle.Value,
    #                                      focal_length=150, part_number='AC127-075-B', mount_type=optomech.lens_holder_l05g)    
    
    # add waveplate along the transmitted beam, mounted in a rotation stage
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b101, distance=1.5*layout.inch, angle=layout.cardinal['left'],
                                       mount_type=optomech.rotation_stage_rsp05)

    baseplate.place_element_along_beam("Iris", optomech.pinhole_ida12, beam,
                                       beam_index=0b100, distance=8.25*layout.inch, angle=layout.cardinal['left'])
    
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b101, distance=1.25*layout.inch, angle=layout.cardinal['left'],
                                       mount_type=optomech.rotation_stage_rsp05)

    baseplate.place_element_along_beam("SRS SR475 Shutter", optomech.shutter_sr475, beam,
                                       beam_index=0b101, distance=4*layout.inch, angle=layout.cardinal['right'])


    # add output fiberport along the transmitted beam (replaced km05T by KA05T)
    #baseplate.place_element_along_beam("Output Fiberport", optomech.fiberport_mount_km05T, beam,
    #                                   beam_index=0b101, distance=2.5*layout.inch, angle=layout.cardinal['right'],
    #                                   mount_args=dict(thumbscrews=True))    
    baseplate.place_element_along_beam("Output Fiberport", optomech.fiberport_mount_KA05T, beam,
                                       beam_index=0b101, distance=2.0*layout.inch, angle=layout.cardinal['right'],
                                       mount_args=dict(thumbscrews=True))

if __name__ == "__main__":
    example_baseplate()
    layout.redraw()
