﻿# coding:utf-8
"""Common objects for wizards genearting command files.
"""
import os
import os.path as osp

from aster_s.utils import Singleton


class CommFilePart(object):
    """Contract for building the command file
    """
    pattern_key = None

    def add_to(self, writer):
        """Add value to command file"""
        raise NotImplementedError


class PatternValue(CommFilePart):
    """A value filling the pattern from a key
    """

    def __init__(self, pattern_key, value):
        self.pattern_key = pattern_key
        self.value = value

    def add_to(self, writer):
        """Add the value to the command file"""
        writer.subs(self.pattern_key, str(self.value))


class ModelType(object):
    """The model type used for the modelisation
    """

    def __init__(self, aster_value, dim):
        self._aster_value = aster_value
        self.dim = dim

    def __repr__(self):
        """Return its Aster value"""
        return self._aster_value


class Modelisation(PatternValue):
    """Modelisation for defining the modele
    """

    def __init__(self, modele_type):
        PatternValue.__init__(self, "modelisation_key", modele_type)

    def give_dim(self):
        """Return the model dimension"""
        return self.value.dim


class Lines(object):
    """Lines producing a part of the command file
    """

    def __init__(self, init_idt="", idt=" " * 4):
        self.init_idt = init_idt
        self.idt = idt
        self._lines = []

    def add(self, line, idt_nb=0):
        """Add a line with an optional indentation number"""
        self._lines.append(self.init_idt + idt_nb * self.idt + line)

    def add_many(self, lines, idt_nb=0):
        """Add several lines with an optional indentation number"""
        for line in lines:
            self.add(line, idt_nb)

    def build_part(self):
        """Build a part of the command file"""
        return os.linesep.join(self._lines)


class Constraint(object):
    """A constraint contract
    """

    def add_to(self, constraints, writer):
        """Add the constraints to the list"""
        raise NotImplementedError


def quote(string):
    """Return a quoted string"""
    return "'%s'" % string


class Arg(object):
    """An argument for the arguments constraint
    """
    _pattern = "%s=%s,"

    def __init__(self, key, value):
        self.line = self._pattern % (key, value)

    def add_prefix(self, prefix):
        """Add a prefix in front of the line"""
        self.line = prefix + self.line

    def add_suffix(self, suffix):
        """Add a suffix at the end of the line"""
        self.line = self.line + suffix


class ArgsConstraint(Constraint):
    """Add several arguments A, B, C in the form:

        _F(keyA=valA,
           keyB=valB,
           keyC=valC,),

    """

    def __init__(self, args):
        self._args = args

    def add_to(self, consts, writer):
        """Add several arguments to constraint lines"""
        args = self._args
        args[0].add_prefix("_F(")
        indent = " " * 3
        for arg in args[1:]:
            arg.add_prefix(indent)
        args[-1].add_suffix("),")
        consts.lines.add_many([arg.line for arg in args], idt_nb=1)



class ConstraintSection(Constraint):
    """A section of constraints"""

    def __init__(self):
        self._consts = []

    def add(self, const):
        """Add a constraint to the section"""
        self._consts.append(const)
        return const

    def write_section(self, name, parent_consts, writer):
        """Write the section with the given name"""
        consts = self._consts
        if consts:
            lines = parent_consts.lines
            lines.add("%s=(" % name)
            for const in consts:
                const.add_to(parent_consts, writer)
            lines.add("),", idt_nb=1)


class Constraints(CommFilePart):
    """Add several constraints
    """
    pattern_key = ""

    def __init__(self):
        self._consts = []
        self.lines = None 

    def add(self, const):
        """Add a constraint"""
        self._consts.append(const)
        return const

    def write_cmd(self, init_cmd, cpl_cmd, writer):
        """Write the constraints command to the command file"""
        lines = Lines()
        self.lines = lines
        if init_cmd:
            lines.add(init_cmd + cpl_cmd)
            lines.init_idt = " " * len(init_cmd)
            for const in self._consts:
                const.add_to(self, writer)
            lines.add(");")
        writer.subs(self.pattern_key, lines.build_part())


class PatternLoader(Singleton):
    """Load command file patterns
    """

    def init(self):
        """Initialize the path where patterns are stored"""
        self._path = osp.dirname(__file__)

    def load(self, fname):
        """Load the command file pattern written in the given filename"""
        fid = open(osp.join(self._path, fname))
        pattern = fid.read()
        fid.close()
        return pattern


def load_pattern(fname):
    """Load the command file pattern written in the given filename"""
    return PatternLoader().load(fname)


class CommWriter(object):
    """The command file writter
    """
    _pattern = "BEGIN(); FIN();"

    def __init__(self):
        self._parts = []
        self._data = {}

    def use(self, part):
        """Add a building part of the command file"""
        # XXX could ensure only a given part type
        self._parts.append(part)
        return part

    def get(self, part_type):
        """Get the first part matching the given type"""
        parts = self.get_all(part_type)
        if parts:
            return parts[0]

    def get_all(self, part_type):
        """Get all the parts matching the given type"""
        parts = []
        for part in self._parts:
            if isinstance(part, part_type):
                parts.append(part)
        return parts

    def subs(self, pattern_key, bloc):
        """Replace the pattern_key by the given bloc"""
        self._data[pattern_key] = bloc

    def write(self, fname):
        """Write the command file in the given filename"""
        data = {}
        self._data = data
        for part in self._parts:
            part.add_to(self)
        fid = open(fname, "w")
        fid.write(self._pattern % data)
        fid.close()


class GrpType(object):
    """Type of group used from Aster
    """

    def __init__(self, aster_grp_type):
        self._grp_type = aster_grp_type

    def __repr__(self):
        """Return the Aster type of group"""
        return self._grp_type


ASTER_GRPS = ["GROUP_MA", "GROUP_NO"]
GRP_MA, GRP_NO = [GrpType(agrp_type) for agrp_type in ASTER_GRPS]


Mode3D = ModelType("3D", 3)
Mode3DV = Mode3D
PlaneStress = ModelType("C_PLAN", 2)
PlaneStrain = ModelType("D_PLAN", 2)
AxisSymmetric = ModelType("AXIS", 2)
Plane = ModelType("PLAN", 2)
Ele_filaire = ModelType("ELE_FIL", 1)
Ele_surface = ModelType("ELE_SURF", 2)
POU_D_E = ModelType("POU_D_E", 1)
POU_D_T = ModelType("POU_D_T", 1)
DKT = ModelType("DKT", 2)
DST = ModelType("DST", 2)
COQUE_3D = ModelType("COQUE_3D", 2)

class YoungModulus(PatternValue):
    """Young modulus for defining material
    """

    def __init__(self, value):
        PatternValue.__init__(self, "young_key", value)


class PoissonRatio(PatternValue):
    """Poisson ratio for defining material
    """

    def __init__(self, value):
        PatternValue.__init__(self, "poisson_key", value)


class Density(PatternValue):
    """Density defining material
    """

    def __init__(self, value):
        PatternValue.__init__(self, "density_key", value)


class DplFromName(ArgsConstraint):
    """Displacement boundary condition
    """
    _keys = ("DX", "DY", "DZ")

    def __init__(self, grp_type, name, dplx=None, dply=None, dplz=None):
        args = [Arg(grp_type, quote(name))]
        for key, dpl in zip(self._keys, (dplx, dply, dplz)):
            if dpl is not None:
                args.append(Arg(key, dpl))
        ArgsConstraint.__init__(self, args)

#added by zxq 
from PyQt4 import QtCore as qtc
from PyQt4 import QtGui as qt
class Analysis_Type:
     Linear_Elatic = 0
     Modal_Analysis = 1
     Linear_Thermic = 2
     Crack_Analysis = 3

class Model_Type:
     TriD = 0
     Plane = 1
     Plane_Stess = 2
     Plane_Strain = 3
     Axis_Symmetric = 4
     Euler_Beam = 5
     Timoshenko_Beam = 6
     DKT = 7
     DST = 8
     
class Group_Type:
      Invalided = 0
      Mesh_Groups = 1
      Geometry_Groups = 2
      Num_Group_Type = 3
      
class Dim_Type:#1 一维，2二维，3三维
     One_Dim = 1
     Two_Dim = 2
     Three_Dim = 3
     
class ItemData:
       def __init__(self, typename, dim, selectable, parent = None, childen = []):
           
           self.childen = childen
           if (parent):
             parent.addchild(self)
           self.name = typename
           self.dim = dim
           self.selectable = selectable
           
       def addchild(self, child):
           child.parent = self
           self.childen.append(child)
           
       def parent(self):
           return child.parent
           
           
           
class Model_Type_List:
        def __init__(self,analysis_type):
            self.itemlist = []
            self.set_analysis_type(analysis_type)
            
        def get_item(self,item_name):
            res = None
            if (item_name == "defult"):
                res = self.itemlist[0]
            else:    
                for item in self.itemlist:
                    if (item_name == item.name):
                       res = item
                    elif item.childen:
                       for childitem in item.childen:
                           if (item_name == childitem.name):
                              res = childitem
            return res
            
        def set_analysis_type(self,analysis_type):
            del self.itemlist[:]
            if (analysis_type == Analysis_Type.Linear_Elatic or analysis_type == Analysis_Type.Crack_Analysis):
               tri_itemdata = ItemData(u"3D", Dim_Type.Three_Dim, True, None, [])
               plane_stess_itemdata = ItemData(u"Plane Stess", Dim_Type.Two_Dim, True, None, [])
               plane_strain_itemdata = ItemData(u"Plane Strain", Dim_Type.Two_Dim, True, None, [])
               axis_symmetric_itemdata = ItemData(u"Axis Symmetric", Dim_Type.Two_Dim, True, None, [])
               self.itemlist.append(tri_itemdata)
               self.itemlist.append(plane_stess_itemdata)
               self.itemlist.append(plane_strain_itemdata)
               self.itemlist.append(axis_symmetric_itemdata)
                
            elif(analysis_type == Analysis_Type.Modal_Analysis):
               vol_itemdata = ItemData(u"Volumetric Elements", Dim_Type.Two_Dim, True, None, [])
               plane_stess_itemdata = ItemData(u"Plane Stess", Dim_Type.Two_Dim, True, None, [])
               plane_strain_itemdata = ItemData(u"Plane Strain", Dim_Type.Two_Dim, True, None, [])
               axis_symmetric_itemdata = ItemData(u"Axis Symmetric", Dim_Type.Two_Dim, True, None, [])
               wire_elements = ItemData(u"Wire elements", Dim_Type.One_Dim, False, None, [])
               euler_beam = ItemData(u"Euler Beam", Dim_Type.One_Dim, True, wire_elements, [])
               timoshenko_beam = ItemData(u"Timoshenko Beam", Dim_Type.One_Dim, True, wire_elements, [])
               
               plate_shell_elements = ItemData(u"Plate and shell elements", Dim_Type.One_Dim, False, None, [])
               DKT = ItemData(u"DKT (Discrete Kirchhoff Theory)", Dim_Type.Two_Dim, True, plate_shell_elements, [])
               DST = ItemData(u"DST (Discrete Shear Theory) ", Dim_Type.Two_Dim, True, plate_shell_elements, [])
               COQUE_3D = ItemData(u"Volumetric shell", Dim_Type.Two_Dim, True, plate_shell_elements, [])
               self.itemlist.append(vol_itemdata)
               self.itemlist.append(plane_stess_itemdata)
               self.itemlist.append(plane_strain_itemdata)
               self.itemlist.append(axis_symmetric_itemdata)
               self.itemlist.append(wire_elements)
               self.itemlist.append(plate_shell_elements)
               
            elif(analysis_type == Analysis_Type.Linear_Thermic):
               tri_itemdata = ItemData(u"3D", Dim_Type.Three_Dim, True, None, [])
               plane_itemdata = ItemData(u"Plane", Dim_Type.Two_Dim, True, None, [])
               self.itemlist.append(tri_itemdata)
               self.itemlist.append(plane_itemdata)
            else:
               pass
            return self.itemlist

#作为所有aster界面中组件的基类added by zxq 2017.2.17
connect = qtc.QObject.connect
class AstObject(qtc.QObject):
    def __init__(self, parent):
        qtc.QObject.__init__(self, parent)
        self.related_component = []
        connect(self, qtc.SIGNAL("dataChanged"), self.update_related_component)
    
    def reset(self):
        pass
    
    def setdata(self):
        pass
       
    def emit_datachanged(self):
        self.emit (qtc.SIGNAL("dataChanged"), self.related_component)
    
    def update_related_component(self):
        for component in self.related_component:
            component.reset()
         
    def add_related_component(self,component):
        self.related_component.append(component)
    