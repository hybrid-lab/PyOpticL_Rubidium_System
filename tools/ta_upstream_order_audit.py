"""Verify actual TA / two folds / HWP / isolator / QWP order in native CAD."""
import math
import FreeCAD as App


def audit(doc, info):
    labels = ['TA', 'TA steering fold 1', 'TA steering fold 2', 'TA output HWP',
              'Hana long isolator', 'TA output QWP', 'Common post-isolator fold 1']
    errors, evidence = [], []
    try:
        plate = info['plate']
        if info.get('mode') != 'ta' or plate.Document != doc:
            raise ValueError('Current TA document and plate required')
        inverse = plate.Placement.inverse()
        paths = [p for p in info['paths'] if p['name'] == 'TA supply']
        if len(paths) != 1:
            raise ValueError('Exactly one TA supply path required')
        points = paths[0]['points']
        accumulated = [0.]
        for a,b in zip(points,points[1:]): accumulated.append(accumulated[-1]+math.dist(a,b))
        previous = -1.
        for label in labels:
            obj = info['roots'][label]
            if obj.Document != doc or doc.getObject(obj.Name) != obj:
                raise ValueError('Actual upstream object belongs to another document')
            p = inverse.multVec(obj.Placement.Base)
            matches = [i for i,q in enumerate(points) if math.dist([p.x,p.y],q)<1.e-6]
            if len(matches) != 1 or abs(p.z)>1.e-6:
                raise ValueError(label+': actual optical datum is not its unique registered vertex')
            index = matches[0]
            travel = accumulated[index]
            if travel<=previous+1.e-6:
                raise ValueError('Actual upstream optical order differs from the original sequence')
            if label in ('TA output HWP','TA output QWP','Hana long isolator'):
                axis = inverse.Rotation.multVec(obj.Placement.Rotation.multVec(App.Vector(1,0,0)))
                delta = [points[index+1][i]-points[index-1][i] for i in range(2)]
                length = math.hypot(*delta)
                if length<=0 or abs(abs(sum(axis[i]*delta[i]/length for i in range(2)))-1)>1.e-6:
                    raise ValueError(label+': actual transmission axis is not aligned with the ray')
            if 'fold' in label:
                a,b,c=points[index-1],points[index],points[index+1]
                u=[b[i]-a[i] for i in range(2)]; v=[c[i]-b[i] for i in range(2)]
                du,dv=math.hypot(*u),math.hypot(*v)
                n=inverse.Rotation.multVec(obj.Placement.Rotation.multVec(App.Vector(1,0,0)))
                dot=sum(u[i]/du*n[i] for i in range(2))
                incidence=math.degrees(math.acos(min(1,abs(dot))))
                residual=math.hypot(*[u[i]/du-2*dot*n[i]-v[i]/dv for i in range(2)])
                if abs(incidence-45)>1.e-6 or residual>1.e-6:
                    raise ValueError(label+': actual mirror does not produce its 45 degree fold')
            evidence.append({'label':label,'object':obj.Name,'actual_xyz_mm':list(p),
                             'path_vertex':index,'propagation_from_TA_mm':travel})
            previous=travel
    except Exception as exc:
        errors.append(str(exc))
    return {'passed':not errors,'errors':errors,'actual_sequence':evidence,
            'expected_sequence':labels,'scope':'Actual native centres, axes, mirror normals and original upstream order; independent clearance audits remain required.'}
