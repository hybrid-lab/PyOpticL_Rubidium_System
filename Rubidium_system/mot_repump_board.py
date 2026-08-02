from PyOpticL import layout, optomech

# define baseplate constants, calculate parameters, etc.

# baseplate sizing
base_dx = 15*layout.inch #14
base_dy = 8*layout.inch
base_dz = layout.inch
gap = layout.inch/8

# x-y coordinates of mount holes (in inches)
mount_holes = [(3, 0), (13, 0), (2, 7), (12, 7)]

# y coordinate of beam input
input_y = 1.5*layout.inch
x_offset = 0.5*layout.inch


def add_relative_fiberport_holes(baseplate, name, fiberport, angle, distance=30):
    """Add a board-only hole pair behind a fiberport adapter lip."""
    x_offset = 9.7 + distance
    if angle == layout.cardinal['right']:
        x_offset = -x_offset
    baseplate.place_element_relative(
        f"{name} Rear Hole Left", optomech.tapped_8_32_hole, fiberport,
        angle=0, x_off=x_offset, y_off=9.164,
    )
    baseplate.place_element_relative(
        f"{name} Rear Hole Right", optomech.tapped_8_32_hole, fiberport,
        angle=0, x_off=x_offset, y_off=-9.164,
    )

# define the baseplate as a function so it can be imported into other files
def example_baseplate(x=0, y=0, angle=0):
    baseplate = layout.baseplate(base_dx, base_dy, base_dz, x=x, y=y, angle=angle,
                                 gap=gap, mount_holes=mount_holes)
    beam_MOT = baseplate.add_beam_path(x=gap+layout.inch+layout.inch + x_offset, y=gap+layout.inch*4.6, angle=layout.cardinal['right'])

    # add input fiberport, defined at the same coordinates as beam
    baseplate.place_element("Input Fiberport MOT", optomech.fiberport_mount_km05T,
                            x=gap+layout.inch+x_offset*1.25, y=gap+layout.inch*4.6, angle=layout.cardinal['right'], mount_args=dict(thumbscrews=True))

    # Board-only 8-32 hole pair, 25 mm behind the first input fiberport.
    input_mot_x = gap+layout.inch+x_offset*1.25
    input_mot_y = gap+layout.inch*4.6
    baseplate.place_element(
        "Input Fiberport MOT Rear Hole Left",
        optomech.tapped_8_32_hole,
        x=input_mot_x-9.7-28,
        y=input_mot_y+9.164,
        angle=0,
    )
    baseplate.place_element(
        "Input Fiberport MOT Rear Hole Right",
        optomech.tapped_8_32_hole,
        x=input_mot_x-9.7-28,
        y=input_mot_y-9.164,
        angle=0,
    )
    
    beam_repump = baseplate.add_beam_path(x=gap+layout.inch+layout.inch+x_offset, y=gap+layout.inch*2.4, angle=layout.cardinal['right'])

    # add input fiberport, defined at the same coordinates as beam
    baseplate.place_element("Input Fiberport Repump", optomech.fiberport_mount_km05T,
                            x=gap + layout.inch*1.25 + x_offset, y=gap+layout.inch*2.4, angle=layout.cardinal['right'], mount_args=dict(thumbscrews=True))
    input_repump_x = gap + layout.inch*1.25 + x_offset
    input_repump_y = gap+layout.inch*2.4
    baseplate.place_element(
        "Input Fiberport Repump Rear Hole Left",
        optomech.tapped_8_32_hole,
        x=input_repump_x-9.7-30,
        y=input_repump_y+9.164,
        angle=0,
    )
    baseplate.place_element(
        "Input Fiberport Repump Rear Hole Right",
        optomech.tapped_8_32_hole,
        x=input_repump_x-9.7-30,
        y=input_repump_y-9.164,
        angle=0,
    )
    
    baseplate.place_element_along_beam("MOT Half Waveplate", optomech.waveplate, beam_MOT,
                                       beam_index=0b1, distance=layout.inch*1, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Mixing Cube", optomech.cube_splitter, beam_MOT,
                                       beam_index=0b1, distance=0.9*layout.inch, angle=layout.cardinal['right'],
                                       mount_type=optomech.skate_mount)
    
    baseplate.place_element_along_beam("SRS SR475 Shutter", optomech.shutter_sr475, beam_MOT,
                                       beam_index=0b10, distance=1.15*layout.inch, angle=layout.cardinal['right'])
    
    baseplate.place_element_along_beam("Mirror Repump Static", optomech.circular_mirror, beam_repump,
                                       beam_index=0b1, distance=1.9*layout.inch, angle=layout.turn['down-left'],
                                       mount_type=optomech.mirror_mount_M05, mount_args = dict(thumbscrews=True), adapter_type = optomech.surface_adapter)
    
    baseplate.place_element_along_beam("Repump Half Waveplate", optomech.waveplate, beam_repump,
                                       beam_index=0b1, distance=.75*layout.inch, angle=layout.cardinal['up'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Mixing Half Waveplate", optomech.waveplate, beam_MOT,
                                       beam_index=0b10, distance=layout.inch*1.5, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("2/3 Cube", optomech.cube_splitter, beam_MOT,
                                       beam_index=0b10, distance=layout.inch*1.4, angle=layout.cardinal['up'],
                                       mount_type=optomech.skate_mount)
#add something for the last 1/4 of light that would otherwise be dumped
    baseplate.place_element_along_beam("Half Waveplate", optomech.waveplate, beam_MOT,
                                       beam_index=0b101, distance=layout.inch*.9, angle=layout.cardinal['up'],
                                       mount_type=optomech.rotation_stage_rsp05)
    baseplate.place_element_along_beam("Cube", optomech.cube_splitter, beam_MOT,
                                       beam_index=0b101, distance=layout.inch*0.8, angle=layout.cardinal['up'],
                                       mount_type=optomech.skate_mount)

    baseplate.place_element_along_beam("Mirror Static", optomech.circular_mirror, beam_MOT,
                                beam_index=0b1011, distance=5.5*layout.inch, angle=layout.turn['up-left'],
                                mount_type=optomech.mirror_mount_FMP05)
    
    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, beam_MOT,
                                       beam_index=0b1011, distance=2 *layout.inch, angle=layout.turn['down-left'],
                                       mount_type=optomech.mirror_mount_M05, mount_args=dict(thumbscrews=True),
                                       adapter_type=optomech.surface_adapter)
    
    baseplate.place_element_along_beam("Half Waveplate", optomech.waveplate, beam_MOT,
                                       beam_index=0b1011, distance=layout.inch*1.6, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Half Waveplate", optomech.waveplate, beam_MOT,
                                       beam_index=0b1011, distance=layout.inch*.9, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Output Fiberport", optomech.fiberport_mount_km05T, beam_MOT,
                                       beam_index=0b1011, distance=layout.inch*8.5, angle=layout.cardinal['right'], mount_args=dict(thumbscrews=True),adapter_args=dict(
        rear_pair_43=True,
        rear_pair_63=False,
        rear_pair_73=False,))


#back to coupling the original 3 outputs
    baseplate.place_element_along_beam("Mirror 1", optomech.circular_mirror, beam_MOT,
                                       beam_index=0b1010, distance=.9*layout.inch, angle=layout.turn['down-right'],
                                       mount_type=optomech.mirror_mount_M05, mount_args=dict(thumbscrews=True),
                                       adapter_type=optomech.surface_adapter)
    
    baseplate.place_element_along_beam("Half Waveplate 1-1", optomech.waveplate, beam_MOT,
                                       beam_index=0b1010, distance=layout.inch*1.2, angle=layout.cardinal['left'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Half Waveplate 1-2", optomech.waveplate, beam_MOT,
                                       beam_index=0b1010, distance=layout.inch*.9, angle=layout.cardinal['left'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    output_fiberport_1 = baseplate.place_element_along_beam("Output Fiberport 1", optomech.fiberport_mount_km05T, beam_MOT,
                                       beam_index=0b1010, distance=layout.inch*2.5, angle=layout.cardinal['left'], mount_args=dict(thumbscrews=True))
    add_relative_fiberport_holes(baseplate, "Output Fiberport 1", output_fiberport_1,
                                 layout.cardinal['left'])
    
    baseplate.place_element_along_beam("2/3 Half Waveplate", optomech.waveplate, beam_MOT,
                                       beam_index=0b100, distance=layout.inch*1.3, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("1/2 Cube", optomech.cube_splitter, beam_MOT,
                                       beam_index=0b100, distance=layout.inch*.9, angle=layout.cardinal['right'],
                                       mount_type=optomech.skate_mount)

    baseplate.place_element_along_beam("Mirror 2 Static", optomech.circular_mirror, beam_MOT,
                                beam_index=0b1000, distance=3*layout.inch, angle=layout.turn['down-left'],
                                mount_type=optomech.mirror_mount_FMP05)
    
    baseplate.place_element_along_beam("Mirror 2", optomech.circular_mirror, beam_MOT,
                                       beam_index=0b1000, distance=1.4*layout.inch, angle=layout.turn['up-left'],
                                       mount_type=optomech.mirror_mount_M05, mount_args=dict(thumbscrews=True),
                                       adapter_type=optomech.surface_adapter)
    
    baseplate.place_element_along_beam("Half Waveplate 2-1", optomech.waveplate, beam_MOT,
                                       beam_index=0b1000, distance=layout.inch*0.8, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Half Waveplate 2-2", optomech.waveplate, beam_MOT,
                                       beam_index=0b1000, distance=layout.inch*1, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    output_fiberport_2 = baseplate.place_element_along_beam("Output Fiberport 2", optomech.fiberport_mount_km05T, beam_MOT,
                                       beam_index=0b1000, distance=layout.inch*2.8, angle=layout.cardinal['right'], mount_args=dict(thumbscrews=True),adapter_args=dict(
        rear_pair_43=False,
        rear_pair_63=False,
        rear_pair_73=False,))
    add_relative_fiberport_holes(baseplate, "Output Fiberport 2", output_fiberport_2,
                                 layout.cardinal['right'], distance=140)
#5.7
    baseplate.place_element_along_beam("Mirror 3", optomech.circular_mirror, beam_MOT,
                                       beam_index=0b1001, distance=2.2*layout.inch, angle=layout.turn['up-left'],
                                       mount_type=optomech.mirror_mount_M05, mount_args=dict(thumbscrews=True),
                                       adapter_type=optomech.surface_adapter)
    
    baseplate.place_element_along_beam("Half Waveplate 3-1", optomech.waveplate, beam_MOT,
                                       beam_index=0b1001, distance=layout.inch*3.5, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    baseplate.place_element_along_beam("Half Waveplate 3-2", optomech.waveplate, beam_MOT,
                                       beam_index=0b1001, distance=layout.inch*2.9, angle=layout.cardinal['right'],
                                       mount_type=optomech.rotation_stage_rsp05)
    
    output_fiberport_3 = baseplate.place_element_along_beam("Output Fiberport 3", optomech.fiberport_mount_km05T, beam_MOT,
                                       beam_index=0b1001, distance=layout.inch*2.5, angle=layout.cardinal['right'], mount_args=dict(thumbscrews=True))
    add_relative_fiberport_holes(baseplate, "Output Fiberport 3", output_fiberport_3,
                                 layout.cardinal['right'])

# draw the baseplate if the file is run as a macro
if __name__ == "__main__":
    example_baseplate()
    layout.redraw()
