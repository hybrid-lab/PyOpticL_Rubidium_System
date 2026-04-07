from PyOpticL import layout, optomech

# define baseplate constants, calculate parameters, etc.

# baseplate sizing
base_dx = 15*layout.inch #14
base_dy = 8*layout.inch
base_dz = layout.inch
gap = layout.inch/8

# x-y coordinates of mount holes (in inches)
mount_holes = [(1, 0), (12, 0), (1, 7), (12, 7)]

# y coordinate of beam input
input_y = 1.5*layout.inch
x_offset = 0*1.35*layout.inch

# define the baseplate as a function so it can be imported into other files
def example_baseplate(x=0, y=0, angle=0):
    baseplate = layout.baseplate(base_dx, base_dy, base_dz, x=x, y=y, angle=angle,
                                 gap=gap, mount_holes=mount_holes)
    beam_MOT = baseplate.add_beam_path(x=gap+layout.inch*3/4+layout.inch + x_offset, y=gap+layout.inch*3.75, angle=layout.cardinal['right'])

    # add input fiberport, defined at the same coordinates as beam
    baseplate.place_element("Input Fiberport MOT", optomech.fiberport_mount_km05T, hole_config='Y_shape',
                            x=gap+layout.inch*3/4+x_offset, y=gap+layout.inch*3.75, angle=layout.cardinal['right'], mount_args=dict(thumbscrews=True))
    
    beam_repump = baseplate.add_beam_path(x=gap+layout.inch*3/4+layout.inch+x_offset, y=gap+layout.inch, angle=layout.cardinal['right'])

    # add input fiberport, defined at the same coordinates as beam
    baseplate.place_element("Input Fiberport Repump", optomech.fiberport_mount_km05T, hole_config='two_hole',
                            x=gap + layout.inch*3/4 + x_offset, y=gap+layout.inch, angle=layout.cardinal['right'], mount_args=dict(thumbscrews=True))
    
    baseplate.place_element_along_beam("MOT Half Waveplate", optomech.waveplate, beam_MOT,
                                       beam_index=0b1, distance=layout.inch*1.5, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Mixing Cube", optomech.cube_splitter, beam_MOT,
                                       beam_index=0b1, distance=layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.skate_mount)
    
    baseplate.place_element_along_beam("SRS SR475 Shutter", optomech.shutter_sr475, beam_MOT,
                                       beam_index=0b10, distance=1.25*layout.inch, angle=layout.cardinal['right'])
    
    baseplate.place_element_along_beam("Mirror Repump Static", optomech.circular_mirror, beam_repump,
                                       beam_index=0b1, distance=2.5*layout.inch, angle=layout.turn['down-left'],
                                       mount_type=optomech.mirror_mount_M05, mount_args = dict(thumbscrews=True), adapter_type = optomech.surface_adapter)
    
    baseplate.place_element_along_beam("Repump Half Waveplate", optomech.waveplate, beam_repump,
                                       beam_index=0b1, distance=layout.inch, angle=layout.cardinal['up'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Mixing Half Waveplate", optomech.waveplate, beam_MOT,
                                       beam_index=0b10, distance=layout.inch*1.5, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("2/3 Cube", optomech.cube_splitter, beam_MOT,
                                       beam_index=0b10, distance=layout.inch*1.3, angle=layout.cardinal['up'],
                                       mount_type=optomech.skate_mount)
    
    baseplate.place_element_along_beam("Mirror 1", optomech.circular_mirror, beam_MOT,
                                       beam_index=0b101, distance=2.5*layout.inch, angle=layout.turn['down-right'],
                                       mount_type=optomech.mirror_mount_M05, mount_args=dict(thumbscrews=True),
                                       adapter_type=optomech.surface_adapter)
    
    baseplate.place_element_along_beam("Half Waveplate 1-1", optomech.waveplate, beam_MOT,
                                       beam_index=0b101, distance=layout.inch*1, angle=layout.cardinal['left'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Half Waveplate 1-2", optomech.waveplate, beam_MOT,
                                       beam_index=0b101, distance=layout.inch*1, angle=layout.cardinal['left'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Output Fiberport 1", optomech.fiberport_mount_km05T, beam_MOT, hole_config='two_hole_inverted',
                                       beam_index=0b101, distance=layout.inch*3.5, angle=layout.cardinal['left'], mount_args=dict(thumbscrews=True))
    
    baseplate.place_element_along_beam("2/3 Half Waveplate", optomech.waveplate, beam_MOT,
                                       beam_index=0b100, distance=layout.inch*1.3, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("1/2 Cube", optomech.cube_splitter, beam_MOT,
                                       beam_index=0b100, distance=layout.inch*1, angle=layout.cardinal['right'],
                                       mount_type=optomech.skate_mount)

    baseplate.place_element_along_beam("Mirror 2 Static", optomech.circular_mirror, beam_MOT,
                                beam_index=0b1000, distance=3.25*layout.inch, angle=layout.turn['down-left'],
                                mount_type=optomech.mirror_mount_FMP05)
    
    baseplate.place_element_along_beam("Mirror 2", optomech.circular_mirror, beam_MOT,
                                       beam_index=0b1000, distance=1.5*layout.inch, angle=layout.turn['up-left'],
                                       mount_type=optomech.mirror_mount_M05, mount_args=dict(thumbscrews=True),
                                       adapter_type=optomech.surface_adapter)
    
    baseplate.place_element_along_beam("Half Waveplate 2-1", optomech.waveplate, beam_MOT,
                                       beam_index=0b1000, distance=layout.inch*1, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Half Waveplate 2-2", optomech.waveplate, beam_MOT,
                                       beam_index=0b1000, distance=layout.inch*1, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Output Fiberport 2", optomech.fiberport_mount_km05T, beam_MOT, hole_config='aziza_fiber_adapter_extended',
                                       beam_index=0b1000, distance=layout.inch*2.8, angle=layout.cardinal['right'], mount_args=dict(thumbscrews=True))
#5.7
    baseplate.place_element_along_beam("Mirror 3", optomech.circular_mirror, beam_MOT,
                                       beam_index=0b1001, distance=3*layout.inch, angle=layout.turn['up-left'],
                                       mount_type=optomech.mirror_mount_M05, mount_args=dict(thumbscrews=True),
                                       adapter_type=optomech.surface_adapter)
    
    baseplate.place_element_along_beam("Half Waveplate 3-1", optomech.waveplate, beam_MOT,
                                       beam_index=0b1001, distance=layout.inch*3.4, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Half Waveplate 3-2", optomech.waveplate, beam_MOT,
                                       beam_index=0b1001, distance=layout.inch*1, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Output Fiberport 3", optomech.fiberport_mount_km05T, beam_MOT, hole_config='aziza_fiber_adapter',
                                       beam_index=0b1001, distance=layout.inch*2.5, angle=layout.cardinal['right'], mount_args=dict(thumbscrews=True))

# draw the baseplate if the file is run as a macro
if __name__ == "__main__":
    example_baseplate()
    layout.redraw()
