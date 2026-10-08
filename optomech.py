from math import *
import json
from pathlib import Path

import FreeCAD as App
import Mesh
import numpy as np
import Part

from . import layout

stl_path = str(Path(__file__).parent.resolve()) + "/stl/"
drill_depth = 100
inch = 25.4

bolt_4_40 = {
    "clear_dia":0.120*inch,
    "tap_dia":0.089*inch,
    "head_dia":5.50,
    "head_dz":2.5 # TODO measure this
}

bolt_8_32 = {
    "clear_dia":0.172*inch,
    "tap_dia":0.136*inch,
    "head_dia":7,
    "head_dz":4.4
}

bolt_14_20 = {
    "clear_dia":0.260*inch,
    "tap_dia":0.201*inch,
    "head_dia":9.8,
    "head_dz":8,
    "washer_dia":9/16*inch
}

bolt_m2p5x4p5 = {
    "clear_dia":0.260*inch,
    "tap_dia":0.201*inch,
    "head_dia":9.8,
    "head_dz":8,
    "washer_dia":9/16*inch
}


bolt_M2_5 = {
    "clear_dia": 2.7,      # clearance hole diameter for M2.5
    "tap_dia": 2.05,       # tapping drill size for M2.5 threads
    "head_dia": 4.5,       # typical pan or button head diameter
    "head_dz": 2.0         # typical head thickness (varies by head type)
}

bolt_M4 = {
    "clear_dia": 4.3,     # closefit clearance
    "tap_dia": 3.3,       # tapping drill size for M4 by 0.7
    "head_dia": 7.0,      # example for socket cap
    "head_dz": 4.0        # head thickness (socket cap)
}

bolt_M6 = {
    "clear_dia": 6.6,     # closefit clearance
    "tap_dia": 5.0,       # drill size for M6 by 1.0 threads
    "head_dia": 10.0,     # example for socket cap
    "head_dz": 4.0        # head thickness
}

adapter_color = (0.6, 0.9, 0.6)
mount_color = (0.5, 0.5, 0.55)
glass_color = (0.5, 0.5, 0.8)
misc_color = (0.2, 0.2, 0.2)

# Used to tranform an STL such that it's placement matches the optical center
def _import_stl(stl_name, rotate, translate, scale=1):
    mesh = Mesh.read(stl_path+stl_name)
    mat = App.Matrix()
    mat.scale(App.Vector(scale, scale, scale))
    mesh.transform(mat)
    mesh.rotate(*np.deg2rad(rotate))
    mesh.translate(*translate)
    return mesh

def _bounding_box(obj, tol, fillet, x_tol=True, y_tol=True, z_tol=False, min_offset=(0, 0, 0), max_offset=(0, 0, 0), plate_off=0):
    if hasattr(obj, "Shape"):
        obj_body = obj.Shape.copy()
    elif hasattr(obj, "Mesh"):
        obj_body = obj.Mesh.copy()
    else:
        obj_body = obj
    obj_body.Placement = App.Placement()
    if hasattr(obj, "RelativePlacement"):
        obj_body.Placement = obj.RelativePlacement
        temp = obj
        while hasattr(temp, "ParentObject") and hasattr(temp.ParentObject, "RelativePlacement"):
            temp = temp.ParentObject
        #    obj_body.Placement *= temp.RelativePlacement
    global_bound = obj_body.BoundBox
    obj_body.Placement = App.Placement()
    bound = obj_body.BoundBox

    x_min, x_max = bound.XMin-tol*x_tol+min_offset[0], bound.XMax+tol*x_tol+max_offset[0]
    y_min, y_max = bound.YMin-tol*y_tol+min_offset[1], bound.YMax+tol*y_tol+max_offset[1]
    z_min = min(global_bound.ZMin-tol*z_tol+min_offset[2], -layout.inch/2+plate_off)-global_bound.ZMin+bound.ZMin
    z_max = max(global_bound.ZMax+tol*z_tol+max_offset[2], -layout.inch/2+plate_off)-global_bound.ZMax+bound.ZMax
    bound_part = _custom_box(dx=x_max-x_min, dy=y_max-y_min, dz=z_max-z_min,
                    x=x_min, y=y_min, z=z_min, dir=(1, 1, 1),
                    fillet=fillet, fillet_dir=(0, 0, 1))
    return bound_part

def _add_linked_object(obj, obj_name, obj_class, pos_offset=(0, 0, 0), rot_offset=(0, 0, 0), **args):
    new_obj = App.ActiveDocument.addObject(obj_class.type, obj_name)
    new_obj.addProperty("App::PropertyLinkHidden","Baseplate").Baseplate = obj.Baseplate
    new_obj.Label = obj_name
    obj_class(new_obj, **args)
    new_obj.setEditorMode('Placement', 2)
    new_obj.addProperty("App::PropertyPlacement","BasePlacement")
    if not hasattr(obj, "ChildObjects"):
        obj.addProperty("App::PropertyLinkListChild","ChildObjects")
    obj.ChildObjects += [new_obj]
    new_obj.addProperty("App::PropertyLinkHidden","ParentObject").ParentObject = obj
    new_obj.addProperty("App::PropertyPlacement","RelativePlacement").RelativePlacement
    rotx = App.Rotation(App.Vector(1,0,0), rot_offset[0])
    roty = App.Rotation(App.Vector(0,1,0), rot_offset[1])
    rotz = App.Rotation(App.Vector(0,0,1), rot_offset[2])
    new_obj.RelativePlacement.Rotation = App.Rotation(rotz*roty*rotx)
    new_obj.RelativePlacement.Base = App.Vector(*pos_offset)
    return new_obj

def _drill_part(part, obj, drill_obj):
    if hasattr(drill_obj, "DrillPart"):
        drill = drill_obj.DrillPart.copy()
        drill.Placement = obj.BasePlacement.inverse().multiply(drill.Placement)
        part = part.cut(drill)
    if hasattr(drill_obj, "ChildObjects"):
        for sub in drill_obj.ChildObjects:
            part = _drill_part(part, obj, sub)
    return part

def _custom_box(dx, dy, dz, x, y, z, fillet=0, dir=(0,0,1), fillet_dir=None):
    if fillet_dir == None:
        fillet_dir = np.abs(dir)
    part = Part.makeBox(dx, dy, dz)
    if fillet != 0:
        for i in part.Edges:
            if i.tangentAt(i.FirstParameter) == App.Vector(*fillet_dir):
                part = part.makeFillet(fillet-1e-3, [i])
    part.translate(App.Vector(x-(1-dir[0])*dx/2, y-(1-dir[1])*dy/2, z-(1-dir[2])*dz/2))
    part = part.fuse(part)
    return part

def _fillet_all(part, fillet, dir=(0, 0, 1)):
    for i in part.Edges:
        if i.tangentAt(i.FirstParameter) == App.Vector(*dir):
            try:
                part = part.makeFillet(fillet-1e-3, [i])
            except:
                pass
    return part

def _custom_cylinder(dia, dz, x, y, z, head_dia=0, head_dz=0, dir=(0, 0, -1), countersink=False):
    part = Part.makeCylinder(dia/2, dz, App.Vector(0, 0, 0), App.Vector(*dir))
    if head_dia != 0 and head_dz != 0:
        if countersink:
            part = part.fuse(Part.makeCone(head_dia/2, dia/2, head_dz, App.Vector(0, 0, 0), App.Vector(*dir)))
        else:
            part = part.fuse(Part.makeCylinder(head_dia/2, head_dz, App.Vector(0, 0, 0), App.Vector(*dir)))
    part.translate(App.Vector(x, y, z))
    part = part.fuse(part)
    return part.removeSplitter()


class example_component:
    '''
    An example component class for reference on importing new components
    creates a simple cube which mounts using a single bolt

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        side_length (float) : The side length of the cube
    '''
    type = 'Part::FeaturePython' # if importing from stl, this will be 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, side_len=15):
        # required for all object classes
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        # define any user-accessible properties here
        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'Side_Length').Side_Length = side_len

        # additional parameters (ie color, constants, etc)
        obj.ViewObject.ShapeColor = adapter_color
        self.mount_bolt = bolt_8_32
        self.mount_dz = -obj.Baseplate.OpticsDz.Value

    # this defines the component body and drilling
    def execute(self, obj):
        part = _custom_box(dx=obj.Side_Length.Value, dy=obj.Side_Length.Value, dz=obj.Side_Length.Value,
                           x=0, y=0, z=self.mount_dz)
        part = part.cut(_custom_cylinder(dia=self.mount_bolt['clear_dia'], dz=obj.Side_Length.Value,
                                         head_dia=self.mount_bolt['head_dia'], head_dz=self.mount_bolt['head_dz'],
                                         x=0, y=0, z=obj.Side_Length.Value+self.mount_dz))
        obj.Shape = part

        # drilling part definition
        part = _custom_cylinder(dia=self.mount_bolt['tap_dia'], dz=drill_depth,
                                x=0, y=0, z=self.mount_dz)
        part.Placement = obj.Placement
        obj.DrillPart = part



class baseplate_mount:
    '''
    Mount holes for attaching to an optical table
    Uses 14_20 bolts with washers

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        bore_depth (float) : The depth for the counterbore of the mount hole
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, bore_depth=10, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'BoreDepth').BoreDepth = bore_depth
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color

    def execute(self, obj):
        bolt_len = inch-(obj.BoreDepth.Value-bolt_14_20['head_dz'])

        part = _custom_cylinder(dia=bolt_14_20['tap_dia'], dz=bolt_len,
                                head_dia=bolt_14_20['head_dia'], head_dz=bolt_14_20['head_dz'],
                                x=0, y=0, z=-(obj.Baseplate.OpticsDz.Value + obj.Baseplate.dz.Value)+bolt_len)
        obj.Shape = part

        part = _custom_cylinder(dia=bolt_14_20['clear_dia'], dz=drill_depth,
                                head_dia=bolt_14_20["washer_dia"], head_dz=obj.BoreDepth.Value,
                                x=0, y=0, z=-obj.Baseplate.OpticsDz.Value)
        part.Placement = obj.Placement
        obj.DrillPart = part

class pinhole_self_design:
    '''
    design a pinhole, 2mm in diameter. It have a similar function as iris. It can help the alignment

    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_hole_dy=20, adapter_height=8, outer_thickness=2):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
        obj.addProperty('App::PropertyLength', 'AdapterHeight').AdapterHeight = adapter_height
        obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)
        self.drill_tolerance = 1

    def execute(self, obj):
        dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2
        dy = dx+obj.MountHoleDistance.Value
        dz = obj.AdapterHeight.Value
        z_translate = -10
        part = _custom_box(dx=dx, dy=dy, dz=dz,
                           x=0, y=0, z=z_translate, dir=(0, 0, -1),
                           fillet=5)
        part = part.fuse(_custom_box(dx=5, dy=10, dz=20,
                           x=0, y=0, z=z_translate, dir=(0, 0, 1),
                           fillet=2))
        part = part.cut(_custom_cylinder(dia = 2, dz = 100, x=-10, y=0, z=0, dir=(1,0,0)))
        # part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
        #                                  head_dia=bolt_8_32['head_dia'], head_dz=bolt_8_32['head_dz'],
        #                                  x=0, y=0, z=z_translate-dz, dir=(0,0,1)))
        for i in [-1, 1]:
            part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz ,
                                             head_dia=bolt_8_32['head_dia'], head_dz=bolt_8_32['head_dz'],
                                             x=0, y=i*obj.MountHoleDistance.Value/2, z=0 + z_translate))
        obj.Shape = part
        
        part = _bounding_box(obj, self.drill_tolerance, 6)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=0, y=i*obj.MountHoleDistance.Value/2, z=0 + z_translate))
        # part.translate(App.Vector(0,0,-30))
        part.Placement = obj.Placement
        obj.DrillPart = part

class surface_adapter_405:
    '''
    Surface adapter for post-mounted parts

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mount_hole_dy (float) : The spacing between the two mount holes of the adapter
        adapter_height (float) : The height of the suface adapter
        outer_thickness (float) : The thickness of the walls around the bolt holes
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_hole_dy=20, adapter_height=8, outer_thickness=2, slot=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
        obj.addProperty('App::PropertyLength', 'AdapterHeight').AdapterHeight = adapter_height
        obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)
        self.drill_tolerance = 1

    def execute(self, obj):
        dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2
        dy = dx+obj.MountHoleDistance.Value
        dz = obj.AdapterHeight.Value

        part = _custom_box(dx=dx, dy=dy, dz=dz,
                           x=0, y=0, z=0, dir=(0, 0, -1),
                           fillet=5)
        part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
                                         head_dia=bolt_8_32['head_dia'], head_dz=bolt_8_32['head_dz'],
                                         x=0, y=0, z=-dz, dir=(0,0,1)))
        for i in [-1, 1]:
            if obj.Slots:
                slot = 10
                dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2+slot
                part = part.cut(_custom_box(dx=bolt_8_32['head_dia'], dy=slot+bolt_8_32['head_dia'], dz=bolt_8_32['head_dz'],
                                            x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+dz,
                                            fillet=bolt_8_32['head_dia']/2, dir=(0,0,-1)))
                
                part = part.cut(_custom_box(dx=bolt_8_32['clear_dia'], dy=slot+bolt_8_32['clear_dia'], dz=bolt_8_32['head_dz'],
                                            x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+dz-bolt_8_32['head_dz'],
                                            fillet=bolt_8_32['clear_dia']/2, dir=(0,0,-1)))
            else:
                slot = 0
                dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2
                part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
                                             head_dia=bolt_8_32['head_dia'], head_dz=bolt_8_32['head_dz'],
                                             x=0, y=i*obj.MountHoleDistance.Value/2, z=0))
        obj.Shape = part

        part = _bounding_box(obj, self.drill_tolerance, 6)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=0, y=i*obj.MountHoleDistance.Value/2, z=0))
        part.Placement = obj.Placement
        obj.DrillPart = part

class skate_mount_crossholes:
    '''
    Skate mount for splitter cubes, add up one cross holes for other handedness

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        cube_dx, cube_dy (float) : The side length of the splitter cube
        mount_hole_dy (float) : The spacing between the two mount holes of the adapter
        cube_depth (float) : The depth of the recess for the cube
        outer_thickness (float) : The thickness of the walls around the bolt holes
        cube_tol (float) : The tolerance for size of the recess in the skate mount
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, cube_dx=10, cube_dy=10, cube_dz=10, mount_hole_dy=20, cube_depth=1, outer_thickness=2, cube_tol=0.1, slots=False):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'CubeDx').CubeDx = cube_dy
        obj.addProperty('App::PropertyLength', 'CubeDy').CubeDy = cube_dx
        obj.addProperty('App::PropertyLength', 'CubeDz').CubeDz = cube_dz
        obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
        obj.addProperty('App::PropertyLength', 'CubeDepth').CubeDepth = cube_depth+1e-3
        obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
        obj.addProperty('App::PropertyLength', 'CubeTolerance').CubeTolerance = cube_tol
        obj.addProperty('App::PropertyBool', 'Slots').Slots = slots
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)

    def execute(self, obj):
        if obj.Slots:
            slot = 5
            dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2+slot
        else:
            slot = 0
            dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2
        dy = dx+obj.MountHoleDistance.Value
        raw_dz = obj.Baseplate.OpticsDz.Value-obj.CubeDz.Value/2+obj.CubeDepth.Value
        dz = max(raw_dz, 8)
        cut_dy = obj.CubeDx.Value+obj.CubeTolerance.Value
        cut_dx = obj.CubeDy.Value+obj.CubeTolerance.Value

        part = _custom_box(dx=dx, dy=dy, dz=dz,
                           x=0, y=0, z=-obj.Baseplate.OpticsDz.Value, fillet=5)
        part = part.cut(_custom_box(dx=cut_dx, dy=cut_dy, dz=obj.CubeDepth.Value+1e-3,
                                    x=0, y=0, z=-obj.Baseplate.OpticsDz.Value+dz-obj.CubeDepth.Value-1e-3))
        
        for i in [-1, 1]:
            if obj.Slots:
                part = part.cut(_custom_box(dx=slot+bolt_8_32['head_dia'], dy=bolt_8_32['head_dia'], dz=bolt_8_32['head_dz'],
                                            x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+dz,
                                            fillet=bolt_8_32['head_dia']/2, dir=(0,0,-1)))
                part = part.cut(_custom_box(dx=slot+bolt_8_32['clear_dia'], dy=bolt_8_32['clear_dia'], dz=bolt_8_32['head_dz'],
                                            x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+dz-bolt_8_32['head_dz'],
                                            fillet=bolt_8_32['clear_dia']/2, dir=(0,0,-1)))
            else:
                part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
                                                head_dia=bolt_8_32['head_dia'], head_dz=bolt_8_32['head_dz'],
                                                x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+dz))
            
        part.translate(App.Vector(0, 0, obj.CubeDz.Value/2+(raw_dz-dz)))
        part = part.fuse(part)
        obj.Shape = part

        part = _bounding_box(obj, 1, 6,min_offset=(-slot, 0, 0), max_offset=(slot, 0, 0))
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+obj.CubeDz.Value/2))
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              y=0, x=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+obj.CubeDz.Value/2))
        part.Placement = obj.Placement
        obj.DrillPart = part

class skate_mount:
    '''
    Skate mount for splitter cubes

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        cube_dx, cube_dy (float) : The side length of the splitter cube
        mount_hole_dy (float) : The spacing between the two mount holes of the adapter
        cube_depth (float) : The depth of the recess for the cube
        outer_thickness (float) : The thickness of the walls around the bolt holes
        cube_tol (float) : The tolerance for size of the recess in the skate mount
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, cube_dx=10, cube_dy=10, cube_dz=10, mount_hole_dy=20, cube_depth=1, outer_thickness=2, cube_tol=0.1, slots=False):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'CubeDx').CubeDx = cube_dy
        obj.addProperty('App::PropertyLength', 'CubeDy').CubeDy = cube_dx
        obj.addProperty('App::PropertyLength', 'CubeDz').CubeDz = cube_dz
        obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
        obj.addProperty('App::PropertyLength', 'CubeDepth').CubeDepth = cube_depth+1e-3
        obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
        obj.addProperty('App::PropertyLength', 'CubeTolerance').CubeTolerance = cube_tol
        obj.addProperty('App::PropertyBool', 'Slots').Slots = slots
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)

    def execute(self, obj):
        if obj.Slots:
            slot = 5
            dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2+slot + 5
        else:
            slot = 0
            dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2 + 5
        dy = dx+obj.MountHoleDistance.Value
        raw_dz = obj.Baseplate.OpticsDz.Value-obj.CubeDz.Value/2+obj.CubeDepth.Value
        dz = max(raw_dz, 8)
        cut_dy = obj.CubeDx.Value+obj.CubeTolerance.Value
        cut_dx = obj.CubeDy.Value+obj.CubeTolerance.Value

        part = _custom_box(dx=dx, dy=dy, dz=dz,
                           x=0, y=0, z=-obj.Baseplate.OpticsDz.Value, fillet=5)
        part = part.cut(_custom_box(dx=cut_dx, dy=cut_dy, dz=obj.CubeDepth.Value+1e-3,
                                    x=0, y=0, z=-obj.Baseplate.OpticsDz.Value+dz-obj.CubeDepth.Value-1e-3))
        
        for i in [-1, 1]:
            if obj.Slots:
                part = part.cut(_custom_box(dx=slot+bolt_8_32['head_dia'], dy=bolt_8_32['head_dia'], dz=bolt_8_32['head_dz'],
                                            x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+dz,
                                            fillet=bolt_8_32['head_dia']/2, dir=(0,0,-1)))
                part = part.cut(_custom_box(dx=slot+bolt_8_32['clear_dia'], dy=bolt_8_32['clear_dia'], dz=bolt_8_32['head_dz'],
                                            x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+dz-bolt_8_32['head_dz'],
                                            fillet=bolt_8_32['clear_dia']/2, dir=(0,0,-1)))
            else:
                part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
                                                head_dia=bolt_8_32['head_dia'], head_dz=bolt_8_32['head_dz'],
                                                x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+dz))
            
        part.translate(App.Vector(0, 0, obj.CubeDz.Value/2+(raw_dz-dz)))
        part = part.fuse(part)
        obj.Shape = part

        part = _bounding_box(obj, 1, 0.125*layout.inch,min_offset=(-slot, 0, 0), max_offset=(slot, 0, 0))
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+obj.CubeDz.Value/2))
        part.Placement = obj.Placement
        obj.DrillPart = part

class Prism_pair:
    '''
    this is prism pair for laser profile
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj,drill = True , mount_type=None, mount_args=dict(), deviate_angle = 16.81):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)
        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.ViewObject.ShapeColor = glass_color
        self.part_numbers = ['Prism pair']
        self.transmission = True
        self.max_angle = 90
        self.max_width = 1 * inch
        # self.transmission = True
        # obj.addProperty('App::PropertyAngle', 'DiffractionAngle').DiffractionAngle = deviate_angle
        # obj.addProperty('App::PropertyInteger', 'ForwardDirection').ForwardDirection = forward_direction
        # obj.addProperty('App::PropertyInteger', 'BackwardDirection').BackwardDirection = backward_direction
        # self.deviate_angle = 16.81
        # self.diffraction_angle = diffraction_angle
        # self.diffraction_dir = (forward_direction, backward_direction)
        # self.transmission = True
        if mount_type != None:
           _add_linked_object(obj, "Mount", mount_type, pos_offset=(0, 0, -8), **mount_args)

    def execute(self, obj):
        mesh = _import_stl("Prism pair.stl", (180, 0, -110), (13,-7,0.8))
        mesh_ = _import_stl("Prism pair.stl", (0, 0, -276), (-3,1,-2))
        mesh.addMesh(mesh_)
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh      
          
class prism_pair_mount:
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, cube_dx=9, cube_dy=12, cube_dz=11, mount_hole_dy=20, cube_depth=1, outer_thickness=10, cube_tol=0.1, slots=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'CubeDx').CubeDx = cube_dy
        obj.addProperty('App::PropertyLength', 'CubeDy').CubeDy = cube_dx
        obj.addProperty('App::PropertyLength', 'CubeDz').CubeDz = cube_dz
        obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
        obj.addProperty('App::PropertyLength', 'CubeDepth').CubeDepth = cube_depth+1e-3
        obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
        obj.addProperty('App::PropertyLength', 'CubeTolerance').CubeTolerance = cube_tol
        obj.addProperty('App::PropertyBool', 'Slots').Slots = slots
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)

    def execute(self, obj):
        if obj.Slots:
            slot = 10
            dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2+slot
        else:
            slot = 0
            dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2
        dy = dx+obj.MountHoleDistance.Value
        raw_dz = obj.Baseplate.OpticsDz.Value-obj.CubeDz.Value/2+obj.CubeDepth.Value
        dz = max(raw_dz, 8)
        cut_dy = obj.CubeDx.Value+obj.CubeTolerance.Value
        cut_dx = obj.CubeDy.Value+obj.CubeTolerance.Value

        part = _custom_box(dx=dx, dy=dy, dz=dz,
                           x=0, y=0, z=-obj.Baseplate.OpticsDz.Value, fillet=5)
        part.rotate(App.Vector(0,0,0), App.Vector(0,0,1), -5)
        part = part.cut(_custom_box(dx=cut_dx, dy=cut_dy, dz=obj.CubeDepth.Value+1e-3,
                                    x=-8, y=2, z=-obj.Baseplate.OpticsDz.Value+dz-obj.CubeDepth.Value-1e-3))
        part.rotate(App.Vector(0,0,0), App.Vector(0,0,1), 37.5)
        
        part = part.cut(_custom_box(dx=cut_dx, dy=cut_dy, dz=obj.CubeDepth.Value+1e-3,
                                    x=8, y=6, z=-obj.Baseplate.OpticsDz.Value+dz-obj.CubeDepth.Value-1e-3))
        part.rotate(App.Vector(0,0,0), App.Vector(0,0,1),-32.5)
        for i in [-1.5, 1.5]:
            if obj.Slots:
                part = part.cut(_custom_box(dx=slot+bolt_8_32['head_dia'], dy=bolt_8_32['head_dia'], dz=bolt_8_32['head_dz'],
                                            x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+dz,
                                            fillet=bolt_8_32['head_dia']/2, dir=(0,0,-1)))
                part = part.cut(_custom_box(dx=slot+bolt_8_32['clear_dia'], dy=bolt_8_32['clear_dia'], dz=bolt_8_32['head_dz'],
                                            x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+dz-bolt_8_32['head_dz'],
                                            fillet=bolt_8_32['clear_dia']/2, dir=(0,0,-1)))
            else:
                part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
                                                head_dia=bolt_8_32['head_dia'], head_dz=bolt_8_32['head_dz'],
                                                x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+dz))

        part.rotate(App.Vector(0,0,0), App.Vector(0,0,1),0)    
        part.translate(App.Vector(0, 0, obj.CubeDz.Value/2+(raw_dz-dz)))
        part = part.fuse(part)
        obj.Shape = part

        part = _bounding_box(obj, 1, 6,min_offset=(-slot/4, 0, 0), max_offset=(slot/4, 0, 0))
        for i in [-1.5, 1.5]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+obj.CubeDz.Value/2))
        part.Placement = obj.Placement
        obj.DrillPart = part


class prism_pair_mount_circle:
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, cube_dx=9, cube_dy=12, cube_dz=11, mount_hole_dy=28, cube_depth=1, outer_thickness=10, cube_tol=0.1, slots=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'CubeDx').CubeDx = cube_dy
        obj.addProperty('App::PropertyLength', 'CubeDy').CubeDy = cube_dx
        obj.addProperty('App::PropertyLength', 'CubeDz').CubeDz = cube_dz
        obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
        obj.addProperty('App::PropertyLength', 'CubeDepth').CubeDepth = cube_depth+1e-3
        obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
        obj.addProperty('App::PropertyLength', 'CubeTolerance').CubeTolerance = cube_tol
        obj.addProperty('App::PropertyBool', 'Slots').Slots = slots
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)

    def execute(self, obj):
        if obj.Slots:
            slot = 15
            dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2+slot
        else:
            slot = 0
            dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2
        dy = dx+obj.MountHoleDistance.Value
        raw_dz = obj.Baseplate.OpticsDz.Value-obj.CubeDz.Value/2+obj.CubeDepth.Value
        dz = max(raw_dz, 8)
        dz1=5
        cut_dy = obj.CubeDx.Value+obj.CubeTolerance.Value
        cut_dx = obj.CubeDy.Value+obj.CubeTolerance.Value

        part = _custom_box(dx=dx, dy=dy, dz=dz,
                           x=0, y=0, z=-obj.Baseplate.OpticsDz.Value, fillet=5)
        part.rotate(App.Vector(0,0,0), App.Vector(0,0,1), 0)
        part = part.cut(_custom_cylinder(dia=16, dz=dz1,
                                                head_dia=16, head_dz=1,
                                                x=-8, y=4, z=-obj.Baseplate.OpticsDz.Value+dz))
        part.rotate(App.Vector(0,0,0), App.Vector(0,0,1), 0)
        
        part = part.cut(_custom_cylinder(dia=16, dz=dz1,
                                                head_dia=16, head_dz=1,
                                                x=8, y=-4, z=-obj.Baseplate.OpticsDz.Value+dz))
        part.rotate(App.Vector(0,0,0), App.Vector(0,0,1),0)
        for i in [-1.5, 1.5]:
            if obj.Slots:
                part = part.cut(_custom_box(dx=bolt_8_32['head_dia'], dy=slot+bolt_8_32['head_dia'], dz=bolt_8_32['head_dz'],
                                            x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+dz,
                                            fillet=bolt_8_32['head_dia']/2, dir=(0,0,-1)))
                
                part = part.cut(_custom_box(dx=bolt_8_32['clear_dia'], dy=slot+bolt_8_32['clear_dia'], dz=bolt_8_32['head_dz'],
                                            x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+dz-bolt_8_32['head_dz'],
                                            fillet=bolt_8_32['clear_dia']/2, dir=(0,0,-1)))
                 

            else:
                part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
                                                head_dia=bolt_8_32['head_dia'], head_dz=bolt_8_32['head_dz'],
                                                x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+dz))

        part.rotate(App.Vector(0,0,0), App.Vector(0,0,1),0)    
        part.translate(App.Vector(0, 0, obj.CubeDz.Value/2+(raw_dz-dz)))
        part = part.fuse(part)
        obj.Shape = part

        part = _bounding_box(obj, 1, 6,min_offset=(0,-slot/2, 0), max_offset=(0, slot/2, 0))
        for i in [-1.5, 1.5]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+obj.CubeDz.Value/2))
        part.Placement = obj.Placement
        obj.DrillPart = part

class prism_pair_mount_chess:
    '''
    just put it on the plate. no need to drill
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, cube_dx=9, cube_dy=12, cube_dz=11, mount_hole_dy=28, cube_depth=1, outer_thickness=10, cube_tol=0.1, slots=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        # obj.addProperty('App::PropertyLength', 'CubeDx').CubeDx = cube_dy
        # obj.addProperty('App::PropertyLength', 'CubeDy').CubeDy = cube_dx
        # obj.addProperty('App::PropertyLength', 'CubeDz').CubeDz = cube_dz
        # obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
        # obj.addProperty('App::PropertyLength', 'CubeDepth').CubeDepth = cube_depth+1e-3
        # obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
        # obj.addProperty('App::PropertyLength', 'CubeTolerance').CubeTolerance = cube_tol
        # obj.addProperty('App::PropertyBool', 'Slots').Slots = slots
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)

    def execute(self, obj):
        # for i in [-1., 1.]:
        part = _custom_cylinder(dia = 15, dz = 8, x = 8, y = -6, z = -4.70,head_dia=19.9, head_dz=3,dir=(0,0,1))
        # part = part.fuse(_custom_cylinder())  
        part = part.cut(_custom_box(dx=9,dy=12,dz = 6,x=8,y = -6,z = 2))  
        # part.translate(App.Vector(20 , 5, 0))
        # part = part.fuse(_custom_cylinder(dia = 15, dz = 8, x = -8, y = 6, z = -4.70,head_dia=19.9, head_dz=3,dir=(0,0,1)))
        # part = part.fuse(_custom_cylinder())  
        # part = part.cut(_custom_box(dx=9,dy=12,dz = 6,x=-8,y = 6,z = 2))  
        # part.translate(App.Vector(-20 , 5, 0))
            # part = part.fuse(part)
        obj.Shape = part

class slide_mount:
    '''
    Slide mount adapter for post-mounted parts

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        slot_length (float) : The length of the slot used for mounting to the baseplate
        drill_offset (float) : The distance to offset the drill hole along the slot
        adapter_height (float) : The height of the suface adapter
        post_thickness (float) : The thickness of the post that mounts to the element
        outer_thickness (float) : The thickness of the walls around the bolt holes
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, slot_length=10, drill_offset=0, adapter_height=8, post_thickness=4, outer_thickness=2):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'SlotLength').SlotLength = slot_length
        obj.addProperty('App::PropertyDistance', 'DrillOffset').DrillOffset = drill_offset
        obj.addProperty('App::PropertyLength', 'AdapterHeight').AdapterHeight = adapter_height
        obj.addProperty('App::PropertyLength', 'PostThickness').PostThickness = post_thickness
        obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')
        
        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)

    def execute(self, obj):
        dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2
        dy = dx+obj.SlotLength.Value+obj.PostThickness.Value
        dz = obj.AdapterHeight.Value

        part = _custom_box(dx=dx, dy=dy, dz=dz,
                           x=0, y=-dy/2, z=-obj.Baseplate.OpticsDz.Value, fillet=4)
        part = part.cut(_custom_box(dx=bolt_8_32['clear_dia'], dy=obj.SlotLength.Value+bolt_8_32['clear_dia'], dz=dz,
                                    x=0, y=-dy/2-obj.PostThickness.Value/2, z=-obj.Baseplate.OpticsDz.Value, fillet=bolt_8_32['clear_dia']/2))
        part = part.cut(_custom_box(dx=bolt_8_32['head_dia'], dy=obj.SlotLength.Value+bolt_8_32['head_dia'], dz=bolt_8_32['head_dz'],
                                    x=0, y=-dy/2-obj.PostThickness.Value/2, z=-obj.Baseplate.OpticsDz.Value+bolt_8_32['head_dz'], fillet=bolt_8_32['head_dia']/2))
        part = part.fuse(_custom_box(dx=dx, dy=obj.PostThickness.Value, dz=obj.Baseplate.OpticsDz.Value+bolt_8_32['head_dz'],
                                     x=0, y=-obj.PostThickness.Value/2, z=-obj.Baseplate.OpticsDz.Value))
        part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=obj.PostThickness.Value,
                                    x=0, y=0, z=0, dir=(0, -1, 0)))
        obj.Shape = part

        part = _custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                x=0, y=-dy/2-obj.PostThickness.Value/2+obj.DrillOffset.Value, z=-obj.Baseplate.OpticsDz.Value)
        part.Placement = obj.Placement
        obj.DrillPart = part


class mount_hca3:
    '''
    Part for mounting an HCA3 fiberport coupler to the side of a baseplate

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['HCA3', 'PAF2-5A']
        self.max_angle = 0
        self.max_width = 1

    def execute(self, obj):
        mesh = _import_stl("HCA3-Step.stl", (90, -0, 90), (-6.35, 19.05, -26.87))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _custom_cylinder(dia=bolt_8_32['tap_dia'], dz=inch,
                                              x=0, y=0, z=-20.65, dir=(1,0,0))
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=inch,
                                              x=0, y=i*12.7, z=-20.65, dir=(1,0,0)))
        part.Placement = obj.Placement
        obj.DrillPart = part


class rotation_stage_rsp05:
    '''
    Rotation stage, model RSP05

    Args:
        invert (bool) : Whether the mount should be offset 90 degrees from the component
        mount_hole_dy (float) : The spacing between the two mount holes of it's adapter
        wave_plate_part_num (string) : The Thorlabs part number of the wave plate being used

    Sub-Parts:
        surface_adapter (adapter_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, invert=False, adapter_args=dict(), adapter = True):
        adapter_args.setdefault("mount_hole_dy", 25)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Invert').Invert = invert

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['RSP05']
        self.transmission = True
        self.max_angle = 90
        self.max_width = inch/2

        if adapter:
            _add_linked_object(obj, "Surface Adapter", surface_adapter_rotation_stage_lip, pos_offset=(1.397, 0, -13.97), rot_offset=(0, 0, 90*obj.Invert), **adapter_args)

    def execute(self, obj):
        mesh = _import_stl("RSP05-Step.stl", (90, -0, 90), (2.032, -0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

class rotation_stage_rsp05_2inch:
    '''
    Rotation stage, model RSP05

    Args:
        invert (bool) : Whether the mount should be offset 90 degrees from the component
        mount_hole_dy (float) : The spacing between the two mount holes of it's adapter
        wave_plate_part_num (string) : The Thorlabs part number of the wave plate being used

    Sub-Parts:
        surface_adapter (adapter_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, invert=False, adapter_args=dict(), adapter = True):
        adapter_args.setdefault("mount_hole_dy", 25)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Invert').Invert = invert

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['RSP05']
        self.transmission = True
        self.max_angle = 90
        self.max_width = inch/2

        if adapter:
            _add_linked_object(obj, 'surface_adapter', surface_adapter_fiberport_lip, pos_offset=(-9.7, 0, -14.7),
                               rot_offset=(0, 0, 180), **adapter_args)

    def execute(self, obj):
        mesh = _import_stl("RSP05-Step.stl", (90, -0, 90), (2.032, -0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

class surface_adapter_rotation_stage:
    '''
    Surface adapter for post-mounted parts

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mount_hole_dy (float) : The spacing between the two mount holes of the adapter
        adapter_height (float) : The height of the surface adapter
        outer_thickness (float) : The thickness of the walls around the bolt holes
        center_thread_depth (float) : The depth of the threaded portion in the center hole
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_hole_dy=36, adapter_height=8, outer_thickness=2, center_thread_depth=3):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
        obj.addProperty('App::PropertyLength', 'AdapterHeight').AdapterHeight = adapter_height
        obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
        obj.addProperty('App::PropertyLength', 'CenterThreadDepth').CenterThreadDepth = center_thread_depth
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)
        self.drill_tolerance = 1

    def execute(self, obj):
        dx = bolt_8_32['head_dia'] + obj.OuterThickness.Value * 2 + 10
        dy = dx + obj.MountHoleDistance.Value
        dz = obj.AdapterHeight.Value

        part = _custom_box(dx=dx, dy=dy, dz=dz,
                           x=0, y=0, z=0, dir=(0, 0, -1),
                           fillet=5)
        
        for i in [-1, 1]:
            part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
                                             head_dia=bolt_8_32['head_dia']+obj.OuterThickness.Value, head_dz=bolt_8_32['head_dz'],
                                             x=0, y=i*obj.MountHoleDistance.Value/2, z=0))
    
        part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
                                        head_dia=bolt_8_32['head_dia']+obj.OuterThickness.Value, head_dz=bolt_8_32['head_dz'],
                                        x=0, y=0, z=-dz, dir=(0,0,1)))

        obj.Shape = part

        part = _bounding_box(obj, self.drill_tolerance, 6)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=0, y=i*obj.MountHoleDistance.Value/2, z=0))
        part.Placement = obj.Placement
        obj.DrillPart = part

class surface_adapter_rotation_stage_lip:
    '''
    Surface adapter for RSP05 with a lip 
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, mount_hole_dy=36, adapter_height=8, outer_thickness=2, center_thread_depth=3):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
        obj.addProperty('App::PropertyLength', 'AdapterHeight').AdapterHeight = adapter_height
        obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
        obj.addProperty('App::PropertyLength', 'CenterThreadDepth').CenterThreadDepth = center_thread_depth
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)
        self.drill_tolerance = 1

    def execute(self, obj):
        mesh = _import_stl("Surface_Adapter_rsp05_lip.stl", (0, 0, 0), ([0, 0, 0]))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, self.drill_tolerance, 0.125*layout.inch)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=0, y=i*obj.MountHoleDistance.Value/2, z=0))
        part.Placement = obj.Placement
        obj.DrillPart = part

class surface_adapter_PD:
    '''
    Surface adapter for RSP05 with a lip 
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, mount_hole_dy=110, adapter_height=8, outer_thickness=2, center_thread_depth=3):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
        obj.addProperty('App::PropertyLength', 'AdapterHeight').AdapterHeight = adapter_height
        obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
        obj.addProperty('App::PropertyLength', 'CenterThreadDepth').CenterThreadDepth = center_thread_depth
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)
        self.drill_tolerance = 1

    def execute(self, obj):
        mesh = _import_stl("Surface_Adapter_PD.stl", (0, 0, 0), ([0, 0, 0]))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, self.drill_tolerance, 0.125*layout.inch)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=0, y=i* 55, z=16.5))
        part.Placement = obj.Placement
        obj.DrillPart = part

class rotation_stage_rsp05_wide:
    '''
    Rotation stage, model RSP05

    Args:
        invert (bool) : Whether the mount should be offset 90 degrees from the component
        mount_hole_dy (float) : The spacing between the two mount holes of it's adapter
        wave_plate_part_num (string) : The Thorlabs part number of the wave plate being used

    Sub-Parts:
        surface_adapter (adapter_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, invert=False, adapter_args=dict(), adapter = True):
        # adapter_args.setdefault("mount_hole_dy", 25)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Invert').Invert = invert

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['RSP05']
        self.transmission = True
        self.max_angle = 90
        self.max_width = inch/2

        if adapter:
            _add_linked_object(obj, "Surface Adapter", surface_adapter_wide, pos_offset=(1.397, 0, -13.97), rot_offset=(0, 0, 90*obj.Invert), **adapter_args)

    def execute(self, obj):
        mesh = _import_stl("RSP05-Step.stl", (90, -0, 90), (2.032, -0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

class pinhole_p2000k05_LMR05:
    '''
    Pinhole, 2mm 
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, adapter_args=dict()):
        adapter_args.setdefault("mount_hole_dy", 25)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['p2000k05']

        _add_linked_object(obj, "Surface Adapter", surface_adapter, pos_offset=(0, 3.82, -16.00), rot_offset=(0, 0, 90), **adapter_args)

    def execute(self, obj):
        mesh = _import_stl("P2000K05_LMR05.stl", (90, -0, 0), (0, -0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

class BSH01_cube_mount:
    '''
    BSH01 screw mount for 10mm cube polarized beam splitter
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, adapter_args=dict()):
        adapter_args.setdefault("mount_hole_dy", 25)
        adapter_args.setdefault("outer_thickness", 3)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['BSH01']

        _add_linked_object(obj, "Surface Adapter", surface_adapter_4_40, pos_offset=(0, 0, 0), rot_offset=(0, 0, 90), **adapter_args)
        # _add_linked_object(obj, "Surface Adapter", surface_adapter_4_40, pos_offset=(0, 0, -5.15), rot_offset=(0, 0, 90), **adapter_args)

    def execute(self, obj):
        mesh = _import_stl("BSH10.stl", (90, -0, 0), (101.4, 74.1, -22))
        mesh.Placement = obj.Mesh.Placement

        obj.Mesh = mesh
        # part = _bounding_box(obj, 2, 2)
        # part.Placement = obj.Placement
        # obj.DrillPart = part
        obj.Mesh = mesh

# ==== 1/2" PBS Cube Mount (uses cube_mount_halfinch.stl) ====
class cube_mount_halfinch:
    """
    Cube mount for 1/2" (12.7 mm) PBS.
    """
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, bolt_length=15, mount_hole_dy=22.6):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool',   'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'BoltLength').BoltLength = bolt_length
        obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)
        self.drill_tolerance = 1  # matches the approach used elsewhere
        self.part_numbers = ['CUBE-MOUNT-1/2IN']

    def execute(self, obj):
        # 1) place the mesh
        mesh = _import_stl("Cube_Mount_Halfinch.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        # 2) create drill geometry (tap holes) in a bounding box
        part = _bounding_box(obj, self.drill_tolerance, 0.125*layout.inch)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(
                dia=bolt_8_32['tap_dia'],  # tap drill (e.g., #29 for 8-32)
                dz=drill_depth,
                x=0,
                y=i * obj.MountHoleDistance.Value/2,
                z=0
            ))

        part.Placement = obj.Placement
        obj.DrillPart = part


class rotation_stage_rsp05_lying_down:
    '''
    Rotation stage, model RSP05

    Args:
        invert (bool) : Whether the mount should be offset 90 degrees from the component
        mount_hole_dy (float) : The spacing between the two mount holes of it's adapter
        wave_plate_part_num (string) : The Thorlabs part number of the wave plate being used

    Sub-Parts:
        surface_adapter (adapter_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, invert=False, adapter_args=dict()):
        adapter_args.setdefault("mount_hole_dy", 25)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Invert').Invert = invert

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['RSP05']

        _add_linked_object(obj, "Surface Adapter", surface_adapter_lying_down, pos_offset=(1.397, 0, -13.97), rot_offset=(0, 0, 90*obj.Invert), **adapter_args)

    def execute(self, obj):
        mesh = _import_stl("RSP05-Step.stl", (90, -0, 90), (2.032, -0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh



class mirror_mount_k05s2:
    '''
    Mirror mount, model K05S2

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, thumbscrews=False):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['POLARIS-K05S2']

        if thumbscrews:
            _add_linked_object(obj, "Upper Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-12.43, 8.89, 8.89))
            _add_linked_object(obj, "Lower Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-12.43, -8.89, -8.89))

    def execute(self, obj):
        mesh = _import_stl("POLARIS-K05S2-Step.stl", (90, -0, -90), (-4.514, 0.254, -0.254))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                x=-8.017, y=0, z=-layout.inch/2)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=2, dz=2.2,
                                              x=-8.017, y=i*5, z=-layout.inch/2))
        part.Placement = obj.Placement
        obj.DrillPart = part


class mirror_mount_k05s1:
    '''
    Mirror mount, model K05S1

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, thumbscrews=False):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['POLARIS-K05S1']

        if thumbscrews:
            _add_linked_object(obj, "Upper Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-11.22, 8.89, 8.89))
            _add_linked_object(obj, "Lower Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-11.22, -8.89, -8.89))

    def execute(self, obj):
        mesh = _import_stl("POLARIS-K05S1-Step.stl", (90, 0, -90), (-4.514, 0.254, -0.254))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                x=-8.017, y=0, z=-layout.inch/2)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=2, dz=2.2,
                                              x=-8.017, y=i*5, z=-layout.inch/2))
        part.Placement = obj.Placement
        obj.DrillPart = part


class mirror_mount_M05:
    '''
    Mirror mount, model M05

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, thumbscrews=False):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['Newport-M05']

        if thumbscrews:
            _add_linked_object(obj, "Upper Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-12.7, 9.144, 9.144))
            _add_linked_object(obj, "Lower Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-13.208, -9.144, -9.144))

    def execute(self, obj):
        mesh = _import_stl("Newport-M05.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        # Add cylinders for mounting hole and 2 alignment pins
        part = _custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                x=-0.274*layout.inch, y=0, z=-layout.inch/2)

        # # Alignment pin farther from mirror
        # part = part.fuse(_custom_cylinder(dia=1.6, dz=1.6,
        #                                   x=-0.454*layout.inch, y=0, z=-layout.inch/2))

        # # Alignment pin closer to mirror
        # part = part.fuse(_custom_cylinder(dia=1.6, dz=1.5,
        #                                   x=-0.134*layout.inch, y=0, z=-layout.inch/2))

        part.Placement = obj.Placement
        obj.DrillPart = part

class mirror_mount_FMP05:
    '''
    Mirror mount, model FMP05

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['Thorlabs-FMP05']
        _add_linked_object(obj, "FMP05 Adapter", adapter_FMP05, pos_offset=(-6.9, 0, -24.25), rot_offset=(0, 0, -90))

    def execute(self, obj):
        mesh = _import_stl("FMP05.stl", (90, 0, 90), (3.1, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        # Add cylinders for mounting hole and 2 alignment pins
        part = _custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                x=-0.274*layout.inch, y=0, z=-layout.inch/2)

        # # Alignment pin farther from mirror
        # part = part.fuse(_custom_cylinder(dia=1.6, dz=1.6,
        #                                   x=-0.454*layout.inch, y=0, z=-layout.inch/2))

        # # Alignment pin closer to mirror
        # part = part.fuse(_custom_cylinder(dia=1.6, dz=1.5,
        #                                   x=-0.134*layout.inch, y=0, z=-layout.inch/2))

        part.Placement = obj.Placement
        obj.DrillPart = part


class PBS_2in_mounted:
    '''
    Adapter for AOMs on KM100PM Mount
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['Mounted PBS 2 inch']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

    def execute(self, obj):
        mesh = _import_stl("pbs_2in_mounted.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 1.5, 0.25*layout.inch)

        part = _bounding_box(obj, 1.0, 0.25*layout.inch)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=-12.4, y=i*(39) , z=0))

        part.Placement = obj.Placement
        obj.DrillPart = part


# 2 inch waveplate:

class waveplate_2in:
    '''
    Adapter for AOMs on KM100PM Mount
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['Mounted 2 inch waveplate']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

    def execute(self, obj):
        mesh = _import_stl("rotated_waveplate_indexrotstage.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 1.5, 0.25*layout.inch)

        part = _bounding_box(obj, 1.0, 0.25*layout.inch)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=0, y=i * 50.0, z=0))

        part.Placement = obj.Placement
        obj.DrillPart = part
# MIRROR MOUNT BUT WITH a 2inch mount:

class mirror_mount_KM2CE:
    '''
    Mirror mount, model M05

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, thumbscrews=False):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['Newport-M05']

        if thumbscrews:
            _add_linked_object(obj, "Upper Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-12.7, 9.144, 9.144))
            _add_linked_object(obj, "Lower Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-13.208, -9.144, -9.144))

    def execute(self, obj):
        mesh = _import_stl("rotated_2inmirror_adapter_longer.stl", (0, 0, 0),
                           #original rot (0, -90, 0)
                           #original translate (11, 0, 0.25)
                            (11, 0, 0.25))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 1/2*layout.inch, z_tol=True)

        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_M4['tap_dia'], dz=drill_depth,
                                              x=-7, y=1.6+(i*12) , z=0.25))

        part = part.fuse(_custom_cylinder(dia=bolt_M4['tap_dia'], dz=drill_depth,
                                            x=-7, y=-0.28 , z=0.25))

        part.Placement = obj.Placement
        obj.DrillPart = part



class mirror_mount_M05_rot90:
    '''
    Mirror mount, model M05

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, thumbscrews=False):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['Newport-M05']

        if thumbscrews:
            _add_linked_object(obj, "Upper Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-12.7, -9.144, 9.144 ))
            _add_linked_object(obj, "Lower Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-13.208 , 9.144 , -9.144 ))

    def execute(self, obj):
        mesh = _import_stl("Newport-M05.stl", (-90, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        # Add cylinders for mounting hole and 2 alignment pins
        part = _custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                x=-0.274*layout.inch, y=0, z=-layout.inch/2)

        # Alignment pin farther from mirror
        part = part.fuse(_custom_cylinder(dia=1.6, dz=1.6,
                                          x=-0.454*layout.inch, y=0, z=-layout.inch/2))

        # Alignment pin closer to mirror
        part = part.fuse(_custom_cylinder(dia=1.6, dz=1.5,
                                          x=-0.134*layout.inch, y=0, z=-layout.inch/2))

        part.Placement = obj.Placement
        obj.DrillPart = part


class moon_mirror_mount:
    '''
    Mirror mount, model K05S1

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, thumbscrews=False):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['DMM05-Step']

    def execute(self, obj):
        mesh = _import_stl("DMM05-Step.stl", (-183, -9, 3), (-3, 3, 1.5))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _custom_cylinder(dia=bolt_8_32['clear_dia'], dz=inch,
                                          head_dia=bolt_8_32['head_dia'], head_dz=0.92*inch-15,
                                          x=-7.2, y=6.2, z=-inch*3/2, dir=(0,0,1))
        
        # part = _fillet_all(part, 3)
        # part = part.fuse()
        part.Placement = obj.Placement
        obj.DrillPart = part
        # for i in [-1, 1]:
        #     part = part.fuse(_custom_cylinder(dia=2, dz=2.2,
        #                                       x=-7.2, y=i*12.2, z=-layout.inch/2))
        part.Placement = obj.Placement
        obj.DrillPart = part

class moon_mirror_mount_left:
    '''
    Mirror mount, model K05S1

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, thumbscrews=False):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['DMM05-Step']

    def execute(self, obj):
        mesh = _import_stl("DMM05-Step.stl", (177, -9, 3), (-3, 3, 1.5))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                x=-7.2, y=6.2, z=-layout.inch/2)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=2, dz=2.2,
                                              x=-7.2, y=6.2, z=-layout.inch/2))
        part.Placement = obj.Placement
        obj.DrillPart = part

class splitter_mount_b05g:
    '''
    Splitter mount, model B05G

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        splitter (bool) : Whether to add a splitter plate component to the mount

    Sub-Parts:
        circular_splitter (mirror_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['POLARIS-B05G']

    def execute(self, obj):
        mesh = _import_stl("POLARIS-B05G-Step.stl", (90, -0, 90), (-17.54, -5.313, -19.26))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                x=-5, y=0, z=-layout.inch/2)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=2, dz=2.2,
                                              x=-5, y=i*5, z=-layout.inch/2))
        part.Placement = obj.Placement
        obj.DrillPart = part


class mirror_mount_c05g:
    '''
    Mirror mount, model C05G

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount

    Sub-Parts:
        circular_mirror (mirror_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['POLARIS-C05G']

    def execute(self, obj):
        mesh = _import_stl("POLARIS-C05G-Step.stl", (90, -0, 90), (-18.94, -4.246, -15.2))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                x=-6.35, y=0, z=-layout.inch/2)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=2, dz=2.2,
                                              x=-6.35, y=i*5, z=-layout.inch/2))
        part.Placement = obj.Placement
        obj.DrillPart = part

class KMS_MH_12:
    '''
    KMSS mirror mount
    Ø1/2" MH_12 mirror holder
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, bolt_length = 15):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')
        obj.addProperty('App::PropertyLength', 'BoltLength').BoltLength = bolt_length
        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['MH12']

    def execute(self, obj):
        mesh = _import_stl("KMSS_MH12_step.stl", (-90, -90, 90), (-5, 0, -0.4))
        mesh.Placement = obj.Mesh.Placement

        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 0.1, 15, min_offset=(0,2,0))
        part = _fillet_all(part, 3)
        part = part.fuse(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz= 1*inch,
                                          head_dia=bolt_8_32['head_dia'], head_dz=0.92*inch-obj.BoltLength.Value,
                                          x=-7.29-7, y=-29-10, z=-inch*3/2+37.7, dir=(0,1,0)))
        part.Placement = obj.Placement
        # part.Placement = obj.Placement
        obj.DrillPart = part

class rotation_stage_rsp1:
    '''
    Rotation stage, model RSP1

    Args:
        invert (bool) : Whether the mount should be offset 90 degrees from the component
        mount_hole_dy (float) : The spacing between the two mount holes of it's adapter
        wave_plate_part_num (string) : The Thorlabs part number of the wave plate being used

    Sub-Parts:
        surface_adapter (adapter_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, invert=False, adapter_args=dict()):
        adapter_args.setdefault("mount_hole_dy", 25)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Invert').Invert = invert

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['RSP1']

        _add_linked_object(obj, "Surface Adapter", surface_adapter, pos_offset=(5.461, 0, -27.73), rot_offset=(0, 0, 90*obj.Invert), **adapter_args)

    def execute(self, obj):
        mesh = _import_stl("RSP1-Step.stl", (180, -0, 90), (5.969, -0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

class mirror_mount_km100:
    '''
    Mirror mount, model KM100

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
        bolt_length (float) : The length of the bolt used for mounting

    Sub-Parts:
        circular_mirror (mirror_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')
        obj.addProperty('App::PropertyLength', 'BoltLength').BoltLength = 15
        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['KM100']

    def execute(self, obj):
        mesh = _import_stl("KM100-Step.stl", (-180, 0, -90), (4.972, 0.084, -1.089))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 3, min_offset=(4.35, 0, 0))
        part = part.fuse(_bounding_box(obj, 2, 3, max_offset=(0, -20, 0)))
        part = _fillet_all(part, 3)
        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=inch+100,
                                        #  head_dia=bolt_8_32['head_dia'], head_dz=0.92*inch-obj.BoltLength.Value+drill_depth+10,
                                         x=-7.29-1.19, y=0, z=-inch*3/2-drill_depth, dir=(0,0,1)))
        
        #########
        part = part.fuse(_custom_box(dx=0.55 * inch, dy=0.55 * inch, dz=11, x=-7.29-1.19, y = 0, z = -42,fillet=0, dir=(0,0,-1), fillet_dir=None))
        # for cnc machining
        for j in [1,-1]:
            for k in [1, -1]:
                part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'] * 2, dz=drill_depth,
                                x=-7.29-1.19 + j * 0.25 * inch , y=0 + k * 0.25*inch, z=-42, dir=(0,0,-1)))
        #########

        part = part.fuse(_custom_box(dx = 20, dy= 22, dz= 6, x=-7.29-18.9, y=-7.29-11.9, z=-31, fillet=3, dir=(0,0,1), fillet_dir=None))
        part.Placement = obj.Placement
        obj.DrillPart = part
        
class mirror_mount_km05:
    '''
    Mirror mount, model KM05

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
        bolt_length (float) : The length of the bolt used for mounting

    Sub-Parts:
        circular_mirror (mirror_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, thumbscrews=False, bolt_length=15):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
        obj.addProperty('App::PropertyLength', 'BoltLength').BoltLength = bolt_length
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['KM05']

        if thumbscrews:
            _add_linked_object(obj, "Upper Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-10.54, 9.906, 9.906))
            _add_linked_object(obj, "Lower Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-10.54, -9.906, -9.906))

    def execute(self, obj):
        mesh = _import_stl("KM05-Step.stl", (90, -0, 90), (2.084, -1.148, 0.498))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 3, min_offset=(4.35, 0, 0))
        part = part.fuse(_bounding_box(obj, 2, 3, max_offset=(0, -20, 0)))
        part = _fillet_all(part, 3)
        part = part.fuse(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=inch,
                                          head_dia=bolt_8_32['head_dia'], head_dz=0.92*inch-obj.BoltLength.Value,
                                          x=-7.29, y=0, z=-inch*3/2, dir=(0,0,1)))
        part.Placement = obj.Placement
        obj.DrillPart = part



class mirror_mount_km05_rot90:
    '''
    Mirror mount, model KM05

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
        bolt_length (float) : The length of the bolt used for mounting

    Sub-Parts:
        circular_mirror (mirror_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, thumbscrews=False, bolt_length=15):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.ddProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
        obj.addProperty('App::PropertyLength', 'BoltLength').BoltLength = bolt_length
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['KM05']

        if thumbscrews:
            _add_linked_object(obj, "Upper Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-10.54, 9.906, -9.906))
            _add_linked_object(obj, "Lower Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-10.54, -9.906, 9.906))

    def execute(self, obj):
        mesh = _import_stl("KM05-Step.stl", (90, 90, 90), (1.784, 0.1, 0.498))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 1, 3, min_offset=(3.35, 0, 0))
        part = part.fuse(_bounding_box(obj, 1, 3, max_offset=(0, 3, 0)))
        part = _fillet_all(part, 3)
        part = part.fuse(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=inch,
                                          head_dia=bolt_8_32['head_dia']+1, head_dz=0.92*inch-obj.BoltLength.Value,
                                          x=-7.49, y=-0.38, z=-inch*3/2, dir=(0,0,1)))
        part.Placement = obj.Placement
        obj.DrillPart = part

class mirror_mount_km05T:
    '''
    Mirror mount, model KM05T

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
        bolt_length (float) : The length of the bolt used for mounting

    Sub-Parts:
        circular_mirror (mirror_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, thumbscrews=False, bolt_length=15):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
        obj.addProperty('App::PropertyLength', 'BoltLength').BoltLength = bolt_length
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['KM05T']

        if thumbscrews:
            _add_linked_object(obj, "Upper Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-10.668, 9.906, 9.906))
            _add_linked_object(obj, "Lower Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-10.668 , -9.906, -9.906))

    def execute(self, obj):
        mesh = _import_stl("KM05T.stl", (90, 0, 90), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh
        
        part = _bounding_box(obj, 2, 0.125*layout.inch)
        part.Placement = obj.Placement
        obj.DrillPart = part


class mirror_mount_KA05TB:
    '''
    Mirror mount, model KA05TB

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
        bolt_length (float) : The length of the bolt used for mounting

    Sub-Parts:
        circular_mirror (mirror_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, thumbscrews=False, bolt_length=15):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
        obj.addProperty('App::PropertyLength', 'BoltLength').BoltLength = bolt_length
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color

        self.part_numbers = ['KA05TB']

        # if mirror:
        #     _add_linked_object(obj, "Mirror", circular_mirror, pos_offset=(...), rot_offset=(...), **mirror_args)

        '''if thumbscrews:
            _add_linked_object(obj, "Upper Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-10.668, 9.906, 9.906))
            _add_linked_object(obj, "Lower Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-10.668 , -9.906, -9.906))'''
        if thumbscrews:
            _add_linked_object(obj, "Upper Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-0.384*layout.inch, 0.35*layout.inch, 0.35*layout.inch))
            _add_linked_object(obj, "Lower Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-0.384*layout.inch, -0.35*layout.inch, -0.35*layout.inch))

    def execute(self, obj):
        mesh = _import_stl("KA05TB.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 0.125*layout.inch)
        part.Placement = obj.Placement
        obj.DrillPart = part



class fiberport_mount_KA05TB:
    '''
    Mirror mount, model KA05TB, adapted to use as fiberport mount

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        mirror_mount_KA05TB (mount_args)
        fiber_adapter_sm05fca2
        lens_tube_sm05l05
        lens_adapter_s05tm09
        mounted_lens_c220tmda
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_args=dict(), adapter_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill

        obj.ViewObject.ShapeColor = misc_color

        _add_linked_object(obj, "Mount", mirror_mount_KA05TB, pos_offset=(0, 0, 0), **mount_args)


        _add_linked_object(obj, "Fiber Adapter", fiber_adapter_sm05fca2, pos_offset=(1.524, 0, 0))
        _add_linked_object(obj, "Lens Tube",    lens_tube_sm05l05,       pos_offset=(1.524+3.812, 0, 0))
        _add_linked_object(obj, "Lens Adapter", lens_adapter_s05tm09,     pos_offset=(1.524+5, 0, 0))
        _add_linked_object(obj, "Lens",         mounted_lens_c220tmda,    pos_offset=(1.524+3.167+5, 0, 0))

        """
        # surface adapter (fiberport lip)
        _add_linked_object(
            obj, 'surface_adapter', surface_adapter_fiberport_lip,
            pos_offset=(-9.7, 0, -14.7), rot_offset=(0, 0, 180), **adapter_args
        ) """

class mirror_mount_KA05T:
    '''
    Mirror mount, model KA05T

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
        bolt_length (float) : The length of the bolt used for mounting

    Sub-Parts:
        circular_mirror (mirror_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, thumbscrews=False, bolt_length=15):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
        obj.addProperty('App::PropertyLength', 'BoltLength').BoltLength = bolt_length
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color

        self.part_numbers = ['KA05T']

        # if mirror:
        #     _add_linked_object(obj, "Mirror", circular_mirror, pos_offset=(...), rot_offset=(...), **mirror_args)

        if thumbscrews:
            _add_linked_object(obj, "Upper Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-10.668, 9.906, 9.906))
            _add_linked_object(obj, "Lower Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-10.668 , -9.906, -9.906))

    def execute(self, obj):
        mesh = _import_stl("KA05T.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 0.125*layout.inch)
        part.Placement = obj.Placement
        obj.DrillPart = part


class fiberport_mount_KA05T:
    '''
    Mirror mount, model KA05T, adapted to use as fiberport mount

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        mirror_mount_KA05TB (mount_args)
        fiber_adapter_sm05fca2
        lens_tube_sm05l05
        lens_adapter_s05tm09
        mounted_lens_c220tmda
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_args=dict(), adapter_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill

        obj.ViewObject.ShapeColor = misc_color

        _add_linked_object(obj, "Mount", mirror_mount_KA05T, pos_offset=(0, 0, 0), **mount_args)


        _add_linked_object(obj, "Fiber Adapter", fiber_adapter_sm05fca2, pos_offset=(1.524, 0, 0))
        _add_linked_object(obj, "Lens Tube",    lens_tube_sm05l05,       pos_offset=(1.524+3.812, 0, 0))
        _add_linked_object(obj, "Lens Adapter", lens_adapter_s05tm09,     pos_offset=(1.524+5, 0, 0))
        _add_linked_object(obj, "Lens",         mounted_lens_c220tmda,    pos_offset=(1.524+3.167+5, 0, 0))
        # # rear tapped holes ONLY (no adapter body)
        # _add_linked_object(
        #     obj, 'rear_holes', fiberport_mount_KA05T_rear_holes,
        #     pos_offset=(-9.7, 0, -14.7), rot_offset=(0, 0, 180), **adapter_args
        # )

        """
        # surface adapter (fiberport lip)
        _add_linked_object(
            obj, 'surface_adapter', surface_adapter_fiberport_lip,
            pos_offset=(-9.7, 0, -14.7), rot_offset=(0, 0, 180), **adapter_args
        ) """

class fiberport_mount_KA05T_holes:
    '''
    Mirror mount, model KA05T, adapted to use as fiberport mount with integrated drilling

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        hole_config (str) : Configuration for the rear holes
        rear_hole_x_offset (float) : X offset for rear holes from the mount center
        rear_hole_y_spacing (float) : Y spacing between rear holes

    Sub-Parts:
        mirror_mount_KA05TB (mount_args)
        fiber_adapter_sm05fca2
        lens_tube_sm05l05
        lens_adapter_s05tm09
        mounted_lens_c220tmda
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, rear_holes=True, 
                 rear_hole_x_offset=68, rear_hole_y_spacing=18.328, 
                 mount_args=dict(), adapter_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyBool', 'RearHoles').RearHoles = rear_holes
        obj.addProperty('App::PropertyLength', 'RearHoleXOffset').RearHoleXOffset = rear_hole_x_offset
        obj.addProperty('App::PropertyLength', 'RearHoleYSpacing').RearHoleYSpacing = rear_hole_y_spacing
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = misc_color

        _add_linked_object(obj, "Mount", mirror_mount_KA05T, pos_offset=(0, 0, 0), **mount_args)
        _add_linked_object(obj, "Fiber Adapter", fiber_adapter_sm05fca2, pos_offset=(1.524, 0, 0))
        _add_linked_object(obj, "Lens Tube", lens_tube_sm05l05, pos_offset=(1.524+3.812, 0, 0))
        _add_linked_object(obj, "Lens Adapter", lens_adapter_s05tm09, pos_offset=(1.524+5, 0, 0))
        _add_linked_object(obj, "Lens", mounted_lens_c220tmda, pos_offset=(1.524+3.167+5, 0, 0))

        self.drill_tolerance = 1

    def execute(self, obj):
        # Only proceed if drilling is enabled for this part
        if obj.Drill and obj.RearHoles:
            
            # Extract values from properties
            x_offset = obj.RearHoleXOffset.Value
            y_spacing = obj.RearHoleYSpacing.Value / 2
            
            # Create a list of (x, y) coordinates for all holes
            # Row 1
            hole_locations = [
                (-x_offset, y_spacing),
                (-x_offset, -y_spacing)
            ]
            
            # Row 2 (if enabled)
            if hasattr(obj, 'SecondRowHoles'):
                hole_locations.append((x_offset + 20, y_spacing))
                hole_locations.append((x_offset + 20, -y_spacing))
            
            drill_shape = None

            # Generate the cylinders and fuse them together
            for (x_pos, y_pos) in hole_locations:
                hole = _custom_cylinder(
                    dia=bolt_8_32['tap_dia'], 
                    dz=drill_depth,
                    x=x_pos, 
                    y=y_pos, 
                    z=0
                )
                
                if drill_shape is None:
                    drill_shape = hole
                else:
                    drill_shape = drill_shape.fuse(hole)
            
            # Apply the object's current placement to the combined hole pattern
            if drill_shape:
                drill_shape.Placement = obj.Placement
                obj.DrillPart = drill_shape
        else:
            # If drilling is turned off, assign an empty shape so 
            # no holes are rendered from previous executions
            obj.DrillPart = Part.Compound([])

class mirror_mount_km05T_custom:
    '''
    Mirror mount, model KM05T-8CB-SP

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
        bolt_length (float) : The length of the bolt used for mounting

    Sub-Parts:
        circular_mirror (mirror_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, thumbscrews=False, bolt_length=15):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
        obj.addProperty('App::PropertyLength', 'BoltLength').BoltLength = bolt_length
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['KM05T-8CB-SP']

        if thumbscrews:
            _add_linked_object(obj, "Upper Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-0.673*layout.inch, 0.35*layout.inch, 0.35*layout.inch))
            _add_linked_object(obj, "Lower Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-0.673*layout.inch, -0.35*layout.inch, -0.35*layout.inch))

    def execute(self, obj):
        mesh = _import_stl("KM05T-8CB-SP.stl", (90, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 3, min_offset=(4.35, 0, 0))
        part = part.fuse(_bounding_box(obj, 2, 3, max_offset=(0, -20, 0)))
        part = _fillet_all(part, 3)
        # part = part.fuse(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=inch,
        #                                   head_dia=bolt_8_32['head_dia'], head_dz=0.92*inch-obj.BoltLength.Value,
        #                                   x=-7.29, y=0, z=-inch*3/2, dir=(0,0,1)))
        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=inch, x=-7.29, y=0, z=-inch*3/2, dir=(0,0,1)))
        # part = _custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth, x=-7.4168, y=0, z=-14.732)
        part.Placement = obj.Placement
        obj.DrillPart = part




class fixed_mount_smr05:
    '''
    Fixed mount, model SMR05

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        bolt_length (float) : The length of the bolt used for mounting

    Sub-Parts:
        circular_mirror (mirror_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, thumbscrews=False, bolt_length=15):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'BoltLength').BoltLength = bolt_length
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['SMR05']


    def execute(self, obj):
        mesh = _import_stl("SMR05-Step.stl", (90, 0, 90), (-3.81, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _custom_cylinder(dia=bolt_8_32['clear_dia'], dz=inch,
                                          head_dia=bolt_8_32['head_dia'], head_dz=0.92*inch-obj.BoltLength.Value,
                                          x=-3.81, y=0, z=-16-obj.BoltLength.Value, dir=(0,0,1))
        part.Placement = obj.Placement
        obj.DrillPart = part


class prism_mount_km05pm:
    '''
    Mount, model KM05PM

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, thumbscrews=False, bolt_length=15, arm=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyBool', 'Arm').Arm = arm
        obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
        obj.addProperty('App::PropertyLength', 'BoltLength').BoltLength = bolt_length
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['KM05PM']

        if thumbscrews:
            _add_linked_object(obj, "Upper Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-19.05, 6.985, 15.49))
            _add_linked_object(obj, "Lower Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-19.05, -12.83, -4.318))

    def execute(self, obj):
        #mesh = _import_stl("KM05PM-Step.stl", (90, 0, 90), (-12.39, -0.894, 1.514))
        if obj.Arm:
            mesh = _import_stl("KM05PM-Step-No-Plate.stl", (90, -0, 90), (-6.425, -4.069, 6.086))
        else:
            mesh = _import_stl("KM05PM-Step-NoArm.stl", (90, 0, 90), (-3.25, -8.26, 10.4))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 3, 3, min_offset=(4.35, 0, 0))
        part = part.fuse(_bounding_box(obj, 3, 3, max_offset=(0, -20, 0)))
        part = part.fuse(_bounding_box(obj, 3, 3, min_offset=(14, 0, 0), z_tol=True))
        part = _fillet_all(part, 3)
        part = part.fuse(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=drill_depth,
                                          head_dia=bolt_8_32['head_dia'], head_dz=drill_depth-obj.BoltLength.Value,
                                          x=-15.8, y=-2.921, z=-9.144-drill_depth, dir=(0,0,1)))
        part.Placement = obj.Placement
        obj.DrillPart = part


class grating_mount_on_km05pm:
    '''
    Grating and Parallel Mirror Mounted on MK05PM

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        littrow_angle (float) : The angle of the grating and parallel mirror

    Sub_Parts:
        mount_mk05pm (mount_args)
        square_grating (grating_args)
        square_mirror (mirror_args)
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, littrow_angle=55, mount_args=dict(), grating_args=dict(), mirror_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyAngle', 'LittrowAngle').LittrowAngle = littrow_angle

        obj.ViewObject.ShapeColor = adapter_color
        self.dx = 12/tan(radians(2*obj.LittrowAngle))

        gap = 10
        lit_angle = radians(90-obj.LittrowAngle.Value)
        beam_angle = radians(obj.LittrowAngle.Value)
        ref_len = gap/sin(2*beam_angle)
        ref_x = ref_len*cos(2*beam_angle)
        dx = ref_x+12.7*cos(lit_angle)+(6+3.2)*sin(lit_angle)
        extra_x = 20-dx
        grating_dx = -(6*sin(lit_angle)+12.7/2*cos(lit_angle))-extra_x
        mirror_dx = grating_dx-ref_x

        _add_linked_object(obj, "Mount MK05PM", prism_mount_km05pm, pos_offset=(-3.175, 8, -10), rot_offset=(0, 0, 180), drill=drill, **mount_args)
        _add_linked_object(obj, "Grating", square_grating, pos_offset=(grating_dx, 0, 0), rot_offset=(0, 0, 180-obj.LittrowAngle.Value), **grating_args)
        _add_linked_object(obj, "Mirror", square_mirror, pos_offset=(mirror_dx, gap, 0), rot_offset=(0, 0, -obj.LittrowAngle.Value), **mirror_args)

    def execute(self, obj):
        extra_y = 2
        gap = 10
        lit_angle = radians(90-obj.LittrowAngle.Value)
        beam_angle = radians(obj.LittrowAngle.Value)
        ref_len = gap/sin(2*beam_angle)
        ref_x = ref_len*cos(2*beam_angle)
        dx = ref_x+12.7*cos(lit_angle)+(6+3.2)*sin(lit_angle)
        extra_x = 20-dx
        dy = gap+12.7*sin(lit_angle)+(6+3.2)*cos(lit_angle)
        dz = inch/2
        cut_x = 12.7*cos(lit_angle)

        part = _custom_box(dx=dx+extra_x, dy=dy+extra_y, dz=dz,
                           x=extra_x, y=0, z=-10, dir=(-1, 1, 1))
        temp = _custom_box(dx=ref_len*cos(beam_angle)+6+3.2, dy=dy/sin(lit_angle)+10, dz=dz,
                           x=-cut_x, y=-(dx-cut_x)*cos(lit_angle), z=-6, dir=(-1, 1, 1))
        temp.rotate(App.Vector(-cut_x, 0, 0), App.Vector(0, 0, 1), -obj.LittrowAngle.Value)
        part = part.cut(temp)
        part = part.cut(_custom_box(dx=8, dy=16, dz=dz-4,
                           x=extra_x, y=dy+extra_y, z=-6, dir=(-1, -1, 1)))
        part.translate(App.Vector(-extra_x, -12.7/2*sin(lit_angle)-6*cos(lit_angle), 0))
        part = part.fuse(part)
        part = part.cut(_custom_cylinder(dia=bolt_4_40['clear_dia'], dz=4,
                                         head_dia=bolt_4_40['head_dia'], head_dz=2,
                                         x=-3.175, y=8, z=-6, dir=(0, 0, -1)))
        part = part.cut(_custom_cylinder(dia=bolt_4_40['clear_dia'], dz=4,
                                         head_dia=bolt_4_40['head_dia'], head_dz=2,
                                         x=-3.175, y=8+2*3.175, z=-6, dir=(0, 0, -1)))
        obj.Shape = part


class grating_mount_on_km05pm_no_arm:
    '''
    Grating and Parallel Mirror Mounted on MK05PM

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        littrow_angle (float) : The angle of the grating and parallel mirror

    Sub_Parts:
        mount_mk05pm (mount_args)
        square_grating (grating_args)
        square_mirror (mirror_args)
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, littrow_angle=55, mount_args=dict(), grating_args=dict(), mirror_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyAngle', 'LittrowAngle').LittrowAngle = littrow_angle

        obj.ViewObject.ShapeColor = adapter_color
        self.dx = 12/tan(radians(2*obj.LittrowAngle))

        gap = 10
        lit_angle = radians(90-obj.LittrowAngle.Value)
        beam_angle = radians(obj.LittrowAngle.Value)
        ref_len = gap/sin(2*beam_angle)
        ref_x = ref_len*cos(2*beam_angle)
        dx = ref_x+12.7*cos(lit_angle)+(6+3.2)*sin(lit_angle)
        extra_x = 20-dx
        grating_dx = -(6*sin(lit_angle)+12.7/2*cos(lit_angle))-extra_x
        mirror_dx = grating_dx-ref_x

        _add_linked_object(obj, "Mount MK05PM", prism_mount_km05pm, pos_offset=(-3.175, 8, 4.064-inch/2), rot_offset=(0, 0, 180), arm=False, drill=drill, **mount_args)
        _add_linked_object(obj, "Grating", square_grating, pos_offset=(grating_dx, 0, 0), rot_offset=(0, 0, 180-obj.LittrowAngle.Value), **grating_args)
        _add_linked_object(obj, "Mirror", square_mirror, pos_offset=(mirror_dx, gap, 0), rot_offset=(0, 0, -obj.LittrowAngle.Value), **mirror_args)

    def execute(self, obj):
        extra_y = 2
        gap = 10
        lit_angle = radians(90-obj.LittrowAngle.Value)
        beam_angle = radians(obj.LittrowAngle.Value)
        ref_len = gap/sin(2*beam_angle)
        ref_x = ref_len*cos(2*beam_angle)
        dx = ref_x+12.7*cos(lit_angle)+(6+3.2)*sin(lit_angle)
        extra_x = 20-dx
        dy = gap+12.7*sin(lit_angle)+(6+3.2)*cos(lit_angle)
        dz = inch/2
        cut_x = 12.7*cos(lit_angle)

        part = _custom_box(dx=dx+extra_x, dy=dy+extra_y, dz=dz,
                           x=extra_x, y=0, z=-10, dir=(-1, 1, 1))
        temp = _custom_box(dx=ref_len*cos(beam_angle)+6+3.2, dy=dy/sin(lit_angle)+10, dz=dz,
                           x=-cut_x, y=-(dx-cut_x)*cos(lit_angle), z=-6, dir=(-1, 1, 1))
        temp.rotate(App.Vector(-cut_x, 0, 0), App.Vector(0, 0, 1), -obj.LittrowAngle.Value)
        part = part.cut(temp)
        part = part.cut(_custom_box(dx=8, dy=16, dz=dz-4,
                           x=extra_x, y=dy+extra_y, z=-6, dir=(-1, -1, 1)))
        part.translate(App.Vector(-extra_x, -12.7/2*sin(lit_angle)-6*cos(lit_angle), 0))
        part = part.fuse(part)
        part = part.cut(_custom_cylinder(dia=bolt_4_40['clear_dia'], dz=4,
                                         head_dia=bolt_4_40['head_dia'], head_dz=2,
                                         x=-3.175, y=8, z=-6, dir=(0, 0, -1)))
        part = part.cut(_custom_cylinder(dia=bolt_4_40['clear_dia'], dz=4,
                                         head_dia=bolt_4_40['head_dia'], head_dz=2,
                                         x=-3.175, y=8+2*3.175, z=-6, dir=(0, 0, -1)))
        obj.Shape = part


class mount_tsd_405sluu:
    '''
    Mount, model KM05PM

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['TSD-405SLUU']

    def execute(self, obj):
        mesh = _import_stl("TSD-405SLUU.stl", (0, 0, -90), (-19, 0, -62))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 3, 3)
        for x, y in [(-34.88, 15.88), (-34.88, -15.88), (-3.125, 15.88), (-3.125, -15.88)]:
            part = part.fuse(_custom_cylinder(dia=bolt_4_40['tap_dia'], dz=drill_depth,
                                            x=x, y=y, z=-62))
        part.Placement = obj.Placement
        obj.DrillPart = part


class mirror_mount_ks1t:
    '''
    Mirror mount, model KS1T

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount

    Sub-Parts:
        circular_mirror (mirror_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['KM1T']

    def execute(self, obj):
        mesh = _import_stl("KS1T-Step.stl", (90, -0, -90), (22.06, 13.37, -30.35))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh
        dz = -0.5
        # dz = -inch-obj.Mesh.BoundBox.ZMin
        part = _bounding_box(obj, 3, 3, min_offset=(0, 0, dz))
        part = part.fuse(_bounding_box(obj, 3, 3, z_tol=True, max_offset=(-28, 0, 0)))
        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                          x=-16.94, y=0, z=-layout.inch/2, dir=(0,0,-1)))
        part.Placement = obj.Placement
        obj.DrillPart = part


class fiberport_mount_km05:
    '''
    Mirror mount, model KM05, adapted to use as fiberport mount

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        mirror_mount_km05 (mount_args)
        fiber_adapter_sm05fca2
        lens_tube_sm05l05
        lens_adapter_s05tm09
        mounted_lens_c220tmda
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill

        obj.ViewObject.ShapeColor = misc_color

        _add_linked_object(obj, "Mount", mirror_mount_km05, pos_offset=(0, 0, 0), **mount_args)
        _add_linked_object(obj, "Fiber Adapter", fiber_adapter_sm05fca2, pos_offset=(1.524, 0, 0))
        _add_linked_object(obj, "Lens Tube", lens_tube_sm05l05, pos_offset=(1.524+3.812, 0, 0))
        _add_linked_object(obj, "Lens Adapter", lens_adapter_s05tm09, pos_offset=(1.524+5, 0, 0))
        _add_linked_object(obj, "Lens", mounted_lens_c220tmda, pos_offset=(1.524+3.167+5, 0, 0))

class fiberport_mount_km05T:
    '''
    Mirror mount, model KM05T-8CB-SP, adapted to use as fiberport mount
    add a hole at center for mirror_mount_km05T mounting

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        mirror_mount_km05T (mount_args)
        fiber_adapter_sm05fca2
        lens_tube_sm05l05
        lens_adapter_s05tm09
        mounted_lens_c220tmda
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, hole_config = 'Y_shape', mount_args=dict(), adapter_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill

        obj.ViewObject.ShapeColor = misc_color

        adapter_args['hole_config'] = hole_config

        _add_linked_object(obj, "Mount", mirror_mount_km05T, pos_offset=(0, 0, 0), **mount_args)
        _add_linked_object(obj, "Fiber Adapter", fiber_adapter_sm05fca2, pos_offset=(1.524, 0, 0))
        _add_linked_object(obj, "Lens Tube", lens_tube_sm05l05, pos_offset=(1.524+3.812, 0, 0))
        _add_linked_object(obj, "Lens Adapter", lens_adapter_s05tm09, pos_offset=(1.524+5, 0, 0))
        _add_linked_object(obj, "Lens", mounted_lens_c220tmda, pos_offset=(1.524+3.167+5, 0, 0))
        _add_linked_object(obj, 'surface_adapter', surface_adapter_fiberport_lip, pos_offset=(-9.7, 0, -14.7),rot_offset=(0, 0, 180), **adapter_args)

class fiberport_mount_km05T_2inch:
    '''
    Mirror mount, model KM05T-8CB-SP, adapted to use as fiberport mount
    add a hole at center for mirror_mount_km05T mounting

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        mirror_mount_km05T (mount_args)
        fiber_adapter_sm05fca2
        lens_tube_sm05l05
        lens_adapter_s05tm09
        mounted_lens_c220tmda
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_args=dict(), adapter_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill

        obj.ViewObject.ShapeColor = misc_color

        _add_linked_object(obj, "Mount", mirror_mount_km05T, pos_offset=(0, 0, 0), **mount_args)
        _add_linked_object(obj, "Fiber Adapter", fiber_adapter_sm05fca2, pos_offset=(1.524, 0, 0))
        _add_linked_object(obj, "Lens Tube", lens_tube_sm05l05, pos_offset=(1.524+3.812, 0, 0))
        _add_linked_object(obj, "Lens Adapter", lens_adapter_s05tm09, pos_offset=(1.524+5, 0, 0))
        _add_linked_object(obj, "Lens", mounted_lens_c220tmda, pos_offset=(1.524+3.167+5, 0, 0))
        _add_linked_object(obj, 'surface_adapter', surface_adapter_fiberport_lip, pos_offset=(-9.7, 0, -14.7),rot_offset=(0, 0, 180), **adapter_args)


class fiberport_mount_km05T_raised:
    '''
    Mirror mount, model KM05T-8CB-SP, adapted to use as fiberport mount
    add a hole at center for mirror_mount_km05T mounting

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        mirror_mount_km05T (mount_args)
        fiber_adapter_sm05fca2
        lens_tube_sm05l05
        lens_adapter_s05tm09
        mounted_lens_c220tmda
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_args=dict(), adapter_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill

        obj.ViewObject.ShapeColor = misc_color

        _add_linked_object(obj, "Mount", mirror_mount_km05T, pos_offset=(0, 0, 0), **mount_args)
        _add_linked_object(obj, "Fiber Adapter", fiber_adapter_sm05fca2, pos_offset=(1.524, 0, 0))
        _add_linked_object(obj, "Lens Tube", lens_tube_sm05l05, pos_offset=(1.524+3.812, 0, 0))
        _add_linked_object(obj, "Lens Adapter", lens_adapter_s05tm09, pos_offset=(1.524+5, 0, 0))
        _add_linked_object(obj, "Lens", mounted_lens_c220tmda, pos_offset=(1.524+3.167+5, 0, 0))
        _add_linked_object(obj, 'surface_adapter', surface_adapter_fiberport_lip, pos_offset=(-9.7, 0, -14.7),rot_offset=(0, 0, 180), **adapter_args)
        _add_linked_object(obj, 'SAFL extra', SAFL_extra, pos_offset=(0,0,0),rot_offset=(0, 0, 0), **adapter_args)

class SAFL_extra:
    '''
    Surface adapter with a lip for the fiber port

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mount_hole_dy (float) : The spacing between the two mount holes of the adapter
        adapter_height (float) : The height of the surface adapter
        outer_thickness (float) : The thickness of the walls around the bolt holes
        center_thread_depth (float) : The depth of the threaded portion in the center hole
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, mount_hole_dy=16, adapter_height=30.5, outer_thickness=10, center_thread_depth=27.5):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
        obj.addProperty('App::PropertyLength', 'AdapterHeight').AdapterHeight = adapter_height
        obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
        obj.addProperty('App::PropertyLength', 'CenterThreadDepth').CenterThreadDepth = center_thread_depth
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)
        self.drill_tolerance = 1

    def execute(self, obj):
        mesh = _import_stl("fiberport_to_board_adapter.stl", (90, 0, 90), (-9.7, 0, -14.7-8.5-12))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 1, 0.125*layout.inch)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=-9.7, y=i*obj.MountHoleDistance.Value/2, z=0))

        for i in [1, 2, 3]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x = 16 + i * 10, y=0, z=14.7))

        part.Placement = obj.Placement
        obj.DrillPart = part

class fiberport_mount_km05T_rotated_90:
    '''
    Mirror mount, model KM05T-8CB-SP, adapted to use as fiberport mount
    add a hole at center for mirror_mount_km05T mounting

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        mirror_mount_km05T (mount_args)
        fiber_adapter_sm05fca2
        lens_tube_sm05l05
        lens_adapter_s05tm09
        mounted_lens_c220tmda
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_args=dict(), adapter_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill

        obj.ViewObject.ShapeColor = misc_color

        _add_linked_object(obj, "Mount", mirror_mount_km05T, pos_offset=(0, 0, 0), **mount_args)
        _add_linked_object(obj, "Fiber Adapter", fiber_adapter_sm05fca2, pos_offset=(1.524, 0, 0))
        _add_linked_object(obj, "Lens Tube", lens_tube_sm05l05, pos_offset=(1.524+3.812, 0, 0))
        _add_linked_object(obj, "Lens Adapter", lens_adapter_s05tm09, pos_offset=(1.524+5, 0, 0))
        _add_linked_object(obj, "Lens", mounted_lens_c220tmda, pos_offset=(1.524+3.167+5, 0, 0))
        _add_linked_object(obj, 'surface_adapter', surface_adapter_rotated_90, pos_offset=(-9.7, 0, -14.7),rot_offset=(0, 0, 0), **adapter_args)


class mirror_mount_KA05T:
    '''
    Mirror mount, model KA05T

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
        bolt_length (float) : The length of the bolt used for mounting

    Sub-Parts:
        circular_mirror (mirror_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, thumbscrews=False, bolt_length=15):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
        obj.addProperty('App::PropertyLength', 'BoltLength').BoltLength = bolt_length
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color

        self.part_numbers = ['KA05T']

        # if mirror:
        #     _add_linked_object(obj, "Mirror", circular_mirror, pos_offset=(...), rot_offset=(...), **mirror_args)

        if thumbscrews:
            _add_linked_object(obj, "Upper Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-10.668, 9.906, 9.906))
            _add_linked_object(obj, "Lower Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-10.668 , -9.906, -9.906))

    def execute(self, obj):
        mesh = _import_stl("KA05T.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 0.125*layout.inch)

        part = part.fuse(_custom_cylinder(
            dia=bolt_8_32["tap_dia"],   
            dz=drill_depth,             
            x=-0.32264471*layout.inch,  
            y=0,
            z=-0.5*layout.inch,
            dir=(0, 0, -1)              
        ))

        part.Placement = obj.Placement
        obj.DrillPart = part


class fiberport_mount_KA05T:
    '''
    Mirror mount, model KA05T, adapted to use as fiberport mount

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        mirror_mount_KA05T (mount_args)
        fiber_adapter_sm05fca2
        lens_tube_sm05l05
        lens_adapter_s05tm09
        mounted_lens_c220tmda
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_args=dict(), adapter_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill

        obj.ViewObject.ShapeColor = misc_color

        _add_linked_object(obj, "Mount", mirror_mount_KA05T, pos_offset=(0, 0, 0), **mount_args)


        _add_linked_object(obj, "Fiber Adapter", fiber_adapter_sm05fca2, pos_offset=(1.524, 0, 0))
        _add_linked_object(obj, "Lens Tube",    lens_tube_sm05l05,       pos_offset=(1.524+3.812, 0, 0))
        _add_linked_object(obj, "Lens Adapter", lens_adapter_s05tm09,     pos_offset=(1.524+5, 0, 0))
        _add_linked_object(obj, "Lens",         mounted_lens_c220tmda,    pos_offset=(1.524+3.167+5, 0, 0))

        """
        # surface adapter (fiberport lip)
        _add_linked_object(
            obj, 'surface_adapter', surface_adapter_fiberport_lip,
            pos_offset=(-9.7, 0, -14.7), rot_offset=(0, 0, 180), **adapter_args
        ) """
        

class splitter_mount_b1g:
    '''
    Splitter mount, model B1G

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        splitter (bool) : Whether to add a splitter plate component to the mount

    Sub-Parts:
        circular_splitter (mirror_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=False):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['POLARIS-B1G']

        _add_linked_object(obj, "Surface Adapter", surface_adapter, pos_offset=(-5, 0, -19.05), rot_offset=(0, 0, 0), mount_hole_dy=30)

    def execute(self, obj):
        mesh = _import_stl("POLARIS-B1G-Step.stl", (90, 0, 90), (-43.59, 1.26, -23.78))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                x=-5, y=0, z=-layout.inch/2)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=2, dz=2.2,
                                              x=-5, y=i*5, z=-layout.inch/2))
        part.Placement = obj.Placement
        obj.DrillPart = part

class fiberport_mount_k1t1:
    '''
    Mirror mount, model KM05, adapted to use as fiberport mount

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        mirror_mount_km05 (mount_args)
        fiber_adapter_sm05fca2
        lens_tube_sm05l05
        lens_adapter_s05tm09
        mounted_lens_c220tmda
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill

        obj.ViewObject.ShapeColor = misc_color

        _add_linked_object(obj, "Mount", mirror_mount_k1t1, pos_offset=(0, 0, 0), **mount_args)
        # _add_linked_object(obj, "Fiber Adapter", fiber_adapter_sm05fca2, pos_offset=(1.524, 0, 0))
        # _add_linked_object(obj, "Lens Tube", lens_tube_sm05l05, pos_offset=(1.524+3.812, 0, 0))
        # _add_linked_object(obj, "Lens Adapter", lens_adapter_s05tm09, pos_offset=(1.524+5, 0, 0))
        # _add_linked_object(obj, "Lens", mounted_lens_c220tmda, pos_offset=(1.524+3.167+5, 0, 0))
        _add_linked_object(obj, "Fiber Adapter", fiber_adapter_sm1fca2, pos_offset=(-3, 0, 0))
        _add_linked_object(obj, "Lens Tube", lens_tube_sm1l05, pos_offset=(0+10.6-2-2, 0, 0))
        _add_linked_object(obj, "Lens Adapter", lens_adapter_s1tm09, pos_offset=(1.524+6+13.6, 0, 0))
        _add_linked_object(obj, "Lens", mounted_lens_c220tmda, pos_offset=(1.524+2, 0, 0))

class mirror_mount_k1t1:
    '''
    Mirror mount, model K1t1

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount

    Sub-Parts:
        circular_mirror (mirror_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['KM1T']

    def execute(self, obj):
        mesh = _import_stl("Fiberport_mount_k1t1.stl", (90, -0, -90), (97.06, 17.87, -10.35))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh
        dz = -0.5
        # dz = -inch-obj.Mesh.BoundBox.ZMin
        part = _bounding_box(obj, 3, 3, min_offset=(0, 0, dz))
        part = part.fuse(_bounding_box(obj, 3, 3, z_tol=True, max_offset=(-28-2-5, 0, 0)))

        # part for a square washer
        # https://www.mcmaster.com/99041A204/
        # Zinc-Plated Steel Square Washer
        # for Number 6 Screw Size, 0.156" ID, 0.500" Wide
        part = part.fuse(_custom_box(dx=0.55 * inch, dy=0.55 * inch, dz=11, x=-15.76, y = 0, z = -42,fillet=0, dir=(0,0,-1), fillet_dir=None))
        # for cnc machining
        for j in [1,-1]:
            for k in [1, -1]:
                part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'] * 2, dz=drill_depth,
                                x=-15.76 + j * 0.25 * inch , y=0 + k * 0.25*inch, z=-42, dir=(0,0,-1)))

        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                          x=-15.76, y=0, z=-layout.inch/2, dir=(0,0,-1)))
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=2, dz=2.2,
                                              x=-15.667, y=i*5.05, z=-layout.inch/2-12.5))
        
       

        part.Placement = obj.Placement
        obj.DrillPart = part  

class fiberport_mount_ks1t:
    '''
    Mirror mount, model KM05, adapted to use as fiberport mount

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        mirror_mount_km05 (mount_args)
        fiber_adapter_sm05fca2
        lens_tube_sm05l05
        lens_adapter_s05tm09
        mounted_lens_c220tmda
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill

        obj.ViewObject.ShapeColor = misc_color

        _add_linked_object(obj, "Mount", mirror_mount_ks1t, pos_offset=(0, 0, 0), **mount_args)
        _add_linked_object(obj, "Fiber Adapter", fiber_adapter_sm1fca2, pos_offset=(-3, 0, 0))
        _add_linked_object(obj, "Lens Tube", lens_tube_sm1l05, pos_offset=(0, 0, 0))
        _add_linked_object(obj, "Lens Adapter", lens_adapter_s1tm09, pos_offset=(1.524+6, 0, 0))
        _add_linked_object(obj, "Lens", mounted_lens_c220tmda, pos_offset=(1.524+2, 0, 0))

class fiberport_mount_ks1t_with_tube:
    '''
    Mirror mount, model KM05, adapted to use as fiberport mount

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        mirror_mount_km05 (mount_args)
        fiber_adapter_sm05fca2
        lens_tube_sm05l05
        lens_adapter_s05tm09
        mounted_lens_c220tmda
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill

        obj.ViewObject.ShapeColor = misc_color

        _add_linked_object(obj, "Mount", mirror_mount_ks1t, pos_offset=(0, 0, 0), **mount_args)
        _add_linked_object(obj, "Fiber Adapter", fiber_adapter_sm1fca2, pos_offset=(-3, 0, 0))
        # _add_linked_object(obj, "Lens Tube", lens_tube_sm1l05, pos_offset=(0, 0, 0))
        _add_linked_object(obj, "Lens Adapter", lens_adapter_s1tm09, pos_offset=(1.524+6, 0, 0))
        _add_linked_object(obj, "Lens", mounted_lens_c220tmda, pos_offset=(1.524+2, 0, 0))
        _add_linked_object(obj, "Lens Slot Tube", lens_slot_tube, pos_offset=(1.524+2+5, 0, 0))

class lens_slot_tube:
    '''
    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = misc_color
        # self.part_numbers = ['HCA3', 'PAF2-5A']
        self.max_angle = 0
        self.max_width = 1

    def execute(self, obj):
        mesh = _import_stl("SM1L10C_slot_tube.stl", (90, 180, -90), (18.35, 0.05, -81.87))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 3, 3, min_offset=(0, 0, -3))
        part.Placement = obj.Placement
        obj.DrillPart = part

class km05_50mm_laser:
    '''
    Mirror mount, model KM05, adapted to use as laser mount

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        tec_thickness (float) : The thickness of the TEC used

    Sub-Parts:
        mirror_mount_km05 (mount_args)
        km05_tec_upper_plate (upper_plate_args)
        km05_tec_lower_plate (lower_plate_args)
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, tec_thickness=4, mount_args=dict(), upper_plate_args=dict(), lower_plate_args=dict()):
        mount_args.setdefault("bolt_length", 2)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'TecThickness').TecThickness = tec_thickness
        obj.ViewObject.ShapeColor = misc_color
        
        self.part_numbers = [] # TODO add part numbers
        self.max_angle = 0
        self.max_width = 1

        dx = -5.334+2.032
        _add_linked_object(obj, "Diode Adapter", diode_adapter_s05lm56, pos_offset=(0, 0, 0))
        _add_linked_object(obj, "Lens Tube", lens_tube_sm05l05, pos_offset=(dx+1.524+3.812, 0, 0))
        _add_linked_object(obj, "Lens Adapter", lens_adapter_s05tm09, pos_offset=(dx+1.524+5, 0, 0))
        _add_linked_object(obj, "Lens", mounted_lens_c220tmda, pos_offset=(dx+1.524+3.167+5, 0, 0))

        mount = _add_linked_object(obj, "Mount", mirror_mount_km05, pos_offset=(dx, 0, 0), drill=False, **mount_args)
        upper_plate = _add_linked_object(obj, "Upper Plate", km05_tec_upper_plate, pos_offset=(dx-4, 0, -0.08*inch), drill_obj=mount, **upper_plate_args)
        _add_linked_object(obj, "Lower Plate", km05_tec_lower_plate, pos_offset=(dx-4, 0, -0.08*inch-tec_thickness-upper_plate.Thickness.Value), **lower_plate_args)

class km05_50mm_laser_no_pad:
    '''
    Mirror mount, model KM05, adapted to use as laser mount

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        tec_thickness (float) : The thickness of the TEC used

    Sub-Parts:
        mirror_mount_km05 (mount_args)
        km05_tec_upper_plate (upper_plate_args)
        km05_tec_lower_plate (lower_plate_args)
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, tec_thickness=4, mount_args=dict(), upper_plate_args=dict(), lower_plate_args=dict()):
        mount_args.setdefault("bolt_length", 2)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'TecThickness').TecThickness = tec_thickness
        obj.ViewObject.ShapeColor = misc_color
        
        self.part_numbers = [] # TODO add part numbers
        self.max_angle = 0
        self.max_width = 1

        dx = -5.334+2.032
        _add_linked_object(obj, "Diode Adapter", diode_adapter_s05lm56, pos_offset=(0, 0, 0))
        _add_linked_object(obj, "Lens Tube", lens_tube_sm05l05, pos_offset=(dx+1.524+3.812, 0, 0))
        _add_linked_object(obj, "Lens Adapter", lens_adapter_s05tm09, pos_offset=(dx+1.524+5, 0, 0))
        _add_linked_object(obj, "Lens", mounted_lens_c220tmda, pos_offset=(dx+1.524+3.167+5, 0, 0))

        mount = _add_linked_object(obj, "Mount", mirror_mount_km05, pos_offset=(dx, 0, 0), drill=True, **mount_args)
        # upper_plate = _add_linked_object(obj, "Upper Plate", km05_tec_upper_plate, pos_offset=(dx-4, 0, -0.08*inch), drill_obj=mount, **upper_plate_args)
        # _add_linked_object(obj, "Lower Plate", km05_tec_lower_plate, pos_offset=(dx-4, 0, -0.08*inch-tec_thickness-upper_plate.Thickness.Value), **lower_plate_args)

class laser_cavity_mount:
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, tec_thickness=4, mount_args=dict(), grating_args=dict(), upper_plate_args=dict(), lower_plate_args=dict()):
        mount_args.setdefault("bolt_length", 12.5)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'TecThickness').TecThickness = tec_thickness
        obj.ViewObject.ShapeColor = misc_color
        
        self.part_numbers = [] # TODO add part numbers
        self.max_angle = 0
        self.max_width = 1

        dx = -5.334+2.032
        _add_linked_object(obj, "Diode Adapter", diode_adapter_s05lm56, pos_offset=(0, 0, 0))
        _add_linked_object(obj, "Lens Tube", lens_tube_sm05l05, pos_offset=(dx+1.524+3.812, 0, 0))
        _add_linked_object(obj, "Lens Adapter", lens_adapter_s05tm09, pos_offset=(dx+1.524+5, 0, 0))
        _add_linked_object(obj, "Lens", mounted_lens_c220tmda, pos_offset=(dx+1.524+3.167+5, 0, 0))

        width = 3*inch
        mount = _add_linked_object(obj, "Mount", fixed_mount_smr05, pos_offset=(dx+5.334, 0, 16-inch/2), drill=False, **mount_args)
        grating = _add_linked_object(obj, "Grating", grating_mount_on_km05pm_no_arm, pos_offset=(dx+width*3/4, 0, 16-inch/2), drill=False, **grating_args)
        upper_plate = _add_linked_object(obj, "Upper Plate", laser_cavity_mount_upper_plate, pos_offset=(dx-8+width/2, 0, ), drill_objs=[mount, grating], **upper_plate_args)
        _add_linked_object(obj, "Lower Plate", laser_cavity_mount_lower_plate, pos_offset=(dx-8+width/2, 0, -tec_thickness-upper_plate.Thickness.Value), **lower_plate_args)

class laser_cavity_mount_upper_plate:
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill_objs, width=inch, length=3*inch, thickness=0.25*inch):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyLength', 'Width').Width = width
        obj.addProperty('App::PropertyLength', 'Length').Length = length
        obj.addProperty('App::PropertyLength', 'Thickness').Thickness = thickness
        obj.addProperty('App::PropertyLinkListHidden', 'DrillObjects').DrillObjects = drill_objs

        obj.ViewObject.ShapeColor = adapter_color

    def execute(self, obj):
        part = _custom_box(dx=obj.Length.Value, dy=obj.Width.Value, dz=obj.Thickness.Value,
                           x=0, y=0, z=-inch/2, dir=(0, 0, -1))
        for sub_obj in obj.DrillObjects:
            part = _drill_part(part, obj, sub_obj)
            obj.Shape = part

class laser_cavity_mount_lower_plate:
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, width=1.5*inch, length=3.5*inch, thickness=0.25*inch):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'Width').Width = width
        obj.addProperty('App::PropertyLength', 'Length').Length = length
        obj.addProperty('App::PropertyLength', 'Thickness').Thickness = thickness
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color

    def execute(self, obj):
        part = _custom_box(dx=obj.Length.Value, dy=obj.Width.Value, dz=obj.Thickness.Value,
                                     x=0, y=0, z=-inch/2, dir=(0, 0, -1))
        for x, y in [(1,1), (1,-1), (-1,1), (-1,-1)]:
            part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=obj.Thickness.Value,
                                        x=(obj.Length.Value/2-4)*x, y=(obj.Width.Value/2-4)*y, z=-inch/2, dir=(0, 0, -1)))
        obj.Shape = part

        part = _bounding_box(obj, 3, 3)
        for x, y in [(1,1), (1,-1), (-1,1), (-1,-1)]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=(obj.Length.Value/2-4)*x, y=(obj.Width.Value/2-4)*y, z=0, dir=(0, 0, -1)))
        part = part.fuse(_custom_box(dx=20, dy=5, dz=inch/2,
                                     x=part.BoundBox.XMin, y=(part.BoundBox.YMax+part.BoundBox.YMin)/2, z=0,
                                     dir=(-1, 0, -1)))
        part.Placement = obj.Placement
        obj.DrillPart = part

class km05_tec_upper_plate:
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill_obj, width=inch, thickness=0.25*inch):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyLength', 'Width').Width = width
        obj.addProperty('App::PropertyLength', 'Thickness').Thickness = thickness
        obj.addProperty('App::PropertyLinkHidden', 'DrillObject').DrillObject = drill_obj

        obj.ViewObject.ShapeColor = adapter_color

    def execute(self, obj):
        part = _custom_box(dx=obj.Width.Value, dy=obj.Width.Value, dz=obj.Thickness.Value,
                           x=0, y=0, z=-inch/2, dir=(0, 0, -1))
        part = _drill_part(part, obj, obj.DrillObject)
        obj.Shape = part


class km05_tec_lower_plate:
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, width=3*inch, height=.25*inch, thickness=3*inch, part_number=''): #thickness=130-inch/2-1,
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'Thickness').Thickness = thickness
        obj.addProperty('App::PropertyLength', 'Width').Width = width
        obj.addProperty('App::PropertyLength', 'Height').Height = height

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = [part_number]

    def execute(self, obj):
        x_off = 0 #-2
        y_off = 0 #-4
        bolt_off = 2.5
        part = _custom_box(dx=obj.Thickness.Value, dy=obj.Width.Value, dz=obj.Height.Value,
                           x=x_off, y=y_off, z=-3/2*inch-3.95-obj.Thickness.Value, dir=(0, 0, -1))
        
        for x, y in [(0,0)]:
            part = part.cut(_custom_cylinder(dia=bolt_14_20['clear_dia'], dz=drill_depth,
                                    head_dia=bolt_14_20["washer_dia"], head_dz=8,
                                    x=1.5*inch*x+x_off, y=inch*y+y_off-bolt_off, z=-3/2*inch-3.95-inch/2))
        
        obj.Shape = part


class mirror_mount_mk05:
    '''
    Mirror mount, model MK05

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        circular_mirror (mirror_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['MK05']
        self.reflection_angle = 0
        self.max_angle = 90
        self.max_width = inch/2

    def execute(self, obj):
        mesh = _import_stl("MK05-Step.stl", (90, -0, -90), (-22.91-obj.ChildObjects[0].Thickness.Value, 26, -5.629))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _custom_cylinder(dia=bolt_4_40['tap_dia'], dz=drill_depth,
                           head_dia=bolt_4_40['head_dia'], head_dz=drill_depth-10,
                           x=-5.562, y=0, z=-10.2-drill_depth, dir=(0, 0, 1))
        part.Placement = obj.Placement
        obj.DrillPart = part


class mount_mk05pm:
    '''
    Mount, model MK05PM

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['MK05PM']

    def execute(self, obj):
        mesh = _import_stl("MK05PM-Step.stl", (180, 90, 0), (-7.675, 7.699, 4.493))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 2)
        part = part.cut(_custom_box(dx=4, dy=15, dz=-layout.inch/2-obj.Mesh.BoundBox.ZMin,
                                    x=part.BoundBox.XMin, y=part.BoundBox.YMax, z=part.BoundBox.ZMin,
                                    dir=(1, -1, 1), fillet=2))
        part = _fillet_all(part, 2)
        part = part.fuse(_custom_cylinder(dia=bolt_4_40['tap_dia'], dz=drill_depth,
                           head_dia=bolt_4_40['head_dia'], head_dz=drill_depth-5,
                           x=-7.675, y=7.699, z=4.493-10.2-drill_depth, dir=(0,0,1)))
        part.Placement = obj.Placement
        obj.DrillPart = part

class dichoric_mirror_mount_km05fl:
    '''
    Mirror mount, model MK05

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        circular_mirror (mirror_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['KM05fl']
        self.reflection_angle = 0
        self.max_angle = 90
        self.max_width = inch/2

    def execute(self, obj):
        mesh = _import_stl("KM05FL-Step.stl", (-180, 0, -90), (-11.53, -10.16, -10.16))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 2)
        part = part.cut(_custom_box(dx=4, dy=15, dz=-layout.inch/2-obj.Mesh.BoundBox.ZMin,
                                    x=part.BoundBox.XMin, y=part.BoundBox.YMax, z=part.BoundBox.ZMin,
                                    dir=(1, -1, 1), fillet=2))
        part = _fillet_all(part, 2)

        part = part.fuse(_custom_cylinder(dia=bolt_4_40['tap_dia'], dz=drill_depth,
                           head_dia=bolt_4_40['head_dia'], head_dz=drill_depth-10,
                           x=7.378, y=7.378, z=-4.373-drill_depth, dir=(0, 0, 1)))
        part.Placement = obj.Placement
        obj.DrillPart = part

class dichoric_mirror_mount_km05fR:
    '''
    Mirror mount, model KM05FR

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        circular_mirror (mirror_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['KM05fR']
        self.reflection_angle = 0
        self.max_angle = 90
        self.max_width = inch/2

    def execute(self, obj):
        mesh = _import_stl("KM05FR_M-Step.stl", (-90, 0, 0), (-11.53, -10.16, -10.16))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 2)
        part = part.cut(_custom_box(dx=4, dy=15, dz=-layout.inch/2-obj.Mesh.BoundBox.ZMin,
                                    x=part.BoundBox.XMin, y=part.BoundBox.YMax, z=part.BoundBox.ZMin,
                                    dir=(1, -1, 1), fillet=2))
        part = _fillet_all(part, 2)
        part = part.fuse(_custom_cylinder(dia=bolt_4_40['tap_dia'], dz=drill_depth,
                           head_dia=bolt_4_40['head_dia'], head_dz=drill_depth-5,
                           x=-11.53, y=14.53, z=.275-drill_depth, dir=(0,0,1)))
        part.Placement = obj.Placement
        obj.DrillPart = part


class grating_mount_on_mk05pm:
    '''
    Grating and Parallel Mirror Mounted on MK05PM

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        littrow_angle (float) : The angle of the grating and parallel mirror

    Sub_Parts:
        mount_mk05pm (mount_args)
        square_grating (grating_args)
        square_mirror (mirror_args)
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, littrow_angle=45, mount_args=dict(), grating_args=dict(), mirror_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyAngle', 'LittrowAngle').LittrowAngle = littrow_angle

        obj.ViewObject.ShapeColor = adapter_color
        self.dx = 12/tan(radians(2*obj.LittrowAngle))

        _add_linked_object(obj, "Mount MK05PM", mount_mk05pm, pos_offset=(-12, -4, -4-12.7/2+2), drill=drill, **mount_args)
        _add_linked_object(obj, "Grating", square_grating, pos_offset=(0, 0, 2), rot_offset=(0, 0, -obj.LittrowAngle.Value), **grating_args)
        _add_linked_object(obj, "Mirror", square_mirror, pos_offset=(self.dx, -12, 2), rot_offset=(0, 0, -obj.LittrowAngle.Value+180), **mirror_args)

    def execute(self, obj):
        # TODO add some variables to make this cleaner
        part = _custom_box(dx=25+self.dx, dy=35, dz=4,
                           x=-3.048, y=17.91, z=0, dir=(1, -1, 1))
        
        part = part.cut(_custom_box(dx=6, dy=8.1, dz=4,
                                    x=-3.048, y=17.91, z=0, dir=(1, -1, 1)))
        part = part.cut(_custom_cylinder(dia=bolt_4_40['clear_dia'], dz=4,
                                    x=0, y=0, z=0, dir=(0, 0, 1)))
        part = part.cut(_custom_cylinder(dia=bolt_4_40['clear_dia'], dz=4,
                                    x=13.34, y=15.62, z=0, dir=(0, 0, 1)))
        part.translate(App.Vector(-12, -4, -4))

        temp = _custom_box(dx=4, dy=12, dz=12,
                           x=-6, y=0, z=0, dir=(-1, 0, 1))
        temp.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), -obj.LittrowAngle.Value)
        part = part.fuse(temp)
        temp = _custom_box(dx=4, dy=12, dz=12,
                           x=self.dx+3.2, y=-12, z=0, dir=(1, 0, 1))
        temp.rotate(App.Vector(self.dx, -12, 0), App.Vector(0, 0, 1), -obj.LittrowAngle.Value)
        part = part.fuse(temp)
        part.translate(App.Vector(0, 0, -12.7/2+2))
        part = part.fuse(part)
        obj.Shape = part


class lens_holder_l05g:
    '''
    Lens Holder, Model L05G

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        circular_lens (lens_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['POLARIS-L05G']

    def execute(self, obj):
        mesh = _import_stl("POLARIS-L05G-Step.stl", (90, -0, 90), (-26.57, -13.29, -18.44))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                x=-8, y=0, z=-layout.inch/2)
        for i in [-1, 1]:
            part = part.fuse(_custom_box(dx=5, dy=2, dz=2.2,
                                         x=-8, y=i*5, z=-layout.inch/2,
                                         fillet=1, dir=(0, 0, -1)))
        part.Placement = obj.Placement
        obj.DrillPart = part


class pinhole_ida12:
    '''
    Pinhole Iris, Model IDA12

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        slide_mount (adapter_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, adapter_args=dict()):
        adapter_args.setdefault("slot_length", 10)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['IDA12-P5']
        self.transmission = True
        self.max_angle = 90
        self.max_width = 1
        self.block_width=inch/2
        self.slot_length=adapter_args['slot_length']

        _add_linked_object(obj, "Slide Mount", slide_mount,
                           pos_offset=(1.956, -12.83, 0), **adapter_args)

    def execute(self, obj):
        mesh = _import_stl("IDA12-P5-Step.stl", (90, 0, -90), (1.549, 0, -0))
        mesh.rotate(-pi/2, 0, 0)
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _custom_box(dx=6.5, dy=15+obj.ChildObjects[0].SlotLength.Value, dz=1,
                           x=1.956, y=0, z=-layout.inch/2,
                           fillet=0.125*layout.inch, dir=(0,0,-1))
        part.Placement = obj.Placement
        obj.DrillPart = part


class prism_mount_km100pm:
    '''
    Kinematic Prism Mount, Model KM100PM

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['KM100PM']

    def execute(self, obj):
        mesh = _import_stl("KM100PM.stl", (90, -0, -90), (-8.877, 38.1, -6.731))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 6, 0.125*layout.inch, max_offset=(-18, -38, 0), z_tol=True)
        part = part.fuse(_bounding_box(obj, 3, 0.125*layout.inch, min_offset=(17, 0, 0.63)))    
        # part = part.fuse(_bounding_box(obj, 3, 4, max_offset=(-18, -38, 0), z_tol=True))
        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                     x=-14.02, y=12.63, z=17.5))
        part.Placement = obj.Placement
        obj.DrillPart = part

class prism_mount_km100pm_bridged:
    '''
    Custom KM100PM Mount with a solid bridge for the AOM clearings.
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color # Assuming mount_color is defined globally
        self.part_numbers = ['KM100PM (Bridged)']

    def execute(self, obj):
        mesh = _import_stl("KM100PM.stl", (90, -0, -90), (-8.877, 38.1, -6.731))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        # 1. Generate the original main vertical pill
        part = _bounding_box(obj, 6, 0.125*layout.inch, max_offset=(-18, -38, 0), z_tol=True)

        # --- NEW CODE: MAKE THE PILL A THROUGH-HOLE ---
        bb = part.BoundBox
        deep_z = 100 # Arbitrarily large number to pierce the board completely
        
        # Make a box that perfectly matches the pill's X/Y footprint but goes extremely deep
        through_hole_extension = Part.makeBox(bb.XMax - bb.XMin, bb.YMax - bb.YMin, deep_z)
        
        # Place it precisely under the pill's footprint, pushing downward into the negative Z
        through_hole_extension.Placement.Base = App.Base.Vector(bb.XMin, bb.YMin, -deep_z)
        
        # Fuse this deep column to the original shallow pocket
        part = part.fuse(through_hole_extension)
        # ----------------------------------------------

        # Add the remaining original mount pockets (side knobs, etc.)
        part = part.fuse(_bounding_box(obj, 3, 0.125*layout.inch, min_offset=(17, 0, 0.63)))    
        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                     x=-14.02, y=12.63, z=17.5))

        # --- 2. CARVE OUT THE BRIDGE ---
        # (Keep your exact tuned code here!)
        bridge_x = 23
        bridge_y = 26.444
        bridge_z = 50.0  
        
        bridge_saver = Part.makeBox(bridge_x, bridge_y, bridge_z)
        
        tuned_x = -40+14.884-.484
        tuned_y = -30+13.728-3.444
        tuned_z = -50-10.5
        
        bridge_saver.Placement.Base = App.Base.Vector(tuned_x, tuned_y, tuned_z)
        
        part = part.cut(bridge_saver)
        # -------------------------------

        part.Placement = obj.Placement
        obj.DrillPart = part

    # def execute(self, obj):
    #     mesh = _import_stl("KM100PM.stl", (90, -0, -90), (-8.877, 38.1, -6.731))
    #     mesh.Placement = obj.Mesh.Placement
    #     obj.Mesh = mesh

    #     # 1. Generate the original deep mount pockets
    #     part = _bounding_box(obj, 6, 0.125*layout.inch, max_offset=(-18, -38, 0), z_tol=True)
    #     part = part.fuse(_bounding_box(obj, 3, 0.125*layout.inch, min_offset=(17, 0, 0.63)))    
    #     part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
    #                                  x=-14.02, y=12.63, z=17.5))

    #     # --- 2. CARVE OUT THE BRIDGE ---
    #     bridge_x = 23
    #     bridge_y = 26.444
    #     bridge_z = 50.0  # Make this huge again so it definitely blocks the drill underneath!
        
    #     bridge_saver = Part.makeBox(bridge_x, bridge_y, bridge_z)
        
    #     # Replace these with your best X and Y from your tuning step
    #     tuned_x = -40+14.884-.484
    #     tuned_y = -30+13.728-3.444
        
    #     # FreeCAD boxes grow UPWARD. 
    #     # If tuned_z is -50, and the box is 50 tall, the top of the bridge is exactly at Z = 0.
    #     # If you want the floor of the bridge to sit below the surface (e.g., flush with Region 1 & 3),
    #     # make tuned_z slightly lower, like -53.175.
    #     tuned_z = -50 -10.5
        
    #     bridge_saver.Placement.Base = App.Base.Vector(tuned_x, tuned_y, tuned_z)
        
    #     # Subtract the bridge from the mount's cutouts
    #     part = part.cut(bridge_saver)
    #     # -------------------------------

    #     part.Placement = obj.Placement
    #     obj.DrillPart = part

class wire_tube:
    '''
    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        # self.part_numbers = ['HCA3', 'PAF2-5A']
        self.max_angle = 0
        self.max_width = 1

    def execute(self, obj):
        mesh = _import_stl("wire_tube.stl", (90, 90, 90), (-133, 0, -29.25))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 3, 3, min_offset=(0, 0, -3))
        part.Placement = obj.Placement
        obj.DrillPart = part      

class brewster_window:
    '''
    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = glass_color
        # self.part_numbers = ['HCA3', 'PAF2-5A']
        self.max_angle = 0
        self.max_width = 1

    def execute(self, obj):
        mesh = _import_stl("BW20M.stl", (90, 0, 90), (90, 20.79, -40.46))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 3, 3, min_offset=(0, 0, 0))
        part.Placement = obj.Placement
        obj.DrillPart = part            

class laser_box:

    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, thickness=115 + inch/4*2 +  inch, width=95 + inch, height=95, mat_thickness=0, part_number=''):
        # (self, obj, drill=True, thickness=4.5*inch, width=3.5*inch, height=80, mat_thickness=0, part_number=''):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'Thickness').Thickness = thickness
        obj.addProperty('App::PropertyLength', 'Width').Width = width
        obj.addProperty('App::PropertyLength', 'Height').Height = height
        obj.addProperty('App::PropertyLength', 'MatThickness').MatThickness = mat_thickness

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = [part_number]

    def execute(self, obj):
        x_off = -2
        y_off = -4
        thickness = inch/4
        part = _custom_box(dx=obj.Thickness.Value, dy=obj.Width.Value, dz=obj.Height.Value,
                           x=x_off, y=y_off, z=-3/2*inch-3.95, dir=(0, 0, 1))
        
        # Bottom cuttout
        part = part.cut(_custom_box(dx=obj.Thickness.Value-inch/4*2-.7*inch, dy=obj.Width.Value-.7*inch, dz=80,   #-2*inch+5
                           x=x_off, y=y_off, z=-3/2*inch-3.95, dir=(0, 0, 1)))
        
        # Component cutouts
        parent = obj.ParentObject
        mount = parent.ChildObjects[0]
        parent.Proxy.execute(parent)
        for cutObj in [mount, parent]:
            try:
                temp = _bounding_box(cutObj, 19, 19, z_tol=False)
                temp.translate(cutObj.Placement.Base)
                temp.translate(App.Vector(-8,-7,0))
                #temp.rotate(App.Vector(0,0,0),App.Vector(0,0,1),0)
                part = part.cut(temp)
                print("yup")
            except Exception as e:
                print(e)
                pass
        
        #part = _custom_box(dx=obj.Thickness.Value, dy=obj.Width.Value, dz=obj.Height.Value,
        #                   x=x_off, y=y_off, z=-3/2*inch-3.95-inch/2-obj.MatThickness.Value, dir=(0, 0, 1))
        #part = part.cut(_custom_box(dx=obj.Thickness.Value-inch/4*2, dy=obj.Width.Value-inch/4*2, dz=obj.Height.Value-inch/4,
        #                   x=x_off, y=y_off, z=-3/2*inch-3.95-inch/2-obj.MatThickness.Value, dir=(0, 0, 1)))
        
        # Cable opening
        #Square cut 
        #part = part.cut(_custom_box(dx=obj.Width.Value, dy=10, dz=50,
        #                   x=x_off-obj.Thickness.Value/2, y=y_off+0, z=-2*inch-3.95-inch, dir=(0, 0, 1)))
        
        #Circular cut
        part = part.cut(_custom_cylinder(dia=28, dz=obj.Thickness.Value/2,
                           x=x_off-obj.Thickness.Value/2, y=y_off+4, z=-42, dir=(1, 0, 0)))

        # Laser opening
        part = part.cut(_custom_cylinder(dia=25.8, dz=obj.Thickness.Value/2,
                           x=x_off+obj.Thickness.Value/2, y=y_off+24, z=-2, dir=(-1, 0, 0)))
        
        # Bolt openings
        part = part.cut(_custom_cylinder(dia=5, dz=obj.Thickness.Value/2,
                           x=x_off-obj.Thickness.Value/2, y=y_off+25.5, z=12.9+6.4, dir=(1, 0, 0)))
        part = part.cut(_custom_cylinder(dia=5, dz=obj.Thickness.Value/2,
                           x=x_off-obj.Thickness.Value/2, y=y_off-12.2, z=-24.8+6.4, dir=(1, 0, 0)))
        obj.Shape = part

class laser_base:

    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, thickness=125 + inch/4*2 + 1 * inch, width=100+ inch, height=0.25*inch, mat_thickness=0.5*inch, part_number=''):
    #(self, obj, drill=True, thickness=4*inch, width=3*inch, height=0.25*inch, mat_thickness=0.25*inch, part_number=''): #thickness=130-inch/2-1,
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'Thickness').Thickness = thickness
        obj.addProperty('App::PropertyLength', 'Width').Width = width
        obj.addProperty('App::PropertyLength', 'Height').Height = height
        obj.addProperty('App::PropertyLength', 'MatThickness').MatThickness = mat_thickness

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = [part_number]

    def execute(self, obj):
        x_off = -2
        y_off = -4
        bolt_off = 1.5
        part = _custom_box(dx=obj.Thickness.Value, dy=obj.Width.Value, dz=obj.Height.Value,
                           x=x_off, y=y_off, z=-3/2*inch-3.95-obj.MatThickness.Value, dir=(0, 0, -2))
        
        
        for x, y in [(-2,-2), (-2,1), (2,-2), (2,1)]:
            
            part = part.cut(_custom_cylinder(dia=6.6, dz=drill_depth,
                                    head_dia=6.6, head_dz=8,
                                    x=1*inch*x+x_off, y=inch*y+y_off-bolt_off+.5*inch, z=-3/2*inch-3.95-inch/2))  #bolt_14_20['tap_dia']
        
        obj.Shape = part

class ECDL:
    """
    ECDL device 
    """
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, slot_length=0, countersink=False, counter_depth=3, arm_thickness=8, arm_clearance=2, stage_thickness=6, stage_length=20, mat_thickness=10, littrow_angle=56.6): 
        obj.Proxy = self
        # obj.addProperty("App::PropertyPlacement", "BasePlacement")
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'SlotLength').SlotLength = slot_length
        obj.addProperty('App::PropertyBool', 'Countersink').Countersink = countersink
        obj.addProperty('App::PropertyLength', 'CounterDepth').CounterDepth = counter_depth
        obj.addProperty('App::PropertyLength', 'ArmThickness').ArmThickness = arm_thickness
        obj.addProperty('App::PropertyLength', 'ArmClearance').ArmClearance = arm_clearance
        obj.addProperty('App::PropertyLength', 'StageThickness').StageThickness = stage_thickness
        obj.addProperty('App::PropertyLength', 'StageLength').StageLength = stage_length
        obj.addProperty('App::PropertyLength', 'MatThickness').MatThickness = mat_thickness
        obj.addProperty('App::PropertyAngle', 'LittrowAngle').LittrowAngle = littrow_angle
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)


        dx = -5.334+2.032
        mount = _add_linked_object(obj, "Mount KM100PM", prism_mount_km100pm, pos_offset=(2.032+13.96-3.8, -25.91+16, -18.67))
        _add_linked_object(obj, "Diode Adapter", diode_adapter_s05lm56, pos_offset=(0, 0, 0))
        _add_linked_object(obj, "Lens Tube", lens_tube_sm05l05, pos_offset=(dx+1.524+3.812, 0, 0))
        _add_linked_object(obj, "Lens Adapter", lens_adapter_s05tm09, pos_offset=(dx+1.524+5, 0, 0))
        _add_linked_object(obj, "Lens", mounted_lens_c220tmda, pos_offset=(dx+1.524+3.167+5, 0, 0))

        _add_linked_object(obj, "Mount", fixed_mount_smr05, pos_offset=(2.032, 0, 0), rot_offset=(90, 0, 0), drill=False)
        _add_linked_object(obj, "Wire Tube", wire_tube, pos_offset=(0, 0, -.5*inch), rot_offset=(0, 0, 0), drill=False)
        _add_linked_object(obj, "Brewster_window", brewster_window, pos_offset=(0, 20, 1*inch), rot_offset=(0, 0, 0), drill=False)

        gap =22
        lit_angle = radians(90-obj.LittrowAngle.Value)
        beam_angle = radians(obj.LittrowAngle.Value)
        ref_len = gap/sin(2*beam_angle)
        ref_x = ref_len*cos(2*beam_angle)
        dx = ref_x+12.7*cos(lit_angle)+(6+3.2)*sin(lit_angle)
        extra_x = 20-dx
        grating_dx = -(6*sin(lit_angle)+12.7/2*cos(lit_angle))-extra_x
        mirror_dx = grating_dx-ref_x

        _add_linked_object(obj, "Grating", square_grating, pos_offset=(grating_dx+47, -2+5, -2.7), rot_offset=(0, 0, 180-obj.LittrowAngle.Value))
        _add_linked_object(obj, "PZT", box, pos_offset=(grating_dx+48.6, -7+5, -2.7), rot_offset=(0, 0, 180-obj.LittrowAngle.Value))
        _add_linked_object(obj, "Mirror", square_mirror, pos_offset=(mirror_dx+36.5, gap-3, -2.7), rot_offset=(0, 0, -obj.LittrowAngle.Value))

        upper_plate = _add_linked_object(obj, "Upper Plate", km05_tec_upper_plate, pos_offset=(2.032+13.96-3.8-13.96, 0, -inch/4-6.3), width=1.5*inch, drill_obj=mount)
        _add_linked_object(obj, "TEC", TEC, pos_offset=(grating_dx+20, 0, -33.7), rot_offset=(90, 90, 90))
        _add_linked_object(obj, "Lower Plate", km05_tec_lower_plate, pos_offset=(2.032+13.96-3.8-13.96, 0, 3.25*inch), width=3*inch)
        _add_linked_object(obj, "Box", laser_box, pos_offset=(0, 0, 0*inch), rot_offset=(0, 0, 0), mat_thickness=mat_thickness)

    def execute(self, obj):
        dx = obj.ArmThickness.Value
        dy = 45
        dz = 17
        stage_dx = obj.StageLength.Value
        stage_dz = obj.StageThickness.Value

        part = _custom_box(dx=dx, dy=dy, dz=dz-obj.ArmClearance.Value,
                           x=0, y=4, z=obj.ArmClearance.Value)
        part = part.fuse(_custom_box(dx=stage_dx, dy=dy, dz=dz-obj.ArmClearance.Value,
                                     x=0, y=4, z=dz, dir=(1, 0, -1)))
        for ddy in [15.2, 38.1]:
            part = part.cut(_custom_box(dx=stage_dx+dx, dy=obj.SlotLength.Value+bolt_4_40['clear_dia'], dz=bolt_4_40['clear_dia'],
                                        x=stage_dx, y=25.4-ddy+2.5, z=6.4,
                                        fillet=bolt_4_40['clear_dia']/2, dir=(-1, 0, 0)))
            part = part.cut(_custom_box(dx=stage_dx+dx-5-4, dy=obj.SlotLength.Value+bolt_4_40['head_dia'], dz=bolt_4_40['head_dia'],
                                        x=stage_dx, y=25.4-ddy+2.5, z=6.4,
                                        fillet=bolt_4_40['head_dia']/2, dir=(-1, 0, 0)))
            
        extra_y = 0
        gap = 22
        lit_angle = radians(90-obj.LittrowAngle.Value)
        beam_angle = radians(obj.LittrowAngle.Value)
        ref_len = gap/sin(2*beam_angle)
        ref_x = ref_len*cos(2*beam_angle)
        dx2 = ref_x+9.7*cos(lit_angle)+(6+3.2)*sin(lit_angle)
        extra_x = 18-dx2
        dy2 = gap+9.7*sin(lit_angle)+(6+3.2)*cos(lit_angle)
        dz2 = inch/2
        cut_x = 18.7*cos(lit_angle)

        part = part.fuse(_custom_box(dx=stage_dx+dx/2, dy=dy, dz=stage_dz+12.7,
                                     x=-dx/2, y=4, z=dz+12.7, dir=(1, 0, -1)))

        part.translate(App.Vector(dx/2, 25.4-15.2+obj.SlotLength.Value/2, -6.4))
        part.translate(App.Vector(2.032+13.96-3.8, -25.91+16, -18.67))
        part = part.fuse(part)

        temp = _custom_box(dx=ref_len*cos(beam_angle)+12.2, dy=dy/sin(lit_angle)+15, dz=dz,
                           x=-cut_x+9, y=-(dx-cut_x)*cos(lit_angle)-15, z=-6-3.07, dir=(-1, 1, 1))
        temp.rotate(App.Vector(-cut_x, 0, 0), App.Vector(0, 0, 1), -obj.LittrowAngle.Value)
        temp.translate(App.Vector(-extra_x+36, -20.7/2*sin(lit_angle)-6*cos(lit_angle), .2))

        part = part.cut(temp)
        part.Placement = obj.Placement
        obj.Shape = part

        # part = _bounding_box(obj, 3, 4, z_tol=True, min_offset=(0, 0, 0.668))
        # part.Placement = obj.Placement 
        obj.DrillPart = part

        #_add_linked_object(obj, "Box", laser_box, pos_offset=(0, 5, 0), rot_offset=(0, 0, 0), mat_thickness=0)

class laser_mount_km100pm_LMR1:
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, slot_length=0, countersink=False, counter_depth=3, arm_thickness=8, arm_clearance=2, stage_thickness=6, stage_length=20, mat_thickness=0, littrow_angle=53.43): #54 for 674
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'SlotLength').SlotLength = slot_length
        obj.addProperty('App::PropertyBool', 'Countersink').Countersink = countersink
        obj.addProperty('App::PropertyLength', 'CounterDepth').CounterDepth = counter_depth
        obj.addProperty('App::PropertyLength', 'ArmThickness').ArmThickness = arm_thickness
        obj.addProperty('App::PropertyLength', 'ArmClearance').ArmClearance = arm_clearance
        obj.addProperty('App::PropertyLength', 'StageThickness').StageThickness = stage_thickness
        obj.addProperty('App::PropertyLength', 'StageLength').StageLength = stage_length
        obj.addProperty('App::PropertyLength', 'MatThickness').MatThickness = mat_thickness
        obj.addProperty('App::PropertyAngle', 'LittrowAngle').LittrowAngle = littrow_angle
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)


        dx = -5.334+2.032
        _add_linked_object(obj, "Diode Adapter", diode_adapter_s05lm56, pos_offset=(0, 0, 0))
        _add_linked_object(obj, "Lens Tube", lens_tube_sm05l05, pos_offset=(dx+1.524+3.812, 0, 0))
        _add_linked_object(obj, "Lens Adapter", lens_adapter_s05tm09, pos_offset=(dx+1.524+5, 0, 0))
        _add_linked_object(obj, "Lens", mounted_lens_c220tmda, pos_offset=(dx+1.524+3.167+5, 0, 0))

        mount = _add_linked_object(obj, "Mount KM100PM", prism_mount_km100pm, pos_offset=(2.032+13.96-3.8, -25.91+16, -18.67))
        _add_linked_object(obj, "Mount", fixed_mount_smr05, pos_offset=(2.032, 0, 0), rot_offset=(90, 0, 0), drill=False)
       # _add_linked_object(obj, "Box", laser_box, pos_offset=(-10, 0, 0), rot_offset=(0, 0, 0), mat_thickness=mat_thickness)
       # _add_linked_object(obj, "Base", laser_base, pos_offset=(0, 0, 0), rot_offset=(0, 0, 0), mat_thickness=mat_thickness)

        gap = 23
        lit_angle = radians(90-obj.LittrowAngle.Value)
        beam_angle = radians(obj.LittrowAngle.Value)
        ref_len = gap/sin(2*beam_angle)
        ref_x = ref_len*cos(2*beam_angle)
        dx = ref_x+12.7*cos(lit_angle)+(6+3.2)*sin(lit_angle)
        extra_x = 20-dx
        grating_dx = -(6*sin(lit_angle)+12.7/2*cos(lit_angle))-extra_x
        mirror_dx = grating_dx-ref_x

        _add_linked_object(obj, "Grating", square_grating, pos_offset=(grating_dx+40, -1, -2.7), rot_offset=(0, 0, 180-obj.LittrowAngle.Value))
        _add_linked_object(obj, "PZT", box, pos_offset=(grating_dx+34.6+9.2, -5.8, -2.7), rot_offset=(0, 0, 180-obj.LittrowAngle.Value))
        _add_linked_object(obj, "Mirror", square_mirror, pos_offset=(mirror_dx+36.5, gap-3, -2.7), rot_offset=(0, 0, -obj.LittrowAngle.Value))

        upper_plate = _add_linked_object(obj, "Upper Plate", km05_tec_upper_plate, pos_offset=(2.032+13.96-3.8-13.96, 0, -inch/4-6.3), width=1.5*inch, drill_obj=mount)
        _add_linked_object(obj, "TEC", TEC, pos_offset=(grating_dx+11.1, 0, -33.7), rot_offset=(90, 90, 90))
        _add_linked_object(obj, "Lower Plate", km05_tec_lower_plate, pos_offset=(2.032+13.96-3.8-13.96, 0, -inch/4-6.3-4-upper_plate.Thickness.Value), width=2.5*inch)

    def execute(self, obj):
        dx = obj.ArmThickness.Value
        dy = 45
        dz = 27
        stage_dx = obj.StageLength.Value
        stage_dz = obj.StageThickness.Value

        part = _custom_box(dx=dx, dy=dy, dz=dz-obj.ArmClearance.Value,
                           x=0, y=4, z=obj.ArmClearance.Value)
        part = part.fuse(_custom_box(dx=stage_dx, dy=dy, dz=dz-obj.ArmClearance.Value,
                                     x=0, y=4, z=dz, dir=(1, 0, -1)))
        for ddy in [15.2, 38.1]:
            part = part.cut(_custom_box(dx=stage_dx+dx, dy=obj.SlotLength.Value+bolt_4_40['clear_dia'], dz=bolt_4_40['clear_dia'],
                                        x=stage_dx, y=25.4-ddy+2.5, z=6.4,
                                        fillet=bolt_4_40['clear_dia']/2, dir=(-1, 0, 0)))
            part = part.cut(_custom_box(dx=stage_dx+dx-5-4, dy=obj.SlotLength.Value+bolt_4_40['head_dia'], dz=bolt_4_40['head_dia'],
                                        x=stage_dx, y=25.4-ddy+2.5, z=6.4,
                                        fillet=bolt_4_40['head_dia']/2, dir=(-1, 0, 0)))
            
        extra_y = 0
        gap = 23
        lit_angle = radians(90-obj.LittrowAngle.Value)
        beam_angle = radians(obj.LittrowAngle.Value)
        ref_len = gap/sin(2*beam_angle)
        ref_x = ref_len*cos(2*beam_angle)
        dx2 = ref_x+12.7*cos(lit_angle)+(6+3.2)*sin(lit_angle)
        extra_x = 18-dx2
        dy2 = gap+12.7*sin(lit_angle)+(6+3.2)*cos(lit_angle)
        dz2 = inch/2
        cut_x = 17.7*cos(lit_angle)

        part = part.fuse(_custom_box(dx=stage_dx+dx/2, dy=dy, dz=stage_dz+12.7,
                                     x=-dx/2, y=4, z=dz+12.7, dir=(1, 0, -1)))

        part.translate(App.Vector(dx/2, 25.4-15.2+obj.SlotLength.Value/2, -6.4))
        part.translate(App.Vector(2.032+13.96-3.8, -25.91+16, -18.67))
        part = part.fuse(part)

        temp = _custom_box(dx=ref_len*cos(beam_angle)+6+3.2+3, dy=dy/sin(lit_angle)+15, dz=dz,
                           x=-cut_x+5, y=-(dx-cut_x)*cos(lit_angle)-15, z=-6-3.07, dir=(-1, 1, 1))
        temp.rotate(App.Vector(-cut_x, 0, 0), App.Vector(0, 0, 1),-obj.LittrowAngle.Value)
        temp.translate(App.Vector(-extra_x+36, -17.7/2*sin(lit_angle)-6*cos(lit_angle), .2))

        part = part.cut(temp)
        obj.Shape = part

        part = _bounding_box(obj, 3, 4, z_tol=True, min_offset=(0, 0, 0.668))
        part.Placement = obj.Placement
        obj.DrillPart = part

class mount_for_km100pm:
    '''
    Adapter for mounting isomet AOMs to km100pm kinematic mount

    Args:
        mount_offset (float[3]) : The offset position of where the adapter mounts to the component
        drill (bool) : Whether baseplate mounting for this part should be drilled
        slot_length (float) : The length of the slots used for mounting to the km100pm
        countersink (bool) : Whether to drill a countersink instead of a counterbore for the AOM mount holes
        counter_depth (float) : The depth of the countersink/bores for the AOM mount holes
        arm_thickness (float) : The thickness of the arm the mounts to the km100PM
        arm_clearance (float) : The distance between the bottom of the adapter arm and the bottom of the km100pm
        stage_thickness (float) : The thickness of the stage that mounts to the AOM
        stage_length (float) : The length of the stage that mounts to the AOM
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, slot_length=5, countersink=False, counter_depth=3, arm_thickness=8, arm_clearance=2, stage_thickness=4, stage_length=21):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'SlotLength').SlotLength = slot_length
        obj.addProperty('App::PropertyBool', 'Countersink').Countersink = countersink
        obj.addProperty('App::PropertyLength', 'CounterDepth').CounterDepth = counter_depth
        obj.addProperty('App::PropertyLength', 'ArmThickness').ArmThickness = arm_thickness
        obj.addProperty('App::PropertyLength', 'ArmClearance').ArmClearance = arm_clearance
        obj.addProperty('App::PropertyLength', 'StageThickness').StageThickness = stage_thickness
        obj.addProperty('App::PropertyLength', 'StageLength').StageLength = stage_length
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)

    def execute(self, obj):
        dx = obj.ArmThickness.Value
        dy = 47.5
        dz = 16.92
        stage_dx = obj.StageLength.Value
        stage_dz = obj.StageThickness.Value

        part = _custom_box(dx=dx, dy=dy, dz=dz-obj.ArmClearance.Value,
                           x=0, y=0, z=obj.ArmClearance.Value)
        part = part.fuse(_custom_box(dx=stage_dx, dy=dy, dz=stage_dz,
                                     x=0, y=0, z=dz, dir=(1, 0, -1)))
        for ddy in [15.2, 38.1]:
            part = part.cut(_custom_box(dx=dx, dy=obj.SlotLength.Value+bolt_4_40['clear_dia'], dz=bolt_4_40['clear_dia'],
                                        x=dx/2, y=25.4-ddy, z=6.4,
                                        fillet=bolt_4_40['clear_dia']/2, dir=(-1, 0, 0)))
            part = part.cut(_custom_box(dx=dx/2, dy=obj.SlotLength.Value+bolt_4_40['head_dia'], dz=bolt_4_40['head_dia'],
                                        x=dx/2, y=25.4-ddy, z=6.4,
                                        fillet=bolt_4_40['head_dia']/2, dir=(-1, 0, 0)))
        for ddy in [0, -11.42, -26.65, -38.07]:
            part = part.cut(_custom_cylinder(dia=bolt_4_40['clear_dia'], dz=stage_dz, head_dia=bolt_4_40['head_dia'],
                                        head_dz=obj.CounterDepth.Value, countersink=obj.Countersink,
                                        x=11.25, y=18.9+ddy, z=dz-4, dir=(0,0,1)))
        part.translate(App.Vector(dx/2, 25.4-15.2+obj.SlotLength.Value/2, -6.4))
        part = part.fuse(part)
        obj.Shape = part

        part = _bounding_box(obj, 3, 4, z_tol=True, min_offset=(0, 0, 0.668))
        part.Placement = obj.Placement
        obj.DrillPart = part

class lens_mount_fmp1:
    type = 'Mesh::FeaturePython'
    # type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, adapter_args = {}):#, thumbscrews=False):
        adapter_args.setdefault("mount_hole_dy", 35)
        adapter_args.setdefault("outer_thickness", 3)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        # obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')
        obj.ViewObject.ShapeColor = mount_color
        _add_linked_object(obj, 'surface_adapter', surface_adapter_wide, pos_offset=(1.5 ,0 ,-22.1),rot_offset=(0, 0, 0), **adapter_args)

    def execute(self, obj):
        # mesh = _import_stl("POLARIS-K05S2-Step.stl", (90, -0, -90), (-4.514, 0.254-20, -0.254))
        mesh = _import_stl("FMP1-Step.stl", (180,180, 0), (4.65,0,0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

class lens_mount_sm1tc:
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, adapter_args = {}):#, thumbscrews=False):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')
        obj.addProperty('App::PropertyLength', 'BoltLength').BoltLength = 15
        obj.ViewObject.ShapeColor = mount_color

    def execute(self, obj):        
        mesh = _import_stl("SM1TC_SM1L03.stl", (90,0,90), (1.3,0,0,)) # clamp for tube for lens
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh       
        
        part = _custom_cylinder(dia=bolt_8_32['clear_dia']+0.35, dz=inch + 15, #  dia is expanded since it is M4
                                          head_dia= bolt_8_32['clear_dia']+0.35 , head_dz=0.92*inch-obj.BoltLength.Value +1 , # head_dia = bolt_8_32['head_dia']
                                          x=1.3, y=0, z=-inch*3/2-13, dir=(0,0,1))
        
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=2, dz=2.2,
                                              x=-5.75, y=i*5, z=-layout.inch)) # pinholes for assistance of the accurate position 
        
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=2, dz=2.2,
                                              x=7.95, y=i*5, z=-layout.inch))

        # part for a square washer
        # https://www.mcmaster.com/99041A204/
        # Zinc-Plated Steel Square Washer
        # for Number 6 Screw Size, 0.156" ID, 0.500" Wide
        part = part.fuse(_custom_box(dx=0.55 * inch, dy=0.55 * inch, dz=11, x=1.3, y = 0, z = -42,fillet=0, dir=(0,0,-1), fillet_dir=None))
        # for cnc machining
        for j in [1,-1]:
            for k in [1, -1]:
                part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'] * 2, dz=drill_depth,
                                x=1.3 + j * 0.25 * inch , y=0 + k * 0.25*inch, z=-42, dir=(0,0,-1)))

        part.Placement = obj.Placement
        obj.DrillPart = part

class surface_adapter:
    '''
    Surface adapter for post-mounted parts

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mount_hole_dy (float) : The spacing between the two mount holes of the adapter
        adapter_height (float) : The height of the surface adapter
        outer_thickness (float) : The thickness of the walls around the bolt holes
        center_thread_depth (float) : The depth of the threaded portion in the center hole
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_hole_dy=36, adapter_height=8, outer_thickness=2, center_thread_depth=3, pd_cable=False):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
        obj.addProperty('App::PropertyLength', 'AdapterHeight').AdapterHeight = adapter_height
        obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
        obj.addProperty('App::PropertyLength', 'CenterThreadDepth').CenterThreadDepth = center_thread_depth
        obj.addProperty('App::PropertyBool', 'Cable').Cable = pd_cable
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)
        self.drill_tolerance = 1

    def execute(self, obj):
        dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2
        dy = dx+obj.MountHoleDistance.Value
        dz = obj.AdapterHeight.Value

        part = _custom_box(dx=dx, dy=dy, dz=dz,
                           x=0, y=0, z=0, dir=(0, 0, -1),
                           fillet=5)
        
        for i in [-1, 1]:
            part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
                                             head_dia=bolt_8_32['head_dia']+obj.OuterThickness.Value, head_dz=bolt_8_32['head_dz'],
                                             x=0, y=i*obj.MountHoleDistance.Value/2, z=0))
    
        part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
                                        head_dia=bolt_8_32['head_dia']+obj.OuterThickness.Value, head_dz=bolt_8_32['head_dz'],
                                        x=0, y=0, z=-dz, dir=(0,0,1)))

        obj.Shape = part

        part = _bounding_box(obj, self.drill_tolerance, 6)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=0, y=i*obj.MountHoleDistance.Value/2, z=0))

        if obj.Cable:
            for i in [1, 2]:
                for j in [-3, -1, 1, 3]:
                    part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                                      x=i*10-55, y=j*8.9, z=16.5))

        part.Placement = obj.Placement
        obj.DrillPart = part

class surface_adapter_aom:

    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, mount_hole_dy=36, adapter_height=8, outer_thickness=2, center_thread_depth=3, pd_cable=False):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
        obj.addProperty('App::PropertyLength', 'AdapterHeight').AdapterHeight = adapter_height
        obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
        obj.addProperty('App::PropertyLength', 'CenterThreadDepth').CenterThreadDepth = center_thread_depth
        obj.addProperty('App::PropertyBool', 'Cable').Cable = pd_cable
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)
        self.drill_tolerance = 1

    def execute(self, obj):
        mesh = _import_stl("Surface_Adapter_aom.stl", (0, 0, 0), ([0, 0, 0]))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, self.drill_tolerance, 0.125*layout.inch)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=0, y=i*65/2, z=0))

        part.Placement = obj.Placement
        obj.DrillPart = part

class surface_adapter_isolator:
    '''
    Surface adapter for post-mounted parts

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mount_hole_dy (float) : The spacing between the two mount holes of the adapter
        adapter_height (float) : The height of the surface adapter
        outer_thickness (float) : The thickness of the walls around the bolt holes
        center_thread_depth (float) : The depth of the threaded portion in the center hole
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_hole_dy=36, adapter_height=8, outer_thickness=2, center_thread_depth=3):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
        obj.addProperty('App::PropertyLength', 'AdapterHeight').AdapterHeight = adapter_height
        obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
        obj.addProperty('App::PropertyLength', 'CenterThreadDepth').CenterThreadDepth = center_thread_depth
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)
        self.drill_tolerance = 1

    def execute(self, obj):
        dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2 + 20
        dy = dx+obj.MountHoleDistance.Value - 20
        dz = obj.AdapterHeight.Value

        part = _custom_box(dx=dx, dy=dy, dz=dz,
                           x=0, y=0, z=0, dir=(0, 0, -1),
                           fillet=5)
        
        for i in [-1, 1]:
            part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
                                             head_dia=bolt_8_32['head_dia']+obj.OuterThickness.Value, head_dz=bolt_8_32['head_dz'],
                                             x=0, y=i*obj.MountHoleDistance.Value/2, z=0))
    
        part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
                                        head_dia=bolt_8_32['head_dia']+obj.OuterThickness.Value, head_dz=bolt_8_32['head_dz'],
                                        x=0, y=0, z=-dz, dir=(0,0,1)))

        obj.Shape = part

        part = _bounding_box(obj, self.drill_tolerance, 6)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=0, y=i*obj.MountHoleDistance.Value/2, z=0))
        part.Placement = obj.Placement
        obj.DrillPart = part

class surface_adapter_isolator_lip:
    '''
    Surface adapter for post-mounted parts

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mount_hole_dy (float) : The spacing between the two mount holes of the adapter
        adapter_height (float) : The height of the surface adapter
        outer_thickness (float) : The thickness of the walls around the bolt holes
        center_thread_depth (float) : The depth of the threaded portion in the center hole
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, mount_hole_dy=36, adapter_height=8, outer_thickness=2, center_thread_depth=3):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
        obj.addProperty('App::PropertyLength', 'AdapterHeight').AdapterHeight = adapter_height
        obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
        obj.addProperty('App::PropertyLength', 'CenterThreadDepth').CenterThreadDepth = center_thread_depth
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)
        self.drill_tolerance = 1

    def execute(self, obj):
        mesh = _import_stl("Surface_Adapter_isolator_lip.stl", (0, 0, 0), ([0, 0, 0]))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, self.drill_tolerance, 0.125*layout.inch)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=0, y=i*obj.MountHoleDistance.Value/2, z=0))
        part.Placement = obj.Placement
        obj.DrillPart = part


class surface_adapter_rotated_90:
    '''
    Surface adapter for post-mounted parts

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mount_hole_dy (float) : The spacing between the two mount holes of the adapter
        adapter_height (float) : The height of the surface adapter
        outer_thickness (float) : The thickness of the walls around the bolt holes
        center_thread_depth (float) : The depth of the threaded portion in the center hole
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_hole_dy=36, adapter_height=8, outer_thickness=2, center_thread_depth=3):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
        obj.addProperty('App::PropertyLength', 'AdapterHeight').AdapterHeight = adapter_height
        obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
        obj.addProperty('App::PropertyLength', 'CenterThreadDepth').CenterThreadDepth = center_thread_depth
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)
        self.drill_tolerance = 1

    def execute(self, obj):
        dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2 + 10
        dy = dx+obj.MountHoleDistance.Value
        dz = obj.AdapterHeight.Value

        part = _custom_box(dx=dy, dy=dx, dz=dz,
                           x=0, y=0, z=0, dir=(0, 0, -1),
                           fillet=5)
        
        for i in [-1, 1]:
            part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
                                             head_dia=bolt_8_32['head_dia']+obj.OuterThickness.Value, head_dz=bolt_8_32['head_dz'],
                                             x=i*obj.MountHoleDistance.Value/2, y=0, z=0))
    
        part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
                                        head_dia=bolt_8_32['head_dia']+obj.OuterThickness.Value, head_dz=bolt_8_32['head_dz'],
                                        x=0, y=0, z=-dz, dir=(0,0,1)))

        obj.Shape = part

        part = _bounding_box(obj, self.drill_tolerance, 6)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=i*obj.MountHoleDistance.Value/2, y=0, z=0))

        for i in [1, 2, 3]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x = - 56 - i * 10, y =0, z=14.7))
        part.Placement = obj.Placement
        obj.DrillPart = part

class surface_adapter_wide:
    '''
    Surface adapter for post-mounted parts

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mount_hole_dy (float) : The spacing between the two mount holes of the adapter
        adapter_height (float) : The height of the surface adapter
        outer_thickness (float) : The thickness of the walls around the bolt holes
        center_thread_depth (float) : The depth of the threaded portion in the center hole
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_hole_dy=65, adapter_height=8, outer_thickness=2, center_thread_depth=3):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
        obj.addProperty('App::PropertyLength', 'AdapterHeight').AdapterHeight = adapter_height
        obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
        obj.addProperty('App::PropertyLength', 'CenterThreadDepth').CenterThreadDepth = center_thread_depth
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)
        self.drill_tolerance = 1

    def execute(self, obj):
        dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2 + 10
        dy = dx+obj.MountHoleDistance.Value
        dz = obj.AdapterHeight.Value

        part = _custom_box(dx=dx, dy=dy, dz=dz,
                           x=0, y=0, z=0, dir=(0, 0, -1),
                           fillet=5)
        
        for i in [-1, 1]:
            part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
                                             head_dia=bolt_8_32['head_dia']+obj.OuterThickness.Value, head_dz=bolt_8_32['head_dz'],
                                             x=0, y=i*obj.MountHoleDistance.Value/2, z=0))
    
        part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
                                        head_dia=bolt_8_32['head_dia']+obj.OuterThickness.Value, head_dz=bolt_8_32['head_dz'],
                                        x=0, y=0, z=-dz, dir=(0,0,1)))

        obj.Shape = part

        part = _bounding_box(obj, self.drill_tolerance, 6)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=0, y=i*obj.MountHoleDistance.Value/2, z=0))
        part.Placement = obj.Placement
        obj.DrillPart = part


class surface_adapter_fiberport:
    '''
    Surface adapter for post-mounted parts

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mount_hole_dy (float) : The spacing between the two mount holes of the adapter
        adapter_height (float) : The height of the surface adapter
        outer_thickness (float) : The thickness of the walls around the bolt holes
        center_thread_depth (float) : The depth of the threaded portion in the center hole
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_hole_dy=36, adapter_height=8, outer_thickness=2, center_thread_depth=3):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
        obj.addProperty('App::PropertyLength', 'AdapterHeight').AdapterHeight = adapter_height
        obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
        obj.addProperty('App::PropertyLength', 'CenterThreadDepth').CenterThreadDepth = center_thread_depth
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)
        self.drill_tolerance = 1

    def execute(self, obj):
        dx = bolt_8_32['head_dia'] + obj.OuterThickness.Value * 2
        dy = dx + obj.MountHoleDistance.Value
        dz = obj.AdapterHeight.Value

        part = _custom_box(dx=dx, dy=dy, dz=dz,
                           x=0, y=0, z=0, dir=(0, 0, -1),
                           fillet=5)
        
        for i in [-1, 1]:
            part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
                                             head_dia=bolt_8_32['head_dia']+obj.OuterThickness.Value, head_dz=bolt_8_32['head_dz'],
                                             x=0, y=i*obj.MountHoleDistance.Value/2, z=0))
    
        part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
                                        head_dia=bolt_8_32['head_dia']+obj.OuterThickness.Value, head_dz=bolt_8_32['head_dz'],
                                        x=0, y=0, z=-dz, dir=(0,0,1)))

        obj.Shape = part

        part = _bounding_box(obj, self.drill_tolerance, 6)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=0, y=i*obj.MountHoleDistance.Value/2, z=0))

        for i in [1, 2, 3]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x = - 16 - i * 10, y =0, z=14.7))

        part.Placement = obj.Placement
        obj.DrillPart = part

class surface_adapter_fiberport_lip:
    '''
    Surface adapter with a lip for the fiber port 

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mount_hole_dy (float) : The spacing between the two mount holes of the adapter
        adapter_height (float) : The height of the surface adapter
        outer_thickness (float) : The thickness of the walls around the bolt holes
        center_thread_depth (float) : The depth of the threaded portion in the center hole
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, hole_config = 'Y_shape', mount_hole_dy=36, adapter_height=8, outer_thickness=2, center_thread_depth=3, rear_pair_43=True, rear_pair_63=True, rear_pair_73=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyString', 'HoleConfig').HoleConfig = hole_config
        obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
        obj.addProperty('App::PropertyLength', 'AdapterHeight').AdapterHeight = adapter_height
        obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
        obj.addProperty('App::PropertyLength', 'CenterThreadDepth').CenterThreadDepth = center_thread_depth
        obj.addProperty('App::PropertyBool', 'RearPair43').RearPair43 = rear_pair_43
        obj.addProperty('App::PropertyBool', 'RearPair63').RearPair63 = rear_pair_63
        obj.addProperty('App::PropertyBool', 'RearPair73').RearPair73 = rear_pair_73
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)
        self.drill_tolerance = 1

    def execute(self, obj):
        mesh = _import_stl("Surface_Adapter_fiberport_lip.stl", (0, 0, 0), ([0, 0, 0]))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, self.drill_tolerance, 0.125*layout.inch)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=0, y=i*obj.MountHoleDistance.Value/2, z=0))
            
        if obj.HoleConfig == "Y_shape":
            for i in [1, 2]:
                part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                                x = 33 + i * 10, y=0, z=14.7))

            for i in [-1, 1]:
                part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                                x=30, y=i*9.164, z=14.7))
        elif obj.HoleConfig == "two_hole":
            new_hole_coordinates = [
                (-43, -10-10),  # Hole 1: x=-30, y=10
                (-43, -34-10),   # Hole 2: x=-40, y=10
                (-55, 16),
                (-79, 16)
            ]

            # Loop through the new coordinates and create a hole at each point.
            # We keep the z=14.7 offset, as that was likely important for the original design's height.
            for x_coord, y_coord in new_hole_coordinates:
                part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                                x=x_coord, y=y_coord, z=14.7))
        elif obj.HoleConfig == "two_hole_inverted":
            new_hole_coordinates = [
                (-43, -1*(-10-6)),  # Hole 1: x=-30, y=10
                (-43, -1*(-34-6)),   # Hole 2: x=-40, y=10
                (-186, -7),
                (-210, -7)
            ]

            # Loop through the new coordinates and create a hole at each point.
            # We keep the z=14.7 offset, as that was likely important for the original design's height.
            for x_coord, y_coord in new_hole_coordinates:
                part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                                x=x_coord, y=y_coord, z=14.7))
        elif obj.HoleConfig == "two_hole_extended":
            new_hole_coordinates = [
                (135, -20),  # Hole 1: x=-30, y=10
                (145, -20)   # Hole 2: x=-40, y=10
            ]
        

            # Loop through the new coordinates and create a hole at each point.
            # We keep the z=14.7 offset, as that was likely important for the original design's height.
            for x_coord, y_coord in new_hole_coordinates:
                part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                                x=x_coord, y=y_coord, z=14.7))
        elif obj.HoleConfig == "aziza_fiber_adapter":
            new_hole_coordinates = [
                (69+7, -18),  # Hole 1: x=-30, y=10
                (69+7, 18),   # Hole 2: x=-40, y=10
                (69+7, -12),
                (69+7, 12)
            ] 
        

            # Loop through the new coordinates and create a hole at each point.
            # We keep the z=14.7 offset, as that was likely important for the original design's height.
            for x_coord, y_coord in new_hole_coordinates:
                part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                                x=x_coord, y=y_coord, z=14.7))
        elif obj.HoleConfig == "aziza_fiber_adapter_extended":
            new_hole_coordinates = [
                (184, -18),  # Hole 1: x=-30, y=10
                (184, 18),   # Hole 2: x=-40, y=10
                (184, -12),
                (184, 12)
            ]
        

            # Loop through the new coordinates and create a hole at each point.
            # We keep the z=14.7 offset, as that was likely important for the original design's height.
            for x_coord, y_coord in new_hole_coordinates:
                part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                                x=x_coord, y=y_coord, z=14.7))
                
        else:
            for i in [1, 2]:
                part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                                x = 33 + i * 10, y=0, z=14.7))

            for i in [-1, 1]:
                part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                                x=30, y=i*9.164, z=14.7))
        
        if obj.RearPair43:
            for i in [-1, 1]:
                part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                          x=43, y=i*9.164, z=14.7))

        if obj.RearPair63:
            for i in [-1, 1]:
                part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                          x=63, y=i*9.164, z=14.7))

        if obj.RearPair73:
            for i in [-1, 1]:
                part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                          x=73, y=i*9.164, z=14.7))

        part.Placement = obj.Placement
        obj.DrillPart = part



#this is a square hollow
class square_hollow:
    """
    gemerate a square hollow on the baseplate
    """
    type = 'Mesh::FeaturePython'
    # type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True):#, thumbscrews=False):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        # obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        # self.part_numbers = ['POLARIS-K05S2']

        # if thumbscrews:
        #     _add_linked_object(obj, "Upper Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-15.03, 8.89, 8.89))
        #     _add_linked_object(obj, "Lower Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-15.03, -8.89, -8.89))

    def execute(self, obj):
        # mesh = _import_stl("POLARIS-K05S2-Step.stl", (90, -0, -90), (-4.514, 0.254-20, -0.254))
        mesh = _import_stl("small_box__.stl", (90, -0, -90), (-4.514, 0.254-20, -0.254))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh
        # part = _custom_box(dx=0.1, dy=0.1, dz=0.1,
                        #    x=0, y=0, z=0, dir=(0, 0, 0))
        # obj.Shape = part
        # part = _custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
        #                         x=-8.017, y=0, z=-layout.inch/2)
        # for i in [-1, 1]:
        part = _bounding_box(obj, 20,fillet = 0,x_tol=True, y_tol=True, z_tol=True,min_offset=(0, 0, -40), max_offset=(70, 1000, 0), plate_off=-48)
        part.Placement = obj.Placement
        obj.DrillPart = part

class isomet_1205c_on_km100pm:
    '''
    Isomet 1205C AOM on KM100PM Mount

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        diffraction_angle (float) : The diffraction angle (in degrees) of the AOM
        forward_direction (integer) : The direction of diffraction on forward pass (1=right, -1=left)
        backward_direction (integer) : The direction of diffraction on backward pass (1=right, -1=left)

    Sub-Parts:
        prism_mount_km100pm (mount_args)
        mount_for_km100pm (adapter_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, diffraction_angle=degrees(0.01), forward_direction=1, backward_direction=1, mount_args=dict(), adapter_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyAngle', 'DiffractionAngle').DiffractionAngle = diffraction_angle
        obj.addProperty('App::PropertyInteger', 'ForwardDirection').ForwardDirection = forward_direction
        obj.addProperty('App::PropertyInteger', 'BackwardDirection').BackwardDirection = backward_direction

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['ISOMET_1205C']
        self.diffraction_angle = diffraction_angle
        self.diffraction_dir = (forward_direction, backward_direction)
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

        # TODO fix these parts to remove arbitrary translations
        _add_linked_object(obj, "Mount KM100PM", prism_mount_km100pm,
                           pos_offset=(-15.25, -20.15, -17.50), **mount_args)
        _add_linked_object(obj, "Adapter Bracket", mount_for_km100pm,
                           pos_offset=(-15.25, -20.15, -17.50), **adapter_args)

    def execute(self, obj):
        mesh = _import_stl("isomet_1205c.stl", (0, 0, 90), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

class AOMO_3100_125:
    '''
    G&H AOMO 3100-125 AOM on KM100PM Mount

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        diffraction_angle (float) : The diffraction angle (in degrees) of the AOM
        forward_direction (integer) : The direction of diffraction on forward pass (1=right, -1=left)
        backward_direction (integer) : The direction of diffraction on backward pass (1=right, -1=left)

    Sub-Parts:
        prism_mount_km100pm (mount_args)
        mount_for_km100pm (adapter_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, diffraction_angle=degrees(0.01), forward_direction=1, backward_direction=1, mount_args=dict(), surface_adapter_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')
        obj.addProperty('App::PropertyAngle', 'DiffractionAngle').DiffractionAngle = diffraction_angle
        obj.addProperty('App::PropertyInteger', 'ForwardDirection').ForwardDirection = forward_direction
        obj.addProperty('App::PropertyInteger', 'BackwardDirection').BackwardDirection = backward_direction

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['G&H AOMO 3100-125']
        self.diffraction_angle = diffraction_angle
        self.diffraction_dir = (forward_direction, backward_direction)
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5
        
        _add_linked_object(obj, "Mount KM100PM", prism_mount_km100pm_bridged,
                           pos_offset=(-30.3, -16.4, -24.5), **mount_args)
        _add_linked_object(obj, "AOM Adapter", aom_adapter,
                           pos_offset=(-17, -7.65, -17.1), rot_offset=(0, 0, -90))
        _add_linked_object(obj, "Surface Adapter", surface_adapter_aom,
                           pos_offset=(-44.4, -3.65, -30), **surface_adapter_args)

    def execute(self, obj):
        mesh = _import_stl("aomo_3100-125.stl", (0, 0, -90), (0, -7.65, -7.1))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 0.125*layout.inch)
        for i in [1, 2]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=2.5, y=-40-i*10, z=0))

        part.Placement = obj.Placement
        obj.DrillPart = part

class circular_mirror_union_optic:
    '''
    Circular Mirror

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        thickness (float) : The thickness of the mirror
        diameter (float) : The width of the mirror
        part_number (string) : The part number of the mirror being used
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, thickness=3, diameter=inch/2, part_number='', mount_type=None, mount_args=dict(),mount_height=0, adapter_type=None, adapter_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'Thickness').Thickness = thickness
        obj.addProperty('App::PropertyLength', 'Diameter').Diameter = diameter

        if mount_type != None:
            _add_linked_object(obj, "Mount", mount_type, pos_offset=(-thickness, 0, 0), **mount_args)  

        obj.ViewObject.ShapeColor = glass_color
        self.part_numbers = [part_number]
        self.reflection_angle = 0
        self.max_angle = 90
        self.max_width = diameter

    def execute(self, obj):
        part = _custom_cylinder(dia=obj.Diameter.Value, dz=obj.Thickness.Value,
                           x=0, y=0, z=0, dir=(-1, 0, 0))
        obj.Shape = part

class aom_adapter:
    '''
    Adapter for AOMs on KM100PM Mount
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['AOM Adapter']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

    def execute(self, obj):
        mesh = _import_stl("aom_adapter.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 0.125*layout.inch)
        part.Placement = obj.Placement
        obj.DrillPart = part



# f= 100 asphere, 2 inch lens

class asphere_100:
    '''
    Adapter for AOMs on KM100PM Mount
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, mount_type=None, mount_args=None):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        if mount_type != None:
            _add_linked_object(obj, "Mount", mount_type, pos_offset=(-0, 0, 0), **mount_args)

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['AL50100']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

    def execute(self, obj):
        mesh = _import_stl("AL50100M-B-Step.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 0.125*layout.inch)
        part.Placement = obj.Placement
        obj.DrillPart = part


# MOUNTED f=100, 50mm ASPHERE:
class Mounted_asphere_100:
    '''
    Adapter for AOMs on KM100PM Mount
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['AL50100Mounted']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

    def execute(self, obj):
        mesh = _import_stl("rotated_mounted_f100.stl", (0, 0, 0), (0, 0, 0))
        # original rotation -90, 180, -90
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2.5, 0.25*layout.inch)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=-5.67+0.46, y=i*20.482 , z=0))

        part.Placement = obj.Placement
        obj.DrillPart = part

# f = 60 asphere, 3 inch lens

class asphere_60:
    '''
    Adapter for AOMs on KM100PM Mount
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['AL7560']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

    def execute(self, obj):
        mesh = _import_stl("AL7560-B-Step.stl", (-90, 90, 90), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 0.125*layout.inch)
        part.Placement = obj.Placement
        obj.DrillPart = part

# MOUNTED 60 ASPHERE:

class Mounted_asphere_60:
    '''
    Adapter for AOMs on KM100PM Mount
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['AL7560Mounted']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

    def execute(self, obj):
        mesh = _import_stl("rotated_stage_f60.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2.5, 0.25*layout.inch)

        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_M6['tap_dia'], dz=drill_depth,
                                              x=-31.4+(i*12.5), y=0 , z=0))

        part.Placement = obj.Placement
        obj.DrillPart = part


# ROTATED f150 ON TRANSLATION STAGE:

class Mounted_stage_f150:
    '''
    Adapter for AOMs on KM100PM Mount
    '''
    type = 'Mesh::FeaturePython'

    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['AL75150Mounted']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

    def execute(self, obj):
        mesh = _import_stl("rotated_stage_f150.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2.5, 0.25 * layout.inch)

        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_M6['tap_dia'], dz=drill_depth,
                                              x=-10.3 + (i * 12.5), y=0, z=0))

        part.Placement = obj.Placement
        obj.DrillPart = part


# rotated mounted stage f=200

class Mounted_stage_f200:
    '''
    Adapter for AOMs on KM100PM Mount
    '''
    type = 'Mesh::FeaturePython'

    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['AL75150Mounted']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

    def execute(self, obj):
        mesh = _import_stl("rotated_stage_f200.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2.5, 0.25 * layout.inch)

        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_M6['tap_dia'], dz=drill_depth*10,
                                              x=-12.3+3.23 + (i * 12.5), y=0, z=0))

        part.Placement = obj.Placement
        obj.DrillPart = part

class Mounted_asphere_150:
    '''
    Adapter for AOMs on KM100PM Mount
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['AL75150Mounted']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

    def execute(self, obj):
        mesh = _import_stl("rotated_f150_mounted.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 1.5, 0.25*layout.inch)

        part = _bounding_box(obj, 1.0, 0.25*layout.inch)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=-10.4, y=i*(69.941/2) , z=0))

        part.Placement = obj.Placement
        obj.DrillPart = part

# NOW MOUNTED BUT NO STAGE f150 75mm lens:

class Mounted_nostage_150:
    '''
    Adapter for AOMs on KM100PM Mount
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['AL50100Mounted']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

    def execute(self, obj):
        mesh = _import_stl("Mouted_f150_nostage.stl", (-90, 180, -90), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 1.0, 0.25*layout.inch)
        part.Placement = obj.Placement
        obj.DrillPart = part

# MOUNTED 100 NO STAGE:


class Mounted_nostage_100:
    '''
    Adapter for AOMs on KM100PM Mount
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['AL50100Mounted']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

    def execute(self, obj):
        mesh = _import_stl("Mouted_f100_nostage.stl", (-90, 180, -90), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 1.5, 0.25*layout.inch)
        part.Placement = obj.Placement
        obj.DrillPart = part


# MOUNTED f=200 asphere

class Mounted_nostage_200:
    '''
    Adapter for AOMs on KM100PM Mount
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['AL50100Mounted']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

    def execute(self, obj):
        mesh = _import_stl("rotated_al100f200_asphere.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 1.0, 0.25*layout.inch)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=-11.91+0.62, y=i*50.0 , z=0))

        part.Placement = obj.Placement
        obj.DrillPart = part


# f = 200 asphere, 4 inch lens
class asphere_200:
    '''
    Adapter for AOMs on KM100PM Mount
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['AL7560']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

    def execute(self, obj):
        mesh = _import_stl("AL100200-B-Step.stl", (-90, 90, 90), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 0.125*layout.inch)
        part.Placement = obj.Placement
        obj.DrillPart = part


# f = 150 asphere, 3 inch lens

class asphere_150:
    '''
    Adapter for AOMs on KM100PM Mount
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['AL7560']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

    def execute(self, obj):
        mesh = _import_stl("AL75150-B-Step.stl", (-90, 90, 90), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 0.125*layout.inch)


        part.Placement = obj.Placement
        obj.DrillPart = part

class shutter_sr475:
    '''
    shutter for SRS SR475
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['SRS SR475 Shutter']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

        # _add_linked_object(obj, "Adapter", shutter_adapter, pos_offset=(2.7, 23.83, -25.4), rot_offset=(0, 0, 90))
        _add_linked_object(obj, "Adapter", shutter_adapter, pos_offset=(2.7, 6.35, -4.83), rot_offset=(0, 0, 90))


    def execute(self, obj):
        # mesh = _import_stl("SR475.stl", (180, 0, 90), (0, 23.83, -6.35))
        mesh = _import_stl("SR475.stl", (180, -90, 90), (0, 6.35, 23.83))

        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

class mirror_mount_FMP05:
    '''
    Mirror mount, model FMP05

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['Thorlabs-FMP05']
        _add_linked_object(obj, "FMP05 Adapter", adapter_FMP05, pos_offset=(-6.9, 0, -24.25), rot_offset=(0, 0, -90))

    def execute(self, obj):
        mesh = _import_stl("FMP05.stl", (90, 0, 90), (3.1, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

# 2 inch PBS already mounted:

class PBS_2in_mounted:
    '''
    Adapter for AOMs on KM100PM Mount
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['Mounted PBS 2 inch']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

    def execute(self, obj):
        mesh = _import_stl("pbs_2in_mounted.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 1.5, 0.25*layout.inch)

        part = _bounding_box(obj, 1.0, 0.25*layout.inch)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=-12.4, y=i*(39) , z=0))

        part.Placement = obj.Placement
        obj.DrillPart = part


# 2 inch waveplate:

class waveplate_2in:
    '''
    Adapter for AOMs on KM100PM Mount
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['Mounted 2 inch waveplate']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

    def execute(self, obj):
        mesh = _import_stl("rotated_waveplate_indexrotstage.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 1.5, 0.25*layout.inch)

        part = _bounding_box(obj, 1.0, 0.25*layout.inch)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=0, y=i * 50.0, z=0))

        part.Placement = obj.Placement
        obj.DrillPart = part



class adapter_FMP05:
    '''
    Adapter for mirror mount, model FMP05

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')
        self.drill_tolerance = 1
        obj.ViewObject.ShapeColor = adapter_color

    def execute(self, obj):
        mesh = _import_stl("FMP05_Adapter.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, self.drill_tolerance, 0.125*layout.inch)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=i*5, y=-3.5, z=0))

        part.Placement = obj.Placement
        obj.DrillPart = part


class shutter_adapter:
    '''
    Adapter for SRS SR475 Shutter
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['Shutter SR475 Adapter']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

    def execute(self, obj):
        mesh = _import_stl("shutter_adapter.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 1, 0.125*layout.inch)
        for i in [-1, 1]:
            for j in [-1, 1]:
                part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                                  x=j * 22.86, y=i * 17, z=0))
        part.Placement = obj.Placement
        obj.DrillPart = part


class isolator_670:
    '''
    Isolator Optimized for 670nm, Model IOT-5-670-VLP

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        surface_adapter (adapter_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, adapter_args=dict()):
        adapter_args.setdefault("mount_hole_dy", 45)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['IOT-5-670-VLP']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

        _add_linked_object(obj, "Surface Adapter", surface_adapter_isolator_lip,
                           pos_offset=(0, 0, -22.1), **adapter_args)

    def execute(self, obj):
        mesh = _import_stl("IOT-5-670-VLP-Step.stl", (90, 0, -90), (-19.05, -0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _custom_box(dx=80, dy=25, dz=5,
                           x=0, y= 0, z=-layout.inch/2,
                           fillet=0.125*layout.inch, dir=(0, 0, -1))
        part.Placement = obj.Placement
        obj.DrillPart = part

class isolator_850:
    '''
    Isolator Optimized for 850nm, Model IOT-5-850-VLP

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        surface_adapter (adapter_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, adapter_args=dict()):
        adapter_args.setdefault("mount_hole_dy", 45)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['IOT-5-670-VLP']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

        _add_linked_object(obj, "Surface Adapter", surface_adapter_isolator_lip,
                           pos_offset=(0, 0, -22.1), **adapter_args)

    def execute(self, obj):
        mesh = _import_stl("IOT-5-850-VLP-Step.stl", (90, 0, -90), (-19.05, -0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _custom_box(dx=80, dy=25, dz=5,
                           x=0, y= 0, z=-layout.inch/2,
                           fillet=0.125*layout.inch, dir=(0, 0, -1))
        part.Placement = obj.Placement
        obj.DrillPart = part

class isolator_780:
    '''
    Isolator Optimized for 780nm, Model IO-3D-780-VLP

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        surface_adapter (adapter_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, adapter_args=dict()):
        adapter_args.setdefault("mount_hole_dy", 45)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['IO-3D-780-VLP']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

        _add_linked_object(obj, "Surface Adapter", surface_adapter_isolator_lip,
                           pos_offset=(0, 0, -17.15), **adapter_args)

    def execute(self, obj):
        mesh = _import_stl("IO-3D-780-VLP-Step.stl", (90, 0, -90), (-15.66, -0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _custom_box(dx=40, dy=25, dz=5,
                           x=0, y= 0, z=-layout.inch/2,
                           fillet=0.125*layout.inch, dir=(0, 0, -1))
        part.Placement = obj.Placement
        obj.DrillPart = part

class isolator_405:
    '''
    Isolator Optimized for 405nm, Model IO-3D-405-PBS

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        surface_adapter
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, adapter_args=dict()):
        adapter_args.setdefault("mount_hole_dy", 36)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['IO-3D-405-PBS']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

        _add_linked_object(obj, "Surface Adapter", surface_adapter,
                           pos_offset=(0, 0, -17.15), **adapter_args)

    def execute(self, obj):
        mesh = _import_stl("IO-3D-405-PBS-Step.stl", (90, 0, -90), (-9.461, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _custom_box(dx=25, dy=15, dz=drill_depth,
                           x=0, y=0, z=-layout.inch/2,
                           fillet=0.125*layout.inch, dir=(0, 0, 1))
        part.Placement = obj.Placement
        obj.DrillPart = part

class rb_cell_holder_old:
    '''
    Rubidium Cell Holder

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color

    def execute(self, obj):
        mesh = _import_stl("rb_cell_holder_middle.stl", (0, 0, 0), ([0, 5, 0]))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 6, 3)
        dx = 90
        for x, y in [(1,1), (-1,1), (1,-1), (-1,-1)]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                         x=x*dx/2, y=y*15.7, z=-layout.inch/2))
        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                     x=45, y=-15.7, z=-layout.inch/2))
        for x in [1,-1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                         x=x*dx/2, y=25.7, z=-layout.inch/2))
        part.Placement = obj.Placement
        obj.DrillPart = part
class photodiode_fds010:
    '''
    Photodiode, model FDS010
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = True
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['FDS010']
        self.max_angle = 0
        self.max_width = 1

    def execute(self, obj):
        mesh = _import_stl("FDS010-Step.stl", (-90, -90, 0), (-0.7, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _custom_cylinder(dia=8.5, dz=4,
                                x=0, y=0, z=0, dir=(1, 0, 0))
        part.Placement = obj.Placement
        obj.DrillPart = part
class rb_cell_cube:
    '''
    Rubidium Cell Holder

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, cube_size=10, mount_type=None, mount_args=dict(), drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyLength', 'CubeSize').CubeSize = cube_size
        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = glass_color
        obj.ViewObject.Transparency=50
        self.transmission = True
        self.max_angle = 10
        self.max_width = 1

    def execute(self, obj):
        part = _custom_box(dx=obj.CubeSize.Value, dy=obj.CubeSize.Value, dz=obj.CubeSize.Value,
                           x=0, y=0, z=0, dir=(0, 0, 0))
        obj.Shape = part
        
        part = _bounding_box(obj, 0, 0)
        for x, y in [(-1,-1), (-1,1), (1,-1), (1,1)]:
            part = part.fuse(_custom_cylinder(dia=5, dz=drill_depth,
                                            x=x*obj.CubeSize.Value/2, y=y*obj.CubeSize.Value/2, z=-obj.CubeSize.Value/2, dir=(0, 0, 1)))
        part.Placement = obj.Placement
        obj.DrillPart = part
# this is cylindrical rb_cell version, more used in demo
class rb_cell_cylindrical:
    '''
    Rubidium Cell Holder

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, mount_type=None, mount_args=dict(), drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = glass_color
        self.transmission = True
        self.max_angle = 10
        self.max_width = 1

        if mount_type != None:
            _add_linked_object(obj, "Mount", mount_type, **mount_args)

    def execute(self, obj):
        cell_dx = 80
        cell_dia = 22
        end_dia = 26
        part = _custom_cylinder(dia=cell_dia, dz=cell_dx,
                                x=-cell_dx/2, y=0, z=0,
                                dir=(1, 0, 0))
        part = part.fuse(_custom_cylinder(dia=end_dia, dz=8,
                                          x=-cell_dx/2, y=0, z=0,
                                          dir=(1, 0, 0)))
        part = part.fuse(_custom_cylinder(dia=end_dia, dz=8,
                                          x=cell_dx/2, y=0, z=0,
                                          dir=(-1, 0, 0)))
        
        obj.Shape = part

        temp = _bounding_box(obj, 0, 0, min_offset=(0, 0, cell_dia/2))
        part = part.fuse(temp)

        part.Placement = obj.Placement
        obj.DrillPart = part

class rotation_stage_rsp05_vertical:
    '''
    Rotation stage, model RSP05

    Args:
        invert (bool) : Whether the mount should be offset 90 degrees from the component
        mount_hole_dy (float) : The spacing between the two mount holes of it's adapter
        wave_plate_part_num (string) : The Thorlabs part number of the wave plate being used

    Sub-Parts:
        surface_adapter (adapter_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, thumbscrews=False, bolt_length=15):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
        obj.addProperty('App::PropertyLength', 'BoltLength').BoltLength = bolt_length
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['RSP05']

    def execute(self, obj):
        mesh = _import_stl("RSP05-Step.stl", (90, -0, 90), (2.084, -1.148, 0.498))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 0, 0, min_offset=(0, 0, 0))
        part = part.fuse(_bounding_box(obj, 0, 0, max_offset=(0, 0, 0)))
        part = _fillet_all(part, 0)
        part = part.fuse(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=inch,head_dia=bolt_8_32['head_dia'], head_dz=0.92*inch-obj.BoltLength.Value,x=1.4, y=-1.1, z=-inch*3/2, dir=(0,0,1)))
        part.Placement = obj.Placement
        obj.DrillPart = part

# this is rb_cell with mount
class rb_cell:
    '''
    Rubidium Cell Holder

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill = True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.transmission = True
        self.max_angle = 10
        self.max_width = 1

    def execute(self, obj):
        mesh = _import_stl("rb_cell_holder_middle.stl", (0, 0, 0), ([0, 5, 0]))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 0.125*layout.inch)
        dx = 90
        for x, y in [(1,1), (-1,1), (1,-1), (-1,-1)]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                         x=x*dx/2, y=y*15.7, z=-layout.inch/2))
        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                     x=45, y=-15.7, z=-layout.inch/2))
        for x in [1,-1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                         x=x*dx/2, y=25.7, z=-layout.inch/2))
        part.Placement = obj.Placement
        obj.DrillPart = part


class rb_cell_new:
    #Rb cell with changed wall thickness and longer tube
    '''
    Rubidium Cell Holder

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.transmission = True
        self.max_angle = 10
        self.max_width = 1

    def execute(self, obj):
        cell_dx = 88        #longer tibe, was 88
        cell_dia = 25
        end_dia = 28
        wall_thickness = 30    # Wall thickness was 15 mm before
        base_dy=5.75*inch
        dx = cell_dx+wall_thickness*2
        dy = cell_dia+wall_thickness*2
        dz = cell_dia+15*2
        base = _custom_box(dx=dx, dy=dy, dz=dz/2,
                           x=0, y=0, z=dz/2, dir=(0, 0, -1))
        base = base.fuse(_custom_box(dx=dx, dy=base_dy, dz=3/4*inch,
                           x=0, y=0, z=-(1/2*inch-dz/2), dir=(0, 0, -1)))
        cover = _custom_box(dx=dx, dy=dy, dz=dz/2,
                           x=0, y=0, z=dz/2, dir=(0, 0, 1))
        cover = cover.cut(_custom_box(dx=20, dy=dy/2, dz=5,
                           x=0, y=0, z=dz/2+2.5, dir=(0, -1, 0)))
        cell = _custom_cylinder(dia=cell_dia, dz=cell_dx,
                                x=-cell_dx/2, y=0, z=dz/2,
                                dir=(1, 0, 0))
        cell = cell.fuse(_custom_cylinder(dia=end_dia, dz=10,               # Longer tube, it was 10 mm before
                                          x=-cell_dx/2, y=0, z=dz/2,
                                          dir=(1, 0, 0)))
        cell = cell.fuse(_custom_cylinder(dia=end_dia, dz=10,               # longer tube, it was 10 mm before.
                                          x=cell_dx/2, y=0, z=dz/2,
                                          dir=(-1, 0, 0)))
        cell = cell.fuse( _custom_cylinder(dia=5, dz=dx,
                                           x=-dx/2, y=0, z=dz/2,
                                           dir=(1, 0, 0)))
        cell = cell.fuse(_custom_cylinder(dia=15, dz=cell_dia/2+10,
                                         x=0, y=0, z=dz/2,
                                         dir=(0, 1, 0)))
        
        base = base.cut(cell)
        cover = cover.cut(cell)

        for x, y in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            hole = _custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz/2,
                                    x=x*(dx/2-wall_thickness/2), y=y*(dy/2-wall_thickness/2), z=dz,
                                    head_dia=bolt_8_32['head_dia'], head_dz=dz/4)
            hole = hole.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=3/2*inch,
                                    x=x*(dx/2-wall_thickness/2), y=y*(dy/2-wall_thickness/2), z=dz/2))
            base = base.cut(hole)
            cover = cover.cut(hole)
            base = base.cut(_custom_cylinder(dia=bolt_14_20['clear_dia'], dz=inch,
                                             x=x*1.5*inch, y=y*2*inch, z=-(1/2*inch-dz/2),
                                             head_dia=bolt_14_20['washer_dia'], head_dz=10))

        base.translate(App.Vector(0, 0, -dz/2))
        cover.translate(App.Vector(0, 0, -dz/2))
   
        obj.Shape = Part.Compound([base, cover])

class telescope_track:
    '''
    a long track enables us to walk the distance of the lens of the telescope
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
    def execute(self, obj):
        base_dx = 10 * layout.inch
        base_dy = 3 * layout.inch
        base_dz = 1 * layout.inch
        baseplate = _custom_box(dx=base_dx, dy=base_dy, dz=base_dz,
                           x=0, y=0, z=- layout.inch, dir=(1, 0, 0))
        baseplate = baseplate.fuse(_custom_box(dx=base_dx, dy=5, dz=20,x = 0, y = 9.125 + 2.5, z = -4, dir=(1,0,0)))
        baseplate = baseplate.fuse(_custom_box(dx=base_dx, dy=5, dz=20,x = 0, y = -9.125 - 2.5, z = -4, dir=(1,0,0)))
        part = _custom_cylinder(dia=bolt_14_20['clear_dia'], dz=drill_depth,
                                head_dia=bolt_14_20["washer_dia"], head_dz=10,
                                x=9.5 * layout.inch, y=1*layout.inch, z=-layout.inch / 2)
        baseplate = baseplate.cut(part)
        part = _custom_cylinder(dia=bolt_14_20['clear_dia'], dz=drill_depth,
                                head_dia=bolt_14_20["washer_dia"], head_dz=10,
                                x=0.5 * layout.inch, y=1*layout.inch, z=-layout.inch / 2)
        baseplate = baseplate.cut(part)
        part = _custom_cylinder(dia=bolt_14_20['clear_dia'], dz=drill_depth,
                                head_dia=bolt_14_20["washer_dia"], head_dz=10,
                                x=9.5 * layout.inch, y=-1 * layout.inch, z=-layout.inch / 2)
        baseplate = baseplate.cut(part)
        part = _custom_cylinder(dia=bolt_14_20['clear_dia'], dz=drill_depth,
                                head_dia=bolt_14_20["washer_dia"], head_dz=10,
                                x=0.5 * layout.inch, y=-1 * layout.inch, z=-layout.inch / 2)
        baseplate = baseplate.cut(part)
        baseplate.Placement = obj.Placement
        # obj.DrillPart = baseplate
        obj.Shape = baseplate


class photodetector_pda10a2:
    '''
    Photodetector, model pda10a2

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        surface_adapter (adapter_args)
    
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, adapter_args=dict()):
        adapter_args.setdefault("mount_hole_dy", 60)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['PDA10A2']
        self.max_angle = 80
        self.max_width = 5

        _add_linked_object(obj, "Surface Adapter", surface_adapter, pos_offset=(-10.54, 0, -25), **adapter_args)
        _add_linked_object(obj, "Lens Tube", lens_tube_SM1L03, pos_offset=(-0.124, 0, -0))

    def execute(self, obj):
        mesh = _import_stl("PDA10A2-Step.stl", (90, 0, -90), (-19.87, -0, -0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 6, 4)
        part.Placement = obj.Placement
        obj.DrillPart = part

class photodetector_pdb210a:
    '''
    Photodetector, model PDB210A

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        surface_adapter (adapter_args)
    
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, adapter_args=dict()):
        adapter_args.setdefault("mount_hole_dy", 60)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['PDB250A']
        self.max_angle = 80
        self.max_width = 5

        _add_linked_object(obj, "Surface Adapter for PD", surface_adapter_PD, pos_offset=(-17.75, 0, -16.6), **adapter_args)

    def execute(self, obj):
        mesh = _import_stl("PDB210A_M.stl", (-90, 0, -90), (-26.15, 0.1, 10.76))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 0.125*layout.inch)
        part.Placement = obj.Placement
        obj.DrillPart = part

class photodetector_pdb250a:
    '''
    Photodetector, model PDB250A

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        surface_adapter (adapter_args)
    
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, adapter_args=dict()):
        adapter_args.setdefault("mount_hole_dy", 60)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['PDB250A']
        self.max_angle = 80
        self.max_width = 5

        _add_linked_object(obj, "Surface Adapter for PD", surface_adapter_PD, pos_offset=(-17.75, 0, -16.6), **adapter_args)

    def execute(self, obj):
        mesh = _import_stl("PDB250A.stl", (-90, 0, -90), (21.099, 74.492, 20.816))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 0.125*layout.inch)
        part.Placement = obj.Placement
        obj.DrillPart = part


class lens_tube_SM1L03:
    '''
    SM1 Lens Tube, model SM1L03
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, bounding_box = True):
        self.bounding_box = bounding_box
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['SM1L03']
        self.max_angle = 0
        self.max_width = 1

    def execute(self, obj):
        mesh = _import_stl("SM1L03-Step.stl", (90, -0, 0), (8.382, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh
        # if self.bounding_box:
        #     part = _bounding_box(obj, 2, 3, z_tol=True, min_offset=(0, 4, 0), max_offset=(0, -4, 0))
        #     part.Placement = obj.Placement
        #     obj.DrillPart = part


class periscope:
    '''
    Custom periscope mount

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        lower_dz (float) : Distance from the bottom of the mount to the center of the lower mirror
        upper_dz (float) : Distance from the bottom of the mount to the center of the upper mirror
        mirror_type (obj class) : Object class of mirrors to be used
        table_mount (bool) : Whether the periscope is meant to be mounted directly to the optical table

    Sub-Parts:
        mirror_type x2 (mirror_args)
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, lower_dz=1.5*inch, upper_dz=3*inch, invert=True, mirror_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'LowerHeight').LowerHeight = lower_dz
        obj.addProperty('App::PropertyLength', 'UpperHeight').UpperHeight = upper_dz
        obj.addProperty('App::PropertyBool', 'Invert').Invert = invert

        obj.ViewObject.ShapeColor = adapter_color
        if obj.Baseplate == None:
            self.z_off = -layout.inch*3/2
        else:
            self.z_off = 0

        _add_linked_object(obj, "Lower Mirror", circular_mirror, rot_offset=((-1)**invert*90, -45, 0), pos_offset=(0, 0, obj.LowerHeight.Value+self.z_off), **mirror_args)
        _add_linked_object(obj, "Upper Mirror", circular_mirror, rot_offset=((-1)**invert*90, 135, 0), pos_offset=(0, 0, obj.UpperHeight.Value+self.z_off), **mirror_args)

    def execute(self, obj):
        width = 2*inch #Must be inch wide to keep periscope mirrors 1 inch from mount holes. 
        fillet = 15
        part = _custom_box(dx=70, dy=width, dz=obj.UpperHeight.Value+20,
                           x=0, y=0, z=0)
        for i in [-1, 1]:
            part = part.cut(_custom_box(dx=fillet*2+4, dy=width, dz=obj.UpperHeight.Value+20,
                                        x=i*(35+fillet), y=0, z=20, fillet=15,
                                        dir=(-i,0,1), fillet_dir=(0,1,0)))
            for y in [-inch/2, inch/2]:
                part = part.cut(_custom_cylinder(dia=bolt_14_20['clear_dia']+0.5, dz=inch+5,
                                            head_dia=bolt_14_20['head_dia']+0.5, head_dz=10,
                                            x=i*inch, y=y, z=25, dir=(0,0,-1)))
        part.translate(App.Vector(0, (-1)**obj.Invert*(width/2+inch/2), self.z_off))
        part = part.fuse(part)
        for i in obj.ChildObjects:
            part = _drill_part(part, obj, i)
        obj.Shape = part

class periscope_for_redstone:
    '''
    Custom periscope mount

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        lower_dz (float) : Distance from the bottom of the mount to the center of the lower mirror
        upper_dz (float) : Distance from the bottom of the mount to the center of the upper mirror
        mirror_type (obj class) : Object class of mirrors to be used
        table_mount (bool) : Whether the periscope is meant to be mounted directly to the optical table

    Sub-Parts:
        mirror_type x2 (mirror_args)
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, lower_dz=1.5*inch, upper_dz=3*inch, invert=True, mirror_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'LowerHeight').LowerHeight = lower_dz
        obj.addProperty('App::PropertyLength', 'UpperHeight').UpperHeight = upper_dz
        obj.addProperty('App::PropertyBool', 'Invert').Invert = invert

        # obj.ViewObject.ShapeColor = adapter_color
        if obj.Baseplate == None:
            self.z_off = -layout.inch*3/2
        else:
            self.z_off = 0

        # _add_linked_object(obj, "Lower Mirror", circular_mirror, rot_offset=((-1)**invert*90, -45, 0), pos_offset=(0, 0, obj.LowerHeight.Value+self.z_off), **mirror_args)
        # _add_linked_object(obj, "Upper Mirror", circular_mirror, rot_offset=((-1)**invert*90, 135, 0), pos_offset=(0, 0, obj.UpperHeight.Value+self.z_off), **mirror_args)
        # for i in range(6):
        #     for j in range(6):
        #         _add_linked_object(obj, 'Upper Mirror' + str(i) + str(j), circular_mirror, rot_offset=(135,90,45), pos_offset=(-110 +  i * 35, 100 -  j * 24, 20 +  j * 24 ), **mirror_args)

        #         _add_linked_object(obj, 'Lower Mirror' + str(i) + str(j), circular_mirror, rot_offset=(0, 0, 45), pos_offset=(- 110 + j * 35, 250 - j * 24, 20 +  i * 27), **mirror_args)
                

    def execute(self, obj):
        width = 0.8*inch 
        # mesh = _import_stl("baseplate_for_periscope_redstone.stl", rotate=(0, 0, 0), translate=(0, 0, 3))
        
        # mesh.Placement = obj.Mesh.Placement

        # obj.Mesh = mesh
        part = _custom_box(dx=210, dy=  1.1 * width, dz=obj.UpperHeight.Value + 78,
                           x=-20, y= - 20, z=0)
        
        for i in range(6): # lower
            part = part.fuse(_custom_box(dx=1.7 * width  , dy=150 + 18 - (i + 1 )*25 , dz=obj.UpperHeight.Value + 95   ,
                           x= 100 - (i + 1 )*35, y=200 + width + (i + 1 )*12.5, z=0))

        for i in range(6): # upper
            part = part.fuse(_custom_box(dx=210  , dy=1.2 * width, dz=obj.UpperHeight.Value + 78 - (i + 1 )*23 ,
                           x= -20, y= -20 +  1.1 * width * (i+1), z=-3))
        part.translate(App.Vector(0, (-1)**obj.Invert*(width/2+inch/2), 0))
        part.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 90)
        part = part.fuse(part)
        # # for i in obj.ChildObjects:
        # #     part = _drill_part(part, obj, i)
        obj.Shape = part
        part.Placement = obj.Placement
        obj.DrillPart = part

class thumbscrew_hkts_5_64:
    '''
    Thumbscrew for 5-64 hex adjusters, model HKTS 5-64

    Sub-Parts:
        slide_mount (adapter_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, adapter_args=dict()):
        adapter_args.setdefault("slot_length", 10)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['HKTS-5/64(P4)']

    def execute(self, obj):
        mesh = _import_stl("HKTS-5_64-Step.stl", (90, 0, 90), (-11.31, -0.945, 0.568))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2.75, 0.125*layout.inch, z_tol=True, min_offset=(-6, 0, 0), max_offset=(-6, 0, 0))
        part.Placement = obj.Placement
        obj.DrillPart = part

class fiber_adapter_sm05fca2:
    '''
    Fiber Adapter Plate, model SM05FCA2
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['SM05FCA2']
        self.max_angle = 0
        self.max_width = 1

    def execute(self, obj):
        mesh = _import_stl("SM05FCA2-Step.stl", (0, 90, 0), (-2.334, -3.643, -0.435))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh


class fiber_adapter_sm1fca2:
    '''
    Fiber Adapter Plate, model SM1FCA2
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['SM1FCA2']
        self.max_angle = 0
        self.max_width = 1

    def execute(self, obj):
        mesh = _import_stl("SM1FCA2-Step.stl", (-180, 90, 0), (-12.47, -0.312, 15.41))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh


class lens_adapter_s05tm09:
    '''
    SM05 to M9x0.5 Lens Cell Adapter, model S05TM09
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['S05TM09']

    def execute(self, obj):
        mesh =  _import_stl("S05TM09-Step.stl", (90, 0, -90), (6.973, 0, -0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh


class lens_adapter_s1tm09:
    '''
    SM1 to M9x0.5 Lens Cell Adapter, model S1TM09
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['S1TM09']

    def execute(self, obj):
        mesh =  _import_stl("S1TM09-Step.stl", (90, 0, 90), (-3.492, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh


class lens_tube_sm05l05:
    '''
    Lens Tube, model SM05L05
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['SM05L05']

    def execute(self, obj):
        mesh = _import_stl("SM05L05-Step.stl", (90, 0, -90), (0, 0, -0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh


class lens_tube_sm1l05:
    '''
    Lens Tube, model SM1L05
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['SM1L05']

    def execute(self, obj):
        mesh = _import_stl("SM1L05-Step.stl", (90, -0, 0), (13.46, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 3, z_tol=True)
        part.Placement = obj.Placement
        obj.DrillPart = part


class mounted_lens_c220tmda:
    '''
    Mounted Aspheric Lens, model C220TMD-A
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.ViewObject.ShapeColor = glass_color
        self.part_numbers = ['C220TMD-A']

    def execute(self, obj):
        mesh = _import_stl("C220TMD-A-Step.stl", (-90, 0, -180), (0.419, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh


class diode_adapter_s05lm56:
    '''
    Diode Mount Adapter, model S05LM56
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['S05LM56']

    def execute(self, obj):
        mesh = _import_stl("S05LM56-Step.stl", (90, 0, -90), (0, 0, -0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh


class DFB_butterfly_diode:
    '''
    Diode Mount Adapter, model eyP-BFW01-171218
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.ViewObject.ShapeColor = (1.0, 1.0, 0.0)
        self.part_numbers = ['eyP-BFW01-171218']

    def execute(self, obj):
        mesh = _import_stl("eyP-BFW01-171218.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh


class IPS_butterfly_diode:
    '''
    Diode Mount Adapter, model I0780.2SB0050PA-IS
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.ViewObject.ShapeColor = (1.0, 1.0, 0.0)
        self.part_numbers = ['IPS-laser']

    def execute(self, obj):
        mesh = _import_stl("IPS_laser.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh


class Laser_adapter:
    '''
    Koheron Laser adapter
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['laser-adapter']
    def execute(self, obj):
        mesh = _import_stl("laser_adapter.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 0.125*layout.inch)

        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth, x=5, y=37.5, z=0))

        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth, x=5, y=-37.5, z=0))

        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth, x=-70, y=-37.5, z=0))

        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth, x=-70, y=37.5, z=0))

        part.Placement = obj.Placement
        obj.DrillPart = part


class DFB_adapter:
    '''
    Koheron Laser adapter with DFB
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['DFB-adapter']
    def execute(self, obj):
        mesh = _import_stl("DFB_adapter.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 0.125*layout.inch)

        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth, x=7, y=37.5, z=0))

        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth, x=7, y=-37.5, z=0))

        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth, x=-68, y=-37.5, z=0))

        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth, x=-68, y=37.5, z=0))

        part.Placement = obj.Placement
        obj.DrillPart = part


class IPS_adapter:
    '''
    Koheron Laser adapter with IPS
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['IPS-adapter']
    def execute(self, obj):
        mesh = _import_stl("IPS_adapter.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 0.125*layout.inch)

        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth, x=9, y=37.5, z=0))

        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth, x=9, y=-37.5, z=0))

        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth, x=-66, y=-37.5, z=0))

        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth, x=-66, y=37.5, z=0))

        part.Placement = obj.Placement
        obj.DrillPart = part


class Koheron_adapter:
    """
    Adapter for Koheron in unified size
    """
    type = 'Mesh::FeaturePython'

    def __init__(self, obj, drill=True, bolt_length=15):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'BoltLength').BoltLength = bolt_length
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['Koheron_adapter']

    def execute(self, obj):
        mesh = _import_stl("Koheron_adapter.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 0.125*layout.inch)

        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth, x=9,   y= 37.5,  z=0))
        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth, x=9,   y=-37.5, z=0))
        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth, x=-66, y=-37.5, z=0))
        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth, x=-66, y= 37.5,  z=0))

        part.Placement = obj.Placement
        obj.DrillPart = part


class TA_adapter:
    """
    Adapter for TA board in unified size
    """
    type = 'Mesh::FeaturePython'

    def __init__(self, obj, drill=True, bolt_length=15):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'BoltLength').BoltLength = bolt_length
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        self.part_numbers = ['TA_adapter']

    def execute(self, obj):
        mesh = _import_stl("TA_adapter.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _bounding_box(obj, 2, 0.125*layout.inch)

        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth, x=9,   y= 37.5,  z=0))
        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth, x=9,   y=-37.5, z=0))
        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth, x=-66, y=-37.5, z=0))
        part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth, x=-66, y= 37.5,  z=0))

        part.Placement = obj.Placement
        obj.DrillPart = part


class Koheron_Controller:
    '''
    Koheron Current + TEC Controller

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['koheron-CTL200-V5']


    def execute(self, obj):
        mesh = _import_stl("koheron-CTL200-V5.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        # Alignment pin farther from mirror
        part = _custom_cylinder(dia=0.097*layout.inch, dz=2.2, x=-2.511*layout.inch, y=-0.9845*layout.inch, z=-0.531*layout.inch)

        # Alignment pin farther from mirror
        part = part.fuse(_custom_cylinder(dia=0.097*layout.inch, dz=2.2, x=-2.511*layout.inch, y=+0.9845*layout.inch, z=-0.531*layout.inch))

        # --- Baseplate cutout ---
        # Recessed region beneath controller (like KM05)
        # --- Baseplate cutout ---
        cutout = _bounding_box(obj, 2, 3,
                               min_offset=(0, 0, -0.031*layout.inch),
                               max_offset=(0,  0,  0.0))


        # # Apply fillet to the cutout before fusing
        cutout = _fillet_all(cutout, 1)
        part = part.fuse(cutout)
        for i in [1, 2, 3]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=-65, y=-55-i*10, z=0))

        for i in [1, 2, 3]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=-51, y=-55-i*10, z=0))
            
        for i in [1, 2, 3]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=-37, y=-55-i*10, z=0))
        
        part.Placement = obj.Placement
        obj.DrillPart = part


class Koheron_DFB_Laser:
    '''
    DFB Butterfly Laser mounted on a Koheron Controller Mount

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        DFB_butterfly_diode (mount_args)
        Koheron_Controller
 
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill

        obj.ViewObject.ShapeColor = misc_color

        _add_linked_object(obj, "DFB Laser Diode", DFB_butterfly_diode, pos_offset=(0, 0, 0), **mount_args)
        _add_linked_object(obj, "Koheron Controller", Koheron_Controller, pos_offset=(-1.4, 0, 1.4))
        _add_linked_object(obj, "Laser adapter", DFB_adapter, pos_offset=(0, 0, 0))


class Koheron_IPS_Laser:
    '''
    IPS Butterfly Laser mounted on a Koheron Controller Mount

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        IPS_butterfly_diode (mount_args)
        Koheron_Controller
 
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill

        obj.ViewObject.ShapeColor = misc_color

        _add_linked_object(obj, "IPS Laser Diode", IPS_butterfly_diode, pos_offset=(0, 0, 0), **mount_args)
        _add_linked_object(obj, "Koheron Controller", Koheron_Controller, pos_offset=(0, 0, 0))
        _add_linked_object(obj, "Koheron adapter", IPS_adapter, pos_offset=(0, 0, 0))


class Koheron_IPS_Laser_u:
    '''
    IPS Butterfly Laser mounted on a Koheron Controller Mount with unified adapter

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        IPS_butterfly_diode (mount_args)
        Koheron_Controller
 
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill

        obj.ViewObject.ShapeColor = misc_color

        _add_linked_object(obj, "IPS Laser Diode", IPS_butterfly_diode, pos_offset=(0, 0, 0), **mount_args)
        _add_linked_object(obj, "Koheron Controller", Koheron_Controller, pos_offset=(0, 0, 0))
        _add_linked_object(obj, "Koheron adapter", Koheron_adapter, pos_offset=(0, 0, 0))


class TA_butterfly:
    '''
    Tapered Amplifier Evaluation board, model EYP-TPA-0785-0100-3006-CMT03

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['TAboard']

        _add_linked_object(obj, "TA adapter", TA_adapter, pos_offset=(0, 0, 0))

    def execute(self, obj):
        mesh = _import_stl("TAboard.stl", (90, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _custom_cylinder(dia=bolt_M2_5['tap_dia'], dz=drill_depth,
                        y=15.875, x=-37.2, z=-13)

        part = part.fuse(_custom_cylinder(dia=bolt_M2_5['tap_dia'], dz=drill_depth,
                               y=-15.875, x=-37.2, z=-13))
        # Additional holes (fused)
        part = part.fuse(_custom_cylinder(dia=bolt_M2_5['tap_dia'], dz=drill_depth,
                               x=13.6, y=15.875, z=-13))


        part = part.fuse(_custom_cylinder(dia=bolt_M2_5['tap_dia'], dz=drill_depth,
                        x=13.6, y=-15.875, z=-13))
 
        part.Placement = obj.Placement
        obj.DrillPart = part


class Room_temp_chamber:
    '''
    importing the room temperature schamber
    Room_temperature_Chamber_simplified_version

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['Room_temp_chamber']

    def execute(self, obj):
        mesh = _import_stl("Room_temp_chamber_step.stl", (0, 0, 0), (-48.89, 1.266, 0.813))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh


class Room_temp_chamber_Mechanical:
    '''
    importing the room temperature schamber
    Room_temperature_Chamber_version

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['Room_temp_chamber']

    def execute(self, obj):
        mesh = _import_stl("Room Temp Chamber Mechanical.stl", (0, 0, 0), (-33.46, -10.12, -59.69))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

class rb_cell_holder_top:
    '''
    importing the post mountable v-clamp
    version VBC2
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['VBC2']
    
    def execute(self, obj):
        mesh = _import_stl("rb_cell_holder_top.stl", (0, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

class Vapor_Ref_Cell:
    '''
    importing the vapor reference cell
    Vapor_Reference_Cell_version GC25075-RB

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['GC25075-RB']

        _add_linked_object(obj, "rb cell holder middle", rb_cell, pos_offset=(0, 0, 0))
        _add_linked_object(obj, "rb cell holder top", rb_cell_holder_top, pos_offset=(0, 5, 0))

    def execute(self, obj):
        mesh = _import_stl("GC25075-RB.stl", (90, 90, 90), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh


class Room_temp_chamber_Mechanical_with_chip:
    '''
    importing the room temperature schamber
    Room_temperature_Chamber_version

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['Room_temp_chamber']

    def execute(self, obj):
        mesh = _import_stl("room temperature chamber with chip.stl", (0, 0, 45), (-33.46, -10.12, -59.69))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

class TEC:
    '''
    importing the room temperature schamber
    Room_temperature_Chamber_version

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['TEC']

    def execute(self, obj):
        mesh =  _import_stl("TEC.stl", (180, 0, 90), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh        

class box:

    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, thickness=3, width=10, height=10, part_number=''):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'Thickness').Thickness = thickness
        obj.addProperty('App::PropertyLength', 'Width').Width = width
        obj.addProperty('App::PropertyLength', 'Height').Height = height

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = [part_number]

    def execute(self, obj):
        part = _custom_box(dx=obj.Thickness.Value, dy=obj.Width.Value, dz=obj.Height.Value,
                           x=0, y=0, z=0, dir=(-1, 0, 0))
        obj.Shape = part

class square_grating:
    '''
    Square Grating

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        thickness (float) : The thickness of the grating
        width (float) : The width of the grating
        height (float) : The height of the grating
        part_number (string) : The part number of the grating being used
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, thickness=6, width=12.7, height=12.7, part_number=''):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'Thickness').Thickness = thickness
        obj.addProperty('App::PropertyLength', 'Width').Width = width
        obj.addProperty('App::PropertyLength', 'Height').Height = height

        obj.ViewObject.ShapeColor = glass_color
        self.part_numbers = [part_number]
        self.reflection_angle = 0
        self.max_angle = 90
        self.max_width = width

    def execute(self, obj):
        part = _custom_box(dx=obj.Thickness.Value, dy=obj.Width.Value, dz=obj.Height.Value,
                           x=0, y=0, z=0, dir=(-1, 0, 0))
        obj.Shape = part


class circular_splitter:
    '''
    Circular Beam Splitter Plate

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        thickness (float) : The edge thickness of the plate
        diameter (float) : The width of the plate
        part_number (string) : The part number of the plate being used
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, thickness=3, diameter=inch/2, part_number='', mount_type=None, mount_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'Thickness').Thickness = thickness
        obj.addProperty('App::PropertyLength', 'Diameter').Diameter = diameter

        if mount_type != None:
            _add_linked_object(obj, "Mount", mount_type, pos_offset=(-thickness, 0, 0), **mount_args)

        obj.ViewObject.ShapeColor = glass_color
        obj.ViewObject.Transparency=50
        self.part_numbers = [part_number]
        self.transmission = True
        self.reflection_angle = 0
        self.max_angle = 90
        self.max_width = diameter

    def execute(self, obj):
        part = _custom_cylinder(dia=obj.Diameter.Value, dz=obj.Thickness.Value,
                           x=0, y=0, z=0, dir=(-1, 0, 0))
        obj.Shape = part

class cube_splitter:
    '''
    Beam-splitter cube

    Args:
        cube_size (float) : The side length of the splitter cube
        invert (bool) : Invert pick-off direction, false is left, true is right
        cube_part_number (string) : The Thorlabs part number of the splitter cube being used
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, cube_size=12.7, invert=False, cube_part_number='', mount_type=None, mount_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyLength', 'CubeSize').CubeSize = cube_size
        obj.addProperty('App::PropertyBool', 'Invert').Invert = invert

        obj.ViewObject.ShapeColor = glass_color
        obj.ViewObject.Transparency=50
        self.part_numbers = [cube_part_number]
        
        if invert:
            self.reflection_angle = -135
        else:
            self.reflection_angle = 135
        self.transmission = True
        self.max_angle = 90
        self.max_width = sqrt(200)

        if mount_type != None:
            _add_linked_object(obj, "Mount", mount_type, pos_offset=(0, 0, -cube_size/2), **mount_args)

    def execute(self, obj):
        part = _custom_box(dx=obj.CubeSize.Value, dy=obj.CubeSize.Value, dz=obj.CubeSize.Value,
                           x=0, y=0, z=0, dir=(0, 0, 0))
        temp = _custom_box(dx=sqrt(200)-0.25, dy=0.1, dz=obj.CubeSize.Value-0.25,
                           x=0, y=0, z=0, dir=(0, 0, 0))
        temp.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), -self.reflection_angle)
        part = part.cut(temp)
        obj.Shape = part

class waveplate_with_cube:
    '''
    Beam-splitter cube

    Args:
        cube_size (float) : The side length of the splitter cube
        invert (bool) : Invert pick-off direction, false is left, true is right
        cube_part_number (string) : The Thorlabs part number of the splitter cube being used
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, cube_size=0.5 * inch, invert=False, cube_part_number='', mount_type=None, mount_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyLength', 'CubeSize').CubeSize = cube_size
        obj.addProperty('App::PropertyBool', 'Invert').Invert = invert

        obj.ViewObject.ShapeColor = glass_color
        obj.ViewObject.Transparency=50
        self.part_numbers = [cube_part_number]
        
        if invert:
            self.reflection_angle = -135
        else:
            self.reflection_angle = 135
        self.transmission = True
        self.max_angle = 90
        self.max_width = sqrt(200)

        _add_linked_object(obj, "rotational stage", rotation_stage_rsp05 , pos_offset=(-1/2 + 15, 0, 0),adapter = False)
        _add_linked_object(obj, "Surface Adapter", surface_adapter_for_waveplate_cube, pos_offset=(1.397 + 15, 0, -13.97), rot_offset=(0, 0, 90*obj.Invert))
    def execute(self, obj):
        part = _custom_box(dx=obj.CubeSize.Value, dy=obj.CubeSize.Value, dz=obj.CubeSize.Value,
                           x=0, y=0, z=0, dir=(0, 0, 0))
        part = part.fuse(_custom_cylinder(dia=inch/2, dz=1,
                                x=15, y=0, z=0, dir=(1, 0, 0)))
        temp = _custom_box(dx=sqrt(500)-0.25, dy=0.1, dz=obj.CubeSize.Value-0.25,
                           x=0, y=0, z=0, dir=(0, 0, 0))
        temp.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), -self.reflection_angle)
        part = part.cut(temp)
        
        obj.Shape = part

class surface_adapter_for_waveplate_cube:
    '''
    Surface adapter for post-mounted parts

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mount_hole_dy (float) : The spacing between the two mount holes of the adapter
        adapter_height (float) : The height of the suface adapter
        outer_thickness (float) : The thickness of the walls around the bolt holes
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, mount_hole_dy=20, adapter_height=11.4, outer_thickness=2):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
        obj.addProperty('App::PropertyLength', 'AdapterHeight').AdapterHeight = adapter_height
        obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = adapter_color
        obj.setEditorMode('Placement', 2)
        self.drill_tolerance = 1

        
    def execute(self, obj):
        dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2
        dy = dx+obj.MountHoleDistance.Value
        dz = obj.AdapterHeight.Value

        part = _custom_box(dx=dx, dy=dy, dz=dz,
                           x=0, y=0, z=0, dir=(0, 0, -1),
                           fillet=5)
        part = part.fuse(_custom_box(dx=dx*2.1, dy=dy/2.5, dz=0.5 * dz,
                           x=-10, y=0, z=0, dir=(0, 0, -1),
                           fillet=0))
        part = part.fuse(_custom_box(dx=dx*1.4, dy=dy/1.6, dz=1.79* dz,
                           x=-17, y=0, z=9, dir=(0, 0, -1),
                           fillet=0))
        part = part.cut(_custom_box(dx=0.5 * inch+1, dy=0.5 * inch+1, dz=0.5 * inch+1,
                           x=-16.5, y=0, z=21.2, dir=(0, 0, -1),
                           fillet=0))
        part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz+3,
                                         head_dia=bolt_8_32['head_dia'], head_dz=bolt_8_32['head_dz']+5,
                                         x=0, y=0, z=-dz-2, dir=(0,0,1)))
        for i in [-1, 1]:
            part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz+3,
                                             head_dia=bolt_8_32['head_dia'], head_dz=bolt_8_32['head_dz']+5,
                                             x=0, y=i*obj.MountHoleDistance.Value/2, z=0+1))
        obj.Shape = part


        part = _bounding_box(obj, self.drill_tolerance, 6)
        for i in [-1, 1]:
            part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                              x=0, y=i*obj.MountHoleDistance.Value/2, z=0))
        part.Placement = obj.Placement
        obj.DrillPart = part

class ruler_125mm:
    '''
    125mm ruler
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, focal_length=50, thickness=3, diameter=inch/2, part_number='', mount_type=None, mount_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'FocalLength').FocalLength = focal_length
        obj.addProperty('App::PropertyLength', 'Thickness').Thickness = thickness
        obj.addProperty('App::PropertyLength', 'Diameter').Diameter = diameter

        if mount_type != None:
            _add_linked_object(obj, "Mount", mount_type, pos_offset=(-thickness/2, 0, 0), **mount_args)

        obj.ViewObject.ShapeColor = (0,0,1)
        obj.ViewObject.Transparency=0
        self.part_numbers = [part_number]
        self.transmission = True
        self.focal_length = obj.FocalLength.Value
        self.max_angle = 90
        self.max_width = diameter

    def execute(self, obj):
        part = _custom_cylinder(dia=2, dz=125,
                                x=0, y=0, z=0, dir=(1, 0, 0))
        obj.Shape = part

class circular_lens:
    '''
    Circular Lens

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        focal_length (float) : The focal length of the lens
        thickness (float) : The edge thickness of the lens
        diameter (float) : The width of the lens
        part_number (string) : The part number of the lens being used
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, focal_length=50, thickness=3, diameter=inch/2, part_number='', mount_type=None, mount_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'FocalLength').FocalLength = focal_length
        obj.addProperty('App::PropertyLength', 'Thickness').Thickness = thickness
        obj.addProperty('App::PropertyLength', 'Diameter').Diameter = diameter

        if mount_type != None:
            _add_linked_object(obj, "Mount", mount_type, pos_offset=(-thickness/2, 0, 0), **mount_args)

        obj.ViewObject.ShapeColor = glass_color
        obj.ViewObject.Transparency=50
        self.part_numbers = [part_number]
        self.transmission = True
        self.focal_length = obj.FocalLength.Value
        self.max_angle = 90
        self.max_width = diameter

    def execute(self, obj):
        part = _custom_cylinder(dia=obj.Diameter.Value, dz=obj.Thickness.Value,
                                x=-obj.Thickness.Value/2, y=0, z=0, dir=(1, 0, 0))
        obj.Shape = part


class cylindrical_lens:
    '''
    Cylindrical Lens

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        focal_length (float) : The focal length of the lens
        thickness (float) : The edge thickness of the lens
        width (float) : The width of the lens
        height (float) : The width of the lens
        part_number (string) : The part number of the lens being used
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, focal_length=50, thickness=4, width=20, height=22, slots=False, part_number='', mount_type=skate_mount, mount_args=dict()):
        mount_args.setdefault("cube_dx", thickness)
        mount_args.setdefault("cube_dy", width)
        mount_args.setdefault("cube_dz", height)
        mount_args.setdefault("mount_hole_dy", width+10)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'FocalLength').FocalLength = focal_length
        obj.addProperty('App::PropertyLength', 'Thickness').Thickness = thickness
        obj.addProperty('App::PropertyLength', 'Width').Width = width
        obj.addProperty('App::PropertyLength', 'Height').Height = height

        if mount_type != None:
            _add_linked_object(obj, "Mount", mount_type, pos_offset=(thickness/2, 0, -height/2), mount_hole_dy=width+10, cube_dy=width, cube_dz=height, cube_dx=thickness, slots=slots)

        obj.ViewObject.ShapeColor = glass_color
        obj.ViewObject.Transparency=50
        self.part_numbers = [part_number]
        self.transmission = True
        self.focal_length = obj.FocalLength.Value
        self.max_angle = 90
        self.max_width = width

    def execute(self, obj):
        part = _custom_box(dx=obj.Thickness.Value, dy=obj.Width.Value, dz=obj.Height.Value,
                           x=0, y=0, z=0,
                           dir=(1, 0, 0))
        obj.Shape = part


class waveplate:
    '''
    Waveplate

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        thickness (float) : The thickness of the waveplate
        diameter (float) : The width of the waveplate
        part_number (string) : The part number of the waveplate being used
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, thickness=1, diameter=inch/2, part_number='', mount_type=None, mount_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'Thickness').Thickness = thickness
        obj.addProperty('App::PropertyLength', 'Diameter').Diameter = diameter

        if mount_type != None:
            _add_linked_object(obj, "Mount", mount_type, pos_offset=(-thickness/2, 0, 0), **mount_args)

        obj.ViewObject.ShapeColor = glass_color
        obj.ViewObject.Transparency=50
        self.part_numbers = [part_number]
        self.transmission = True
        self.max_angle = 90
        self.max_width = diameter

    def execute(self, obj):
        part = _custom_cylinder(dia=obj.Diameter.Value, dz=obj.Thickness.Value,
                                x=-obj.Thickness.Value/2, y=0, z=0, dir=(1, 0, 0))
        obj.Shape = part


class circular_mirror:
    '''
    Circular Mirror

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        thickness (float) : The thickness of the mirror
        diameter (float) : The width of the mirror
        part_number (string) : The part number of the mirror being used
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, thickness=6, diameter=inch/2, part_number='', mount_type=None, mount_args=dict(),mount_height=0, adapter_type=None, adapter_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'Thickness').Thickness = thickness
        obj.addProperty('App::PropertyLength', 'Diameter').Diameter = diameter

        if mount_type != None:
            _add_linked_object(obj, "Mount", mount_type, pos_offset=(-thickness, 0, 0), **mount_args)  

        obj.ViewObject.ShapeColor = glass_color
        self.part_numbers = [part_number]
        self.reflection_angle = 0
        self.max_angle = 90
        self.max_width = diameter

    def execute(self, obj):
        part = _custom_cylinder(dia=obj.Diameter.Value, dz=obj.Thickness.Value,
                           x=0, y=0, z=0, dir=(-1, 0, 0))
        obj.Shape = part

class moon_mirror:
    '''
    Circular Mirror

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        thickness (float) : The thickness of the mirror
        diameter (float) : The width of the mirror
        part_number (string) : The part number of the mirror being used
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, thickness=6, diameter=inch/2, part_number='', mount_type=None, mount_args=dict()):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'Thickness').Thickness = thickness
        obj.addProperty('App::PropertyLength', 'Diameter').Diameter = diameter

        if mount_type != None:
            _add_linked_object(obj, "Mount", mount_type, pos_offset=(4.5, -3.5, 0), **mount_args)

        obj.ViewObject.ShapeColor = glass_color
        self.part_numbers = [part_number]
        self.reflection_angle = 0
        self.max_angle = 90
        self.max_width = diameter

    def execute(self, obj):
        mesh = _import_stl("BBD05-E02-Step.stl", (-30,-120,-30), (-3,1, 4))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh        


class square_mirror:
    '''
    Square Mirror

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        thickness (float) : The thickness of the mirror
        width (float) : The width of the mirror
        height (float) : The height of the mirror
        part_number (string) : The part number of the mirror being used
    '''
    type = 'Part::FeaturePython'
    def __init__(self, obj, drill=True, thickness=3.2, width=12.7, height=12.7, part_number=''):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyLength', 'Thickness').Thickness = thickness
        obj.addProperty('App::PropertyLength', 'Width').Width = width
        obj.addProperty('App::PropertyLength', 'Height').Height = height

        obj.ViewObject.ShapeColor = glass_color
        self.part_numbers = [part_number]
        self.reflection_angle = 0
        self.max_angle = 90
        self.max_width = width

    def execute(self, obj):
        part = _custom_box(dx=obj.Thickness.Value, dy=obj.Width.Value, dz=obj.Height.Value,
                           x=0, y=0, z=0, dir=(-1, 0, 0))
        obj.Shape = part


class ViewProvider:
    def __init__(self, obj):
        obj.Proxy = self
        self.Object = obj.Object

    def attach(self, obj):
        return

    def getDefaultDisplayMode(self):
        return "Shaded"

    def onDelete(self, feature, subelements):
        if hasattr(feature.Object, "ParentObject"):
            if feature.Object.ParentObject != None:
                return False
        if hasattr(feature.Object, "ChildObjects"):
            for obj in feature.Object.ChildObjects:
                App.ActiveDocument.removeObject(obj.Name)
        return True
    
    def updateData(self, obj, prop):
        if str(prop) == "BasePlacement":
            if obj.Baseplate != None:
                obj.Placement.Base = obj.BasePlacement.Base + obj.Baseplate.Placement.Base
                obj.Placement = App.Placement(obj.Placement.Base, obj.Baseplate.Placement.Rotation, -obj.BasePlacement.Base)
                obj.Placement.Rotation = obj.Placement.Rotation.multiply(obj.BasePlacement.Rotation)
            else:
                obj.Placement = obj.BasePlacement
            if hasattr(obj, "ChildObjects"):
                for child in obj.ChildObjects:
                    child.BasePlacement.Base = obj.BasePlacement.Base + child.RelativePlacement.Base
                    if hasattr(child, "Angle"):
                        obj.BasePlacement.Rotation = App.Rotation(App.Vector(0, 0, 1), obj.Angle)
                    else:
                        child.BasePlacement = App.Placement(child.BasePlacement.Base, obj.BasePlacement.Rotation, -child.RelativePlacement.Base)
                        child.BasePlacement.Rotation = child.BasePlacement.Rotation.multiply(child.RelativePlacement.Rotation)
            if hasattr(obj, "RelativeObjects"):
                for child in obj.RelativeObjects:
                    child.BasePlacement.Base = obj.BasePlacement.Base + child.RelativePlacement.Base
        if str(prop) == "Angle":
            obj.BasePlacement.Rotation = App.Rotation(App.Vector(0, 0, 1), obj.Angle)
        return
    
    def claimChildren(self):
        if hasattr(self.Object, "ChildObjects"):
            return self.Object.ChildObjects
        else:
            return []

    def getIcon(self):
        return """
            /* XPM */
            static char *_e94ebdf19f64588ceeb5b5397743c6amoxjrynTrPg9Fk5U[] = {
            /* columns rows colors chars-per-pixel */
            "16 16 2 1 ",
            "  c None",
            "& c red",
            /* pixels */
            "                ",
            "  &&&&&&&&&&&&  ",
            "  &&&&&&&&&&&&  ",
            "  &&&&&&&&&&&&  ",
            "  &&&&&&&&&&&&  ",
            "      &&&&      ",
            "      &&&&      ",
            "      &&&&      ",
            "      &&&&      ",
            "      &&&&      ",
            "      &&&&      ",
            "      &&&&      ",
            "      &&&&      ",
            "      &&&&      ",
            "      &&&&      ",
            "                "
            };
            """

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None



####################################### ARXIV #######################################
# just rotate it 90 degrees but do not want to change other code....
# class circular_mirror_rot90:
#     '''
#     Circular Mirror

#     Args:
#         drill (bool) : Whether baseplate mounting for this part should be drilled
#         thickness (float) : The thickness of the mirror
#         diameter (float) : The width of the mirror
#         part_number (string) : The part number of the mirror being used
#     '''
#     type = 'Part::FeaturePython'
#     def __init__(self, obj, drill=True, thickness=6, diameter=inch/2, part_number='', mount_type=None, mount_args=dict()):
#         obj.Proxy = self
#         ViewProvider(obj.ViewObject)

#         obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
#         obj.addProperty('App::PropertyLength', 'Thickness').Thickness = thickness
#         obj.addProperty('App::PropertyLength', 'Diameter').Diameter = diameter

#         if mount_type != None:
#             _add_linked_object(obj, "Mount", mount_type, pos_offset=(-thickness, 0, 0), rot_offset=(0, 0, 90), **mount_args)

#         obj.ViewObject.ShapeColor = glass_color
#         self.part_numbers = [part_number]
#         self.reflection_angle = 0
#         self.max_angle = 90
#         self.max_width = diameter

#     def execute(self, obj):
#         part = _custom_cylinder(dia=obj.Diameter.Value, dz=obj.Thickness.Value,
#                            x=0, y=0, z=0, dir=(-1, 0, 0))
#         obj.Shape = part
# this is zhenyu editing
# class circular_splitter_rot90:
#     '''
#     Circular Beam Splitter Plate

#     Args:
#         drill (bool) : Whether baseplate mounting for this part should be drilled
#         thickness (float) : The edge thickness of the plate
#         diameter (float) : The width of the plate
#         part_number (string) : The part number of the plate being used
#     '''
#     type = 'Part::FeaturePython'
#     def __init__(self, obj, drill=True, thickness=3, diameter=inch/2, part_number='', mount_type=None, mount_args=dict()):
#         obj.Proxy = self
#         ViewProvider(obj.ViewObject)

#         obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
#         obj.addProperty('App::PropertyLength', 'Thickness').Thickness = thickness
#         obj.addProperty('App::PropertyLength', 'Diameter').Diameter = diameter

#         if mount_type != None:
#             _add_linked_object(obj, "Mount", mount_type, pos_offset=(-thickness, 0, 0), rot_offset=(0, 0, 0), **mount_args)

#         obj.ViewObject.ShapeColor = glass_color
#         obj.ViewObject.Transparency=50
#         self.part_numbers = [part_number]
#         self.transmission = True
#         self.reflection_angle = 0
#         self.max_angle = 90
#         self.max_width = diameter

#     def execute(self, obj):
#         part = _custom_cylinder(dia=obj.Diameter.Value, dz=obj.Thickness.Value,
#                            x=0, y=0, z=0, dir=(-1, 0, 0))
#         obj.Shape = part
#this is zhenyu editing
# class lens_mount_optosigma_TSD_1inch_in:
#     type = 'Mesh::FeaturePython'
#     # type = 'Part::FeaturePython'
#     def __init__(self, obj, drill=True):#, thumbscrews=False):
#         obj.Proxy = self
#         ViewProvider(obj.ViewObject)

#         obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
#         # obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
#         obj.addProperty('Part::PropertyPartShape', 'DrillPart')
#         obj.ViewObject.ShapeColor = mount_color

#     def execute(self, obj):
#         # mesh = _import_stl("POLARIS-K05S2-Step.stl", (90, -0, -90), (-4.514, 0.254-20, -0.254))
#         mesh = _import_stl("lens_mount_optosigma_tsd_1inch_in.stl", (0, 0, 180), (16,-135.8,0))
#         mesh.Placement = obj.Mesh.Placement
#         obj.Mesh = mesh
#         # part = _bounding_box(obj, 2,3)#,x_tol=True, y_tol=True, z_tol=True,min_offset=(0, 0, -40), max_offset=(40, 95, 0), plate_off=-28)
#         # part.Placement = obj.Placement
#         # obj.DrillPart = part
# class lens_mount_optosigma_TSD:
#     type = 'Mesh::FeaturePython'
#     # type = 'Part::FeaturePython'
#     def __init__(self, obj, drill=True):#, thumbscrews=False):
#         obj.Proxy = self
#         ViewProvider(obj.ViewObject)

#         obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
#         # obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
#         obj.addProperty('Part::PropertyPartShape', 'DrillPart')
#         obj.ViewObject.ShapeColor = mount_color

#     def execute(self, obj):
#         # mesh = _import_stl("POLARIS-K05S2-Step.stl", (90, -0, -90), (-4.514, 0.254-20, -0.254))
#         mesh = _import_stl("lens_mount_optosigma_TSD.stl", (0, 0, 180), (-10,-135.8,0))
#         mesh.Placement = obj.Mesh.Placement
#         obj.Mesh = mesh
#         part = _bounding_box(obj, 2,3)#,x_tol=True, y_tol=True, z_tol=True,min_offset=(0, 0, -40), max_offset=(40, 95, 0), plate_off=-28)
#         part.Placement = obj.Placement
#         obj.DrillPart = part
# class lens_mount_MT3A:
#     type = 'Mesh::FeaturePython'
#     # type = 'Part::FeaturePython'
#     def __init__(self, obj, drill=True):#, thumbscrews=False):
#         obj.Proxy = self
#         ViewProvider(obj.ViewObject)

#         obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
#         # obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
#         obj.addProperty('Part::PropertyPartShape', 'DrillPart')
#         obj.ViewObject.ShapeColor = mount_color

#     def execute(self, obj):
#         # mesh = _import_stl("POLARIS-K05S2-Step.stl", (90, -0, -90), (-4.514, 0.254-20, -0.254))
#         mesh = _import_stl("MT3A_translation_stage.stl", (90, 0, 90), (-30,158,-70))
#         mesh.Placement = obj.Mesh.Placement
#         obj.Mesh = mesh
#         # part = _custom_box(dx=0.1, dy=0.1, dz=0.1,
#                         #    x=0, y=0, z=0, dir=(0, 0, 0))
#         # obj.Shape = part
#         # part = _custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
#         #                         x=-8.017, y=0, z=-layout.inch/2)
#         # for i in [-1, 1]:
#         # part = _bounding_box(obj, 2,3)#,x_tol=True, y_tol=True, z_tol=True,min_offset=(0, 0, -40), max_offset=(40, 95, 0), plate_off=-28)
#         # part.Placement = obj.Placement
#         # obj.DrillPart = part
#This is zhenyu editing
# class surface_adapter_lying_down:
#     '''
#     Surface adapter for post-mounted parts

#     Args:
#         drill (bool) : Whether baseplate mounting for this part should be drilled
#         mount_hole_dy (float) : The spacing between the two mount holes of the adapter
#         adapter_height (float) : The height of the suface adapter
#         outer_thickness (float) : The thickness of the walls around the bolt holes
#     '''
#     type = 'Part::FeaturePython'
#     def __init__(self, obj, drill=True, mount_hole_dy=20, adapter_height=8, outer_thickness=2):
#         obj.Proxy = self
#         ViewProvider(obj.ViewObject)

#         obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
#         obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
#         obj.addProperty('App::PropertyLength', 'AdapterHeight').AdapterHeight = adapter_height
#         obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
#         obj.addProperty('Part::PropertyPartShape', 'DrillPart')

#         obj.ViewObject.ShapeColor = adapter_color
#         obj.setEditorMode('Placement', 2)
#         self.drill_tolerance = 0.2 * inch

#     def execute(self, obj):
#         dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2
#         dy = dx+obj.MountHoleDistance.Value
#         dz = obj.AdapterHeight.Value

#         part = _custom_box(dx=dx, dy=dy, dz=dz,
#                            x=0, y=0, z=0, dir=(0, 0, -1),
#                            fillet=5)
#         part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
#                                          head_dia=bolt_8_32['head_dia'], head_dz=bolt_8_32['head_dz'],
#                                          x=0, y=0, z=-dz, dir=(0,0,1)))
#         for i in [-1, 1]:
#             part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
#                                              head_dia=bolt_8_32['head_dia'], head_dz=bolt_8_32['head_dz'],
#                                              x=0, y=i*obj.MountHoleDistance.Value/2, z=0))
#         obj.Shape = part

#         part = _bounding_box(obj, self.drill_tolerance, 2,x_tol=1.7,y_tol=0.5,z_tol=True, plate_off=26,min_offset=(0,0,5), max_offset=(0,0,5))
#         for i in [-1, 1]:
#             part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
#                                               x=0, y=i*obj.MountHoleDistance.Value/2, z=0))
#         part.Placement = obj.Placement
#         obj.DrillPart = part
#This is zhenyu editing
# class surface_adapter_4_40:
#     '''
#     Surface adapter for post-mounted parts

#     Args:
#         drill (bool) : Whether baseplate mounting for this part should be drilled
#         mount_hole_dy (float) : The spacing between the two mount holes of the adapter
#         adapter_height (float) : The height of the suface adapter
#         outer_thickness (float) : The thickness of the walls around the bolt holes
#     '''
#     type = 'Part::FeaturePython'
#     def __init__(self, obj, drill=True, mount_hole_dy=20, adapter_height=8, outer_thickness=5):
#         obj.Proxy = self
#         ViewProvider(obj.ViewObject)

#         obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
#         obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
#         obj.addProperty('App::PropertyLength', 'AdapterHeight').AdapterHeight = adapter_height
#         obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
#         obj.addProperty('Part::PropertyPartShape', 'DrillPart')

#         obj.ViewObject.ShapeColor = adapter_color
#         obj.setEditorMode('Placement', 2)
#         self.drill_tolerance = 1#0.2 * inch

#     def execute(self, obj):
#         dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2
#         dy = dx+obj.MountHoleDistance.Value
#         dz = obj.AdapterHeight.Value

#         part = _custom_box(dx=dx+5, dy=dy, dz=dz ,
#                            x=0, y=0, z=0, dir=(0, 0, -1),
#                            fillet=5)
#         part = part.cut(_custom_cylinder(dia=bolt_4_40['clear_dia'], dz=dz,
#                                          head_dia=bolt_4_40['head_dia'], head_dz=bolt_4_40['head_dz'],
#                                          x=0, y=0, z=-dz, dir=(0,0,1)))
#         part = part.cut(_custom_box(dx = 30,dy = 15.21, dz = 17 , x = 0.05, y = 0.69, z = -5, fillet = 1))
#         for x_ in np.linspace(-2.5,2.5,20):
#             for i in [-1, 1]:
#                 part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
#                                                 head_dia=bolt_8_32['head_dia'], head_dz=bolt_8_32['head_dz'],
#                                                 x=x_, y=i*obj.MountHoleDistance.Value/2, z=0))
#         obj.Shape = part

#         # part = _bounding_box(obj, self.drill_tolerance, 6,x_tol=1.7,y_tol=0.5,z_tol=True,plate_off=1,min_offset=(0,0,0), max_offset=(0,0,0))
#         # part = _bounding_box(obj, self.drill_tolerance, 6)
#         for i in [-1, 1]:
#             part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
#                                               x=0, y=i*obj.MountHoleDistance.Value/2, z=0))
#         part.Placement = obj.Placement
#         obj.DrillPart = part
#This is zhenyu editing:
# class mirror_mount_km100:
#     '''
#     Mirror mount, model KM100

#     Args:
#         drill (bool) : Whether baseplate mounting for this part should be drilled
#         mirror (bool) : Whether to add a mirror component to the mount
#         thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
#         bolt_length (float) : The length of the bolt used for mounting

#     Sub-Parts:
#         circular_mirror (mirror_args)
#     '''
#     type = 'Mesh::FeaturePython'
#     def __init__(self, obj, drill=True):
#         obj.Proxy = self
#         ViewProvider(obj.ViewObject)

#         obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
#         obj.addProperty('Part::PropertyPartShape', 'DrillPart')

#         obj.ViewObject.ShapeColor = mount_color
#         self.part_numbers = ['KM100']

#     def execute(self, obj):
#         mesh = _import_stl("KM100-Step.stl", (-180, 0, -90), (4.972, 0.084, -1.089))
#         mesh.Placement = obj.Mesh.Placement
#         obj.Mesh = mesh
# class mirror_mount_km05_lying_down:
#     '''
#     Mirror mount, model KM05

#     Args:
#         drill (bool) : Whether baseplate mounting for this part should be drilled
#         mirror (bool) : Whether to add a mirror component to the mount
#         thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
#         bolt_length (float) : The length of the bolt used for mounting

#     Sub-Parts:
#         circular_mirror (mirror_args)
#     '''
#     type = 'Mesh::FeaturePython'
#     def __init__(self, obj, drill=True, thumbscrews=False, bolt_length=15):
#         obj.Proxy = self
#         ViewProvider(obj.ViewObject)

#         obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
#         obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
#         obj.addProperty('App::PropertyLength', 'BoltLength').BoltLength = bolt_length
#         obj.addProperty('Part::PropertyPartShape', 'DrillPart')

#         obj.ViewObject.ShapeColor = mount_color
#         self.part_numbers = ['KM05']

#         if thumbscrews:
#             _add_linked_object(obj, "Upper Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-10.54, 9.906, 9.906))
#             _add_linked_object(obj, "Lower Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-10.54, -9.906, -9.906))

#     def execute(self, obj):
#         mesh = _import_stl("KM05-Step.stl", (90, -0, 90), (2.084, -1.148, 0.498))
#         mesh.Placement = obj.Mesh.Placement
#         obj.Mesh = mesh

#         part = _bounding_box(obj, 2, 3, min_offset=(4.35, 0, 0))
#         part = part.fuse(_bounding_box(obj, 2, 3, max_offset=(0, -20, 0)))
#         part = part.fuse(_bounding_box(obj, 2, 3, min_offset=(-20, 0, 0)))
#         part = _fillet_all(part, 3)
#         part = part.fuse(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=inch,
#                                           head_dia=bolt_8_32['head_dia'], head_dz=0.92*inch-obj.BoltLength.Value,
#                                           x=-7.29, y=0, z=-inch*3/2, dir=(0,0,1)))
#         part.Placement = obj.Placement
#         obj.DrillPart = part
#this is zhenyu editing:
# class grid_waveplate_lying_down:
#     '''
#     waveplate grid, fixed as 6 * 6

#     coordinates of waveplate:
#     x=(2 * i + 1.25) * layout.inch, y=(2 * j + 1.25) * layout.inch
#     size of grid:
#     base_dx = 2.1 * layout.inch
#     base_dy = 2.1 * layout.inch
#     base_dz = 1 * layout.inch
#     size = base_dx*Row_numnber, base_dy*Column_number
#     '''
#     type = 'Mesh::FeaturePython'
#     def __init__(self, obj):
#         obj.Proxy = self
#         ViewProvider(obj.ViewObject)
#         for i in range(6):
#             for j in range(6):
#                 _add_linked_object(obj, 'waveplate_' + str(i) + str(j), waveplate, pos_offset=( (2 * i + 1.25) * layout.inch,-26.5, -(2 * j + 1.25) * layout.inch),rot_offset=(0, 0, 90))
#                 _add_linked_object(obj, 'rotation stage' + str(i) + str(j), rotation_stage_rsp05_lying_down, pos_offset=( (2 * i + 1.25) * layout.inch,-26.5, -(2 * j + 1.25) * layout.inch),rot_offset=(0, 0, 90))
#                 # _add_linked_object(obj, 'mount_' + str(i) + str(j), thumbscrew_hkts_5_64, pos_offset=(-10.54, 9.906, 9.906))
#                 # _add_linked_object(obj, 'surface_adapter' + str(i) + str(j), thumbscrew_hkts_5_64, pos_offset=(-10.54, -9.906, -9.906))
#     def execute(self, obj):
        
#         mesh = _import_stl("grid_waveplate_lying_down_baseplate.stl", rotate=(270, 0, 0), translate=(0, 0, 0))
        
#         mesh.Placement = obj.Mesh.Placement

#         obj.Mesh = mesh
# this is zhenyu editing:
# class grid_mirror_lying_down:
#     '''
#     mirror grid, fixed as 6 * 6

#     coordinates of waveplate:
#     x=(2 * i + 1.25) * layout.inch, y=(2 * j + 1.25) * layout.inch
#     size of grid:
#     base_dx = 2.1 * layout.inch
#     base_dy = 2.1 * layout.inch
#     base_dz = 1 * layout.inch
#     size = base_dx*Row_numnber, base_dy*Column_number
#     '''
#     type = 'Mesh::FeaturePython'
#     def __init__(self, obj):
#         obj.Proxy = self
#         ViewProvider(obj.ViewObject)
#         for i in range(6):
#             for j in range(6):
#                 _add_linked_object(obj, 'cicular mirror' + str(i) + str(j), circular_mirror, pos_offset=( (2 * i + 1.25) * layout.inch,-18., -(2 * j + 1.25) * layout.inch),rot_offset=(0, 0, 90))
#                 _add_linked_object(obj, 'mirror_mount' + str(i) + str(j), mirror_mount_km05_lying_down, pos_offset=( (2 * i + 1.25) * layout.inch,-18., -(2 * j + 1.25) * layout.inch),rot_offset=(0, 0, 90))
#                 # _add_linked_object(obj, 'mount_' + str(i) + str(j), thumbscrew_hkts_5_64, pos_offset=(-10.54, 9.906, 9.906))
#                 # _add_linked_object(obj, 'surface_adapter' + str(i) + str(j), thumbscrew_hkts_5_64, pos_offset=(-10.54, -9.906, -9.906))
#     def execute(self, obj):
        
#         mesh = _import_stl("grid_mirror_lying_down_baseplate.stl", rotate=(270, 0, 0), translate=(0, 0, 0))
        
#         mesh.Placement = obj.Mesh.Placement

#         obj.Mesh = mesh
# #This is zhenyu editing    
# class skate_mount_lying_down:
#     '''
#     Skate mount for splitter cubes

#     Args:
#         drill (bool) : Whether baseplate mounting for this part should be drilled
#         cube_dx, cube_dy (float) : The side length of the splitter cube
#         mount_hole_dy (float) : The spacing between the two mount holes of the adapter
#         cube_depth (float) : The depth of the recess for the cube
#         outer_thickness (float) : The thickness of the walls around the bolt holes
#         cube_tol (float) : The tolerance for size of the recess in the skate mount
#     '''
#     type = 'Part::FeaturePython'
#     def __init__(self, obj, drill=True, cube_dx=10, cube_dy=10, cube_dz=10, mount_hole_dy=20, cube_depth=1, outer_thickness=2, cube_tol=0.1, slots=False):
#         obj.Proxy = self
#         ViewProvider(obj.ViewObject)

#         obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
#         obj.addProperty('App::PropertyLength', 'CubeDx').CubeDx = cube_dy
#         obj.addProperty('App::PropertyLength', 'CubeDy').CubeDy = cube_dx
#         obj.addProperty('App::PropertyLength', 'CubeDz').CubeDz = cube_dz
#         obj.addProperty('App::PropertyLength', 'MountHoleDistance').MountHoleDistance = mount_hole_dy
#         obj.addProperty('App::PropertyLength', 'CubeDepth').CubeDepth = cube_depth+1e-3
#         obj.addProperty('App::PropertyLength', 'OuterThickness').OuterThickness = outer_thickness
#         obj.addProperty('App::PropertyLength', 'CubeTolerance').CubeTolerance = cube_tol
#         obj.addProperty('App::PropertyBool', 'Slots').Slots = slots
#         obj.addProperty('Part::PropertyPartShape', 'DrillPart')

#         obj.ViewObject.ShapeColor = adapter_color
#         obj.setEditorMode('Placement', 2)

#     def execute(self, obj):
#         if obj.Slots:
#             slot = 5
#             dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2+slot
#         else:
#             slot = 0
#             dx = bolt_8_32['head_dia']+obj.OuterThickness.Value*2
#         dy = dx+obj.MountHoleDistance.Value
#         raw_dz = obj.Baseplate.OpticsDz.Value-obj.CubeDz.Value/2+obj.CubeDepth.Value
#         dz = max(raw_dz, 8)
#         cut_dy = obj.CubeDx.Value+obj.CubeTolerance.Value
#         cut_dx = obj.CubeDy.Value+obj.CubeTolerance.Value

#         part = _custom_box(dx=dx, dy=dy, dz=dz,
#                            x=0, y=0, z=-obj.Baseplate.OpticsDz.Value, fillet=5)
#         part = part.cut(_custom_box(dx=cut_dx, dy=cut_dy, dz=obj.CubeDepth.Value+1e-3,
#                                     x=0, y=0, z=-obj.Baseplate.OpticsDz.Value+dz-obj.CubeDepth.Value-1e-3))
#         for i in [-1, 1]:
#             if obj.Slots:
#                 part = part.cut(_custom_box(dx=slot+bolt_8_32['head_dia'], dy=bolt_8_32['head_dia'], dz=bolt_8_32['head_dz'],
#                                             x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+dz,
#                                             fillet=bolt_8_32['head_dia']/2, dir=(0,0,-1)))
#                 part = part.cut(_custom_box(dx=slot+bolt_8_32['clear_dia'], dy=bolt_8_32['clear_dia'], dz=bolt_8_32['head_dz'],
#                                             x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+dz-bolt_8_32['head_dz'],
#                                             fillet=bolt_8_32['clear_dia']/2, dir=(0,0,-1)))
#             else:
#                 part = part.cut(_custom_cylinder(dia=bolt_8_32['clear_dia'], dz=dz,
#                                                 head_dia=bolt_8_32['head_dia'], head_dz=bolt_8_32['head_dz'],
#                                                 x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+dz))
            
#         part.translate(App.Vector(0, 0, obj.CubeDz.Value/2+(raw_dz-dz)))
#         part = part.fuse(part)
#         obj.Shape = part

#         part = _bounding_box(obj, 0.2*inch, 2,x_tol=4,y_tol=1,z_tol=True, plate_off=20,min_offset=(0,0,5), max_offset=(0,0,5))# ,min_offset=(-slot, 0, 0), max_offset=(slot, 0, 0))
        
#         for i in [-1, 1]:
#             part = part.fuse(_custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
#                                               x=0, y=i*obj.MountHoleDistance.Value/2, z=-obj.Baseplate.OpticsDz.Value+obj.CubeDz.Value/2))
#         part.Placement = obj.Placement
#         obj.DrillPart = part
# this is zhenyu editing
# this is zhenyu and k editing
# class EOM_:
#     '''
#     Isomet 1205C AOM on KM100PM Mount

#     Args:
#         drill (bool) : Whether baseplate mounting for this part should be drilled
#         diffraction_angle (float) : The diffraction angle (in degrees) of the AOM
#         forward_direction (integer) : The direction of diffraction on forward pass (1=right, -1=left)
#         backward_direction (integer) : The direction of diffraction on backward pass (1=right, -1=left)

#     Sub-Parts:
#         prism_mount_km100pm (mount_args)
#         mount_for_km100pm (adapter_args)
#     '''
#     type = 'Mesh::FeaturePython'
#     def __init__(self, obj, drill=True, diffraction_angle=degrees(0.026), forward_direction=1, backward_direction=1, mount_args=dict(), adapter_args=dict()):
#         obj.Proxy = self
#         ViewProvider(obj.ViewObject)

#         obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
#         obj.addProperty('App::PropertyAngle', 'DiffractionAngle').DiffractionAngle = diffraction_angle
#         obj.addProperty('App::PropertyInteger', 'ForwardDirection').ForwardDirection = forward_direction
#         obj.addProperty('App::PropertyInteger', 'BackwardDirection').BackwardDirection = backward_direction

#         obj.ViewObject.ShapeColor = misc_color
#         self.part_numbers = ['ISOMET_1205C']
#         self.diffraction_angle = diffraction_angle
#         self.diffraction_dir = (forward_direction, backward_direction)
#         self.transmission = True
#         self.max_angle = 10
#         self.max_width = 5

#         # TODO fix these parts to remove arbitrary translations
#         _add_linked_object(obj, "Mount KM100PM", prism_mount_km100pm,
#                            pos_offset=(-15.25, -20.15, -17.50), **mount_args)
#         _add_linked_object(obj, "Adapter Bracket", mount_for_km100pm,
#                            pos_offset=(-15.25, -20.15, -17.50), **adapter_args)

#     def execute(self, obj):
#         mesh = _import_stl("isomet_1205c.stl", (0, 0, 90), (0, 0, 0))
#         mesh.Placement = obj.Mesh.Placement
#         obj.Mesh = mesh
# this is zhenyu editing:
# class grid_optics:
#     type = 'Mesh::FeaturePython'
#     def __init__(self, obj):
#         obj.Proxy = self
#         ViewProvider(obj.ViewObject)
#         Number_of_light_source = 13
#         base_dx = Number_of_light_source* 1.5 * layout.inch + 2 + 1 * layout.inch
#         base_dy = Number_of_light_source* 1.5 * layout.inch + 2 + 1 * layout.inch
        
#         base_dz = 1 * layout.inch
#         input_x = 1.0 * layout.inch
#         input_y = 0.3 * layout.inch
#         for i in 1 + np.arange(Number_of_light_source):
#             _add_linked_object(obj, 'Laser_diode_LT230P-B_' + str(i), km05_50mm_laser_no_pad,
#                                     pos_offset=(input_x, input_y + i * 1.5 * layout.inch, 0), rot_offset = (0,0,layout.turn['left-up']))
#             _add_linked_object(obj, 'Laser_diode_LT230P-B_' + str(i), km05_50mm_laser_no_pad,
#                                     pos_offset=(input_y + i * 1.5 * layout.inch,input_x, 0), rot_offset = (0,0,layout.turn['left-up']))
            
#             _add_linked_object(obj, 'mirror_' + str(i), circular_mirror, 
#                                          pos_offset=(base_dx -5, input_y + i * 1.5 * layout.inch, 0) , rot_offset=(0,0,180,),  #layout.turn['up-right'],
#                                         mount_type=mirror_mount_k05s1, mount_args=dict(thumbscrews=True))
            
#             _add_linked_object(obj, 'mirror__' + str(i), circular_mirror, pos_offset=(input_y + i * 1.5 * layout.inch, base_dx - 5, 0), rot_offset=(0,0,-90),  #layout.turn['up-right'],
#                                         mount_type=mirror_mount_k05s1, mount_args=dict(thumbscrews=True))
#     def execute(self, obj):
#         mesh = _import_stl("grid_optics_fast_baseplate.stl", rotate=(0, 0, 0), translate=(0, 0, 0))
        
#         mesh.Placement = obj.Mesh.Placement

#         obj.Mesh = mesh
# # this is zhenyu editing:
# class grid_beamsplitter_lying_down:
#     '''
#     mirror grid, fixed as 6 * 6

#     coordinates of waveplate:
#     x=(2 * i + 1.25) * layout.inch, y=(2 * j + 1.25) * layout.inch
#     size of grid:
#     base_dx = 2.1 * layout.inch
#     base_dy = 2.1 * layout.inch
#     base_dz = 1 * layout.inch
#     size = base_dx*Row_numnber, base_dy*Column_number
#     '''
#     type = 'Mesh::FeaturePython'
#     def __init__(self, obj):
#         obj.Proxy = self
#         ViewProvider(obj.ViewObject)
#         for i in range(6):
#             for j in range(6):
#                 _add_linked_object(obj, 'cube_splitter' + str(i) + str(j), cube_splitter, pos_offset=( (2 * i + 1.25) * layout.inch,-18., -(2 * j + 1.25) * layout.inch),rot_offset=(0, 0, 45))
#                 # _add_linked_object(obj, 'surface_adapter' + str(i) + str(j), skate_mount_lying_down, pos_offset=( (2 * i + 1.25) * layout.inch,-18., -(2 * j + 1.25) * layout.inch),rot_offset=(0, 0, 45))
#                 # _add_linked_object(obj, 'waveplate_' + str(i) + str(j), mirror_mount_km05_lying_down, pos_offset=( (2 * i + 1.25) * layout.inch,-18., -(2 * j + 1.25) * layout.inch),rot_offset=(0, 0, 90))
#                 # _add_linked_object(obj, 'mount_' + str(i) + str(j), thumbscrew_hkts_5_64, pos_offset=(-10.54, 9.906, 9.906))
#                 # _add_linked_object(obj, 'surface_adapter' + str(i) + str(j), thumbscrew_hkts_5_64, pos_offset=(-10.54, -9.906, -9.906))
#     def execute(self, obj):
        
#         mesh = _import_stl("grid_beamsplitter_lying_down_baseplate_mount.stl", rotate=(270, 0, 0), translate=(0, 0, 0))
        
#         mesh.Placement = obj.Mesh.Placement

#         obj.Mesh = mesh
# class periscope_for_redstone_:
#     '''
#     Custom periscope mount

#     Args:
#         drill (bool) : Whether baseplate mounting for this part should be drilled
#         lower_dz (float) : Distance from the bottom of the mount to the center of the lower mirror
#         upper_dz (float) : Distance from the bottom of the mount to the center of the upper mirror
#         mirror_type (obj class) : Object class of mirrors to be used
#         table_mount (bool) : Whether the periscope is meant to be mounted directly to the optical table

#     Sub-Parts:
#         mirror_type x2 (mirror_args)
#     '''
#     type = 'Part::FeaturePython'
#     def __init__(self, obj, drill=True, lower_dz=1.5*inch, upper_dz=3*inch, invert=True, mirror_args=dict()):
#         obj.Proxy = self
#         ViewProvider(obj.ViewObject)

#         obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
#         obj.addProperty('App::PropertyLength', 'LowerHeight').LowerHeight = lower_dz
#         obj.addProperty('App::PropertyLength', 'UpperHeight').UpperHeight = upper_dz
#         obj.addProperty('App::PropertyBool', 'Invert').Invert = invert

#         obj.ViewObject.ShapeColor = adapter_color
#         if obj.Baseplate == None:
#             self.z_off = -layout.inch*3/2
#         else:
#             self.z_off = 0

#         # _add_linked_object(obj, "Lower Mirror", circular_mirror, rot_offset=((-1)**invert*90, -45, 0), pos_offset=(0, 0, obj.LowerHeight.Value+self.z_off), **mirror_args)
#         # _add_linked_object(obj, "Upper Mirror", circular_mirror, rot_offset=((-1)**invert*90, 135, 0), pos_offset=(0, 0, obj.UpperHeight.Value+self.z_off), **mirror_args)
#         # for i in range(6):
#         #     for j in range(6):
#         #         _add_linked_object(obj, 'Upper Mirror' + str(i) + str(j), circular_mirror, rot_offset=(135,90,45), pos_offset=(-110 +  i * 35, 100 -  j * 24, 20 +  j * 24 ), **mirror_args)

#         #         _add_linked_object(obj, 'Lower Mirror' + str(i) + str(j), circular_mirror, rot_offset=(0, 0, 45), pos_offset=(- 110 + j * 35, 250 - j * 24, 20 +  i * 27), **mirror_args)
#     def execute(self, obj):
#         mesh = _import_stl("periscope_for_redstone.stl", (0, 0, 0), (20, 20, 20))
#         mesh.Placement = obj.Mesh.Placement
#         obj.Mesh = mesh


# =============================================================================
# Rb-87 795 nm lattice laser system - components added on this branch
# (lattice / TA / double-pass AOM baseplates V9.2, Rubidium_system/*_V9.py).
# Everything above this banner is the yajur-branch library, unchanged.
# =============================================================================


# --- 1. four variants of existing parts --------------------------------------
class lens_holder_l05g_no_pin_slots:
    '''
    Lens Holder, Model L05G - without the two alignment-pin slots.

    Same mesh and same central 8-32 bore as ``lens_holder_l05g``; the two
    5 x 2 x 2.2 mm pin slots are not cut, so the holder can sit anywhere
    without extra plate features. Used by every lens on the V9 boards.

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        circular_lens (lens_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['POLARIS-L05G']

    def execute(self, obj):
        mesh = _import_stl("POLARIS-L05G-Step.stl", (90, -0, 90), (-26.57, -13.29, -18.44))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                x=-8, y=0, z=-layout.inch/2)
        part.Placement = obj.Placement
        obj.DrillPart = part


class isolator_850_long_pocket:
    '''
    Isolator IOT-5-850-VLP with the full-length 113.5 mm plate pocket.

    Identical to ``isolator_850`` except that the pocket spans the whole
    body (dx 80 -> 113.5 mm), as on the hana-branch boards.

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled

    Sub-Parts:
        surface_adapter (adapter_args)
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, adapter_args=dict()):
        adapter_args.setdefault("mount_hole_dy", 45)
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = misc_color
        self.part_numbers = ['IOT-5-670-VLP']
        self.transmission = True
        self.max_angle = 10
        self.max_width = 5

        _add_linked_object(obj, "Surface Adapter", surface_adapter_isolator_lip,
                           pos_offset=(0, 0, -22.1), **adapter_args)

    def execute(self, obj):
        mesh = _import_stl("IOT-5-850-VLP-Step.stl", (90, 0, -90), (-19.05, -0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _custom_box(dx=113.5, dy=25, dz=5,
                           x=0, y= 0, z=-layout.inch/2,
                           fillet=0.125*layout.inch, dir=(0, 0, -1))
        part.Placement = obj.Placement
        obj.DrillPart = part


class TA_butterfly_on_adapter:
    '''
    Tapered Amplifier evaluation board, model EYP-TPA-0785-0100-3006-CMT03,
    screwed to the TA adapter rather than straight to the baseplate.

    Same mesh and the same linked ``TA_adapter`` as ``TA_butterfly``. The
    board's four M2.5 screws go into the adapter's own tapped holes, and the
    adapter is held down by four 8-32 into the plate, so this part drills
    nothing itself: the plate holes under the TA are the adapter's four 8-32
    only. (``TA_butterfly`` above, which also taps four M2.5 into the plate,
    is kept unchanged and unused.)

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['TAboard']

        _add_linked_object(obj, "TA adapter", TA_adapter, pos_offset=(0, 0, 0))

    def execute(self, obj):
        mesh = _import_stl("TAboard.stl", (90, 0, 0), (0, 0, 0))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        # No plate holes of its own: the board is mounted on the TA adapter,
        # which carries the four 8-32 plate holes (see class doc).
        obj.DrillPart = Part.Shape()


class mirror_mount_k05s1_no_pins:
    '''
    Mirror mount, model K05S1 - without the two 2 mm alignment-pin holes.

    Same mesh and the same single 8-32 tap as ``mirror_mount_k05s1``; the two
    2 x 2.2 mm pin holes are not drilled (a kinematic fold does not need the
    pins, and at the plate corner they would sit 3 mm from the edge).

    Args:
        drill (bool) : Whether baseplate mounting for this part should be drilled
        mirror (bool) : Whether to add a mirror component to the mount
        thumbscrews (bool): Whether or not to add two HKTS 5-64 adjusters
    '''
    type = 'Mesh::FeaturePython'
    def __init__(self, obj, drill=True, thumbscrews=False):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)

        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('App::PropertyBool', 'ThumbScrews').ThumbScrews = thumbscrews
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')

        obj.ViewObject.ShapeColor = mount_color
        self.part_numbers = ['POLARIS-K05S1']

        if thumbscrews:
            _add_linked_object(obj, "Upper Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-11.22, 8.89, 8.89))
            _add_linked_object(obj, "Lower Thumbscrew", thumbscrew_hkts_5_64, pos_offset=(-11.22, -8.89, -8.89))

    def execute(self, obj):
        mesh = _import_stl("POLARIS-K05S1-Step.stl", (90, 0, -90), (-4.514, 0.254, -0.254))
        mesh.Placement = obj.Mesh.Placement
        obj.Mesh = mesh

        part = _custom_cylinder(dia=bolt_8_32['tap_dia'], dz=drill_depth,
                                x=-8.017, y=0, z=-layout.inch/2)
        part.Placement = obj.Placement
        obj.DrillPart = part



# --- 2. machining primitives (bare taps, persistent plate cuts) --------------

def descendants(root):
    """Return the root and every linked hardware child once."""
    found, pending = [], [root]
    seen = set()
    while pending:
        obj = pending.pop(0)
        if obj.Name in seen:
            continue
        seen.add(obj.Name)
        found.append(obj)
        pending.extend(getattr(obj, "ChildObjects", []))
    return found

def _bbox_values(box):
    return [float(x) for x in
            (box.XMin, box.XMax, box.YMin, box.YMax, box.ZMin, box.ZMax)]

class HiddenMachiningViewProvider:
    """Persist the hidden state of an empty machining-only Part feature."""

    def __init__(self, view):
        view.Proxy = self
        view.Visibility = False

    def attach(self, view):
        view.Visibility = False

    def onChanged(self, view, prop):
        if prop == 'Visibility' and view.Visibility:
            view.Visibility = False

    def getDefaultDisplayMode(self):
        return 'Shaded'

    def dumps(self): return None
    def loads(self, state): return None

def keep_machining_hidden(obj):
    view = getattr(obj, 'ViewObject', None)
    if view is not None:
        if not isinstance(view.Proxy, HiddenMachiningViewProvider):
            HiddenMachiningViewProvider(view)
        view.Visibility = False

class PersistentDrillVolume:
    """Parametric hidden plate cut, independent of either upstream library."""

    def __init__(self, obj):
        obj.Proxy = self

    def execute(self, obj):
        if not obj.Drill or obj.Owner is None:
            obj.DrillPart = Part.Shape()
            return
        if obj.CutKind == "isolator-pocket":
            length, width, depth = (obj.PocketLength.Value,
                                    obj.PocketWidth.Value,
                                    obj.PocketDepth.Value)
            top = -obj.Baseplate.OpticsDz.Value
            cut = Part.makeBox(length, width, depth,
                               App.Vector(-length / 2, -width / 2, top - depth))
            radius = obj.CornerRadius.Value
            if radius > 0:
                vertical = [edge for edge in cut.Edges
                            if abs(edge.tangentAt(edge.FirstParameter).z) > 0.999]
                cut = cut.makeFillet(radius, vertical)
        elif obj.CutKind == "fiber-tail-pair":
            offset, half_spacing = obj.RearOffset.Value, obj.HoleSpacing.Value / 2
            # Identical drill standard and direction to yajur's KA05T_holes.
            cuts = [Part.makeCylinder(obj.TapDiameter.Value / 2,
                                      obj.DrillDepth.Value,
                                      App.Vector(-offset, sign * half_spacing, 0),
                                      App.Vector(0, 0, -1)) for sign in (-1, 1)]
            cut = Part.makeCompound(cuts)
        else:
            raise ValueError("Unknown persistent plate cut: " + obj.CutKind)
        cut.Placement = obj.Owner.Placement
        obj.DrillPart = cut
        # No visible stock: this object only supplies a machining volume.
        obj.Shape = Part.Shape()

    def dumps(self):
        return None

    def loads(self, state):
        return None

def _drill_object(bp, owner, name, kind):
    doc = owner.Document
    plate = doc.getObject(bp.active_baseplate)
    if owner.Baseplate != plate:
        raise ValueError("Cut owner belongs to a different baseplate")
    obj = doc.addObject("Part::FeaturePython", name)
    obj.addProperty("App::PropertyLinkHidden", "Baseplate").Baseplate = plate
    obj.addProperty("App::PropertyLink", "Owner", "Cut geometry").Owner = owner
    obj.addProperty("App::PropertyBool", "Drill", "Cut geometry").Drill = True
    obj.addProperty("App::PropertyString", "CutKind", "Cut geometry").CutKind = kind
    obj.addProperty("Part::PropertyPartShape", "DrillPart", "Cut geometry")
    obj.addProperty("App::PropertyString", "Purpose", "Provenance")
    PersistentDrillVolume(obj)
    if obj.ViewObject is not None:
        obj.ViewObject.Visibility = False
    return obj

def deepen_isolator_pocket(bp, isolator, depth=10.0):
    """Add Hana's 113.5 x 25 pocket at the requested full depth (default 10 mm).

    Depth is measured from the plate top, not added to the original 5 mm. At
    standard optical height 12.7 mm this spans z=-12.7 to -22.7. The isolator
    and surface adapter keep their original location and their own drill cuts.
    """
    plate = isolator.Document.getObject(bp.active_baseplate)
    if depth <= 0 or depth >= plate.dz.Value:
        raise ValueError("Isolator pocket depth must be positive and below plate thickness")
    obj = _drill_object(bp, isolator, "Isolator pocket - 10 mm total depth", "isolator-pocket")
    obj.addProperty("App::PropertyLength", "PocketLength", "Cut geometry").PocketLength = 113.5
    obj.addProperty("App::PropertyLength", "PocketWidth", "Cut geometry").PocketWidth = 25
    obj.addProperty("App::PropertyLength", "PocketDepth", "Cut geometry").PocketDepth = depth
    obj.addProperty("App::PropertyLength", "CornerRadius", "Cut geometry").CornerRadius = 3.174
    obj.Purpose = "Hana footprint; original 5 mm pocket doubled to 10 mm total; adapter unchanged"
    obj.Proxy.execute(obj)
    return obj

def add_fiber_tail_alternative(bp, fiber, offset=82.7, spacing=18.328):
    """Add the second rear pair while preserving the original 72.7 mm pair.

    Both dimensions are referenced to the same optical-center frame as the
    original mount: local x=-offset and y=+/-spacing/2. These are 8-32 tapping
    bores, not clearance holes. Use with rear_hole_x_offset=72.7 on the original
    ``fiberport_mount_KA05T_holes`` root.
    """
    if offset <= 0 or spacing <= 0:
        raise ValueError("Fiber-tail hole offsets and spacing must be positive")
    if not hasattr(fiber, "RearHoleXOffset"):
        raise TypeError("Use the original fiberport_mount_KA05T_holes for the first pair")
    if abs(fiber.RearHoleXOffset.Value - offset) < 1e-6:
        raise ValueError("Alternative holes must differ from the first pair")
    obj = _drill_object(bp, fiber, fiber.Name + " - alternate tail holes", "fiber-tail-pair")
    obj.addProperty("App::PropertyLength", "RearOffset", "Cut geometry").RearOffset = offset
    obj.addProperty("App::PropertyLength", "HoleSpacing", "Cut geometry").HoleSpacing = spacing
    obj.addProperty("App::PropertyLength", "TapDiameter", "Cut geometry").TapDiameter = 0.136 * 25.4
    obj.addProperty("App::PropertyLength", "DrillDepth", "Cut geometry").DrillDepth = 100
    obj.Purpose = "Second fiber-tail support position; first pair and KA05T mounting bores preserved"
    obj.Proxy.execute(obj)
    return obj

class BareTappedHole:
    """An 8-32 tap-drill location; no lens, mount, counterbore or adapter."""
    type = 'Part::FeaturePython'

    def __init__(self, obj, drill=True):
        obj.Proxy = self
        keep_machining_hidden(obj)
        obj.addProperty('App::PropertyBool', 'Drill').Drill = drill
        obj.addProperty('Part::PropertyPartShape', 'DrillPart')
        obj.addProperty('App::PropertyString', 'Thread', 'Machining').Thread = '8-32 UNC'
        obj.addProperty('App::PropertyLength', 'TapDrillDiameter', 'Machining').TapDrillDiameter = 3.4544
        obj.addProperty('App::PropertyString', 'Purpose', 'Design')

    def execute(self, obj):
        cut = Part.makeCylinder(obj.TapDrillDiameter.Value/2, 100,
                                App.Vector(0, 0, 0), App.Vector(0, 0, -1))
        cut.Placement = obj.Placement
        obj.DrillPart = cut
        obj.Shape = Part.Shape()
        # Keep empty drilling metadata hidden after recomputing a saved file.
        keep_machining_hidden(obj)

    def onDocumentRestored(self, obj):
        keep_machining_hidden(obj)

    def dumps(self): return None
    def loads(self, state): return None


# --- 3. Rb vapour cell seat: the plate pocket only (no holder, no glass) -----

OPTICAL_HEIGHT = 12.7
# V9.2 pocket-only cell seat (local frame: x along the beam, z = 0 on the axis).

# V9.2 pocket-only cell seat (local frame: x along the beam, z = 0 on the axis).
POCKET_LENGTH = 104.0            # unchanged long side (Hana: -52..52)

POCKET_WIDTH = 56.0              # unchanged short side, now centred on the beam

POCKET_DEPTH = 0.75 * 25.4       # 19.05 mm below the plate top (plate 25.4 thick)

POCKET_CORNER_RADIUS = 3.174

TAP_DIAMETER = 3.4544            # 8-32 UNC tap drill, as every other 8-32 on the plate
# Corner holes: same x as the Hana pattern. Hana's corner holes (y = -15.7 and
# +25.7) sit 5.3 mm inside its -21..31 holder edges = 7.3 mm from the pocket
# wall; for the centred pocket (walls at +/-28) the same inset gives +/-20.7.

# Corner holes: same x as the Hana pattern. Hana's corner holes (y = -15.7 and
# +25.7) sit 5.3 mm inside its -21..31 holder edges = 7.3 mm from the pocket
# wall; for the centred pocket (walls at +/-28) the same inset gives +/-20.7.
TAP_XY = [(-45.0, -20.7), (-45.0, 20.7), (45.0, -20.7), (45.0, 20.7)]

CELL_POCKET_DIMENSIONS = {
    "model": "GC25075-RB",
    "holder": "none installed (V9.2): plate pocket + 4 corner 8-32 taps; enclosure to be added later",
    "cell_bbox_local_mm": [-35.92, 35.92, -12.7, 22.7, -12.7, 12.7],
    "pocket_bbox_local_mm": [-POCKET_LENGTH / 2, POCKET_LENGTH / 2, -POCKET_WIDTH / 2, POCKET_WIDTH / 2,
                             -OPTICAL_HEIGHT - POCKET_DEPTH, -OPTICAL_HEIGHT],
    "pocket_length_mm": POCKET_LENGTH,
    "pocket_width_mm": POCKET_WIDTH,
    "pocket_centred_on_beam": True,
    "pocket_corner_radius_mm": POCKET_CORNER_RADIUS,
    "pocket_depth_below_standard_plate_top_mm": POCKET_DEPTH,
    "pocket_floor_stock_mm": 25.4 - POCKET_DEPTH,
    "tap_hole_diameter_mm": TAP_DIAMETER,
    "tap_holes_local_xy_mm": [list(p) for p in TAP_XY],
    "former_hana_pocket_bbox_local_mm": [-52.0, 52.0, -23.0, 33.0, -25.4, -12.7],
    "former_hana_tap_holes_local_xy_mm": [
        [-45.0, -15.7], [-45.0, 15.7], [-45.0, 25.7],
        [45.0, -15.7], [45.0, 15.7], [45.0, 25.7],
    ],
    "notes": [
        "V9.2: no holder/enclosure body is installed; the GC25075-RB glass is shown only for the optical path.",
        "Pocket 104 x 56 mm, 19.05 mm (3/4 in) deep, short side centred on the beam axis (Hana's was offset +5 mm).",
        "Only the four corner 8-32 taps remain (x = +/-45); the middle pair (y = +15.7) is dropped and the "
        "corner rows sit symmetric at y = +/-20.7 (5.3 mm from the pocket wall, like Hana's corner holes).",
        "The taps are drilled through the 6.35 mm pocket floor (through holes).",
        "The vapor-cell fill stem points toward local +y, not upward.",
    ],
}

class CellPocketMachining:
    """Hidden plate machining: the 3/4 in cell pocket and its four corner taps."""
    type = "Part::FeaturePython"

    def __init__(self, obj, drill=True):
        obj.Proxy = self
        keep_machining_hidden(obj)
        obj.addProperty("App::PropertyBool", "Drill").Drill = drill
        obj.addProperty("Part::PropertyPartShape", "DrillPart")
        obj.addProperty("App::PropertyLength", "PocketLength", "Machining").PocketLength = POCKET_LENGTH
        obj.addProperty("App::PropertyLength", "PocketWidth", "Machining").PocketWidth = POCKET_WIDTH
        obj.addProperty("App::PropertyLength", "PocketDepth", "Machining").PocketDepth = POCKET_DEPTH
        obj.addProperty("App::PropertyLength", "CornerRadius", "Machining").CornerRadius = POCKET_CORNER_RADIUS
        obj.addProperty("App::PropertyLength", "TapDrillDiameter", "Machining").TapDrillDiameter = TAP_DIAMETER
        obj.addProperty("App::PropertyString", "Thread", "Machining").Thread = "8-32 UNC through, 4 corner holes"
        obj.addProperty("App::PropertyString", "Purpose", "Design")
        obj.addProperty("App::PropertyString", "DimensionsJSON", "Design")

    def execute(self, obj):
        top = -obj.Baseplate.OpticsDz.Value          # plate top in the beam frame (-12.7)
        length, width = obj.PocketLength.Value, obj.PocketWidth.Value
        depth = obj.PocketDepth.Value
        # The box reaches 1 mm above the plate top so no coincident faces are cut.
        pocket = Part.makeBox(length, width, depth + 1.0,
                              App.Vector(-length / 2, -width / 2, top - depth))
        radius = obj.CornerRadius.Value
        if radius > 0:
            vertical = [e for e in pocket.Edges if abs(e.tangentAt(e.FirstParameter).z) > 0.999]
            pocket = pocket.makeFillet(radius, vertical)
        cut = pocket
        for x, y in TAP_XY:
            cut = cut.fuse(Part.makeCylinder(obj.TapDrillDiameter.Value / 2, 100.0,
                                             App.Vector(x, y, top + 1.0), App.Vector(0, 0, -1)))
        cut = cut.removeSplitter()
        cut.Placement = obj.Placement
        obj.DrillPart = cut if obj.Drill else Part.Shape()
        obj.Shape = Part.Shape()
        keep_machining_hidden(obj)

    def onDocumentRestored(self, obj):
        keep_machining_hidden(obj)

    def dumps(self):
        return None

    def loads(self, state):
        return None

def place_cell_pocket(bp, x, y, angle=0, name="Rb vapor cell seat - plate pocket 3/4 in + 4 corner taps"):
    """V9.2: the machined pocket seat only - no glass, no holder, no enclosure.

    The enclosure has not been designed yet, so nothing is modelled above the
    plate: the board carries only the pocket and its four corner 8-32 taps.
    Returns ``root`` / ``objects`` / ``cut_object`` / ``dimensions`` so the
    audits treat the pocket as the cell's plate cut.
    """
    pocket = bp.place_element(name, CellPocketMachining, x=x, y=y, angle=angle)
    pocket.Purpose = ("V9.2 cell seat: 104 x 56 mm pocket centred on the beam, 19.05 mm deep, "
                      "8-32 taps at (+/-45, +/-20.7); enclosure to be designed/installed later.")
    pocket.Document.recompute()
    dimensions = json.loads(json.dumps(CELL_POCKET_DIMENSIONS))
    dimensions["placement_xy_angle"] = [float(x), float(y), float(angle)]
    pocket.DimensionsJSON = json.dumps(dimensions)
    return {"root": pocket, "objects": [pocket], "cut_object": pocket,
            "dimensions": dimensions}


# --- 3b. V9.6 split sliding Rb vapour-cell enclosure (plain block) -----------
#
# Local frame of every part below: x along the bore (= the beam), y across the
# beam in the plate plane (the sliding direction), z up. The origin is on the
# bore axis at the middle of the CELL; the parting plane of the two halves is
# z = 0 = the plate's 12.7 mm optical axis, so the beam runs along the split.
#
#   SlidingCellEnclosure  the LOWER half (root): a plain 82 x 43.9 x 24 block
#                         (x = -38 .. +44; 20.2 toward local -y, 23.7 toward
#                         local +y) with the half bore, the lower half of the
#                         stem channel, the cable notch, the through slot and
#                         the four lower cover taps
#   SlidingCellLid        the UPPER half: the same plain block, 24 tall, with the
#                         half bore, the upper half of the stem channel, the
#                         through slot with its counter-slot, the upper taps
#   SlidingCellCover      two 43.9 x 48 x 8 mm end plates, four counterbored
#                         8-32 clearance holes each, NO beam aperture yet
#   SlidingCellGlass      the GC25075-RB envelope (25.4 x 71.84, stem sideways
#                         along local +y, i.e. away from the beam side)
#   SlidingCellSeat       plate machining: the 11.3 mm deep pocket (both halves,
#                         covers and travel) and the single 8-32 tap
#
# One 8-32 x 2 in screw goes from the lid top through the slot of BOTH halves
# into the plate: it clamps the halves together and fixes the position. The
# slot sits in the bore's end region beyond the cell (the body is 6 mm longer
# than the cell needs at that end), on the local +y half of the bore - the beam
# uses the centre and the local -y half - so the screw never meets the cell or
# the beam. The body slides along local +y (board -x on the lattice board,
# where the seat is placed at angle 90) by 0 .. 10.5 mm: at 0 the beam runs
# through the cell centre, at 10.5 it runs 2.2 mm inside the cell wall on the
# local -y side; in the body frame the screw then moves from y = 11 to y = 0.5.

SLIDING_CELL = {
    "model": "GC25075-RB",
    "cell_radius_mm": 12.7,
    "cell_length_mm": 71.84,
    "stem_radius_mm": 3.15,
    "stem_tip_from_axis_mm": 22.7,           # glass 12.7 + 10 mm stem, pointing along local +y
    # body (both halves): a plain rectangular block
    "bore_radius_mm": 15.2,                  # bore 30.4 = cell 25.4 + 5, through the whole length
    "x_range_mm": [-38.0, 44.0],             # 2.08 mm beyond the cell at -x, 8.08 at +x (the slot end)
    "half_width_beam_side_mm": 20.2,         # local -y face (board +x): 5 mm beside the bore
    "half_width_stem_side_mm": 23.7,         # local +y face (board -x): 8.5 mm wall carrying the stem channel
    "half_height_mm": 24.0,                  # lower half z = -24 .. 0, lid z = 0 .. 24: the block is cut in half
    # the single through slot (both halves) in the bore's +x end region, local +y half
    "slot_x_mm": 39.3,                       # 3.4 mm beyond the cell end (35.92), 4.7 mm inside the end face
    "slot_y_mm": [0.5, 11.0],                # screw centre at full travel .. centred (slide 0)
    "slot_width_mm": 0.172*25.4,             # 8-32 close clearance (4.37)
    "travel_mm": 10.5,                       # beam 2.2 mm inside the cell wall at the end (the isolator limits more)
    "lid_counterslot_mm": [8.5, 5.0],        # width, depth from the lid top: the socket head sits 0.6 mm below the top
    # stem channel through the local +y wall, centred on the parting plane, open at the outer face
    "stem_channel_mm": [12.0, 10.0],         # x width, z height (5 in each half): 1.85 mm around the 6.3 mm stem
    # cable notch in the lower half's parting face, through the local +y wall
    "cable_notch_mm": [6.0, 6.0],            # x width, depth below the parting plane
    "cable_notch_x_mm": -20.0,
    # covers
    "cover_thickness_mm": 8.0,
    "cover_hole_yz_mm": [[17.0, 17.0], [-14.5, 17.0], [17.0, -17.0], [-14.5, -17.0]],   # +y pair clears the slot
    "cover_hole_clearance_mm": 0.172*25.4,
    "cover_counterbore_mm": [7.5, 4.5],      # diameter, depth: the socket head sits flush with the cover face
    "cover_screw": "8-32 x 5/8 in socket head cap screw (15.9 mm), 8 per enclosure",
    "cover_tap_depth_mm": 16.0,              # 15.9 - (8 - 4.5) = 12.4 mm of thread engaged, 3.6 mm spare
    "seat_screw": "8-32 x 2 in socket head cap screw (50.8 mm) through the lid and the lower half, 1 per seat",
    # plate machining
    "pocket_clearance_mm": 2.0,              # beyond the covers (x)
    "pocket_clearance_stem_side_mm": 1.0,    # local +y end of the travel: the pocket wall is the travel stop
    "pocket_clearance_beam_side_mm": 6.3,    # local -y edge (board +x): reaches past the injection fold's
                                             # thumbscrew pocket (as the old pocket did) instead of leaving a thin wall
    "pocket_corner_radius_mm": 3.174,        # end-mill fillet on the pocket corners
    "seat_tap_depth_mm": 100.0,              # through the pocket floor (14.1 mm of stock)
    "seat_tap_diameter_mm": 0.136*25.4,
}


def _sliding_cell_slot(x, y0, y1, width, z0, dz):
    """A stadium slot along y at x, between the end centres y0 < y1, from z0 up by dz."""
    r = width/2.
    slot = Part.makeBox(width, y1 - y0, dz, App.Vector(x - r, y0, z0))
    for yy in (y0, y1):
        slot = slot.fuse(Part.makeCylinder(r, dz, App.Vector(x, yy, z0), App.Vector(0, 0, 1)))
    return slot.removeSplitter()


def _sliding_cell_block(p, z0, z1):
    """The plain rectangular plan of either half between z0 and z1."""
    x0, x1 = p["x_range_mm"]
    yb, ys = p["half_width_beam_side_mm"], p["half_width_stem_side_mm"]
    return Part.makeBox(x1 - x0, yb + ys, z1 - z0, App.Vector(x0, -yb, z0))


def _sliding_cell_common_cuts(p, shape, z0, z1, sign):
    """Bore, the half stem channel, the through slot and the cover taps of one half (sign = -1 lower, +1 upper)."""
    x0, x1 = p["x_range_mm"]
    ys = p["half_width_stem_side_mm"]
    shape = shape.cut(Part.makeCylinder(p["bore_radius_mm"], x1 - x0 + 2., App.Vector(x0 - 1., 0, 0),
                                        App.Vector(1, 0, 0)))
    cw, ch = p["stem_channel_mm"]
    # the channel runs from inside the bore out through the +y face; this half
    # takes ch/2 of its height (the box reaches 1 mm past the parting plane)
    z_box = -ch/2. if sign < 0 else -1.
    shape = shape.cut(Part.makeBox(cw, ys - p["bore_radius_mm"] + 4., ch/2. + 1.,
                                   App.Vector(-cw/2., p["bore_radius_mm"] - 2., z_box)))
    y0, y1 = p["slot_y_mm"]
    shape = shape.cut(_sliding_cell_slot(p["slot_x_mm"], y0, y1, p["slot_width_mm"], z0 - 1., z1 - z0 + 2.))
    for x_end, direction in ((x0, 1), (x1, -1)):
        for yy, zz in p["cover_hole_yz_mm"]:
            if (zz > 0) != (sign > 0):
                continue
            shape = shape.cut(Part.makeCylinder(p["seat_tap_diameter_mm"]/2., p["cover_tap_depth_mm"],
                                                App.Vector(x_end, yy, zz), App.Vector(direction, 0, 0)))
    return shape


def sliding_cell_lower_shape(p=None):
    """The lower half in the local frame: trough, lower stem channel, cable notch, slot, lower cover taps."""
    p = p or SLIDING_CELL
    h = p["half_height_mm"]
    shape = _sliding_cell_block(p, -h, 0.)
    shape = _sliding_cell_common_cuts(p, shape, -h, 0., -1)
    nw, nd = p["cable_notch_mm"]
    ys = p["half_width_stem_side_mm"]
    shape = shape.cut(Part.makeBox(nw, ys - p["bore_radius_mm"] + 4., nd + 1.,
                                   App.Vector(p["cable_notch_x_mm"] - nw/2., p["bore_radius_mm"] - 2., -nd)))
    return shape.removeSplitter()


def sliding_cell_lid_shape(p=None):
    """The upper half: trough, upper stem channel, the through slot with its counter-slot, upper cover taps."""
    p = p or SLIDING_CELL
    h = p["half_height_mm"]
    shape = _sliding_cell_block(p, 0., h)
    shape = _sliding_cell_common_cuts(p, shape, 0., h, +1)
    cw, cd = p["lid_counterslot_mm"]
    y0, y1 = p["slot_y_mm"]
    shape = shape.cut(_sliding_cell_slot(p["slot_x_mm"], y0, y1, cw, h - cd, cd + 1.))
    return shape.removeSplitter()


def sliding_cell_body_shape(p=None):
    """Both halves fused (for envelope checks and the assembly STEP)."""
    return sliding_cell_lower_shape(p).fuse(sliding_cell_lid_shape(p)).removeSplitter()


def sliding_cell_cover_shape(p=None):
    """One end cover: its inner face at x = 0, the plate extends to +x (counterbores on the +x face)."""
    p = p or SLIDING_CELL
    t = p["cover_thickness_mm"]
    yb, ys, h = p["half_width_beam_side_mm"], p["half_width_stem_side_mm"], p["half_height_mm"]
    cover = Part.makeBox(t, yb + ys, 2*h, App.Vector(0, -yb, -h))
    cb_dia, cb_depth = p["cover_counterbore_mm"]
    for yy, zz in p["cover_hole_yz_mm"]:
        cover = cover.cut(Part.makeCylinder(p["cover_hole_clearance_mm"]/2., t + 2., App.Vector(-1., yy, zz),
                                            App.Vector(1, 0, 0)))
        cover = cover.cut(Part.makeCylinder(cb_dia/2., cb_depth + 1., App.Vector(t - cb_depth, yy, zz),
                                            App.Vector(1, 0, 0)))
    return cover.removeSplitter()


def sliding_cell_glass_shape(p=None):
    """The GC25075-RB envelope: a 25.4 x 71.84 mm cylinder with the fill stem along local +y."""
    p = p or SLIDING_CELL
    r, length = p["cell_radius_mm"], p["cell_length_mm"]
    glass = Part.makeCylinder(r, length, App.Vector(-length/2., 0, 0), App.Vector(1, 0, 0))
    stem = Part.makeCylinder(p["stem_radius_mm"], p["stem_tip_from_axis_mm"] - r + 1.,
                             App.Vector(0, r - 1., 0), App.Vector(0, 1, 0))
    return glass.fuse(stem).removeSplitter()


def sliding_cell_pocket_outline(p=None):
    """Pocket outline in the seat frame as (x0, y0, x1, y1): one rectangle around the block, the covers and the travel."""
    p = p or SLIDING_CELL
    c = p["pocket_clearance_mm"]
    x0, x1 = p["x_range_mm"]
    t = p["cover_thickness_mm"]
    return (x0 - t - c, -p["half_width_beam_side_mm"] - p["pocket_clearance_beam_side_mm"],
            x1 + t + c, p["half_width_stem_side_mm"] + p["travel_mm"] + p["pocket_clearance_stem_side_mm"])


def sliding_cell_seat_taps(p=None):
    """Seat tap centres in the seat frame: the screw at the slot's outer end when the body is centred."""
    p = p or SLIDING_CELL
    return [[p["slot_x_mm"], p["slot_y_mm"][1]]]


def sliding_cell_pocket_shape(top, p=None):
    """The plate cut in the seat frame: the pocket (floor at the body bottom) plus the tap."""
    p = p or SLIDING_CELL
    depth = top + p["half_height_mm"]
    x0, y0, x1, y1 = sliding_cell_pocket_outline(p)
    pocket = Part.makeBox(x1 - x0, y1 - y0, depth + 1., App.Vector(x0, y0, top - depth))
    radius = p["pocket_corner_radius_mm"]
    if radius > 0:
        edges = [e for e in pocket.Edges if abs(e.tangentAt(e.FirstParameter).z) > 0.999]
        pocket = pocket.makeFillet(radius, edges)
    cut = pocket
    for x, y in sliding_cell_seat_taps(p):
        cut = cut.fuse(Part.makeCylinder(p["seat_tap_diameter_mm"]/2., p["seat_tap_depth_mm"],
                                         App.Vector(x, y, top + 1.), App.Vector(0, 0, -1)))
    return cut.removeSplitter()


def sliding_cell_dimensions(p=None):
    """JSON-safe dimension record for the audits, the BOM and the drawing."""
    p = p or SLIDING_CELL
    pocket = sliding_cell_pocket_outline(p)
    d = json.loads(json.dumps(p))
    width = p["half_width_beam_side_mm"] + p["half_width_stem_side_mm"]
    x0, x1 = p["x_range_mm"]
    d.update({
        "holder": "V9.6 split sliding enclosure: plain block, lower half + lid + 2 covers in an 11.3 mm pocket, "
                  "one through-slot screw",
        "length_mm": x1 - x0,
        "body_size_mm": [x1 - x0, width, 2*p["half_height_mm"]],
        "cover_size_mm": [p["cover_thickness_mm"], width, 2*p["half_height_mm"]],
        "assembly_length_mm": x1 - x0 + 2*p["cover_thickness_mm"],
        "assembly_x_range_mm": [x0 - p["cover_thickness_mm"], x1 + p["cover_thickness_mm"]],
        "cell_bbox_local_mm": [-p["cell_length_mm"]/2., p["cell_length_mm"]/2., -p["cell_radius_mm"],
                               p["stem_tip_from_axis_mm"], -p["cell_radius_mm"], p["cell_radius_mm"]],
        "slot_overall_length_mm": p["slot_y_mm"][1] - p["slot_y_mm"][0] + p["slot_width_mm"],
        "slot_y_range_mm": list(p["slot_y_mm"]),
        "slot_to_cell_end_mm": p["slot_x_mm"] - p["slot_width_mm"]/2. - p["cell_length_mm"]/2.,
        "slot_to_end_face_mm": x1 - p["slot_x_mm"] - p["slot_width_mm"]/2.,
        "pocket_local_mm": list(pocket),
        "pocket_main_local_mm": list(pocket),
        "pocket_ear_local_mm": None,
        "pocket_depth_below_standard_plate_top_mm": p["half_height_mm"] - OPTICAL_HEIGHT,
        "pocket_floor_stock_mm": 25.4 - (p["half_height_mm"] - OPTICAL_HEIGHT),
        "tap_hole_diameter_mm": p["seat_tap_diameter_mm"],
        "tap_holes_local_xy_mm": sliding_cell_seat_taps(p),
        "stem_tip_inside_outer_face_mm": p["half_width_stem_side_mm"] - p["stem_tip_from_axis_mm"],
        "notes": [
            "Local frame: x along the bore and the beam, y across (sliding direction), z up; origin on the bore axis "
            "at the middle of the cell; the parting plane z = 0 is the 12.7 mm optical axis.",
            "Plain rectangular block 82 x 43.9 x 48 (x = -38 .. +44), no boss. Bore 30.4 mm = cell 25.4 + 5, through "
            "the whole length, bored with the two halves clamped together; the cell is centred in the bore by the "
            "heater/insulation (not modelled).",
            "One through slot (4.37 wide, screw centres y = 0.5 .. 11, both halves) at x = 39.3 in the bore's +x end "
            "region, 1.2 mm beyond the cell end and 2.5 mm inside the end face; it lies in the local +y half of the "
            "bore while the beam uses the centre and the local -y half, so the screw never meets the cell or the beam.",
            "Travel 10.5 mm toward local +y (board -x on the lattice board): beam through the cell centre at 0, "
            "2.2 mm inside the cell wall at 10.5; the pocket wall on that side is the travel stop (1 mm clearance). "
            "In the body frame the screw moves from y = 11 (centred) to y = 0.5 (full travel).",
            "One 8-32 x 2 in screw from the lid top through the slot of both halves into the plate tap clamps the "
            "halves and fixes the position; its head rides in the lid's 8.5 x 5 counter-slot. The pocket's end walls "
            "(2 mm clearance) keep the block square; the eight cover screws tie the halves at both ends.",
            "Stem channel 12 x 10 split 5/5 by the parting plane, through the local +y wall and open at its face: the "
            "stem tip ends 1 mm inside the face (a longer stem simply protrudes).",
            "Cable notch 6 x 6 in the lower half's parting face through the local +y wall at x = -20.",
            "Covers 8 mm thick, no beam aperture yet (to be opened later; the beam-passage audit exempts them "
            "explicitly). Cover holes at y = +17 / -14.5, z = +/-17: the +y pair clears the slot by 2.1 mm.",
            "Cover taps 16 mm deep from each end face (two in each half); 5/8 in screws through the 8 mm counterbored "
            "covers engage 12.4 mm and tie the halves together.",
        ],
    })
    return d


class SlidingCellEnclosure:
    """V9.6 split sliding Rb cell enclosure (plain block), lower half (root; the lid, covers and glass are its children)."""
    type = 'Part::FeaturePython'

    def __init__(self, obj, slide=0.0, covers=True, glass=True, lid=True):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)
        obj.ViewObject.ShapeColor = adapter_color
        obj.ViewObject.Transparency = 35
        p = SLIDING_CELL
        obj.addProperty('App::PropertyLength', 'Slide', 'Design').Slide = slide
        obj.addProperty('App::PropertyLength', 'Travel', 'Design').Travel = p["travel_mm"]
        obj.addProperty('App::PropertyLength', 'BoreRadius', 'Design').BoreRadius = p["bore_radius_mm"]
        obj.addProperty('App::PropertyLength', 'CellRadius', 'Design').CellRadius = p["cell_radius_mm"]
        obj.addProperty('App::PropertyString', 'Purpose', 'Design')
        obj.addProperty('App::PropertyString', 'DimensionsJSON', 'Design')
        self.part_numbers = ['Rb cell enclosure lower half (machined, V9.6)']
        if lid:
            _add_linked_object(obj, "Rb cell enclosure lid (upper half)", SlidingCellLid)
        if covers:
            x0, x1 = p["x_range_mm"]
            _add_linked_object(obj, "Rb cell enclosure cover +x", SlidingCellCover, pos_offset=(x1, 0, 0))
            # the -x cover is turned about Y (not Z): the block is 20.2 / 23.7 wide
            # about the axis and the hole pattern is only symmetric in z
            _add_linked_object(obj, "Rb cell enclosure cover -x", SlidingCellCover, pos_offset=(x0, 0, 0),
                               rot_offset=(0, 180, 0))
        if glass:
            _add_linked_object(obj, "Rb vapour cell GC25075-RB (envelope)", SlidingCellGlass)

    def execute(self, obj):
        obj.Shape = sliding_cell_lower_shape()

    def dumps(self): return None
    def loads(self, state): return None


class SlidingCellLid:
    """Upper half of the split enclosure (the long seat screw passes through its slot)."""
    type = 'Part::FeaturePython'

    def __init__(self, obj):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)
        obj.ViewObject.ShapeColor = adapter_color
        obj.ViewObject.Transparency = 35
        obj.addProperty('App::PropertyString', 'Purpose', 'Design')
        obj.Purpose = "V9.6 enclosure upper half; the seat screw passes through its slot and counter-slot"
        self.part_numbers = ['Rb cell enclosure lid (machined, V9.6)']

    def execute(self, obj):
        obj.Shape = sliding_cell_lid_shape()

    def dumps(self): return None
    def loads(self, state): return None


class SlidingCellCover:
    """One end cover of the sliding enclosure (four counterbored 8-32 clearance holes, no aperture yet)."""
    type = 'Part::FeaturePython'

    def __init__(self, obj):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)
        obj.ViewObject.ShapeColor = adapter_color
        obj.ViewObject.Transparency = 35
        obj.addProperty('App::PropertyString', 'Purpose', 'Design')
        obj.Purpose = "V9.6 enclosure end cover (8 mm); the beam aperture is to be machined later"
        self.part_numbers = ['Rb cell enclosure cover (machined, V9.6)']

    def execute(self, obj):
        obj.Shape = sliding_cell_cover_shape()

    def dumps(self): return None
    def loads(self, state): return None


class SlidingCellGlass:
    """Envelope of the GC25075-RB cell inside the enclosure (display and beam audit only)."""
    type = 'Part::FeaturePython'

    def __init__(self, obj):
        obj.Proxy = self
        ViewProvider(obj.ViewObject)
        obj.ViewObject.ShapeColor = glass_color
        obj.ViewObject.Transparency = 50
        self.part_numbers = ['GC25075-RB']

    def execute(self, obj):
        obj.Shape = sliding_cell_glass_shape()

    def dumps(self): return None
    def loads(self, state): return None


class SlidingCellSeat:
    """Hidden plate machining for the sliding enclosure: the pocket and its single 8-32 tap."""
    type = "Part::FeaturePython"

    def __init__(self, obj, drill=True):
        obj.Proxy = self
        keep_machining_hidden(obj)
        p = SLIDING_CELL
        obj.addProperty("App::PropertyBool", "Drill").Drill = drill
        obj.addProperty("Part::PropertyPartShape", "DrillPart")
        obj.addProperty("App::PropertyLength", "PocketDepth", "Machining").PocketDepth = p["half_height_mm"] - OPTICAL_HEIGHT
        obj.addProperty("App::PropertyLength", "CornerRadius", "Machining").CornerRadius = p["pocket_corner_radius_mm"]
        obj.addProperty("App::PropertyLength", "TapDrillDiameter", "Machining").TapDrillDiameter = p["seat_tap_diameter_mm"]
        obj.addProperty("App::PropertyString", "Thread", "Machining").Thread = "8-32 UNC through, 1 hole"
        obj.addProperty("App::PropertyString", "Purpose", "Design")
        obj.addProperty("App::PropertyString", "DimensionsJSON", "Design")

    def execute(self, obj):
        top = -obj.Baseplate.OpticsDz.Value          # plate top in the beam frame (-12.7)
        cut = sliding_cell_pocket_shape(top)
        cut.Placement = obj.Placement
        obj.DrillPart = cut if obj.Drill else Part.Shape()
        obj.Shape = Part.Shape()
        keep_machining_hidden(obj)

    def onDocumentRestored(self, obj):
        keep_machining_hidden(obj)

    def dumps(self): return None
    def loads(self, state): return None


def place_sliding_cell(bp, x, y, angle=90, slide=0.0,
                       name="Rb cell seat - 11.3 mm pocket + 1 slot tap 8-32 (V9.6 split sliding enclosure)"):
    """V9.6: the split sliding enclosure seat (plate machining) and the plain-block enclosure on it.

    ``slide`` (0 .. 10.5 mm) moves the enclosure along its local +y (board -x
    when angle = 90) so that the beam passes the cell centre (0) or runs just
    inside the cell wall (10.5). The seat - pocket and taps - never moves.
    Returns ``root`` (the seat, owner of the tap and the cut), ``cell`` (the
    lower half, with the lid, the covers and the glass envelope as its
    children), ``objects``, ``cut_object`` and ``dimensions`` for the audits.
    """
    p = SLIDING_CELL
    if not 0.0 <= slide <= p["travel_mm"] + 1e-9:
        raise ValueError("slide must be between 0 and %.2f mm" % p["travel_mm"])
    seat = bp.place_element(name, SlidingCellSeat, x=x, y=y, angle=angle)
    seat.Purpose = ("V9.6 cell seat: pocket %.1f mm deep for the split sliding enclosure (both halves, covers "
                    "and %.1f mm of travel), one 8-32 tap through the floor; the enclosure is a separate part "
                    "on it." % (p["half_height_mm"] - OPTICAL_HEIGHT, p["travel_mm"]))
    a = radians(angle)
    body = bp.place_element("Rb cell enclosure (sliding lower half, slide %.1f mm)" % slide, SlidingCellEnclosure,
                            x=x - slide*sin(a), y=y + slide*cos(a), angle=angle, slide=slide)
    body.Purpose = ("V9.6 split sliding enclosure (plain block); slide %.1f of %.1f mm along local +y (beam %.1f mm from the "
                    "cell axis)." % (slide, p["travel_mm"], slide))
    dimensions = sliding_cell_dimensions(p)
    dimensions["placement_xy_angle"] = [float(x), float(y), float(angle)]
    dimensions["slide_mm"] = float(slide)
    seat.DimensionsJSON = json.dumps(dimensions)
    body.DimensionsJSON = json.dumps(dimensions)
    seat.Document.recompute()
    objects = [seat] + descendants(body)
    return {"root": seat, "cell": body, "objects": objects, "cut_object": seat,
            "dimensions": dimensions}


# --- 4. integral AOM seat machined into the baseplate ------------------------

# Aperture centre read from the unchanged AOMO_3100_125 mesh, in its root frame.
AOM_APERTURE_LOCAL = (0.0, -0.030, -0.115)
# Bearing band in the seat frame (x along the beam, origin = central 8-32).
# It carries the fixed KM100PM back plate (x = -4.94..5.22) and the lip only;
# the moving front plate starts at x = 7.75 and must stay over the pocket.
# SEAT_X_MIN is the lower-knob pocket wall: KM100PM mesh x-min (-23.179 in the
# seat frame) - 3 mm tolerance + 17 mm knob-box offset. _geometry() re-derives
# it from the mesh and refuses to build if the two disagree by > 0.05 mm.
SEAT_X_MIN = -9.179
SEAT_X_MAX = 5.2
SEAT_X_MIN_TOLERANCE = 0.05
# KM100PM 'pill' through-cut: +x end at seat x = 35.975 + PILL_MAX_OFFSET[0]
# (5.175 mm, i.e. 0.025 mm inside the band edge, so no through-sliver remains
# in front of the band). V8 used -18 (through-cut ending at x = 17.975).
PILL_MAX_OFFSET = (-30.8, -38, 0)
# KM pocket floor relative to the lowest KM100PM mesh point (lower knob):
# V8 used +0.63 (floor at seat z = -1.24); V9 uses -0.4 (floor at -2.27).
KNOB_FLOOR_OFFSET = -0.4
# Bearing stock is limited to the existing KM100PM pocket length: the original
# 86 mm lower adapter footprint is deliberately not used by this design.
LIP_X = -7.15
LIP_Y = -15.0
LIP_WIDTH = 2.0
LIP_LENGTH = 30.0
LIP_HEIGHT = 2.0
# Request-4 plate intrusion checks confirmed the original KM100PM mesh extends
# 1.231 mm below the adapter bearing plane. The penetrating connected component
# projects to x=-4.937..5.223, y=-15.887548..15.910609 in the lower-adapter frame.
# V8/V9.1 milled a narrow, round-ended relief slot for it. V9.2 (user request,
# cheaper machining): the whole band face is cut flat at the slot's floor,
# seat z = -KM_RELIEF_DEPTH, so the boss bears on the flat face and the
# KM100PM elevation is unchanged. The constants below still describe the
# boss footprint (used by the probes); no slot is cut any more.
KM_RELIEF_DEPTH = 1.231
KM_RELIEF_X_MIN = -5.037
KM_RELIEF_WIDTH = 10.36
KM_RELIEF_Y_CENTRES = (-15.887548, 15.910609)
# V9.2: seat z of the flat screw-bearing face (former relief-slot floor).
BEARING_FACE_Z = -KM_RELIEF_DEPTH


def _descendants(root):
    result, pending, seen = [], [root], set()
    while pending:
        obj = pending.pop()
        if obj.Name in seen:
            continue
        seen.add(obj.Name)
        result.append(obj)
        pending.extend(getattr(obj, "ChildObjects", []))
    return result


def _km_bearing_relief():
    """V8/V9.1 round-ended relief slot (kept for reference; V9.2 does not cut it).

    V9.2 lowers the whole band face to the slot floor instead, see
    ``BEARING_FACE_Z``; the boss footprint constants remain valid.
    """
    radius = KM_RELIEF_WIDTH / 2
    x = KM_RELIEF_X_MIN + radius
    ya, yb = KM_RELIEF_Y_CENTRES
    height = KM_RELIEF_DEPTH + 0.01
    part = Part.makeBox(KM_RELIEF_WIDTH, yb - ya, height,
                        App.Vector(KM_RELIEF_X_MIN, ya, -KM_RELIEF_DEPTH))
    for y in (ya, yb):
        part = part.fuse(Part.makeCylinder(radius, height,
                         App.Vector(x, y, -KM_RELIEF_DEPTH)))
    return part.removeSplitter()


def seat_placement(obj):
    """Locate plate machining directly from the retained AOM assembly."""
    if "SeatRelativePlacement" in obj.PropertiesList:
        return obj.AOMRoot.Placement.multiply(obj.SeatRelativePlacement)
    # Permit opening earlier V4 documents before their explicit migration.
    return obj.Owner.Placement


def _remove_lower_adapter(seat, lower):
    """Keep numeric mounting coordinates, then delete the obsolete mesh."""
    aom, doc = seat.AOMRoot, seat.Document
    if "SeatRelativePlacement" not in seat.PropertiesList:
        if lower is None:
            raise ValueError("Cannot migrate a seat without its original location")
        seat.addProperty("App::PropertyPlacement", "SeatRelativePlacement", "Integral AOM mechanics")
        seat.SeatRelativePlacement = aom.Placement.inverse().multiply(lower.Placement)
    if "Owner" in seat.PropertiesList:
        seat.Owner = None
        seat.removeProperty("Owner")
    seat.Label = aom.Label + " - baseplate machining / integral seat"
    seat.ViewObject.Visibility = False
    seat.Proxy = IntegralAOMSeat(seat)
    if lower is None:
        return None
    if not isinstance(getattr(lower, "Proxy", None), surface_adapter_aom):
        raise ValueError("Refusing to remove a component other than the lower AOM adapter")
    name = lower.Name
    for parent in list(lower.InList):
        if hasattr(parent, "ChildObjects") and lower in parent.ChildObjects:
            parent.ChildObjects = [child for child in parent.ChildObjects if child != lower]
    if hasattr(lower, "ParentObject"):
        lower.ParentObject = None
    if lower.InList:
        raise ValueError("Unexpected remaining references to obsolete adapter: " + name
                         + " from " + repr([(p.Name, p.PropertiesList) for p in lower.InList]))
    doc.removeObject(name)
    if doc.getObject(name) is not None:
        raise RuntimeError("FreeCAD did not remove obsolete adapter: " + name)
    return name


def remove_legacy_adapters(doc):
    """Remove obsolete adapter objects and apply integral machining to existing seats."""
    removed = []
    for seat in list(doc.Objects):
        if type(getattr(seat, "Proxy", None)).__name__ != "IntegralAOMSeat":
            continue
        lower = getattr(seat, "Owner", None)
        name = _remove_lower_adapter(seat, lower)
        if name:
            removed.append(name)
        _own_aom_machining(seat)
        _update_notes(seat)
        seat.Baseplate.Proxy = _make_IntegralAOMBaseplate()(seat.Baseplate.Name)
    return removed


def _km_clearance(km, placement):
    """Original main/knob clearances, without the separate adapter's holes.

    Keep the original deep clearance under the moving portion of KM100PM.
    Bearing stock is subsequently excluded from this cutter, not added back
    to the machined plate. Dimensions are read from the unchanged KM mesh.
    """
    main = _bounding_box(
        km, 6, 0.125 * layout.inch, max_offset=PILL_MAX_OFFSET, z_tol=True)
    bounds = main.BoundBox
    main = main.fuse(Part.makeBox(
        bounds.XLength, bounds.YLength, 100,
        App.Vector(bounds.XMin, bounds.YMin, -100)))
    knobs = _bounding_box(
        km, 3, 0.125 * layout.inch, min_offset=(17, 0, KNOB_FLOOR_OFFSET))
    cut = main.fuse(knobs)
    cut.Placement = placement.inverse().multiply(km.Placement)
    return cut


def knob_pocket_wall_x(km, placement):
    """Seat-frame x of the lower-knob pocket wall, read from the KM mesh."""
    knobs = _bounding_box(
        km, 3, 0.125 * layout.inch, min_offset=(17, 0, KNOB_FLOOR_OFFSET))
    knobs.Placement = placement.inverse().multiply(km.Placement)
    return knobs.BoundBox.XMin


def _geometry(obj):
    """Return the complete assembly cutter and an empty compatibility shape."""
    plate, placement = obj.Baseplate, seat_placement(obj)
    owner_on_plate = plate.Placement.inverse().multiply(placement)
    # All board components use yaw only; support walls are parallel to board z.
    axis = owner_on_plate.Rotation.multVec(App.Vector(0, 0, 1))
    if (axis - App.Vector(0, 0, 1)).Length > 1.e-8:
        raise ValueError("Integral AOM seat requires its z axis parallel to the board")
    floor = -plate.OpticsDz.Value - plate.dz.Value - owner_on_plate.Base.z
    if floor >= 0:
        raise ValueError("AOM bearing surface is below or at the plate bottom")
    top = -plate.OpticsDz.Value - owner_on_plate.Base.z
    if top <= LIP_HEIGHT:
        raise ValueError("AOM locating lip must remain below the plate top")

    retained = _descendants(obj.AOMRoot)
    mounts = [o for o in retained
              if isinstance(getattr(o, "Proxy", None), prism_mount_km100pm_bridged)]
    if len(mounts) != 1:
        raise ValueError("Expected exactly one retained original KM100PM")
    km = mounts[0]
    cavity = _km_clearance(km, placement)
    cb = cavity.BoundBox
    # V9.1: the band starts exactly at the lower-knob pocket wall so that no
    # stock protrudes behind that wall (the former 1.3 mm sliver).
    wall = knob_pocket_wall_x(km, placement)
    if abs(wall - SEAT_X_MIN) > SEAT_X_MIN_TOLERANCE:
        raise ValueError("Knob pocket wall at seat x = %.3f disagrees with SEAT_X_MIN = %.3f"
                         % (wall, SEAT_X_MIN))
    # A rectangular bearing band remains part of the original blank. Its ends
    # stop at the main KM pocket walls; there are no projecting adapter ears.
    # V9.2: the band's top (the screw-bearing face) is one flat plane at seat
    # z = BEARING_FACE_Z (-1.231, the former relief-slot floor). The KM100PM
    # underside boss rests on it; no relief slot is milled. The locating lip
    # rises from that face to the unchanged top at z = LIP_HEIGHT.
    support = Part.makeBox(SEAT_X_MAX - wall, cb.YLength, BEARING_FACE_Z - floor,
                           App.Vector(wall, cb.YMin, floor))
    lip = Part.makeBox(LIP_WIDTH, LIP_LENGTH, LIP_HEIGHT - BEARING_FACE_Z,
                       App.Vector(LIP_X, LIP_Y, BEARING_FACE_Z))
    cavity = cavity.cut(support.fuse(lip))
    # Use only the AOM body envelope, never its two unused mounting bores at
    # local (2.5, -50) and (2.5, -60). Upper adapter geometry stays unchanged.
    for component in retained:
        if component == km:
            continue
        if isinstance(getattr(component, "Proxy", None),
                      (AOMO_3100_125, aom_adapter)):
            body = _bounding_box(component, 2, 0.125 * layout.inch)
            body.Placement = placement.inverse().multiply(component.Placement)
            cavity = cavity.fuse(body)
    central = Part.makeCylinder(TAP_DIAMETER / 2, top - floor + 2,
                                App.Vector(0, 0, top + 1), App.Vector(0, 0, -1))
    machining = cavity.fuse(central)
    machining = machining.removeSplitter()
    machining.Placement = placement
    return machining, Part.Shape()


class IntegralAOMSeat:
    """Invisible machining specification for one integral lower AOM seat."""

    def __init__(self, obj):
        obj.Proxy = self
        keep_machining_hidden(obj)

    def execute(self, obj):
        if obj.AOMRoot is None or not obj.Drill:
            obj.DrillPart = Part.Shape()
            obj.SupportPart = Part.Shape()
        else:
            obj.DrillPart, obj.SupportPart = _geometry(obj)
        obj.Shape = Part.Shape()
        # This is machining metadata, not an installed piece of hardware.
        # FreeCAD may reset an empty Part feature's visibility on recompute.
        keep_machining_hidden(obj)

    def onDocumentRestored(self, obj):
        keep_machining_hidden(obj)

    def dumps(self):
        return None

    def loads(self, state):
        return None



# ``IntegralAOMBaseplate`` subclasses ``layout.baseplate``. optomech is imported
# while layout is still executing (layout imports optomech), so the subclass
# cannot be created at import time. It is built on first access instead: a
# module __getattr__ is what FreeCAD itself uses when it restores the proxy of
# a saved document, so the name resolves exactly as a plain class would.
def _make_IntegralAOMBaseplate():
    cls = globals().get('IntegralAOMBaseplate')
    if cls is not None:
        return cls
    class IntegralAOMBaseplate(layout.baseplate):
        """Machine integral seats directly as cuts in the single baseplate."""

        def __init__(self, name):
            self.active_baseplate = name

        def execute(self, obj):
            # Upstream source is untouched, and remains responsible for every
            # ordinary component pocket, the table holes, perimeter and thickness.
            # The unchanged upstream implementation reads App.ActiveDocument.
            # Recomputing a background tab must still machine its own objects.
            for seat in obj.Document.Objects:
                if (isinstance(getattr(seat, "Proxy", None), IntegralAOMSeat)
                        and seat.Baseplate == obj):
                    _own_aom_machining(seat)
                    # Refresh before upstream execute: no stale cutter after moving
                    # an AOM and no dependence on object execution order on reopen.
                    seat.Proxy.execute(seat)
            previous = App.ActiveDocument
            if previous != obj.Document:
                App.setActiveDocument(obj.Document.Name)
            try:
                layout.baseplate.execute(self, obj)
            finally:
                if previous is not None and previous != obj.Document:
                    App.setActiveDocument(previous.Name)

        def dumps(self):
            return {"active_baseplate": self.active_baseplate}

        def loads(self, state):
            self.active_baseplate = state["active_baseplate"]


    globals()['IntegralAOMBaseplate'] = IntegralAOMBaseplate
    return IntegralAOMBaseplate


def __getattr__(name):
    if name == 'IntegralAOMBaseplate':
        cls = _make_IntegralAOMBaseplate()
        globals()[name] = cls
        return cls
    raise AttributeError(name)


def _own_aom_machining(seat):
    """Disable obsolete component cutters; their original models stay intact."""
    for component in _descendants(seat.AOMRoot):
        if hasattr(component, "Drill") and component.Drill:
            component.Drill = False


def _update_notes(seat):
    """Canonical V9 machining metadata for a newly built or migrated seat."""
    group = "V9 mechanics"
    if "MachiningNotes" not in seat.PropertiesList:
        seat.addProperty("App::PropertyString", "MachiningNotes", group)
    if "DimensionsJSON" not in seat.PropertiesList:
        seat.addProperty("App::PropertyString", "DimensionsJSON", group)
    seat.MachiningNotes = (
        "V9 direct baseplate machining: main/knob KM100PM clearances with "
        "integral central bearing stock and original 2 x 30 mm lip. "
        "V9: bearing band x = %g..%g (rear end flush with the lower-knob pocket "
        "wall, front end behind the fixed back plate, not under the moving front "
        "plate); pill through-cut ends at the band, so the former front "
        "through-slot is filled to the pocket floor; KM pocket floor "
        "lowered to seat z = %.2f for pitch clearance. "
        % (SEAT_X_MIN, SEAT_X_MAX, -31.87 + 30.0 + KNOB_FLOOR_OFFSET) +
        "V9.2: the screw-bearing face of the band is one flat plane at seat "
        "z = %.3f mm (the floor level of the former 10.36 x 42.16 mm round-ended "
        "relief slot); the slot is not milled any more. The KM100PM underside "
        "boss (x %.3f..%.3f, y %.2f..%.2f in the seat frame) bears directly on "
        "the flat face, so the KM100PM/AOM elevation is unchanged; the lip rises "
        "from the face to z = +%g. "
        % (BEARING_FACE_Z, KM_RELIEF_X_MIN, KM_RELIEF_X_MIN + KM_RELIEF_WIDTH,
           KM_RELIEF_Y_CENTRES[0], KM_RELIEF_Y_CENTRES[1], LIP_HEIGHT) +
        "The side-knob clearance floor remains below the central screw-bearing "
        "plane to preserve AOM adjustment travel. "
        "Old 21 x 86 mm projecting seat pocket omitted; both ear holes at "
        "seat y=+/-32.5 mm and unused AOM holes at (2.5,-50), (2.5,-60) omitted. "
        "Only the central 8-32 UNC through tapping bore remains. "
        "CAD shows the 3.4544 mm tap-drill bore; thread is specified, not helical. "
        "Central screw installs from above through KM100PM into the plate. "
        "No counterbore, bottom screw-head recess, added support object, "
        "or post-machining fill solid. SupportPart is empty compatibility data.")
    seat.DimensionsJSON = json.dumps({
        "revision": "V9.2",
        "construction": "direct cuts in original baseplate blank",
        "bearing_width_mm": SEAT_X_MAX - SEAT_X_MIN,
        "bearing_x_range_seat_mm": [SEAT_X_MIN, SEAT_X_MAX],
        "bearing_rear_flush_with_knob_pocket_wall": True,
        "bearing_face_seat_z_mm": BEARING_FACE_Z,
        "bearing_face_flat_no_relief_slot": True,
        "bearing_face_below_km_flat_underside_mm": KM_RELIEF_DEPTH,
        "pill_max_offset_mm": list(PILL_MAX_OFFSET),
        "front_through_slot_filled_to_pocket_floor": True,
        "knob_pocket_floor_offset_from_km_min_mm": KNOB_FLOOR_OFFSET,
        "bearing_length": "bounded by existing KM100PM pocket",
        "old_ear_pocket_removed": True,
        "lip_origin_local_mm": [LIP_X, LIP_Y, BEARING_FACE_Z],
        "lip_size_mm": [LIP_WIDTH, LIP_LENGTH, LIP_HEIGHT - BEARING_FACE_Z],
        "lip_top_seat_z_mm": LIP_HEIGHT,
        "tap_diameter_mm": TAP_DIAMETER, "thread": "8-32 UNC through",
        "hole_xy_local_mm": [[0, 0]],
        "deleted_ear_hole_xy_local_mm": [[0, -32.5], [0, 32.5]],
        "deleted_unused_hole_xy_aom_mm": [[2.5, -50], [2.5, -60]],
        "aperture_correction_local_mm": [0, 0.030, 0.115],
        "km_underside_boss_depth_mm": KM_RELIEF_DEPTH,
        "km_underside_boss_x_range_seat_mm": [KM_RELIEF_X_MIN, KM_RELIEF_X_MIN + KM_RELIEF_WIDTH],
        "km_underside_boss_y_range_seat_mm": list(KM_RELIEF_Y_CENTRES),
        "former_relief_slot_removed": True,
        "side_clearance_floor_at_bearing_plane": False,
        "central_thread_engagement_at_25_4_plate_mm": 6.984 - KM_RELIEF_DEPTH,
    })


def integrate_aom(bp, aom, align_aperture=True):
    """Create persistent integral machining and return its specification object.

    ``align_aperture=True`` shifts the entire original linked AOM assembly by
    local (0, +0.030, +0.115) mm once, so the measured aperture centre coincides
    with the original nominal root position. No optic/model dimensions change.
    Use ``optical_center(aom)`` for cat-eye distance checks after this correction.
    After all placement, call the usual redraw/recompute and plate.Drill=True;
    no one-off final solid operation is required, including after reopening.
    """
    plate = aom.Document.getObject(bp.active_baseplate)
    if aom.Baseplate != plate:
        raise ValueError("AOM and integral seat must belong to the same baseplate")
    existing = [o for o in aom.Document.Objects
                if type(getattr(o, "Proxy", None)).__name__ == "IntegralAOMSeat"
                and o.AOMRoot == aom]
    if existing:
        _remove_lower_adapter(existing[0], getattr(existing[0], "Owner", None))
        _own_aom_machining(existing[0])
        _update_notes(existing[0])
        plate.Proxy = _make_IntegralAOMBaseplate()(plate.Name)
        return existing[0]
    adapters = [o for o in _descendants(aom)
                if isinstance(getattr(o, "Proxy", None), surface_adapter_aom)]
    if len(adapters) != 1:
        raise ValueError("Expected exactly one original lower AOM surface adapter")
    lower = adapters[0]

    if "ApertureAlignmentApplied" not in aom.PropertiesList:
        aom.addProperty("App::PropertyBool", "ApertureAlignmentApplied", "V9 mechanics")
        aom.addProperty("App::PropertyVector", "MeshApertureLocal", "V9 mechanics")
        aom.MeshApertureLocal = App.Vector(*AOM_APERTURE_LOCAL)
    if align_aperture and not aom.ApertureAlignmentApplied:
        placement = aom.BasePlacement
        placement.Base += placement.Rotation.multVec(App.Vector(0, 0.030, 0.115))
        aom.BasePlacement = placement
        aom.ApertureAlignmentApplied = True
    seat = aom.Document.addObject("Part::FeaturePython", aom.Name + "_integral_seat")
    seat.addProperty("App::PropertyLinkHidden", "Baseplate").Baseplate = plate
    seat.addProperty("App::PropertyLink", "AOMRoot", "V9 mechanics").AOMRoot = aom
    seat.addProperty("App::PropertyBool", "Drill", "V9 mechanics").Drill = True
    seat.addProperty("Part::PropertyPartShape", "DrillPart", "V9 mechanics")
    seat.addProperty("Part::PropertyPartShape", "SupportPart", "V9 mechanics")
    _update_notes(seat)
    IntegralAOMSeat(seat)
    _remove_lower_adapter(seat, lower)
    _own_aom_machining(seat)
    if not isinstance(plate.Proxy, _make_IntegralAOMBaseplate()):
        plate.Proxy = _make_IntegralAOMBaseplate()(plate.Name)
    return seat


def optical_center(aom):
    """Global point at the measured centre of the original AOM mesh aperture."""
    return aom.Placement.multVec(App.Vector(*AOM_APERTURE_LOCAL))


def audit_machining(seat):
    """Probe the final plate, including removed holes and the filled ear regions.

    Intended for both isolated CAD tests and the final board audit. If unrelated
    hardware drills through a removed-hole location, this flags it for review.
    This is a material probe check; full KM mesh clearance is audited separately.
    """
    plate, placement = seat.Baseplate, seat_placement(seat)
    if not plate.Drill:
        return {"seat": seat.Name, "status": "not_checked_plate_drilling_disabled"}
    inverse = plate.Placement.inverse()
    on_plate = inverse.multiply(placement)
    floor = -plate.OpticsDz.Value - plate.dz.Value - on_plate.Base.z
    top = -plate.OpticsDz.Value - on_plate.Base.z
    checks = []
    plate_box = plate.Shape.BoundBox

    def material(name, world, expected):
        # Some legacy-adapter hole positions fall beyond the intentionally
        # open edge of this compact baseplate. There can be no stock to probe
        # there; only in-plate positions may prove that an obsolete recess was
        # filled. Do not exempt an in-plate pocket or hole from the test.
        in_stock_xy = (plate_box.XMin <= world.x <= plate_box.XMax and
                       plate_box.YMin <= world.y <= plate_box.YMax)
        if not in_stock_xy:
            checks.append({"name": name, "point_world_mm": list(world),
                           "material_expected": expected, "material_present": False,
                           "status": "not_applicable_outside_plate_xy"})
            return
        actual = plate.Shape.isInside(world, 1.e-5, False)
        checks.append({"name": name, "point_world_mm": list(world),
                       "material_expected": expected, "material_present": actual,
                       "status": "pass" if actual == expected else "fail"})

    def not_cut_by_this_seat(name, world):
        # V9.2: the obsolete ear pockets/holes are a property of THIS seat's
        # cutter, so probe the seat's own DrillPart rather than the final
        # plate: a neighbouring component's legitimate pocket (e.g. an RSP05
        # adapter 36 mm from the AOM axis) must not read as a leftover ear.
        # Plate material at the point is reported for information only.
        cut = seat.DrillPart
        cut_here = (not cut.isNull()) and cut.isInside(world, 1.e-5, False)
        in_stock_xy = (plate_box.XMin <= world.x <= plate_box.XMax and
                       plate_box.YMin <= world.y <= plate_box.YMax)
        checks.append({"name": name, "point_world_mm": list(world),
                       "cut_by_this_seat": bool(cut_here),
                       "plate_material_present": bool(plate.Shape.isInside(world, 1.e-5, False))
                       if in_stock_xy else None,
                       "status": "fail" if cut_here else "pass"})

    for y in (-39.0, 39.0):
        not_cut_by_this_seat("former_ear_recess_not_cut_" + str(y),
                             placement.multVec(App.Vector(0, y, top - 1)))
    for y in (-32.5, 32.5):
        not_cut_by_this_seat("former_ear_tap_not_cut_" + str(y),
                             placement.multVec(App.Vector(0, y, floor + 2)))
    for y in (-50.0, -60.0):
        point = seat.AOMRoot.Placement.multVec(App.Vector(2.5, y, 0))
        point.z = plate.Placement.Base.z - plate.OpticsDz.Value - plate.dz.Value / 2
        not_cut_by_this_seat("unused_AOM_tap_not_cut_" + str(y), point)
    material("central_top_installed_thread_bore_open",
             placement.multVec(App.Vector(0, 0, floor + 2)), False)
    # V9 probes (seat frame; y = -19.25 is the middle of the pill y-range).
    # V9.2: the band's top face is at BEARING_FACE_Z, so "band present" probes
    # sit 0.3 mm below that face and "no stock" probes 0.3 mm above it.
    ym = -19.25
    below = BEARING_FACE_Z - 0.3
    above = BEARING_FACE_Z + 0.3
    material("v9_front_slot_filled_at_plate_bottom",
             placement.multVec(App.Vector(14.0, ym, floor + 1)), True)
    material("v9_front_pocket_floor_lowered",
             placement.multVec(App.Vector(14.0, ym, -1.8)), False)
    material("v9_no_band_under_front_plate",
             placement.multVec(App.Vector(8.0, ym, below)), False)
    material("v9_band_present_behind_back_plate",
             placement.multVec(App.Vector(-9.0, ym, below)), True)
    # V9.1: nothing of the band remains behind the knob pocket wall (-9.18).
    material("v9_1_no_band_sliver_behind_knob_wall",
             placement.multVec(App.Vector(SEAT_X_MIN - 0.4, ym, below)), False)
    material("v9_1_band_starts_at_knob_wall",
             placement.multVec(App.Vector(SEAT_X_MIN + 0.4, ym, below)), True)
    material("v9_lower_knob_access_open",
             placement.multVec(App.Vector(-17.5, ym, floor + 1)), False)
    # V9.2: flat screw-bearing face at BEARING_FACE_Z, no relief slot, no
    # stock above the face anywhere on the band except the locating lip.
    # Probe points lie inside the KM100PM boss footprint (former slot), where
    # the cavity certainly reaches down to the band.
    for label, x, y in (("boss_y_plus", 0.0, 12.0), ("boss_y_minus", 0.0, -12.0),
                        ("boss_x_plus", 4.0, 0.0), ("boss_x_minus", -4.0, -8.0)):
        material("v9_2_no_stock_above_bearing_face_" + label,
                 placement.multVec(App.Vector(x, y, above)), False)
        material("v9_2_stock_below_bearing_face_" + label,
                 placement.multVec(App.Vector(x, y, below)), True)
    material("v9_2_lip_present_above_face",
             placement.multVec(App.Vector(LIP_X + LIP_WIDTH / 2, 0.0, 1.0)), True)
    material("v9_2_lip_continuous_down_to_face",
             placement.multVec(App.Vector(LIP_X + LIP_WIDTH / 2, 0.0, above)), True)
    disabled = all(not getattr(o, "Drill", False) for o in _descendants(seat.AOMRoot))
    return {"seat": seat.Name, "checks": checks,
            "obsolete_component_drills_disabled": disabled,
            "support_part_empty": seat.SupportPart.isNull(),
            "plate_valid": plate.Shape.isValid(), "plate_solids": len(plate.Shape.Solids),
            "status": "pass" if disabled and seat.SupportPart.isNull()
            and plate.Shape.isValid() and len(plate.Shape.Solids) == 1
            and all(c["status"] in ("pass", "not_applicable_outside_plate_xy")
                    for c in checks) else "fail"}

