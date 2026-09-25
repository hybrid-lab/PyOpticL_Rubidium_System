"""AOM double-pass baseplate V9 - 17 x 6 in, 795 nm cat-eye with f = 75 mm.

Beam order, read top to bottom in example_baseplate():

    input KA05T -> HWP -> separation PBS -> AOM (integral seat)
                -> LA1612-B cat-eye lens -> QWP -> order iris -> retro mirror
    return      -> separation PBS -> output steering mirror (74 mm above the
                   input line) -> HWP -> rotating PBS -> iris -> output KA05T

Derived from the group's reference AOM_doublepass.py (13 x 5 in). What changed:

* Lens: Thorlabs LA1612-B (1/2", f = 75.0 mm, R = 38.8 mm, tc = 2.5 mm) in a
  POLARIS-L05G, replacing an f = 50 mm lens that had been placed as if it were
  75 mm. Same lens and holder as the lattice board's double-pass arms.
* Spacing uses the 795 nm focal length and the plano-convex principal planes
  (curved face toward the AOM, plane face toward the mirror):
      EFL(795) = R / (n - 1) = 38.8 / 0.51088   = 75.95 mm
      AOM centre -> lens centre = EFL + tc/2    = 77.20 mm
      lens centre -> mirror     = EFL - tc/n + tc/2 = 75.55 mm
  The QWP follows the lens at 30 mm as on the lattice arms; the
  order-selection iris sits 10 mm in front of the retro mirror face, i.e. at
  the cat-eye focal plane.
* AOM seat: the integral seat machined into the plate. The reference's 86 mm
  surface adapter does not fit a 5 in plate at its beam height. The beam line
  is raised from 1.15 in to 1.4 in so the seat's knob pocket keeps a 7 mm wall
  to the plate edge. The RF SMB connector is on the face away from the beam;
  40 mm of free space is reserved for the L-shaped elbow.
* Return line 74 mm above the beam line (reference 67.3 mm): the return beam
  must clear the 40 mm RF elbow space and the RSP05 adapter pockets must clear
  the AOM seat pocket. Output chain: mirror -> HWP 55 mm -> rotating PBS 22 mm
  -> iris 31 mm -> fiber face 42.35 mm (the lattice output geometry).
* Plate 13 x 5 in -> 17 x 6 in, 1 in thick: 0.85 in added at the input end so
  the KA05T's rear tail-clamp holes stay inside the outline, the rest at the
  retro end for the longer cat-eye and output chain.
* Table holes keep the reference pattern (0.6, 0), (11, 4), (0, 4) in, shifted
  0.2 in along the plate so each bolt's access disk clears both fiber ports.

Known note: the return beam passes 4.7 mm beside the axis of table bolt
(11.2, 4), i.e. over its recessed head. The hole-clearance audit records this
as a platform crossing rather than a conflict; moving the bolt row or the
return line would need a 7 in plate.

Run in FreeCAD (Macro > Macros..., or paste into the Python console):
    example_baseplate()
"""
import math

import FreeCAD as App
import Part

from PyOpticL import layout, optomech

# baseplate constants
base_dx = 17*layout.inch
base_dy = 6*layout.inch
base_dz = layout.inch
gap = layout.inch/8

# table holes: the reference pattern shifted 0.2 in along the plate
HOLE_PATTERN_SHIFT = 0.2
mount_holes = [(0.6+HOLE_PATTERN_SHIFT, 0), (11+HOLE_PATTERN_SHIFT, 4), (0+HOLE_PATTERN_SHIFT, 4)]

IN_SHIFT = 0.85*layout.inch      # added at the input end
BEAM_Y = 1.4*layout.inch         # 35.56
RETURN_OFFSET = 74.
RETURN_Y = BEAM_Y + RETURN_OFFSET                          # 109.56

N_BK7_795 = 1.51088
LENS = 'LA1612-B'
R_LENS = 38.8
TC_LENS = 2.5
EFL_795 = R_LENS/(N_BK7_795-1.)                            # 75.95 mm
AOM_TO_LENS = EFL_795 + TC_LENS/2                          # 77.20 mm
LENS_TO_MIRROR = EFL_795 - TC_LENS/N_BK7_795 + TC_LENS/2   # 75.55 mm
LENS_TO_QWP = 30.
IRIS_TO_MIRROR = 10.
MIRROR_TO_HWP = 55.
HWP_TO_ROT = 22.
ROT_TO_IRIS = 31.
IRIS_TO_PORT = 42.35 + 18.798    # iris -> fiber face 42.35; the KA05T origin is 18.798 behind the face
REAR_CLAMP_OFFSET = 82.7

BLUE = (.1, .35, .95)
GREEN = (.05, .6, .3)
DOWNSTREAM = 'Nominal 0.6 mm-radius beam; measured q/M2 and RF angle pending.'


def coordinates():
    """Every optic coordinate (mm) along the two beam lines."""
    x_port = 3.0*layout.inch + IN_SHIFT
    x_beam0 = 4.0*layout.inch + IN_SHIFT
    x_hwp = x_beam0 + 0.5*layout.inch
    x_pbs = x_hwp + 1.0*layout.inch
    x_aom = x_pbs + 1.25*layout.inch
    x_lens = x_aom + AOM_TO_LENS
    x_qwp = x_lens + LENS_TO_QWP
    x_retro = x_lens + LENS_TO_MIRROR
    x_iris = x_retro - IRIS_TO_MIRROR
    x_out_mirror = x_pbs
    x_out_hwp = x_pbs + MIRROR_TO_HWP
    x_out_rot = x_out_hwp + HWP_TO_ROT
    x_out_iris = x_out_rot + ROT_TO_IRIS
    x_out_port = x_out_iris + IRIS_TO_PORT
    return dict(x_port=x_port, x_beam0=x_beam0, x_hwp=x_hwp, x_pbs=x_pbs, x_aom=x_aom,
                x_lens=x_lens, x_qwp=x_qwp, x_iris=x_iris, x_retro=x_retro,
                x_out_mirror=x_out_mirror, x_out_hwp=x_out_hwp, x_out_rot=x_out_rot,
                x_out_iris=x_out_iris, x_out_port=x_out_port, beam_y=BEAM_Y, return_y=RETURN_Y)


def example_baseplate(x=0, y=0, angle=0, drill=True):
    """Build the standalone double-pass AOM board."""
    c = coordinates()
    if App.ActiveDocument is None:
        App.newDocument('AOM_DoublePass_f75_V9')
    doc = App.ActiveDocument

    baseplate = layout.baseplate(base_dx, base_dy, base_dz, x=x, y=y, angle=angle, gap=gap,
                                 drill=False, mount_holes=mount_holes,
                                 name='Doublepass plate 17 x 6 in')
    plate = doc.getObject(baseplate.active_baseplate)
    info = {'mode': 'dp', 'plate': plate, 'roots': {}, 'paths': [], 'arms': [],
            'reservations': [], 'extra_cuts': [], 'geometry_assertions': [], 'alternate': False,
            'service_regions': [], 'output_optical_routes': [],
            'requirements': {'mirror_roles': [], 'spherical_groups': []},
            'isolator': None, 'cell': None,
            'layout_status': 'V9 double-pass board; see the saved audit report for results.',
            'mount_holes_mm': [[(hx+.5)*layout.inch, (hy+.5)*layout.inch] for hx, hy in mount_holes]}

    # ---- placement helpers, so every optic below is a single readable line ----
    def put(name, cls, px, py, pangle=0, **kw):
        obj = baseplate.place_element(name, cls, x=px, y=py, angle=pangle, **kw)
        info['roots'][name] = obj
        return obj

    def mirror(name, px, py, pangle):
        return put(name, optomech.circular_mirror_union_optic, px, py, pangle, thickness=6,
                   mount_type=optomech.mirror_mount_M05, mount_args={'thumbscrews': True})

    def bend(name, a, p, b):
        u = (p[0]-a[0], p[1]-a[1])
        v = (b[0]-p[0], b[1]-p[1])
        du = math.hypot(*u)
        dv = math.hypot(*v)
        n = (v[0]/dv - u[0]/du, v[1]/dv - u[1]/du)
        return mirror(name, p[0], p[1], math.degrees(math.atan2(n[1], n[0])))

    def wp(name, px, py, pangle=0):
        return put(name, optomech.waveplate, px, py, pangle,
                   mount_type=optomech.rotation_stage_rsp05)

    def fiber(name, px, py, pangle):
        return put(name, optomech.fiberport_mount_KA05T_holes, px, py, pangle,
                   rear_hole_x_offset=REAR_CLAMP_OFFSET, mount_args={'thumbscrews': True})

    def path(name, points, color, envelope, assumption, bidirectional=False):
        obj = doc.addObject('Part::Feature', name)
        obj.Label = name + ' (nominal axis)'
        obj.Shape = Part.makePolygon([App.Vector(px, py, 0) for px, py in points])
        obj.ViewObject.LineColor = color
        obj.ViewObject.LineWidth = 2.5
        obj.addProperty('App::PropertyString', 'Scope').Scope = assumption
        obj.addProperty('App::PropertyBool', 'Bidirectional').Bidirectional = bidirectional
        if isinstance(envelope, (float, int)):
            envelope = [envelope]*len(points)
        info['paths'].append({'name': name, 'points': [tuple(map(float, p)) for p in points],
                              'object': obj.Name, 'envelope': envelope, 'assumption': assumption})
        return obj

    def service(name, kind, owner, origin_xy, direction_xy, length, width, allowed=(), assumptions=()):
        info['service_regions'].append({
            'name': name, 'kind': kind, 'owner': owner.Name if hasattr(owner, 'Name') else owner,
            'origin_xy_mm': [float(origin_xy[0]), float(origin_xy[1])],
            'direction_xy': [float(direction_xy[0]), float(direction_xy[1])],
            'length_mm': float(length), 'width_mm': float(width),
            'allowed_paths': list(allowed), 'dimensions_verified': False,
            'assumptions': list(assumptions)})

    def assert_distance(name, a, b, expected, tol=1e-6):
        def as_xy(o):
            if hasattr(o, 'BasePlacement'):
                return (o.BasePlacement.Base.x, o.BasePlacement.Base.y)
            return (float(o[0]), float(o[1]))
        pa, pb = as_xy(a), as_xy(b)
        info['geometry_assertions'].append(
            {'name': name, 'measured': math.hypot(pa[0]-pb[0], pa[1]-pb[1]),
             'expected': float(expected), 'tolerance': tol})

    # =========================================================================
    # 1. Input line: fiber, HWP, separation PBS
    # =========================================================================
    beam_y = BEAM_Y
    in_port = fiber('Input KA05T', c['x_port'], beam_y, 0)
    wp('Input HWP', c['x_hwp'], beam_y, 0)
    cube = put('Separation PBS', optomech.cube_splitter, c['x_pbs'], beam_y, 0,
               invert=True, mount_type=optomech.cube_mount_halfinch)

    # =========================================================================
    # 2. The double pass: AOM, cat-eye lens, QWP, order iris, retro mirror
    # =========================================================================
    aom = put('AOMO 3100-125', optomech.AOMO_3100_125, c['x_aom'], beam_y, 180,
              forward_direction=-1, backward_direction=1, diffraction_angle=0,
              surface_adapter_args={'adapter_height': 5})
    seat = optomech.integrate_aom(baseplate, aom)
    info['extra_cuts'].append(seat)
    f, tc, te, f795 = 75.0, TC_LENS, 2.0, EFL_795
    cat = put('Cat-eye L75 '+LENS, optomech.circular_lens, c['x_lens'], beam_y, 180,
              focal_length=f, thickness=tc, diameter=12.7, part_number=LENS,
              mount_type=optomech.lens_holder_l05g_no_pin_slots)
    for key, value in (('CatalogEFL', f), ('EstimatedEFL795', f795),
                       ('CenterThickness', tc), ('EdgeThickness', te)):
        cat.addProperty('App::PropertyLength', key, 'Lens specification')
        setattr(cat, key, value)
    cat.addProperty('App::PropertyString', 'LensOrientation', 'Lens specification')
    cat.LensOrientation = ('Curved face toward the AOM (collimated side), plane face toward the '
                           'retro mirror; spacings use the 795 nm EFL and the plano-convex '
                           'principal planes.')
    qwp = wp('Cat-eye QWP', c['x_qwp'], beam_y, 180)
    iris = put('Order selection iris', optomech.pinhole_ida12, c['x_iris'], beam_y, 180)
    retro = mirror('Retro mirror', c['x_retro'], beam_y, 180)

    # =========================================================================
    # 3. Return line, 74 mm above the input line
    # =========================================================================
    # the PBS reflects the double-passed beam north (invert=True, as lattice DP2)
    out_mirror = bend('Output steering mirror', (c['x_pbs'], beam_y),
                      (c['x_out_mirror'], RETURN_Y), (c['x_out_hwp'], RETURN_Y))
    out_hwp = wp('Output HWP', c['x_out_hwp'], RETURN_Y, 0)
    out_rot = put('Output rotating PBS RSP05', optomech.rotation_stage_rsp05,
                  c['x_out_rot'], RETURN_Y, 0)
    out_rot.addProperty('App::PropertyString', 'Purpose').Purpose = (
        'Empty RSP05: user bonds PBS to rotating front face; no PBS or waveplate modeled.')
    # body on the rotating-PBS side, as on the lattice DP1 row
    out_iris = put('Output filtering iris', optomech.pinhole_ida12, c['x_out_iris'], RETURN_Y, 180)
    out_port = fiber('Output KA05T', c['x_out_port'], RETURN_Y, 180)

    # =========================================================================
    # 4. Nominal beam paths
    # =========================================================================
    path('Input feed', [(c['x_beam0'], beam_y), (c['x_pbs'], beam_y)], BLUE, .6, DOWNSTREAM)
    path('DP1 double pass',
         [(c['x_pbs'], beam_y), (c['x_aom'], beam_y), (c['x_lens'], beam_y), (c['x_qwp'], beam_y),
          (c['x_iris'], beam_y), (c['x_retro'], beam_y)], BLUE,
         [.6, .6, .6, .36, .177, .000795*EFL_795/(math.pi*.6)], DOWNSTREAM, bidirectional=True)
    path('Output',
         [(c['x_pbs'], beam_y), (c['x_out_mirror'], RETURN_Y), (c['x_out_hwp'], RETURN_Y),
          (c['x_out_rot'], RETURN_Y), (c['x_out_iris'], RETURN_Y),
          (c['x_out_port']-18.798, RETURN_Y)], GREEN, .6, DOWNSTREAM)

    # =========================================================================
    # 5. Bookkeeping consumed by the audit scripts (no geometry below this line)
    # =========================================================================
    for port, own, access, note in (
            (in_port, 'Input feed', 15.,
             'Reference geometry: the input HWP sits 19 mm in front of the fiber lens; '
             '15 mm axial access reserved.'),
            (out_port, 'Output', 40., '20 mm full front access width; 40 mm axial access.')):
        direction = port.BasePlacement.Rotation.multVec(App.Vector(1, 0, 0))
        origin = port.BasePlacement.Base + direction*18.798
        service(port.Label+' front access', 'fiber_front', port, (origin.x, origin.y),
                (direction.x, direction.y), access, 20., allowed=[own], assumptions=[note])
    info.setdefault('service_clearance', {}).setdefault('min_length_mm', {})['fiber_front'] = 15.
    # the RF SMB elbow on the AOM face away from the beam
    service(aom.Label+' RF elbow', 'aom_sma', aom, (c['x_aom'], beam_y+33.02), (0., 1.), 40., 20.,
            assumptions=['Connector on the AOM face away from the beam (unverified STL box); '
                         '40 mm of free space for the L-shaped SMB elbow; cable taped down afterwards.'])
    info['service_clearance']['min_length_mm']['aom_sma'] = 40.

    info['pbs_path_specs'] = [{'role': 'double_pass', 'cube': cube.Label,
                               'incoming_path': 'Input feed', 'aom_path': 'DP1 double pass',
                               'output_path': 'Output'}]
    info['arms'].append({'id': 1, 'aom': aom.Name, 'lens': cat.Name, 'retro': retro.Name,
                         'integral_seat': seat.Name, 'aom_to_cat': AOM_TO_LENS,
                         'cat_to_mirror': LENS_TO_MIRROR, 'beam_path': 'DP1 double pass'})
    info['output_optical_routes'].append({'arm': 1, 'events': [
        {'type': 'aom', 'name': 'AOM return', 'xy': (c['x_aom'], beam_y)},
        {'type': 'pbs', 'name': cube.Label, 'xy': (c['x_pbs'], beam_y)},
        {'type': 'mirror', 'name': out_mirror.Label, 'xy': (c['x_out_mirror'], RETURN_Y)},
        {'type': 'hwp', 'name': 'Output HWP', 'xy': (c['x_out_hwp'], RETURN_Y)},
        {'type': 'pbs', 'name': 'Output rotating PBS RSP05', 'xy': (c['x_out_rot'], RETURN_Y)},
        {'type': 'iris', 'name': 'Output filtering iris', 'xy': (c['x_out_iris'], RETURN_Y)},
        {'type': 'fiber', 'name': out_port.Label, 'xy': (c['x_out_port']-18.798, RETURN_Y)}]})
    info['output_order_expected_routes'] = 1
    info['expected_arm_count'] = 1
    # the return beam passes over the recessed head of table bolt (11.2, 4)
    info['hole_clearance'] = {'platform_beam_crossings_allowed': True}
    info['optics_table'] = {k: round(v, 3) for k, v in c.items()}
    info['lens_optics'] = {'part': LENS, 'radius_mm': R_LENS, 'centre_thickness_mm': TC_LENS,
                           'n_795': N_BK7_795, 'efl_795_mm': EFL_795,
                           'bfl_795_from_plane_face_mm': EFL_795-TC_LENS/N_BK7_795,
                           'aom_to_lens_centre_mm': AOM_TO_LENS,
                           'lens_centre_to_mirror_mm': LENS_TO_MIRROR}

    assert_distance('AOM centre -> lens centre = EFL795 + tc/2 (nominal AOM axis)',
                    (c['x_aom'], beam_y), cat, AOM_TO_LENS)
    assert_distance('Lens centre -> retro mirror = EFL795 - tc/n + tc/2', cat, retro, LENS_TO_MIRROR)
    assert_distance('Lens -> QWP', cat, qwp, LENS_TO_QWP)
    assert_distance('Iris -> retro mirror face', iris, retro, IRIS_TO_MIRROR)
    assert_distance('Input port -> PBS', in_port, cube, 2.5*layout.inch)
    assert_distance('PBS -> AOM (nominal AOM axis)', cube, (c['x_aom'], beam_y), 1.25*layout.inch)
    assert_distance('Output HWP -> rotating PBS', out_hwp, out_rot, HWP_TO_ROT)
    assert_distance('Rotating PBS -> output iris (>= 20 required)', out_rot, out_iris, ROT_TO_IRIS)
    assert_distance('Output iris -> fiber face (>= 40 required)', out_iris,
                    (c['x_out_port']-18.798, RETURN_Y), 42.35)
    info['geometry_assertions'].extend([
        {'name': 'Retro M05 + thumbscrews inside plate (margin mm)',
         'measured': base_dx-(c['x_retro']+35.72), 'expected': 50.3, 'tolerance': 1.0},
        {'name': 'Input rear tail-clamp holes inside plate (x mm)',
         'measured': c['x_port']-REAR_CLAMP_OFFSET, 'expected': 15.09, 'tolerance': 0.1},
        {'name': 'Output rear tail-clamp holes inside plate (margin mm)',
         'measured': base_dx-(c['x_out_port']+REAR_CLAMP_OFFSET), 'expected': 18.66, 'tolerance': 0.2},
        {'name': 'Output steering mirror thumbscrews inside plate (margin mm)',
         'measured': base_dy-(RETURN_Y+36.03), 'expected': 6.8, 'tolerance': 1.0}])

    # ---- cut the plate once every element and machining volume is in place ----
    doc.recompute()
    layout.redraw()
    plate.Drill = drill
    plate.touch()
    doc.recompute()
    doc.Label = 'AOM double pass f75 (795 nm cat-eye) - V9'

    # the three table holes must keep the reference pattern (0.6,0), (11,4), (0,4) in
    mounts = sorted([o for o in doc.Objects
                     if type(getattr(o, 'Proxy', None)).__name__ == 'baseplate_mount'],
                    key=lambda o: (o.Placement.Base.x, o.Placement.Base.y))
    reference = sorted([(0.6*layout.inch, 0.), (11*layout.inch, 4*layout.inch), (0., 4*layout.inch)])
    for i, j in ((0, 1), (0, 2), (1, 2)):
        expected = math.hypot(reference[i][0]-reference[j][0], reference[i][1]-reference[j][1])
        info['geometry_assertions'].append(
            {'name': 'Table hole pattern distance %d-%d (reference 0.6,0 / 11,4 / 0,4 in)' % (i, j),
             'measured': (mounts[i].Placement.Base-mounts[j].Placement.Base).Length,
             'expected': expected, 'tolerance': 1e-6})
    return info


if __name__ == "__main__":
    example_baseplate()
    layout.redraw()
