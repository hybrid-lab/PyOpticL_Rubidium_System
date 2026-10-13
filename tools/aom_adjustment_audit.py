"""Native evidence for external AOM adjustment clearance on Splitting Board V2.

The continuous envelope contains every rigid rotation of net angle <=4 degrees
about the measured ideal sphere/cone pivot, plus a 1 mm clearance ball. It does
NOT certify two simultaneous +/-4-degree axes or clearance against the original
lattice seat. The original installation is deliberately retained and its known
pitch limitation is reported separately. Convex-hull overlaps are unresolved
candidates, never asserted physical collisions; a PASS requires a separating
plane for every relevant pair.

Call apply(report, doc, info, source_module=loaded_splitting_module). This adds
only aom_adjustment_audit and its own issue count, preserving unrelated results.
"""
import ast
import hashlib
import math
import traceback
from pathlib import Path
from copy import deepcopy
import numpy as np
from scipy.spatial import ConvexHull
from itertools import combinations

THETA=np.deg2rad(4.)

def _reduce(points):
 p=np.unique(points,axis=0)
 if len(p)>4:
  try:p=p[ConvexHull(p).vertices]
  except Exception:pass
 return p

class _Body:
 def __init__(self,name,points,pivot=None,margin=0.,root=None):
  self.name=name;self.points=_reduce(points);self.pivot=pivot;self.margin=margin;self.root=root
  self.clearance_margin = 1. if pivot is not None else 0.
  self.centre=np.mean(self.points,axis=0)
  self.q=None if pivot is None else self.points-pivot
  self.r2=None if pivot is None else np.einsum('ij,ij->i',self.q,self.q)
  self.r=None if pivot is None else np.sqrt(self.r2)
  self.bbox=np.array([[self.support(-n)@n,self.support(n)@n] for n in np.eye(3)])
 def support(self,n):
  length=np.linalg.norm(n)
  if length<1.e-15:raise ValueError('zero support direction')
  n=n/length
  if self.pivot is None:
   p=self.points[np.argmax(self.points@n)]
  else:
   dot=self.q@n; perp=np.sqrt(np.maximum(0,self.r2-dot*dot))
   values=np.where(dot>=self.r*np.cos(THETA),self.r,dot*np.cos(THETA)+perp*np.sin(THETA))
   i=np.argmax(values)
   if dot[i]>=self.r[i]*np.cos(THETA):p=self.pivot+self.r[i]*n
   else:
    tangent=(self.r2[i]*n-dot[i]*self.q[i])/(max(perp[i],1.e-15)*max(self.r[i],1.e-15))
    p=self.pivot+self.q[i]*np.cos(THETA)+tangent*self.r[i]*np.sin(THETA)
  return p+self.margin*n

def _closest(simplex):
 best=None
 for k in range(1,min(4,len(simplex))+1):
  for inds in combinations(range(len(simplex)),k):
   v=np.asarray([simplex[i] for i in inds]);gram=v@v.T
   mat=np.block([[gram,np.ones((k,1))],[np.ones((1,k)),np.zeros((1,1))]])
   rhs=np.r_[np.zeros(k),1.]
   try:w=np.linalg.solve(mat,rhs)[:k]
   except np.linalg.LinAlgError:continue
   if min(w)<-1.e-9:continue
   p=w@v;norm=p@p
   if best is None or norm<best[0]:best=(norm,p,[simplex[i] for i,a in zip(inds,w) if a>1.e-10])
 if best is None:raise ValueError('no simplex')
 return best[1],best[2]

def _separated(a,b):
 delta=a.centre-b.centre
 if np.linalg.norm(delta)<1.e-9:delta=np.array([1.,0.,0.])
 simplex=[];v=delta
 for iteration in range(48):
  length=np.linalg.norm(v)
  if length<1.e-8:return None
  n=v/length
  point=a.support(-n)-b.support(n)
  gap=point@n
  if gap>1.e-7:return {'gap_mm':float(gap),'axis':n.tolist(),'iterations':iteration+1}
  if any(np.linalg.norm(point-x)<1.e-8 for x in simplex):return None
  simplex.append(point);v,simplex=_closest(simplex)
 return None


_LANES = ('A', 'B1', 'B2', 'C1', 'C2', 'C3', 'C4')
_KEY = 'aom_adjustment_audit'
_ISSUE = 'aom_adjustment_audit_issues'

# Reference: committed lattice-compatible library at 8e48c57. function source hashes
# are stable across Python AST versions and reject unreviewed installation edits.
_INSTALLATION_SOURCE_SHA256 = {'_bounding_box': '7ae9906970262ecfefdf31b85a6d79259451991fa6356b2aca1cf7c7efff4157', 'prism_mount_km100pm_bridged': '7fc8989bfbc5adad12b9c3dcc3031497f0a7e089f53670a158f09794de5cb9eb', 'surface_adapter_aom': '43be47bb298f74115272120c0bcaf30ad57dcfa96edf4e0cf55173e5022c9666', 'AOMO_3100_125': '9dd772a6acd5f22296c7f933268407f17d5b44b1745af6a6313f7b094a17bbdc', 'aom_adapter': 'a99f00f7eda024f2b493919af028f7d7bbdef2fa88ce9431ef9be46794170e8b', 'seat_placement': 'daf86b5ba77ad31aa6add1936fbadd13f9d580f5bc3307559ffd11bfbcbed92e', '_remove_lower_adapter': '7ff26e26166b9e0c08cbb4059e4b65d993873e9cc8887547c7c5ffec04653776', '_km_clearance': 'e2e046ce5a528ce89bb646efdb64a93eb50dd225f33a302404bc787a550b6dab', '_geometry': '3734b8d5eb22ab2a5513a584c02ce005c0baf5fd0385a01948e88f5d3c36938f', '_make_IntegralAOMBaseplate': 'ece5cc5f7351cb6f3235b2986d7b31c8451e8836216969c152770f7f9055e73b', 'integrate_aom': '08ee0c9cea82a64123b56a67d0bc3d18b470e18cd8733ab7122fb80a559982a4'}
_SEAT_CONSTANTS = {'SEAT_X_MIN': -9.179, 'SEAT_X_MAX': 5.2, 'PILL_MAX_OFFSET': (-30.8, -38, 0),
                   'KNOB_FLOOR_OFFSET': -.4, 'LIP_X': -7.15, 'LIP_Y': -15., 'LIP_WIDTH': 2.,
                   'LIP_LENGTH': 30., 'LIP_HEIGHT': 2., 'BEARING_FACE_Z': -1.231,
                   'AOM_APERTURE_LOCAL': (0., -.03, -.115)}


def _kind(obj):
    return type(getattr(obj, 'Proxy', None)).__name__


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _near(a, b, tolerance=2.e-5):
    return np.max(np.abs(np.asarray(a, float)-np.asarray(b, float))) <= tolerance


def _children(root):
    pending, seen, result = [root], set(), []
    while pending:
        obj = pending.pop()
        if obj.Name in seen:
            continue
        seen.add(obj.Name)
        result.append(obj)
        pending.extend(getattr(obj, 'ChildObjects', []))
    return result


def _local_topology(obj):
    inverse = obj.Placement.inverse()
    vertices, faces = obj.Mesh.Topology
    return np.asarray([tuple(inverse.multVec(v)) for v in vertices]), np.asarray(faces, int)


def _mesh_matches(actual, reference, tolerance=2.e-5):
    """Match placed-local vertices and the complete triangle multiset."""
    from scipy.spatial import cKDTree
    import km100pm_kinematic_geometry as joint
    p, f = joint._topology(*actual)
    q, g = joint._topology(*reference)
    if p.shape != q.shape or f.shape != g.shape:
        raise ValueError('Installed component topology differs from its unchanged source mesh')
    distance, ids = cKDTree(q).query(p)
    if max(distance) > tolerance or len(set(ids.tolist())) != len(q):
        raise ValueError('Installed component vertices differ from the unchanged source mesh')
    mapped = sorted(map(tuple, np.sort(ids[f], axis=1)))
    expected = sorted(map(tuple, np.sort(g, axis=1)))
    if mapped != expected:
        raise ValueError('Installed component triangle multiset differs from its unchanged source mesh')
    return {'vertices': len(p), 'facets': len(f), 'maximum_vertex_difference_mm': float(max(distance)),
            'triangle_multiset_matches': True}


def _contract(doc, info, source_module):
    design = info.get('aom_adjustment_design', {})
    if (info.get('mode') != 'splitting' or design.get('required') is not True or
            design.get('preserve_lattice_installation') is not True or
            design.get('full_catalogue_travel_certified') is not False or
            float(design.get('external_net_rotation_cone_deg', -1)) != 4. or
            float(design.get('external_clearance_margin_mm', -1)) != 1.):
        raise ValueError('Explicit unchanged-seat / external net-4-degree / 1-mm scope declaration required')
    plate = info.get('plate')
    if plate is None or plate.Document != doc or not plate.Drill or not plate.Shape.isValid():
        raise ValueError('Current valid machined native plate required')
    if not _near([float(plate.dx.Value), float(plate.dy.Value), float(plate.dz.Value),
                  float(plate.OpticsDz.Value)], [609.6, 355.6, 25.4, 12.7]):
        raise ValueError('Original plate dimensions or optical height changed')
    if _kind(plate) != 'IntegralAOMBaseplate':
        raise ValueError('The unchanged lattice IntegralAOMBaseplate implementation is required')
    entries = info.get('pre_aom_waveplates', [])
    if len(entries) != 7 or {e.get('lane') for e in entries} != set(_LANES):
        raise ValueError('Exactly seven actual AOM / entrance-HWP registrations required')
    actual = [o for o in doc.Objects if _kind(o) == 'AOMO_3100_125']
    if len(actual) != 7 or {e.get('aom') for e in entries} != {o.Name for o in actual}:
        raise ValueError('Registered AOM inventory differs from actual geometry')
    if source_module is None:
        raise ValueError('Current board source module or path required')
    source_path = Path(getattr(source_module, '__file__', source_module)).resolve(strict=True)
    constants = {}
    for node in ast.parse(source_path.read_text(encoding='utf-8-sig')).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ('ORDER', 'PLATE_IN'):
                    if target.id in constants:
                        raise ValueError('Ambiguous repeated source declaration: '+target.id)
                    constants[target.id] = ast.literal_eval(node.value)
    if tuple(constants.get('ORDER', ())) != _LANES or tuple(constants.get('PLATE_IN', ())) != (24, 14):
        raise ValueError('The seven lanes and 24 x 14 inch outline must remain unchanged')
    if hasattr(source_module, '__file__'):
        if tuple(source_module.ORDER) != _LANES or tuple(source_module.PLATE_IN) != (24, 14):
            raise ValueError('Loaded source constants differ from source file')
    return plate, entries


def _installed_assembly(doc, plate, entry, optomech, joint, source_stl):
    import FreeCAD as App
    aom = doc.getObject(entry['aom'])
    descendants = _children(aom)
    def one(kind):
        matches = [o for o in descendants if _kind(o) == kind]
        if len(matches) != 1:
            raise ValueError('Expected one '+kind+' in '+aom.Name)
        return matches[0]
    km, adapter = one('prism_mount_km100pm_bridged'), one('aom_adapter')
    if any(_kind(o) == 'surface_adapter_aom' for o in descendants):
        raise ValueError('Legacy removable lower adapter must not replace the integral lattice seat')
    if not aom.ApertureAlignmentApplied or not _near(tuple(aom.MeshApertureLocal), (0., -.03, -.115)):
        raise ValueError('Original AOM bore alignment correction changed')
    for key, expected in _SEAT_CONSTANTS.items():
        if not _near(getattr(optomech, key), expected):
            raise ValueError('Original lattice seat constant changed: '+key)
    relative_km = aom.Placement.inverse().multiply(km.Placement)
    relative_adapter = aom.Placement.inverse().multiply(adapter.Placement)
    if (not _near(tuple(relative_km.Base), (-30.3, -16.4, -24.5)) or
            not _near(tuple(relative_km.Rotation.multVec(App.Vector(1, 0, 0))), (1, 0, 0)) or
            not _near(tuple(relative_adapter.Base), (-17., -7.65, -17.1)) or
            not _near(tuple(relative_adapter.Rotation.multVec(App.Vector(1, 0, 0))), (0, -1, 0))):
        raise ValueError('KM100PM / upper adapter relative placement changed from lattice installation')
    for basis in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
        expected_adapter = (basis[1], -basis[0], basis[2])
        if not _near(tuple(relative_km.Rotation.multVec(App.Vector(*basis))), basis) or not _near(
                tuple(relative_adapter.Rotation.multVec(App.Vector(*basis))), expected_adapter):
            raise ValueError('Full relative component orientation differs from lattice installation')
    on_board = plate.Placement.inverse().multiply(aom.Placement)
    if abs(on_board.Base.z-.115) > 2.e-5:
        raise ValueError('AOM installation height differs from the unchanged lattice bore correction')
    km_local, km_faces = _local_topology(km)
    evidence = joint.audit(km_local, km_faces, source_stl_path=source_stl)
    if not evidence['passed']:
        raise ValueError('Actual KM100PM ideal contact proof failed: '+str(evidence['errors']))
    reference_adapter = optomech._import_stl('aom_adapter.stl', (0, 0, 0), (0, 0, 0))
    adapter_match = _mesh_matches(_local_topology(adapter), reference_adapter.Topology)
    reference_aom = optomech._import_stl('aomo_3100-125.stl', (0, 0, -90), (0, -7.65, -7.1))
    aom_match = _mesh_matches(_local_topology(aom), reference_aom.Topology)
    seats = [o for o in doc.Objects if _kind(o) == 'IntegralAOMSeat' and o.AOMRoot == aom]
    if len(seats) != 1 or seats[0].Baseplate != plate or not seats[0].Drill:
        raise ValueError('Exactly one enabled original IntegralAOMSeat per AOM required')
    seat = seats[0]
    relative_seat = seat.SeatRelativePlacement
    if not _near(tuple(relative_seat.Base), (-44.4, -3.65, -30.)):
        raise ValueError('Original integral-seat relative offset changed')
    for basis in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
        if not _near(tuple(relative_seat.Rotation.multVec(App.Vector(*basis))), basis):
            raise ValueError('Original integral-seat relative orientation changed')
    expected, support = optomech._geometry(seat)
    actual = seat.DrillPart
    if actual.isNull() or (not support.isNull() and support.Volume > 1.e-8) or (
            not seat.SupportPart.isNull() and seat.SupportPart.Volume > 1.e-8):
        raise ValueError('Missing seat cutter or unexpected standalone support geometry')
    common = actual.common(expected).Volume
    if (abs(actual.Volume-expected.Volume) > 1.e-5 or
            abs(common-expected.Volume) > 1.e-5):
        raise ValueError('Seat cutter differs from the unchanged lattice geometry generator')
    point = km.Placement.multVec(App.Vector(*evidence['common_pivot']['center_km_local_mm']))
    pivot = np.array(tuple(plate.Placement.inverse().multVec(point)))
    points, faces = joint._topology(km_local, km_faces)
    parts = joint._components(points, faces)
    transform = plate.Placement.inverse().multiply(km.Placement)
    shells = []
    for part in parts:
        q = np.asarray([tuple(transform.multVec(App.Vector(*p))) for p in part['points']])
        shells.append((part['index'], q))
    audit = {'lane': entry['lane'], 'aom': aom.Name, 'km': km.Name, 'upper_adapter': adapter.Name,
             'seat': seat.Name, 'pivot_board_mm': pivot.tolist(), 'ideal_contact_geometry': evidence,
             'upper_adapter_source_match': adapter_match, 'aom_source_match': aom_match,
             'upper_adapter_nominal_bottom_board_z_mm': float(plate.Placement.inverse().multVec(App.Vector(0, 0, adapter.Mesh.BoundBox.ZMin)).z),
             'aom_root_height_board_mm': float(on_board.Base.z),
             'seat_source_geometry_volume_mm3': float(expected.Volume),
             'seat_actual_geometry_volume_mm3': float(actual.Volume),
             'seat_common_volume_mm3': float(common), 'lattice_installation_unchanged': True}
    audit['original_seat_pose_limits'] = _seat_pose_counterexamples(plate, km, adapter, pivot)
    return aom, km, adapter, pivot, shells, audit


class _AxialControl:
    """Outer circular cylinder, arbitrary screw roll, and proven axial travel."""
    def __init__(self, name, points, axis, origin, travel, root):
        self.name, self.root = name, root
        self.axis = np.asarray(axis, float)
        self.axis = self.axis/np.linalg.norm(self.axis)
        self.origin = np.asarray(origin, float)
        self.margin = 1.
        self.clearance_margin = 1.
        q = np.asarray(points)-self.origin
        axial = q@self.axis
        self.lower, self.upper = float(min(axial)-travel), float(max(axial)+travel)
        self.radius = float(max(np.linalg.norm(q-np.outer(axial, self.axis), axis=1)))
        self.centre = self.origin+(self.lower+self.upper)/2*self.axis
        self.bbox = np.array([[self.support(-n)@n, self.support(n)@n] for n in np.eye(3)])
        self.evidence = {'model': 'actual_mesh_circumscribed_cylinder_plus_axial_travel_and_arbitrary_roll',
                        'axis_board': self.axis.tolist(), 'axis_origin_board_mm': self.origin.tolist(),
                        'radius_mm': self.radius, 'axial_range_including_travel_mm': [self.lower, self.upper],
                        'maximum_axial_travel_each_way_mm': float(travel), 'extra_clearance_mm': self.margin}

    def support(self, direction):
        n = direction/np.linalg.norm(direction)
        axial = float(n@self.axis)
        radial = n-axial*self.axis
        radius = np.linalg.norm(radial)
        point = self.origin+(self.upper if axial >= 0. else self.lower)*self.axis
        if radius > 1.e-14:
            point = point+self.radius*radial/radius
        return point+self.margin*n


def _pairs(bodies, moving):
    unresolved, witnesses, checked = [], [], 0
    minimum = None
    for name, a in moving.items():
        for other, b in bodies.items():
            # Within one AOM assembly the maintained sphere/cone and attachment
            # interfaces are intentional. They are outside this EXTERNAL audit.
            if a.root == b.root or (other in moving and other < name):
                continue
            axis_gaps = np.maximum(a.bbox[:, 0]-b.bbox[:, 1], b.bbox[:, 0]-a.bbox[:, 1])
            box_gap = float(max(axis_gaps))
            if box_gap >= 0.:
                lower = box_gap+a.clearance_margin+b.clearance_margin
                if minimum is None or lower < minimum['clearance_lower_bound_mm']:
                    minimum = {'moving': name, 'other': other, 'clearance_lower_bound_mm': lower,
                               'method': 'axis_aligned_continuous_envelope_separating_plane'}
                continue
            checked += 1
            evidence = _separated(a, b)
            if evidence is None:
                unresolved.append({'moving': name, 'other': other, 'moving_root': a.root,
                                   'other_root': b.root, 'status': 'unresolved_continuous_convex_envelope_overlap'})
            else:
                witnesses.append({'moving': name, 'other': other, **evidence})
                lower = evidence['gap_mm']+a.clearance_margin+b.clearance_margin
                if minimum is None or lower < minimum['clearance_lower_bound_mm']:
                    minimum = {'moving': name, 'other': other, 'clearance_lower_bound_mm': lower,
                               'method': 'continuous_support_function_separating_plane', **evidence}
    return {'bounding_candidates_tested': checked, 'unresolved': unresolved,
            'separating_plane_witnesses': witnesses, 'passed': not unresolved,
            'minimum_certified_external_clearance': minimum if not unresolved else None,
            'minimum_scope': 'A conservative lower bound, not a nearest-distance optimizer; includes the required margin after BREP tessellation uncertainty.'}


def _foreign_beams(bodies, moving, info):
    unresolved, tested = [], 0
    lanes = {entry['aom']: entry['lane'] for entry in info['pre_aom_waveplates']}
    for path in info['paths']:
        points = path.get('points', [])
        if len(points) < 2:
            raise ValueError('Registered optical path has fewer than two actual vertices')
        radius = max(path.get('envelope', [.6]))
        for index, (p, q) in enumerate(zip(points, points[1:])):
            xyz = np.asarray([[p[0], p[1], 0.], [q[0], q[1], 0.]])
            ray = _Body('beam', xyz, margin=max(.6, radius))
            for name, a in moving.items():
                lane = next((v for root, v in lanes.items() if bodies[root].root == a.root), None)
                if path.get('name') == lane+' lane':
                    continue
                if np.any(a.bbox[:, 0] >= ray.bbox[:, 1]) or np.any(a.bbox[:, 1] <= ray.bbox[:, 0]):
                    continue
                tested += 1
                if _separated(a, ray) is None:
                    unresolved.append({'moving': name, 'beam_path': path['name'], 'segment': index})
    return {'passed': not unresolved, 'pairs_tested': tested, 'unresolved': unresolved,
            'scope': 'Unchanged nominal foreign RF-off rays versus continuous physical envelopes. '
                     'The tuned AOM optical axis, RF-on order and full adjustment-control access are not certified.'}


class _XYProjection:
    def __init__(self, body):
        self.body = body
        self.centre = body.centre.copy()
        self.centre[2] = 0.

    def support(self, direction):
        direction = direction.copy()
        direction[2] = 0.
        point = self.body.support(direction).copy()
        point[2] = 0.
        return point


def _dynamic_knob_projection(bodies, moving, info, knob_names):
    unresolved, tested = [], 0
    for path in info['paths']:
        radius = max(.6, max(path.get('envelope', [.6])))
        for index, (p, q) in enumerate(zip(path['points'], path['points'][1:])):
            ray = _Body('nominal ray', [[p[0], p[1], 0.], [q[0], q[1], 0.]], margin=radius)
            for name in knob_names:
                body = moving[name]
                # A knob entirely below the lowest beam edge cannot have a
                # beam underneath it. Every other knob is tested in XY,
                # including on its own AOM path; no whole-lane exemption.
                if body.bbox[2, 1] < -radius:
                    continue
                if (np.any(body.bbox[:2, 0] >= ray.bbox[:2, 1]) or
                        np.any(body.bbox[:2, 1] <= ray.bbox[:2, 0])):
                    continue
                tested += 1
                if _separated(_XYProjection(body), _XYProjection(ray)) is None:
                    unresolved.append({'control': name, 'beam_path': path['name'], 'segment': index})
    return {'passed': not unresolved, 'pairs_tested': tested, 'unresolved': unresolved,
            'scope': 'All 28 actual KM knurled heads and complete shafts, all nominal paths, continuous external 4-degree reserve; '
                     'no above-beam knob may pass over a nominal ray.'}


def _rf_swept_reservations(bodies, info):
    candidates = []
    regions = [r for r in info['service_regions'] if r.get('kind') == 'aom_sma']
    if len(regions) != 7:
        raise ValueError('Exactly seven actual nominal RF reservations required')
    for region in regions:
        if float(region['length_mm']) < 38.1 or float(region['width_mm']) < 20.:
            raise ValueError('RF reservation is smaller than the required 1.5 inches by 20 mm')
        owner = bodies[region['owner']]
        origin = np.r_[region['origin_xy_mm'], 0.]
        direction = np.r_[region['direction_xy'], 0.]
        normal = np.array([-direction[1], direction[0], 0.])
        points = [origin+direction*x+normal*y for x in (0., float(region['length_mm']))
                  for y in (-float(region['width_mm'])/2, float(region['width_mm'])/2)]
        reserve = _Body(region['name'], points, pivot=owner.pivot)
        for name, body in bodies.items():
            if body.root == owner.root:
                continue
            if (np.any(reserve.bbox[:2, 0] >= body.bbox[:2, 1]) or
                    np.any(reserve.bbox[:2, 1] <= body.bbox[:2, 0])):
                continue
            if _separated(_XYProjection(reserve), _XYProjection(body)) is None:
                candidates.append({'reservation': region['name'], 'object': name, 'root': body.root,
                    'status': 'conservative_swept_service_projection_candidate_not_actual_cable_collision'})
    return {'continuous_service_rectangle_candidates': candidates,
            'actual_RF_elbow_or_cable_geometry_modeled': False,
            'continuous_RF_cable_motion_certified': False,
            'required_length_mm': 38.1, 'source_length_mm': 40., 'source_width_mm': 20.,
            'warning': 'Nominal 40 x 20 mm service rectangles remain subject to the independent native service audit. '
                       'Rigidly sweeping those planning rectangles can overlap nearby controls. They are not '
                       'measured elbow/cable solids, so these candidates are reported as additional routing limitations, '
                       'not cleared by the external installed-hardware PASS.'}


def _seat_pose_counterexamples(plate, km, adapter, pivot_board):
    import FreeCAD as App
    inverse = plate.Placement.inverse()
    points = np.asarray([tuple(inverse.multVec(v)) for v in adapter.Mesh.Topology[0]])
    top = -float(plate.OpticsDz.Value)
    nominal_gap = float(points[:, 2].min()-top)
    if abs(nominal_gap-.715) > 2.e-5:
        raise ValueError('Upper adapter to original plate-top clearance changed from 0.715 mm')
    q = points-pivot_board
    radius = np.linalg.norm(q, axis=1)
    projection = -q[:, 2]
    perpendicular = np.sqrt(np.maximum(0., radius*radius-projection*projection))
    def min_z(degrees):
        angle = math.radians(degrees)
        maximum = np.where(projection >= radius*math.cos(angle), radius,
                           projection*math.cos(angle)+perpendicular*math.sin(angle))
        return float(pivot_board[2]-max(maximum))
    lo, hi = 0., 4.
    for unused in range(42):
        mid = (lo+hi)/2
        if min_z(mid) >= top:
            lo = mid
        else:
            hi = mid
    pivot_world = plate.Placement.multVec(App.Vector(*pivot_board))
    samples = []
    world_vertices = adapter.Mesh.Topology[0]
    for axis_name, axis_local in (('KM-local Y', (0, 1, 0)), ('KM-local Z', (0, 0, 1))):
        axis = km.Placement.Rotation.multVec(App.Vector(*axis_local))
        for degrees in (-4., 4.):
            rotation = App.Rotation(axis, degrees)
            moved = [pivot_world+rotation.multVec(v-pivot_world) for v in world_vertices]
            inside = []
            for point in sorted(moved, key=lambda v: inverse.multVec(v).z):
                if inverse.multVec(point).z >= top:
                    break
                if plate.Shape.isInside(point, 1.e-5, False):
                    inside.append(list(inverse.multVec(point)))
                    if len(inside) == 3:
                        break
            samples.append({'ideal_rigid_pose_axis': axis_name, 'degrees': degrees,
                            'upper_adapter_vertices_inside_actual_plate_board_mm': inside})
    return {'nominal_adapter_gap_above_uncut_top_mm': nominal_gap,
            'sufficient_net_angle_adapter_above_uncut_top_deg': lo,
            'sufficient_bound_scope': 'Only the upper adapter versus an uncut plane; not an overall usable mount range.',
            'sampled_pose_counterexamples': samples,
            'full_catalogue_travel_certified': False,
            'warning': 'These actual interior points prove the original seat/plate can block some ideal poses. '
                       'Empty samples are not proof of collision-free continuous motion.'}


def apply(report, doc, info, source_module=None):
    """Add this audit and its own issue count; preserve all other evidence."""
    result = {'schema': 'aom_adjustment_audit/1', 'document': doc.Name, 'passed': False,
              'ideal_contact_geometry_passed': False, 'external_hardware_clearance_passed': False,
              'lattice_installation_unchanged': False, 'scope_contract_passed': False,
              'full_catalogue_travel_certified': False, 'errors': [], 'assemblies': [],
              'scope': {'external_net_rotation_cone_deg': 4., 'extra_clearance_mm': 1.,
                        'actuator_translation_and_arbitrary_screw_roll_included': True,
                        'continuous_not_sampled': True, 'simultaneous_two_axis_plus_minus_4_certified': False,
                        'same_assembly_relative_motion_certified': False, 'same_assembly_pairs_excluded': True, 'original_seat_motion_certified': False,
                        'manufacturing_tolerances_or_joint_play_certified': False,
                        'spring_deformation_or_unmodeled_flexible_parts_certified': False,
                        'all_setting_table_fit_certified': False},
              'existing_seat_limitation': {'warning': 'The unchanged lattice upper adapter has only 0.715 mm '
                  'nominal clearance above uncut plate top. Pitch can meet the original plate before catalogue travel. '
                  'No deeper pocket or mounting-height change is permitted; this external clearance PASS is not a '
                  'full mechanical +/-4-degree PASS.'},
              'preserved_summary_counts': deepcopy(report.get('summary_counts', {})),
              'source_provenance': {'audit_path': str(Path(__file__).resolve()), 'audit_sha256': _hash(__file__)}}
    report[_KEY] = result
    try:
        import ta_projection_audit as projection
        import km100pm_kinematic_geometry as joint
        from PyOpticL import optomech
        import scipy
        result['native_runtime_dependencies'] = {'numpy_version': np.__version__, 'numpy_path': np.__file__,
            'scipy_version': scipy.__version__, 'scipy_path': scipy.__file__}
        plate, entries = _contract(doc, info, source_module)
        library_source = Path(optomech.__file__).read_text(encoding='utf-8-sig')
        nodes = ast.parse(library_source).body
        hashes = {node.name: hashlib.sha256(ast.get_source_segment(library_source, node).encode()).hexdigest()
                  for node in nodes if isinstance(node, (ast.FunctionDef, ast.ClassDef))
                  and node.name in _INSTALLATION_SOURCE_SHA256}
        if hashes != _INSTALLATION_SOURCE_SHA256:
            raise ValueError('Original lattice installation implementation differs from committed reference')
        result['lattice_installation_source_reference'] = {'commit': '8e48c57', 'geometry_function_source_sha256': hashes,
                                                        'seat_constants': deepcopy(_SEAT_CONSTANTS)}
        result['scope_contract_passed'] = True
        repo = Path(__file__).resolve().parents[1]
        result['source_provenance'].update({'board_path': str(Path(getattr(source_module, '__file__', source_module)).resolve()),
            'board_sha256': _hash(getattr(source_module, '__file__', source_module)), 'optomech_path': str(Path(optomech.__file__).resolve()),
            'optomech_sha256': _hash(optomech.__file__), 'joint_helper_path': str(Path(joint.__file__).resolve()),
            'joint_helper_sha256': _hash(joint.__file__)})
        # Derive ownership from current parent links, not a stale saved report.
        root_objects = {obj.Name: label for label, obj in info['roots'].items()}
        if len(root_objects) != len(info['roots']):
            raise ValueError('Duplicate actual optical roots in current board info')
        owner = {}
        for obj in doc.Objects:
            current, seen = obj, set()
            while current is not None and current.Name not in seen:
                seen.add(current.Name)
                if current.Name in root_objects:
                    owner[obj.Name] = root_objects[current.Name]
                    break
                current = getattr(current, 'ParentObject', None)
        saved_owner = {name: root for root, names in report.get('roots', {}).items() for name in names}
        for name, label in owner.items():
            if name in saved_owner and saved_owner[name] != label:
                raise ValueError('Saved report ownership disagrees with actual current assembly: '+name)

        bodies, moving, geometry, knob_names = {}, {}, {}, []
        inverse = plate.Placement.inverse()
        path_objects = {p.get('object') for p in info.get('paths', [])}
        for obj in doc.Objects:
            if obj == plate or obj.Name in path_objects or _kind(obj) in projection._MACHINING:
                continue
            g = projection._board_geometry(obj, inverse)
            if g is None:
                continue
            geometry[obj.Name] = g
            if _kind(obj) != 'prism_mount_km100pm_bridged':
                bodies[obj.Name] = _Body(obj.Name, g['xyz'], margin=g['uncertainty_mm'], root=owner.get(obj.Name, obj.Name))
        if len(geometry) < 200:
            raise ValueError('Actual board physical inventory unexpectedly incomplete')
        for entry in entries:
            aom, km, adapter, pivot, shells, evidence = _installed_assembly(doc, plate, entry, optomech, joint, repo/'stl'/'KM100PM.stl')
            result['assemblies'].append(evidence)
            root = owner.get(aom.Name, aom.Name)
            fixed = evidence['ideal_contact_geometry']['fixed_component_indices']
            actuators = evidence['ideal_contact_geometry'].get('actuators', [])
            if len(actuators) != 2 or not all(a['finite_contact']['passed'] for a in actuators):
                raise ValueError('Both finite actuator contacts and their actual axial travel bounds are required')
            controls = {index: actuator for actuator in actuators for index in actuator['components']}
            if len(controls) != 6:
                raise ValueError('Both shafts, knurled heads and small balls must have distinct motion assignments')
            import FreeCAD as App
            km_on_board = inverse.multiply(km.Placement)
            evidence['control_envelopes'] = []
            for index, points in shells:
                name = km.Name+'/shell%02d'%index
                if index in controls:
                    actuator = controls[index]
                    axis = tuple(km_on_board.Rotation.multVec(App.Vector(*actuator['axis_km_local'])))
                    origin = tuple(km_on_board.multVec(App.Vector(*actuator['axis_origin_km_local'])))
                    b = _AxialControl(name, points, axis, origin,
                                      actuator['max_axial_travel_for_net4_deg_mm'], root)
                    evidence['control_envelopes'].append({'component': index, **b.evidence})
                else:
                    b = _Body(name, points, pivot=None if index in fixed else pivot,
                              margin=0. if index in fixed else 1., root=root)
                bodies[name] = b
                if index not in fixed:
                    moving[name] = b
                    part_evidence = evidence['ideal_contact_geometry']['components'][index]
                    if part_evidence['facets'] in (4260, 754) and part_evidence['bounds_km_local_mm'][0] < -24.:
                        knob_names.append(name)
            for obj in (aom, adapter):
                g = geometry[obj.Name]
                bodies[obj.Name] = moving[obj.Name] = _Body(obj.Name, g['xyz'], pivot=pivot,
                    margin=1.+g['uncertainty_mm'], root=root)
        result['ideal_contact_geometry_passed'] = len(result['assemblies']) == 7
        result['lattice_installation_unchanged'] = all(e['lattice_installation_unchanged'] for e in result['assemblies'])
        result['external_hardware'] = _pairs(bodies, moving)
        result['foreign_nominal_beams'] = _foreign_beams(bodies, moving, info)
        if len(knob_names) != 28:
            raise ValueError('Both real KM100PM knurled heads and complete shafts required for all seven lanes')
        result['adjustment_knob_projection'] = _dynamic_knob_projection(bodies, moving, info, knob_names)
        result['external_hardware_clearance_passed'] = (result['external_hardware']['passed'] and
            result['foreign_nominal_beams']['passed'] and result['adjustment_knob_projection']['passed'])
        if not result['external_hardware_clearance_passed']:
            result['errors'].append('Unresolved external hardware or foreign-beam continuous envelope candidates')
        result['rf_reservation'] = _rf_swept_reservations(bodies, info)
        if report.get('summary_counts', {}).get('service_clearance_issues') != 0:
            result['errors'].append('The independent nominal RF/service audit did not pass')
    except Exception as exc:
        result['errors'].append(str(exc))
        result['failure_traceback'] = traceback.format_exc()
    result['passed'] = (result['scope_contract_passed'] and result['ideal_contact_geometry_passed'] and
                        result['lattice_installation_unchanged'] and result['external_hardware_clearance_passed'] and not result['errors'])
    result['counts'] = {'verified_aom_assemblies': len(result['assemblies']), 'errors': len(result['errors'])}
    report.setdefault('summary_counts', {})[_ISSUE] = len(result['errors']) or int(not result['passed'])
    return report
