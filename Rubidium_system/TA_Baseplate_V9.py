"""TA baseplate V9.15 - 11.625 x 10.625 in, with one fiber output.

2026-10-20 machining-only revision: open the four inspected thin webs and
locally widen two lower-thumbscrew reliefs. Optical placements and component
geometry remain V9.15. The cuts stop at the adjacent original pocket floors;
they are not through-cuts. Native support and hole checks are required.

Beam order, read top to bottom in example_baseplate():

    TA -> two steering folds -> HWP -> isolator -> QWP
       -> four bare 8-32 conditioning stations (two cylindrical, two spherical)
       -> lattice V9.7 sliding Rb cell enclosure -> output fold 1 -> L1
       -> output fold 2 -> L2, HWP, real half-inch PBS bonded to RSP05 -> one KA05T

The TA emits right; its thick cable exits the upper long edge. The HWP and
QWP retain their original order relative to the isolator and every mirror.
Four conditioning taps accept selected POLARIS-L05G holders; their optics
remain unselected. The previous 38.1 mm bottom crop and table-grid phase are
retained. The TA sits above the right half of the isolator lane, clearing
the left folding mirror's support footprint. The post-cell group moves left.
After the cell, two 45-degree mirrors turn the output down and then left.
The second mirror lies between the lenses; their 45.319348 mm propagation
distance is measured along this folded path. The bonded PBS lies upstream of its
second RSP05. Native CAD clearance and platform checks are required;
the source does not assert that those checks have passed.

Positions are millimetres; z = 0 is the 12.7 mm optical
axis. See Production/TABoardV9/ for the renders and the audit report.

Run in FreeCAD (Macro > Macros..., or paste into the Python console):
    example_baseplate()
"""
import json
import math

import FreeCAD as App
import Part

from PyOpticL import layout, optomech

# baseplate constants
base_dx = 11.625*layout.inch
BOTTOM_TRIM_MM = 1.5*layout.inch
TA_TOP_EXTENSION_MM = 1.125*layout.inch
base_dy = 11*layout.inch-BOTTOM_TRIM_MM+TA_TOP_EXTENSION_MM
base_dz = layout.inch
gap = layout.inch/8

# Preserve the previous one-inch table-grid phase after trimming. The former
# lower-right anchor may move by integer inches under the user's new request.
PRIOR_TABLE_ANCHOR_MM = (base_dx-gap-layout.inch, gap+layout.inch)
TABLE_MOUNT_ANCHOR_RELOCATION_IN = (0, 3)
TABLE_MOUNT_ANCHOR_MM = (PRIOR_TABLE_ANCHOR_MM[0],
                         PRIOR_TABLE_ANCHOR_MM[1]+3*layout.inch-BOTTOM_TRIM_MM)
TABLE_MOUNT_OFFSETS_IN = ((0, 0), (-10, -2), (-6, 7), (-9, 7))
mount_holes = [(TABLE_MOUNT_ANCHOR_MM[0]/layout.inch+dx-.5,
                TABLE_MOUNT_ANCHOR_MM[1]/layout.inch+dy-.5)
               for dx, dy in TABLE_MOUNT_OFFSETS_IN]


def board_xy(px, py):
    """Board-frame coordinate pair (shared by placement and audit metadata)."""
    return px, py


def board_direction(dx, dy):
    return dx, dy

# --- common path: lattice ordering and conditioning pitches -----------------
TA_XY = (211., 216.4)
TA_FOLD1_XY = (268., 216.4)
TA_FOLD2_XY = (268., 137.5)
TA_HWP_XY = (245., 137.5)
ISO_XY = (112., 137.5)
QWP_XY = (49., 137.5)
CYLINDRICAL_PITCH = 45.2
STATION_IDS = (1, 2, 5, 6)  # retain four provisions, removing old positions 3 and 4
STATIONS_XY = ((26.8, 103.9), (49., 80.9), (74., 80.9), (114., 80.9))
COMMON_FOLD1_XY = (26.8, 137.5)
COMMON_FOLD2_XY = (26.8, 80.9)
CELL_XY = (180., 80.9)
COMMON_FOLD3_XY = (248., 80.9)
COMMON_FOLD4_XY = (248., 33.9)
OUTPUT_L1_XY = (248., 62.9)

# L1 lies on the downward leg. The remaining distances run leftward from
# the second post-cell mirror, preserving L1 -> mirror -> L2 propagation.
# Reversing the RSP05 puts its real cube 14.297 mm upstream of its reference.
TELESCOPE_DISTANCE = 45.319348
OUT = {'lens2': TELESCOPE_DISTANCE-(OUTPUT_L1_XY[1]-COMMON_FOLD4_XY[1])}
OUT['hwp'] = OUT['lens2']+25.
OUT['rot'] = OUT['hwp']+32.
OUT['fiber_face'] = OUT['rot']+50.
OUT['port'] = OUT['fiber_face']+18.798
OUTPUT_LANE = 'Post-cell output'
REAR_CLAMP_OFFSET = 66.7

LENSES = {
    'LA1289-B': (29.9, 3.2, 1.8, 30.2466184),
    'LA1540-B': (14.9, 5.1, 1.8, 15.0727296),
}
RED = (.85, .15, .1)
BLUE = (.1, .35, .95)
UPSTREAM = 'Assumed upstream clearance radius 2.5 mm; TA measured q/M2 not supplied.'
DOWNSTREAM = 'Nominal conditioned beam envelope, not a measured Gaussian mode or coupling calculation.'
STATION_NOTE = ('Bare 8-32 conditioning hole (retained station %d); selected POLARIS-L05G holder, optics unselected. '
                'The holder optical datum is 8 mm forward from its mounting tap along the beam.')


# Board-local machining, tied to the delivered V9.15 STEP rather than a later
# unapproved layout experiment. Depths are measured down from the plate top.
# A capsule is a constant-radius round-ended slot between its two centres.
WALL_RELIEF_BASELINE_SHA256 = 'b038c4dbdc5f426143e660fdb2bc9721ba11a621c7c8bbec7858b0fe5fc1db74'
WALL_RELIEF_CUTS = (
    {'id': 'W01', 'kind': 'box', 'xy': [129.20003509521, 263.22648828125,
                                      233.20003509521, 267.7],
     'depth_mm': 11.60000114440918, 'purpose': 'Open the TA-adapter upper web to the finished upper edge.'},
    {'id': 'W03', 'kind': 'box', 'xy': [229.026, 113.5, 235.777, 119.1],
     'depth_mm': 9.27,
     'purpose': 'Join cell and upstream-HWP pockets at the shallower HWP floor.'},
    {'id': 'W04', 'kind': 'box', 'xy': [125.326, 154.40048446655, 132.37403509521, 166.5],
     'depth_mm': 11.60000114440918,
     'purpose': 'Join isolator and TA-adapter pockets at the shallower TA floor.'},
    {'id': 'C03_C04', 'kind': 'capsule',
     'centres_xy': [[255.23776680074, 115.19578991377], [253.90721008622, 113.86523319925]],
     'radius_mm': 3.0, 'depth_mm': 6.390338176727293,
     'purpose': 'Locally widen output-fold-3 lower-knob relief across the two inspected tips.'},
    {'id': 'W02', 'kind': 'box', 'xy': [288.48, 11.7, 293.1, 20.3],
     'depth_mm': 6.390338176727293,
     'purpose': 'Open output-fold-4 lower-knob relief to the finished right edge.'},
    {'id': 'C07_C12', 'kind': 'box', 'xy': [272.85, 2.175, 284.85, 9.175],
     'depth_mm': 6.390338176727293,
     'purpose': 'Widen the same lower-knob relief mouth through the finished bottom edge.'},
)


def wall_relief_shapes(top_z=-12.7, specs=WALL_RELIEF_CUTS):
    """Return labelled, board-local cutters; never alter any component cutter."""
    result = []
    for spec in specs:
        floor = float(top_z)-spec['depth_mm']
        height = spec['depth_mm']+1.0  # extend into air above the top face
        if spec['kind'] in ('box', 'rounded_box'):
            x0, y0, x1, y1 = spec['xy']
            shape = Part.makeBox(x1-x0, y1-y0, height, App.Vector(x0, y0, floor))
            if spec['kind'] == 'rounded_box':
                vertical = [edge for edge in shape.Edges
                            if abs(edge.tangentAt(edge.FirstParameter).z) > .999]
                shape = shape.makeFillet(spec['radius_mm'], vertical)
        elif spec['kind'] == 'capsule':
            a, b = spec['centres_xy']
            radius = spec['radius_mm']
            length = math.dist(a, b)
            direction = math.degrees(math.atan2(b[1]-a[1], b[0]-a[0]))
            bridge = Part.makeBox(length, 2*radius, height, App.Vector(0, -radius, floor))
            bridge.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), direction)
            bridge.translate(App.Vector(a[0], a[1], 0))
            ends = [Part.makeCylinder(radius, height, App.Vector(p[0], p[1], floor)) for p in (a, b)]
            shape = bridge.multiFuse(ends).removeSplitter()
        else:
            raise ValueError('Unknown TA relief shape: '+str(spec['kind']))
        if not shape.isValid() or len(shape.Solids) != 1:
            raise ValueError('Invalid TA relief cutter: '+spec['id'])
        result.append((spec['id'], shape))
    return result


class TAWallReliefBaseplate(layout.baseplate):
    """Original V9.15 drilling followed by this board's registered reliefs."""

    def execute(self, obj):
        previous = App.ActiveDocument
        if previous != obj.Document:
            App.setActiveDocument(obj.Document.Name)
        try:
            layout.baseplate.execute(self, obj)
            if obj.Drill and getattr(obj, 'WallReliefEnabled', False):
                specs = json.loads(obj.WallReliefParametersJSON)
                shape = obj.Shape.copy()
                shape.Placement = obj.Placement.inverse().multiply(shape.Placement)
                for _, cutter in wall_relief_shapes(-obj.OpticsDz.Value, specs):
                    shape = shape.cut(cutter)
                shape = shape.removeSplitter()
                if not shape.isValid() or len(shape.Solids) != 1:
                    raise ValueError('TA wall relief must leave one valid plate solid')
                shape.Placement = obj.Placement.multiply(shape.Placement)
                obj.Shape = shape
        finally:
            if previous is not None and previous != obj.Document:
                App.setActiveDocument(previous.Name)

    def dumps(self):
        return {'active_baseplate': self.active_baseplate}

    def loads(self, state):
        self.active_baseplate = state['active_baseplate']


def example_baseplate(x=0, y=0, angle=0, drill=True, cell_slide=0., wall_relief=True):
    """Build the TA board."""
    if App.ActiveDocument is None:
        App.newDocument('TA_Board_V9')
    doc = App.ActiveDocument

    baseplate = TAWallReliefBaseplate(base_dx, base_dy, base_dz, x=x, y=y, angle=angle, gap=gap,
                                 drill=False, mount_holes=mount_holes,
                                 name='TA plate V9.15 supported-mirror single-output')
    plate = doc.getObject(baseplate.active_baseplate)
    plate.addProperty('App::PropertyBool', 'WallReliefEnabled', 'TA machining').WallReliefEnabled = bool(wall_relief)
    plate.addProperty('App::PropertyString', 'WallReliefParametersJSON', 'TA machining').WallReliefParametersJSON = json.dumps(WALL_RELIEF_CUTS, sort_keys=True)
    info = {'mode': 'ta', 'plate': plate, 'roots': {}, 'paths': [], 'arms': [],
            'reservations': [], 'extra_cuts': [], 'geometry_assertions': [], 'alternate': False,
            'service_regions': [], 'output_optical_routes': [], 'bonded_output_pbs': [],
            'requirements': {'mirror_roles': [], 'spherical_groups': []},
            'isolator': None, 'cell': None, 'upstream_order_required': True,
            'layout_status': 'V9.15 optical layout; 2026-10-20 wall-relief machining; native validation required.',
            'optical_reference_model': {'kind': 'single_output_no_aom', 'output_lane': OUTPUT_LANE},
            'mount_holes_mm': [[(hx+.5)*layout.inch, (hy+.5)*layout.inch] for hx, hy in mount_holes]}
    info['wall_relief_design'] = {'schema': 'ta_wall_relief/1', 'enabled': bool(wall_relief),
                                'baseline_revision': 'V9.15', 'baseline_step_sha256': WALL_RELIEF_BASELINE_SHA256,
                                'cuts': list(WALL_RELIEF_CUTS), 'component_positions_changed': False,
                                'through_cut': False, 'validation_status': 'requires_native_checks'}
    info['table_mount_pattern'] = {'pitch_mm': layout.inch, 'prior_right_lower_edge_offset_mm': layout.inch,
                                  'edge_datum': 'finished machined plate edges',
                                  'offsets_in': TABLE_MOUNT_OFFSETS_IN}
    info['table_mount_pattern']['relocated_anchor'] = {
        'schema': 'cropped_grid_reference/1', 'prior_anchor_xy_mm': list(PRIOR_TABLE_ANCHOR_MM),
        'board_translation_xy_mm': [0., -BOTTOM_TRIM_MM],
        'relocation_in': list(TABLE_MOUNT_ANCHOR_RELOCATION_IN),
        'prior_plate_size_mm': [base_dx, 11*layout.inch, base_dz],
        'bottom_trim_mm': BOTTOM_TRIM_MM, 'top_extension_mm': TA_TOP_EXTENSION_MM,
        'authorization': '2026-10-12 user permits integer-inch relocation of the previous lower-right hole after trimming the bottom.'}

    # ---- placement helpers, so every optic below is a single readable line ----
    def put(name, cls, px, py, pangle=0, **kw):
        bx, by = board_xy(px, py)
        obj = baseplate.place_element(name, cls, x=bx, y=by, angle=pangle, **kw)
        info['roots'][name] = obj
        return obj

    def mirror(name, px, py, pangle):
        return put(name, optomech.circular_mirror_union_optic, px, py, pangle, thickness=6,
                   mount_type=optomech.mirror_mount_M05, mount_args={'thumbscrews': True})

    def bend(name, a, p, b):
        """A 45-degree M05 fold at p, turning the beam a->p onto p->b."""
        u = (p[0]-a[0], p[1]-a[1])
        v = (b[0]-p[0], b[1]-p[1])
        du = math.hypot(*u)
        dv = math.hypot(*v)
        n = (v[0]/dv - u[0]/du, v[1]/dv - u[1]/du)
        obj = mirror(name, p[0], p[1], math.degrees(math.atan2(n[1], n[0])))
        normal = obj.BasePlacement.Rotation.multVec(App.Vector(1, 0, 0))
        dot = u[0]/du*normal.x + u[1]/du*normal.y
        reflected = (u[0]/du-2*dot*normal.x, u[1]/du-2*dot*normal.y)
        info['geometry_assertions'].extend([
            {'name': name+': reflection direction residual',
             'measured': math.hypot(reflected[0]-v[0]/dv, reflected[1]-v[1]/dv),
             'expected': 0., 'tolerance': 1e-9},
            {'name': name+': incidence angle (degrees)',
             'measured': math.degrees(math.acos(min(1., abs(dot)))),
             'expected': 45., 'tolerance': 1e-9}])
        return obj

    def wp(name, px, py, pangle=0):
        return put(name, optomech.waveplate, px, py, pangle,
                   mount_type=optomech.rotation_stage_rsp05)

    def lens(name, part, px, py, pangle=180):
        f, tc, te, f795 = LENSES[part]
        obj = put(name, optomech.circular_lens, px, py, pangle, focal_length=f, thickness=tc,
                  diameter=12.7, part_number=part,
                  mount_type=optomech.lens_holder_l05g_no_pin_slots)
        for key, value in (('CatalogEFL', f), ('EstimatedEFL795', f795),
                           ('CenterThickness', tc), ('EdgeThickness', te)):
            obj.addProperty('App::PropertyLength', key, 'Lens specification')
            setattr(obj, key, value)
        obj.addProperty('App::PropertyString', 'LensOrientation', 'Lens specification')
        obj.LensOrientation = ('Holder angle is independent of glass orientation. '
                               'CAD is envelope only.')
        return obj

    def hole(name, px, py, purpose):
        obj = put(name, optomech.BareTappedHole, px, py)
        obj.Purpose = purpose
        info['extra_cuts'].append(obj)
        info['reservations'].append({'object': obj.Name, 'reason': purpose})
        return obj

    def fiber(name, px, py, pangle, rear=REAR_CLAMP_OFFSET):
        return put(name, optomech.fiberport_mount_KA05T_holes, px, py, pangle,
                   rear_hole_x_offset=rear, mount_args={'thumbscrews': True})

    def path(name, points, color, envelope, assumption):
        points = [board_xy(*p) for p in points]
        obj = doc.addObject('Part::Feature', name)
        obj.Label = name + ' (nominal axis)'
        obj.Shape = Part.makePolygon([App.Vector(px, py, 0) for px, py in points])
        obj.ViewObject.LineColor = color
        obj.ViewObject.LineWidth = 2.5
        obj.addProperty('App::PropertyString', 'Scope').Scope = assumption
        obj.addProperty('App::PropertyBool', 'Bidirectional').Bidirectional = False
        if isinstance(envelope, (float, int)):
            envelope = [envelope]*len(points)
        info['paths'].append({'name': name, 'points': [tuple(map(float, p)) for p in points],
                              'object': obj.Name, 'envelope': envelope, 'assumption': assumption})
        return obj

    def service(name, kind, owner, origin_xy, direction_xy, length, width, allowed=(), assumptions=()):
        origin_xy = board_xy(*origin_xy)
        direction_xy = board_direction(*direction_xy)
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
            return board_xy(float(o[0]), float(o[1]))
        pa, pb = as_xy(a), as_xy(b)
        info['geometry_assertions'].append(
            {'name': name, 'measured': math.hypot(pa[0]-pb[0], pa[1]-pb[1]),
             'expected': float(expected), 'tolerance': tol})

    # =========================================================================
    # 1. TA, the two steering folds and the isolator lane
    # =========================================================================
    # The TA emits +x; its thick cable points +y through the upper long edge.
    ta = put('TA', optomech.TA_butterfly_on_adapter, *TA_XY, 0)
    supply = [TA_XY, TA_FOLD1_XY, TA_FOLD2_XY, TA_HWP_XY, ISO_XY, QWP_XY, COMMON_FOLD1_XY, STATIONS_XY[0]]
    bend('TA steering fold 1', TA_XY, TA_FOLD1_XY, TA_FOLD2_XY)
    bend('TA steering fold 2', TA_FOLD1_XY, TA_FOLD2_XY, ISO_XY)
    wp('TA output HWP', *TA_HWP_XY, 180)
    isolator = put('Hana long isolator', optomech.isolator_850_long_pocket, *ISO_XY, 0)
    info['extra_cuts'].append(isolator)
    wp('TA output QWP', *QWP_XY, 180)

    # =========================================================================
    # 2. Four bare conditioning stations (POLARIS-L05G selected, optics undecided)
    # =========================================================================
    lane_stations = [hole('Common station 8-32 '+str(STATION_IDS[i]), *STATIONS_XY[i], STATION_NOTE % STATION_IDS[i])
                     for i in range(2)]
    sphere_stations = [hole('Common station 8-32 '+str(STATION_IDS[i]), *STATIONS_XY[i], STATION_NOTE % STATION_IDS[i])
                       for i in range(2, 4)]

    # =========================================================================
    # 3. Common conditioning folds, complete cell, and two output folds
    # =========================================================================
    output_xy = {key: (COMMON_FOLD4_XY[0]-distance, COMMON_FOLD4_XY[1])
                 for key, distance in OUT.items()}
    output_xy['lens1'] = OUTPUT_L1_XY
    fold1 = bend('Common post-isolator fold 1', QWP_XY, COMMON_FOLD1_XY, STATIONS_XY[0])
    fold2 = bend('Common post-isolator fold 2', STATIONS_XY[0], COMMON_FOLD2_XY, STATIONS_XY[1])
    fold3 = bend('Common post-isolator fold 3', CELL_XY, COMMON_FOLD3_XY, output_xy['lens1'])
    fold4 = bend('Common post-isolator fold 4', output_xy['lens1'], COMMON_FOLD4_XY, output_xy['lens2'])

    # Exactly the lattice V9.7 lower half, lid, covers, glass and sliding seat.
    cell = optomech.place_sliding_cell(baseplate, *CELL_XY, angle=0, slide=cell_slide)
    info['cell'] = dict(cell)
    info['roots']['Rb cell seat (V9.7 pocket + 2 slot taps)'] = cell['root']
    info['roots']['Rb cell enclosure (V9.7 lower half, lid, covers, cell)'] = cell['cell']
    info['extra_cuts'].extend(o for o in cell['objects'] if hasattr(o, 'DrillPart'))
    info['isolator'] = {'source': 'hana-branch original isolator_850',
                        'main_pocket_mm': [113.5, 25., 5.]}

    # =========================================================================
    # 4. Folded telescope followed by the leftward HWP, bonded PBS, KA05T
    # =========================================================================
    l1 = lens(OUTPUT_LANE+' first LA1289-B', 'LA1289-B', *output_xy['lens1'], 90)
    l2 = lens(OUTPUT_LANE+' second LA1540-B', 'LA1540-B', *output_xy['lens2'], 0)
    output_hwp = wp(OUTPUT_LANE+' HWP', *output_xy['hwp'], 180)
    rotating = put(OUTPUT_LANE+' bonded-PBS RSP05', optomech.rotation_stage_rsp05_bonded_cube,
                   *output_xy['rot'], 0, cube_roll_deg=0.)
    rotating.addProperty('App::PropertyString', 'Purpose').Purpose = (
        '12.7 mm PBS cube bonded to the +X engraved rotor, upstream for the -X beam. '
        'This second RSP05 holds the PBS and no waveplate.')
    head = fiber(OUTPUT_LANE+' KA05T', *output_xy['port'], 0)
    # Synchronize the linked glass before publishing its actual optical centre.
    doc.recompute()
    cube = rotating.BondedCube
    output_xy['cube'] = (cube.BasePlacement.Base.x, cube.BasePlacement.Base.y)
    face = head.BasePlacement.multVec(App.Vector(18.798, 0, 0))
    output_xy['fiber_face'] = (face.x, face.y)
    info['bonded_output_pbs'].append({
        'lane': OUTPUT_LANE, 'beam_path': OUTPUT_LANE, 'stage': rotating.Name,
        'cube': cube.Name, 'adhesive': rotating.BondedAdhesive.Name,
        'stage_reference_xy_mm': list(output_xy['rot']),
        'cube_centre_xy_mm': list(output_xy['cube']), 'stage_angle_deg': 0.,
        'hwp_to_stage_reference_mm': OUT['rot']-OUT['hwp'], 'cube_side': 'upstream',
        'cube_size_mm': 12.7, 'cube_roll_deg': 0.,
        'adhesive_thickness_mm': float(rotating.AdhesiveThickness.Value),
        'assumptions': rotating.BondAssumptions})
    info['optical_reference_model'].update(beam_path=OUTPUT_LANE, cell=cell['cell'].Name)
    info['single_output_design'] = {
        'kind': 'ta_single_output', 'beam_path': OUTPUT_LANE, 'cell': cell['cell'].Name,
        'table_size_mm': [711.2, 381.0], 'table_edge_hole_offset_mm': layout.inch,
        'board_limit_mm': [355.6, 279.4], 'cable_exit': '+Y_long_edge',
        'expected_aom_count': 0}

    # =========================================================================
    # 5. Nominal beam paths
    # =========================================================================
    path('TA supply', supply, RED, 2.5, UPSTREAM)
    path('Common cylindrical conditioning provision',
         [STATIONS_XY[0], COMMON_FOLD2_XY, STATIONS_XY[1], STATIONS_XY[2]],
         RED, [2.5, .9, .9, .9],
         'Two cylindrical stations are bare 8-32 holes; optics unselected. The envelope is the intended '
         'conditioned beam.')
    path('Common spherical telescope',
         [STATIONS_XY[2], STATIONS_XY[3], CELL_XY],
         RED, [.9, .6, .6],
         'Stations 5/6 are bare 8-32 holes; optics unselected. ' + DOWNSTREAM)
    # Preserve the nominal linear envelope from L2 (0.035 mm) to the fiber
    # (0.6 mm), including the newly explicit HWP and real cube vertices.
    def downstream_radius(point):
        distance = COMMON_FOLD4_XY[0]-point[0]
        return .035+(.6-.035)*(distance-OUT['lens2'])/(OUT['fiber_face']-OUT['lens2'])
    output_points = [CELL_XY, COMMON_FOLD3_XY, output_xy['lens1'], COMMON_FOLD4_XY,
                     output_xy['lens2'], output_xy['hwp'], output_xy['cube'], output_xy['fiber_face']]
    fold_radius = .6+(.035-.6)*math.dist(output_xy['lens1'], COMMON_FOLD4_XY)/TELESCOPE_DISTANCE
    path(OUTPUT_LANE, output_points,
         BLUE, [.6, .6, .6, fold_radius, .035, downstream_radius(output_xy['hwp']),
                downstream_radius(output_xy['cube']), .6], DOWNSTREAM)

    # =========================================================================
    # 6. Bookkeeping consumed by the audit scripts (no geometry below this line)
    # =========================================================================
    beam_dir = {1: (0., -1.), 2: (1., 0.), 3: (1., 0.), 4: (1., 0.)}
    info['requirements']['mount_only_cylindrical_holes'] = [o.Name for o in lane_stations]
    info['requirements']['provisional_bare_mount_envelopes'] = [
        {'object': o.Name, 'center_xy_mm': [o.BasePlacement.Base.x, o.BasePlacement.Base.y],
         'diameter_mm': 16.0, 'beam_direction_xy': list(board_direction(*beam_dir[i+1]))}
        for i, o in enumerate([*lane_stations, *sphere_stations])]
    info['requirements']['spherical_groups'].append(
        {'name': 'common', 'active_lenses': [], 'spare_holes': [o.Name for o in sphere_stations],
          'stations_only': True, 'spare_required': 2})
    info['requirements']['conditioning_stations'] = {
        'schema': 'conditioning_stations/2',
        'cylindrical_holes': [o.Name for o in lane_stations],
        'spherical_holes': [o.Name for o in sphere_stations],
        'expected_counts': {'cylindrical': 2, 'spherical': 2, 'total': 4},
        'round_envelope_diameter_mm': 16., 'holders_unselected': False,
        'holder_model': 'POLARIS-L05G', 'holder_class': 'lens_holder_l05g_no_pin_slots',
        'holder_selection_confirmed': True, 'optics_unselected': True}

    info['requirements']['spherical_groups'].append(
        {'name': OUTPUT_LANE, 'active_lenses': [l1.Name, l2.Name],
         'spare_holes': [], 'spare_required': 0})
    events = [
        {'type': 'mirror', 'name': fold3.Label, 'object': fold3.Name, 'xy': COMMON_FOLD3_XY},
        {'type': 'lens', 'name': l1.Label, 'object': l1.Name, 'xy': output_xy['lens1'],
         'focal_mm': float(l1.EstimatedEFL795.Value)},
        {'type': 'mirror', 'name': fold4.Label, 'object': fold4.Name, 'xy': COMMON_FOLD4_XY},
        {'type': 'lens', 'name': l2.Label, 'object': l2.Name, 'xy': output_xy['lens2'],
         'focal_mm': float(l2.EstimatedEFL795.Value)},
        {'type': 'hwp', 'name': output_hwp.Label, 'object': output_hwp.Name, 'xy': output_xy['hwp']},
        {'type': 'pbs', 'name': cube.Label, 'object': cube.Name, 'xy': output_xy['cube']},
        {'type': 'fiber', 'name': head.Label, 'object': head.Name, 'xy': output_xy['fiber_face']}]
    info['output_optical_routes'].append({'arm': OUTPUT_LANE, 'events': events})
    registered_points = next(p['points'] for p in info['paths'] if p['name'] == OUTPUT_LANE)
    first = registered_points.index(output_xy['lens1'])
    last = registered_points.index(output_xy['lens2'])
    telescope_points = registered_points[first:last+1]
    telescope_distance = sum(math.dist(a, b) for a, b in zip(telescope_points, telescope_points[1:]))
    info['geometry_assertions'].append({
        'name': 'Output L1 -> fold -> L2 propagation = f1 + f2 (795 nm)',
        'measured': telescope_distance, 'expected': TELESCOPE_DISTANCE, 'tolerance': 1e-6})
    info['single_output_design']['lens_spacing'] = {
        'beam_path': OUTPUT_LANE, 'lens1': l1.Name, 'lens2': l2.Name,
        'fold': fold4.Name, 'path_vertices_xy_mm': telescope_points,
        'propagation_distance_mm': telescope_distance,
        'euclidean_chord_mm': math.dist(output_xy['lens1'], output_xy['lens2'])}
    assert_distance('Output HWP -> bonded RSP05 reference', output_hwp, rotating, 32.)
    assert_distance('Bonded RSP05 reference -> fiber face', rotating, output_xy['fiber_face'], 50.)
    assert_distance('Bonded RSP05 reference -> cube centre', rotating, cube, 14.297)
    assert_distance('KA05T mount reference -> fiber face', head, output_xy['fiber_face'], 18.798)
    service(head.Label+' front access', 'fiber_front', head,
            output_xy['fiber_face'], (1., 0.), 40., 20.,
            allowed=[OUTPUT_LANE], assumptions=['20 mm full front access width; 40 mm axial access.'])

    cable_origin = ta.BasePlacement.multVec(App.Vector(-29.925, 50.155613, 0))
    cable_direction = ta.BasePlacement.Rotation.multVec(App.Vector(0, 1, 0))
    service('TA thick long-edge cable', 'ta_cable', ta,
            (cable_origin.x, cable_origin.y), (cable_direction.x, cable_direction.y), 101.6, 96.25,
            assumptions=['Conservative TA full body-width cable projection; connector dimensions '
                         'unverified. The 101.6 mm corridor extends beyond the upper long edge.'])
    info['service_clearance'] = {'min_length_mm': {'fiber_front': 40., 'ta_cable': 101.6}}
    info['pbs_path_specs'] = []
    info['output_order_expected_routes'] = 1
    info['expected_arm_count'] = 0
    info['routes_without_iris'] = [OUTPUT_LANE]
    info['fiber_clearance'] = {'rear_offsets_mm': [REAR_CLAMP_OFFSET]}

    info['geometry_assertions'].extend([
        {'name': 'Stations 1-2 propagation through fold',
         'measured': math.dist(STATIONS_XY[0], COMMON_FOLD2_XY)+math.dist(COMMON_FOLD2_XY, STATIONS_XY[1]),
         'expected': CYLINDRICAL_PITCH, 'tolerance': 1e-9},
        {'name': 'Spherical stations 5-6 pitch', 'measured': STATIONS_XY[3][0]-STATIONS_XY[2][0],
         'expected': 40., 'tolerance': 1e-9},
        {'name': 'Single output has two steering mirrors',
         'measured': sum(e['type'] == 'mirror' for e in info['output_optical_routes'][0]['events']),
         'expected': 2, 'tolerance': 0.},
        {'name': 'Single KA05T rear-hole axis to left plate edge (mm)',
         'measured': output_xy['port'][0]-REAR_CLAMP_OFFSET-gap,
             'expected': 36.007652, 'tolerance': 1e-6}])
    assert_distance('Cell -> first output fold', CELL_XY, COMMON_FOLD3_XY, 68.)
    assert_distance('Output fold separation', COMMON_FOLD3_XY, COMMON_FOLD4_XY, 47.)

    # ---- cut the plate once every element and machining volume is in place ----
    doc.recompute()
    layout.redraw()
    plate.Drill = drill
    plate.touch()
    doc.recompute()
    info['plate_size_mm'] = [base_dx, base_dy, base_dz]
    doc.Label = 'TA board - V9.15 supported-mirror single-output'
    return info


if __name__ == "__main__":
    example_baseplate()
    layout.redraw()
