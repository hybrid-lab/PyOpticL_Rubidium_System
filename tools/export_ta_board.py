"""Export a production board in FreeCAD (not a system-Python script).

Call export_board(doc, info, full_audit_report, output_directory, fcstd_directory).
The defaults export Rubidium_system/TA_Baseplate_V9.py. For another board,
provide stem and source_module; the latter accepts a loaded module, a dotted
repository module name, or a source-file path. The caller must build that source
with this repository's optomech.py installed as PyOpticL.optomech. The report is
the existing V9 board_tools.inspect_board result augmented by the projection
audit, and by km05t_audit for any KM05T fiber heads.
"""
import collections
import hashlib
import importlib
import json
import math
from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui
import Part


def hole_census(plate):
    """Count full cylindrical holes; exclude rounded pocket corners."""
    shape, acc = plate.Shape, {}
    top, bottom = shape.BoundBox.ZMax, shape.BoundBox.ZMin
    specifications = [(3.4544, '8-32 tap drill (3.454)', 'TAP'),
                      (4.3688, '8-32 clearance (4.369)', 'PLAIN'),
                      (5.1054, '1/4-20 tap drill (5.105)', 'TAP'),
                      (6.604, '1/4-20 clearance (6.604)', 'PLAIN'),
                      (14.2875, '1/4-20 washer counterbore (14.288)', 'COUNTERBORE')]
    for face in shape.Faces:
        surface = face.Surface
        if type(surface).__name__ != 'Cylinder' or abs(abs(surface.Axis.z)-1) > 1e-6:
            continue
        u0, u1, _, _ = face.ParameterRange
        key = (round(surface.Radius*2, 2), round(surface.Center.x, 2), round(surface.Center.y, 2))
        cur = acc.setdefault(key, [0., math.inf, -math.inf])
        cur[0] += abs(u1-u0)
        cur[1] = min(cur[1], face.BoundBox.ZMin)
        cur[2] = max(cur[2], face.BoundBox.ZMax)
    groups, arcs = collections.defaultdict(list), 0
    for (diameter, x, y), (span, low, high) in acc.items():
        if span < 2*math.pi-.05:
            arcs += 1
            continue
        matches = [(name, kind) for value, name, kind in specifications if abs(diameter-value) < .06]
        if not matches:
            raise ValueError('Unclassified hole diameter: %s at %s' % (diameter, (x, y)))
        name, kind = matches[0]
        groups[x, y].append(dict(diameter=diameter, low=low, high=high, spec=name, kind=kind))
    features = []
    for (x, y), group in groups.items():
        group.sort(key=lambda h: -h['diameter'])
        low, high = min(h['low'] for h in group), max(h['high'] for h in group)
        features.append(dict(x=x, y=y, diameters=[h['diameter'] for h in group],
                             spec=' + '.join(h['spec'] for h in group), kind=group[-1]['kind'],
                             through=low-bottom < .05 and top-high < .05,
                             depth_mm=round(high-low, 3), z_top=round(high, 3)))
    return dict(plate=plate.Label, corner_fillet_faces=arcs,
                features=sorted(features, key=lambda h: (h['spec'], h['x'], h['y'])))


def plate_edges(plate):
    box, levels = plate.Shape.BoundBox, {}
    for face in plate.Shape.Faces:
        if type(face.Surface).__name__ != 'Plane' or abs(abs(face.normalAt(0, 0).z)-1) > 1e-6:
            continue
        z = round(face.BoundBox.ZMin, 3)
        if abs(z-box.ZMin) < .01:
            continue
        for edge in face.Edges:
            points = edge.discretize(Deflection=.04)
            if len(points) >= 2:
                levels.setdefault(str(z), []).append([(round(p.x, 3), round(p.y, 3)) for p in points])
    return dict(plate=plate.Label, bbox=[box.XMin, box.YMin, box.XMax, box.YMax],
                top_z=box.ZMax, levels=levels)


def _source_path(repo, source_module):
    if hasattr(source_module, '__file__'):
        path = Path(source_module.__file__)
    elif isinstance(source_module, Path) or str(source_module).endswith('.py'):
        path = Path(source_module)
    else:
        path = Path(*str(source_module).split('.')).with_suffix('.py')
    path = (path if path.is_absolute() else repo/path).resolve()
    if not path.is_file():
        raise FileNotFoundError('Board source for provenance does not exist: '+str(path))
    return path


def export_board(doc, info, report, output_directory, fcstd_directory=None, *,
                 stem='TA_Board_V9', source_module='Rubidium_system.TA_Baseplate_V9'):
    from PyOpticL import optomech, layout
    import ta_projection_audit
    if not stem or Path(stem).name != stem or any(c in stem for c in '/\\'):
        raise ValueError('stem must be a filename without directory components')
    repo = Path(__file__).resolve().parents[1]
    board_source = _source_path(repo, source_module)
    output = Path(output_directory)
    (output/'StepFile').mkdir(parents=True, exist_ok=True)
    plate = info['plate']
    doc.recompute()
    if not plate.Shape.isValid() or len(plate.Shape.Solids) != 1:
        raise ValueError('Expected one valid machined plate solid')
    projection = report['projection_audit']
    if not projection['mechanical_projection_passed']:
        raise ValueError('Resolve projection audit failures before export')
    # V9.7 end covers are deliberately reused without changing their geometry.
    # Preserve their explicit optical block in the delivered report; mechanical
    # export is not a claim that these unfinished covers transmit the beam.
    has_covers = any(o.get('class') == 'SlidingCellCover' for o in report['objects'])
    if has_covers and any(key not in projection for key in ('optical_path_readiness', 'required_follow_up')):
        raise ValueError('Cell-cover optical status and required follow-up must be explicit')
    report['optical_path_readiness'] = projection.get(
        'optical_path_readiness', 'not_certified_by_a_mechanical_projection_audit')
    report['required_follow_up'] = projection.get('required_follow_up', [])
    has_km05t = any(o.get('class') == 'fiberport_mount_km05T' for o in report['objects'])
    km05t_report = report.get('km05t_audit')
    if has_km05t and not km05t_report:
        raise ValueError('KM05T heads require their explicit mounting and service audit')
    if km05t_report is not None and km05t_report.get('passed') is not True:
        raise ValueError('Resolve KM05T mounting/service audit failures before export')
    if info.get('mode') == 'ta' and report.get('table_envelope', {}).get('passed') is not True:
        raise ValueError('TA plate needs a passing table/cable envelope audit')
    issues = {key: value for key, value in report['summary_counts'].items()
              if value and key not in ('outside_plate_xy', 'bbox_overlap_candidates', 'unrelated_beam_proximity')}
    if issues:
        raise ValueError('Resolve engineering audit failures before export: '+repr(issues))
    if any(any('Invalid' in state or 'Error' in state for state in obj.State) for obj in doc.Objects):
        raise ValueError('Document contains an invalid/error object')
    size = info['plate_size_mm']
    inches = [format(d/25.4, 'g').replace('.', 'p') for d in size[:2]]
    step_name = stem+'_baseplate_'+'x'.join(inches)+'in.step'
    step_path = output/'StepFile'/step_name
    plate.Shape.exportStep(str(step_path))
    # Normalize OpenCascade's record-separator whitespace before round-trip QA.
    step_path.write_text('\n'.join(line.rstrip() for line in step_path.read_text(
        encoding='utf-8').splitlines())+'\n', encoding='utf-8', newline='\n')
    check = Part.Shape()
    check.read(str(step_path))
    ratio = check.Volume/plate.Shape.Volume
    if len(check.Solids) != 1 or not check.isValid() or abs(ratio-1.) > 1e-7:
        raise ValueError('STEP round-trip validation failed')
    report['step_round_trip'] = dict(file='StepFile/'+step_name, valid=check.isValid(),
                                    solids=len(check.Solids), volume_ratio=ratio,
                                    actual_dimensions_mm=[check.BoundBox.XLength, check.BoundBox.YLength, check.BoundBox.ZLength])
    board_key = (board_source.relative_to(repo).as_posix() if board_source.is_relative_to(repo)
                 else str(board_source)+' (external board source)')
    source_files = {'optomech.py': Path(optomech.__file__),
                    'PyOpticL/layout.py (external runtime)': Path(layout.__file__),
                    board_key: board_source,
                    'tools/ta_projection_audit.py': Path(ta_projection_audit.__file__),
                    'tools/export_ta_board.py': Path(__file__),
                    'tools/render_ta_documents.py': repo/'tools/render_ta_documents.py',
                    'tools/test_ta_projection.py': repo/'tools/test_ta_projection.py'}
    if km05t_report is not None:
        km05t_source = Path(importlib.import_module('km05t_audit').__file__).resolve()
        key = (km05t_source.relative_to(repo).as_posix() if km05t_source.is_relative_to(repo)
               else str(km05t_source)+' (external audit runtime)')
        source_files[key] = km05t_source
    for key, filename in (('table_envelope', 'table_envelope_audit.py'),
                          ('mesh_candidate_refinement', 'refine_mesh_candidates.py')):
        if key in report:
            source_files['tools/'+filename] = repo/'tools'/filename
    report['source_provenance'] = {name: hashlib.sha256(path.read_bytes()).hexdigest()
                                   for name, path in source_files.items()}
    report['freecad_version'] = list(App.Version())
    for key in ('fiber_tail_pairs', 'lane_geometry', 'beam_crossings'):
        if key in info:
            report[key] = info[key]
    for name, data in ((stem+'_validation.json', report), (stem+'_holes.json', hole_census(plate)),
                       (stem+'_plate_edges.json', plate_edges(plate))):
        (output/name).write_text(json.dumps(data, indent=2, default=str)+'\n', encoding='utf-8', newline='\n')
    view = Gui.activeDocument().activeView()
    view.setCameraType('Orthographic')
    view.viewTop()
    view.fitAll()
    Gui.updateGui()
    view.saveImage(str(output/(stem+'_top.png')), 2200, 2200, 'White')
    view.viewAxonometric()
    view.fitAll()
    Gui.updateGui()
    view.saveImage(str(output/(stem+'_3D.png')), 2200, 1800, 'White')
    view.viewTop()
    view.fitAll()
    if fcstd_directory is not None:
        model_output = Path(fcstd_directory)
        model_output.mkdir(parents=True, exist_ok=True)
        doc.saveAs(str(model_output/(stem+'.FCStd')))
    return step_path
