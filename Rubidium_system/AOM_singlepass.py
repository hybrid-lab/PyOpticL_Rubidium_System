from PyOpticL import layout, optomech
from datetime import datetime


def doublepass_f100(x=0, y=0, angle=0, mirror=optomech.mirror_mount_km05, x_split=False, thumbscrews=True):
    
    # Adding name and date to keep a track of the updates
    name = "Singlepass"
    date_time = datetime.now().strftime("%m/%d/%Y")
    label = ''

    # Dimension of the baseplate
    dx = 11
    dy = 5.3
    base_dx = dx*layout.inch
    base_dy = dy*layout.inch
    base_dz = layout.inch
    gap = layout.inch/8

    input_x = 3.7*layout.inch
    input_y = 1.15*layout.inch

    mount_holes = [(0, 0),  (dx-1, dy-1), (0, dy-1), (dx-1,0)]
    extra_mount_holes = []

    # Difining the baseplate
    baseplate = layout.baseplate(base_dx, base_dy, base_dz, x=x, y=y, angle=angle,
                                 gap=gap, mount_holes=mount_holes+extra_mount_holes,
                                 name=name, label=label, x_splits=[4*layout.inch]*x_split)


    
    # Adding the beam to the baseplate
    # baseplate.place_element("Input Fiberport", optomech.mirror_mount_km05,
    #                                 x=input_x, y=input_y, angle=layout.cardinal['right'])

    baseplate.place_element("Input Fiberport", optomech.fiberport_mount_KA05T, x=3.2*layout.inch, y=input_y, angle=layout.cardinal['right'], 
                                        Fiber_Clamp="V1", mount_args=dict(thumbscrews=True))
    
    beam = baseplate.add_beam_path(x=input_x, y=input_y, angle=layout.cardinal['right'])    

    # Adding a waveplate to control the ploarization
    baseplate.place_element_along_beam("Half waveplate", optomech.waveplate, beam,
                                       beam_index=0b1, distance=1.4*layout.inch, angle=layout.cardinal['left'],
                                       mount_type=optomech.rotation_stage_rsp05)


    # # Adding AOM
    # crystal = baseplate.place_element_along_beam("AOM", optomech.isomet_1205c_on_km100pm, beam,
    #                                 beam_index=0b10, distance = 1.25*layout.inch, angle=layout.cardinal['left'],
    #                                 forward_direction=-1, backward_direction=1)
    # Adding AOM
    surface_adapter_args= dict(adapter_height=5)
    crystal = baseplate.place_element_along_beam("AOM", optomech.AOMO_3100_125, beam,
                                       beam_index=0b1, distance=1.1*layout.inch, angle=layout.cardinal['left'], Fiber_Clamp=False, 
                                       forward_direction=-1, backward_direction=1, diffraction_angle = 1.06, surface_adapter_args=surface_adapter_args,) #422*1e-9 / 0.0002) 0.01
    # diffraction angle is roughtly wavelength_of_light/wavelength_of_sound
    # wavelength of sound is estimated in 20c in quartz
    # but it is usually quite small



    # Adding lens to collimate the 1st-order AOM output
    # lens = baseplate.place_element_along_beam(
    #     "Lens f50mm AB coat", optomech.circular_lens, beam,
    #     beam_index=0b10, distance=75,
    #     angle=layout.cardinal['right']- crystal.DiffractionAngle.Value,
    #     focal_length=75, part_number='LA1213-AB',
    #     mount_type=optomech.lens_holder_l05g
    # )

    # add mirror along the transmitted beam, mounted in a fmp05 mount
    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, beam,
                                       beam_index=0b11, distance=3*layout.inch, angle=layout.turn['right-up'],
                                       mount_type=optomech.mirror_mount_FMP05)



    baseplate.place_element_along_beam("Mirror", optomech.circular_mirror, beam,
                                       beam_index=0b11, distance=2.5*layout.inch, angle=layout.turn['up-left'],
                                       mount_type=optomech.mirror_mount_M05,
                                       mount_args=dict(thumbscrews=True))



        # # Adding Iris to select the beam of right order

    baseplate.place_element_along_beam("Half waveplate", optomech.waveplate, beam,
                                    beam_index=0b11, distance=1*layout.inch, angle=layout.cardinal['right'],
                                    mount_type=optomech.rotation_stage_rsp05)

    baseplate.place_element_along_beam("Half waveplate", optomech.waveplate, beam,
                                    beam_index=0b11, distance=1*layout.inch, angle=layout.cardinal['right'],
                                    mount_type=optomech.rotation_stage_rsp05)


    baseplate.place_element_along_beam("Iris", optomech.pinhole_ida12, beam,
                                       beam_index=0b11, distance=1.5*layout.inch, angle=layout.cardinal['left'])  
    
    
    baseplate.place_element_along_beam("Output Fiberport", optomech.fiberport_mount_KA05T, beam, 
                                    beam_index=0b11, distance=2.5*layout.inch, angle=layout.cardinal['right'], 
                                    Fiber_Clamp=True, mount_args=dict(thumbscrews=True))
    


if __name__ == "__main__":
    doublepass_f100()  # changne the f__ depending on which lens you want
    # doublepass_f100(y = 6)
    layout.redraw()