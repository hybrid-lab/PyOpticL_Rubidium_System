"""FreeCAD regression probe: an elevated knob must block the XY route.

Call negative_knob_projection_test(doc, info, ta_projection_audit). It adds
one ray only to a copied metadata container, never to the CAD document.
"""


def negative_knob_projection_test(doc, info, audit_module):
    before_names = tuple(obj.Name for obj in doc.Objects)
    before_path_count = len(info['paths'])
    radius = .05
    inverse = info['plate'].Placement.inverse()
    target = next((obj for obj in doc.Objects
                   if audit_module._kind(obj) == 'prism_mount_km100pm_bridged'
                   and obj.Baseplate == info['plate']), None)
    subcomponent = None
    if target is not None:
        geometry = audit_module._board_geometry(target, inverse)
        _, controls = audit_module._km_controls(geometry)
        subcomponent = 'upper adjustment knob'
        knob = next(part['geometry'] for part in controls
                    if part['name'] == subcomponent)
    else:
        # The single-output TA has no AOM/KM100PM. Use a real, separately
        # modelled M05 upper adjuster, without modifying any CAD placement.
        candidates = []
        for obj in doc.Objects:
            if (audit_module._kind(obj) != 'thumbscrew_hkts_5_64' or
                    getattr(obj, 'Baseplate', None) != info['plate']):
                continue
            parent = getattr(obj, 'ParentObject', None)
            if parent is None or audit_module._kind(parent) != 'mirror_mount_M05':
                continue
            geometry = audit_module._board_geometry(obj, inverse)
            if geometry['z_range_mm'][0] > radius:
                candidates.append((obj, geometry))
        if not candidates:
            raise AssertionError('No real elevated KM100PM or M05 adjustment knob to test')
        target, knob = candidates[0]
    assert knob['z_range_mm'][0] > radius

    def projected_area2(face):
        a, b, c = [knob['xy'][index] for index in face]
        return abs(audit_module._cross(a, b, c))

    face = max(knob['faces'], key=projected_area2)
    assert projected_area2(face) > 1e-6
    cx = sum(knob['xy'][i][0] for i in face)/3.
    cy = sum(knob['xy'][i][1] for i in face)/3.
    name = '__NEGATIVE_TEST_UNDER_KM_UPPER_KNOB__' if subcomponent else '__NEGATIVE_TEST_UNDER_M05_UPPER_KNOB__'
    assert all(p['name'] != name for p in info['paths'])
    probe = dict(name=name, points=[(cx-1., cy), (cx+1., cy)],
                 envelope=[radius, radius], object=None,
                 assumption='Deliberate test ray at optical z=0 under an elevated knob.')
    negative_info = dict(info)
    negative_info['paths'] = list(info['paths'])+[probe]
    result = audit_module.audit(doc, negative_info)
    hits = [hit for hit in result['thumbscrew_projection_hits'] if hit['path'] == name]
    targets = [hit for hit in hits if hit['object'] == target.Name
               and hit.get('subcomponent') == subcomponent]
    assert len(targets) == 1, targets
    assert targets[0]['status'] == 'projected_surface_hit'
    assert not result['mechanical_projection_passed']
    assert len(info['paths']) == before_path_count
    assert tuple(obj.Name for obj in doc.Objects) == before_names
    return dict(negative_test_passed=True, probe=probe, probe_z_mm=0.,
                target_object=target.Name, target_subcomponent=subcomponent,
                target_knob_z_range_mm=knob['z_range_mm'],
                target_hit_count=len(targets), all_new_thumb_hits=len(hits),
                target_hits=targets, audit_counts=result['counts'], model_unchanged=True)
