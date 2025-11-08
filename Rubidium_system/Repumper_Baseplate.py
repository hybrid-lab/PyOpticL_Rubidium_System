from PyOpticL import layout, optomech

# baseplate constants
base_dx = 26*layout.inch
base_dy = 6*layout.inch
base_dz = layout.inch
gap = layout.inch/8

mount_holes = [(3, 0), (3, 5), (22, 1), (23, 5),  (15, 0), (13, 5), (25, 2)]

def Split_baseplate(x=0, y=0, angle=0):
    baseplate = layout.baseplate(base_dx, base_dy, base_dz, x=x, y=y, angle=angle, gap=gap, mount_holes=mount_holes)

    beam = baseplate.add_beam_path(x=4*layout.inch, y=1.7*layout.inch, angle=layout.cardinal['left'])

    baseplate.place_element("Input Fiberport", optomech.fiberport_mount_km05T, x=4.75*layout.inch, y=1.7*layout.inch, angle=layout.cardinal['left'], mount_args=dict(thumbscrews=True))

    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, beam,
                                       beam_index=0b1, distance=2.75*layout.inch, angle=layout.turn['down-right'],
                                       mount_type=optomech.mirror_mount_FMP05)

    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b1, distance=0.9*layout.inch, angle=layout.cardinal['up'],
                                       mount_type=optomech.rotation_stage_rsp05)

    baseplate.place_element_along_beam("Beam Splitter Cube", optomech.cube_splitter, beam,
                                       beam_index=0b1, distance=1*layout.inch, angle=layout.cardinal['down'],
                                       mount_type=optomech.skate_mount, invert=True)

    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, beam,
                                       beam_index=0b10, distance=1.2*layout.inch, angle=layout.turn['up-right'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))

    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, beam,
                                       beam_index=0b10, distance=1*layout.inch, angle=layout.turn['down-left'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))
    
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b11, distance=3.25*layout.inch, angle=layout.cardinal['left'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Lens f150mm AB coat", optomech.circular_lens, beam,
                                         beam_index=0b11, distance=0.75*layout.inch, angle=layout.cardinal['left'],
                                         focal_length=125, part_number='LA4004-AB', mount_type=optomech.lens_holder_l05g)

    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, beam,
                                       beam_index=0b11, distance=3.2*layout.inch, angle=layout.turn['up-left'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))
    
    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, beam,
                                       beam_index=0b11, distance=1.6*layout.inch, angle=layout.turn['down-right'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))

    aom = baseplate.place_element_along_beam("AOM", optomech.AOMO_3100_125, beam,
                                       beam_index=0b11, distance=150-4.8*layout.inch, angle=layout.cardinal['left'],
                                       forward_direction=-1, backward_direction=1, diffraction_angle = 0)
    
    baseplate.place_element_along_beam("Lens f150mm AB coat", optomech.circular_lens, beam,
                                         beam_index=0b111, distance=150, angle=layout.cardinal['left'],
                                         focal_length=125, part_number='LA4004-AB', mount_type=optomech.lens_holder_l05g)

    baseplate.place_element_along_beam("SRS SR475 Shutter", optomech.shutter_sr475, beam,
                                       beam_index=0b111, distance=1.8*layout.inch, angle=layout.cardinal['left'])
    
    baseplate.place_element_along_beam("Iris", optomech.pinhole_ida12, beam,
                                       beam_index=0b110, distance=5.5*layout.inch, angle=layout.cardinal['left'])

    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, beam,
                                       beam_index=0b110, distance=3.5*layout.inch, angle=layout.turn['down-left'],
                                       mount_type=optomech.mirror_mount_FMP05)

    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, beam,
                                       beam_index=0b110, distance=1.5*layout.inch, angle=layout.turn['up-right'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))

    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b110, distance=1*layout.inch, angle=layout.cardinal['left'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("1/2 Waveplate", optomech.waveplate, beam,
                                       beam_index=0b110, distance=1*layout.inch, angle=layout.cardinal['left'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Output Fiberport", optomech.fiberport_mount_km05T, beam,
                                       beam_index=0b110, distance=2.5*layout.inch, angle=layout.cardinal['left'],
                                       mount_args=dict(thumbscrews=True))
    
if __name__ == "__main__":
    Split_baseplate()
    layout.redraw()
