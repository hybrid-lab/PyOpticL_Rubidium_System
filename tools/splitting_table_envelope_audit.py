"""Check the complete Splitting board against a 28 x 15 inch table area.

Includes physical overhangs, RF/front access reservations, tail clamps, and
fiber corridors. A continuous translation is allowed; table-grid alignment
and mechanical support of overhanging parts are separate checks.
"""
import hashlib
from pathlib import Path

import table_envelope_audit as geometry


def audit(doc, info, board_report):
    plate = info['plate']
    inverse = plate.Placement.inverse()
    dx, dy, _ = info['plate_size_mm']
    table = [28*25.4, 15*25.4]
    errors, contributions = [], []

    def include(name, kind, bounds):
        contributions.append(dict(name=name, kind=kind, bounds_xy_mm=list(bounds)))

    if dx > 24*25.4+1.e-5 or dy > 14*25.4+1.e-5:
        errors.append('Splitting plate exceeds the retained 24 x 14 inch limit')
    include('Nominal plate allocation', 'plate', [0., 0., dx, dy])
    paths = {path.get('object') for path in info['paths']}
    for obj in doc.Objects:
        if obj.Name in paths or geometry._kind(obj) in geometry._MACHINING:
            continue
        owner = geometry._plate_link(obj)
        if owner is not None and owner != plate:
            continue
        try:
            actual = geometry._geometry_bbox(obj, inverse)
            if actual:
                bounds = actual['xyz_bounds_mm']
                include(obj.Name, 'physical_hardware', [bounds[i] for i in (0, 1, 3, 4)])
        except Exception as exc:
            errors.append(dict(object=obj.Name, error=repr(exc)))
    rf = []
    for region in info.get('service_regions', []):
        corners = geometry._rectangle(region['origin_xy_mm'], region['direction_xy'],
                                      region['length_mm'], region['width_mm'])
        include(region['name'], region['kind'], geometry._xy_bbox(corners))
        if region['kind'] == 'aom_sma':
            rf.append(region)
    if len(rf) != 7 or any(r['length_mm'] < 38.1 for r in rf):
        errors.append('Seven AOM RF reservations of at least 38.1 mm are required')
    fibers = board_report['fiber_clearance']
    if not fibers.get('passed') or len(fibers.get('fibers', [])) != 5:
        errors.append('A passing clearance report for all five fiber heads is required')
    for fiber in fibers.get('fibers', []):
        for key in ('clamp_reserved_span_xy_mm', 'corridor_xy_mm'):
            include(fiber['object']+' '+key, 'fiber_service', geometry._xy_bbox(fiber[key]))
    occupied = geometry._union([entry['bounds_xy_mm'] for entry in contributions])
    span = [occupied[2]-occupied[0], occupied[3]-occupied[1]]
    margins = [available-used for available, used in zip(table, span)]
    if min(margins) < -1.e-5:
        errors.append('Physical hardware and reserved services exceed the 28 x 15 inch area')
    return dict(schema='splitting_table_envelope/1', passed=not errors, errors=errors,
                nominal_plate_size_mm=[dx, dy], table_size_mm=table,
                occupied_bounds_xy_mm=occupied, occupied_size_mm=span,
                occupied_size_in=[value/25.4 for value in span],
                remaining_length_width_mm=margins,
                centered_translation_xy_mm=[-occupied[i]+margins[i]/2 for i in range(2)],
                extent_contributions=contributions,
                source_provenance={str(Path(path).name): hashlib.sha256(Path(path).read_bytes()).hexdigest()
                                   for path in (__file__, geometry.__file__)},
                scope='Continuous free placement including all physical overhangs and declared service reservations; '
                      'table-hole grid alignment, unmodeled fiber routing outside the plate, and overhang support are not certified.')
