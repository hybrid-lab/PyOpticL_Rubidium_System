from PyOpticL import layout, optomech

# baseplate constants
base_dx = 20*layout.inch
base_dy = 15*layout.inch
base_dz = layout.inch
gap = layout.inch/8

mount_holes = [(3, 0), (0, 14), (17, 0), (17, 14)]

input_y = 7*layout.inch

def post_TA_baseplate(x=0, y=0, angle=0):

    baseplate = layout.baseplate(base_dx, base_dy, base_dz, x=x, y=y, angle=angle, gap=gap, mount_holes=mount_holes)

    beam = baseplate.add_beam_path(x=4*layout.inch, y=2*layout.inch, angle=layout.cardinal['left'])

    baseplate.place_element("Input Fiberport", optomech.fiberport_mount_km05T, x=4.5*layout.inch, y=2*layout.inch, angle=layout.cardinal['left'], mount_args=dict(thumbscrews=True))

    baseplate.place_element_along_beam("1/4 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b1, distance=1.5*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)

    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, beam,
                                       beam_index=0b1, distance=1*layout.inch, angle=layout.turn['down-right'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))

    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b1, distance=4.25*layout.inch, angle=layout.cardinal['up'],
                                       mount_type=optomech.rotation_stage_rsp05)

    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, beam, beam_index=0b1, distance=2.25  *layout.inch, angle=layout.turn['up-right'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))
    
    baseplate.place_element_along_beam("Beam Splitter Cube", optomech.cube_splitter, beam,
                                       beam_index=0b1, distance=1*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.skate_mount, invert=True)
    
    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, beam,
                                       beam_index=0b11, distance=3.5*layout.inch, angle=layout.turn['down-right'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))
    
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b11, distance=1*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Lens f50mm AB coat", optomech.circular_lens, beam,
                                         beam_index=0b11, distance=0.75*layout.inch, angle=layout.cardinal['left'],
                                         focal_length=50, part_number='LA1213-AB', mount_type=optomech.lens_holder_l05g)
    
    aom_1=baseplate.place_element_along_beam("AOM", optomech.AOMO_3100_125, beam,
                                       beam_index=0b11, distance=50, angle=layout.cardinal['left'],
                                       forward_direction=-1, backward_direction=1, diffraction_angle=0)
    
    baseplate.place_element_along_beam("Lens f50mm AB coat", optomech.circular_lens, beam,
                                         beam_index=0b111, distance=50, angle=layout.cardinal['left'],
                                         focal_length=50, part_number='LA1213-AB', mount_type=optomech.lens_holder_l05g)

    baseplate.place_element_along_beam("SRS SR475 Shutter", optomech.shutter_sr475, beam,
                                       beam_index=0b111, distance=1.75*layout.inch, angle=layout.cardinal['left'])

    baseplate.place_element_along_beam("Iris", optomech.pinhole_ida12, beam,
                                       beam_index=0b110, distance=5*layout.inch, angle=layout.cardinal['left'])

    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b110, distance=1.25*layout.inch, angle=layout.cardinal['left'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Beam Splitter Cube", optomech.cube_splitter, beam,
                                       beam_index=0b110, distance=1*layout.inch, angle=layout.cardinal['left'],
                                       mount_type=optomech.skate_mount, invert=True)
    
    baseplate.place_element_along_beam("Output Fiberport", optomech.fiberport_mount_km05T, beam,
                                       beam_index=0b1100, distance=2.5*layout.inch, angle=layout.cardinal['left'],
                                       mount_args=dict(thumbscrews=True))
    



    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam, beam_index=0b10, distance=1*layout.inch, angle=layout.cardinal['left'],
                                       mount_type=optomech.rotation_stage_rsp05)

    baseplate.place_element_along_beam("Beam Splitter Cube", optomech.cube_splitter, beam,
                                       beam_index=0b10, distance=0.875*layout.inch, angle=layout.cardinal['left'],
                                       mount_type=optomech.skate_mount)
    


    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, beam,
                                       beam_index=0b101, distance=4.25*layout.inch, angle=layout.turn['up-right'],
                                       mount_type=optomech.mirror_mount_M05)

    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b101, distance=1*layout.inch, angle=layout.cardinal['left'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Lens f50mm AB coat", optomech.circular_lens, beam,
                                         beam_index=0b101, distance=1.25*layout.inch, angle=layout.cardinal['left'],
                                         focal_length=50, part_number='LA1213-AB', mount_type=optomech.lens_holder_l05g)
    
    aom_1=baseplate.place_element_along_beam("AOM", optomech.AOMO_3100_125, beam,
                                       beam_index=0b101, distance=50, angle=layout.cardinal['left'],
                                       forward_direction=-1, backward_direction=1, diffraction_angle=0)
    
    baseplate.place_element_along_beam("Lens f50mm AB coat", optomech.circular_lens, beam,
                                         beam_index=0b1011, distance=50, angle=layout.cardinal['left'],
                                         focal_length=50, part_number='LA1213-AB', mount_type=optomech.lens_holder_l05g)

    baseplate.place_element_along_beam("SRS SR475 Shutter", optomech.shutter_sr475, beam,
                                       beam_index=0b1011, distance=1.75*layout.inch, angle=layout.cardinal['left'])

    baseplate.place_element_along_beam("Iris", optomech.pinhole_ida12, beam,
                                       beam_index=0b1010, distance=4.75*layout.inch, angle=layout.cardinal['left'])
    
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b1010, distance=.75*layout.inch, angle=layout.cardinal['left'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Beam Splitter Cube", optomech.cube_splitter, beam,
                                       beam_index=0b1010, distance=.875*layout.inch, angle=layout.cardinal['left'],
                                       mount_type=optomech.skate_mount, invert=True)
    
    baseplate.place_element_along_beam("Output Fiberport", optomech.fiberport_mount_km05T, beam,
                                       beam_index=0b10100, distance=2.5*layout.inch, angle=layout.cardinal['left'],
                                       mount_args=dict(thumbscrews=True))
    

    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam, beam_index=0b100, distance=1*layout.inch, angle=layout.cardinal['left'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Lens f50mm AB coat", optomech.circular_lens, beam,
                                         beam_index=0b100, distance=1.25*layout.inch, angle=layout.cardinal['left'],
                                         focal_length=50, part_number='LA1213-AB', mount_type=optomech.lens_holder_l05g)
    
    aom_1=baseplate.place_element_along_beam("AOM", optomech.AOMO_3100_125, beam,
                                       beam_index=0b100, distance=50, angle=layout.cardinal['left'],
                                       forward_direction=-1, backward_direction=1, diffraction_angle=0)
    
    baseplate.place_element_along_beam("Lens f50mm AB coat", optomech.circular_lens, beam,
                                         beam_index=0b1001, distance=50, angle=layout.cardinal['left'],
                                         focal_length=50, part_number='LA1213-AB', mount_type=optomech.lens_holder_l05g)

    baseplate.place_element_along_beam("SRS SR475 Shutter", optomech.shutter_sr475, beam,
                                       beam_index=0b1001, distance=1.75*layout.inch, angle=layout.cardinal['left'])

    baseplate.place_element_along_beam("Iris", optomech.pinhole_ida12, beam,
                                       beam_index=0b1000, distance=4.75*layout.inch, angle=layout.cardinal['left'])
    
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b1000, distance=.75*layout.inch, angle=layout.cardinal['left'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Beam Splitter Cube", optomech.cube_splitter, beam,
                                       beam_index=0b1000, distance=.875*layout.inch, angle=layout.cardinal['left'],
                                       mount_type=optomech.skate_mount, invert=True)
    
    baseplate.place_element_along_beam("Output Fiberport", optomech.fiberport_mount_km05T, beam,
                                       beam_index=0b10000, distance=2.5*layout.inch, angle=layout.cardinal['left'],
                                       mount_args=dict(thumbscrews=True))
    

if __name__ == "__main__":
    post_TA_baseplate()
    layout.redraw()