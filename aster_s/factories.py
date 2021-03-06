# -*- coding: utf-8 -*-
"""Factories building an Aster study case from user data or from the
Salomé study data exposed in the object browser.
"""
import os.path as osp
import os
from aster_s.utils import Factory, FactoryStore, find_factory
import aster_s.salome_tree as ST
import aster_s.astk as astk
import aster_s.study as AS
import aster_s.components as AC


class Value(Factory):
    """A value factory
    """

    def __init__(self, elt_cls=AS.Elt):
        Factory.__init__(self)
        self._elt_cls = elt_cls

    def load(self, node):
        """Load the element from a given node"""
        return self._elt_cls(node, self.compo_cls)

    def _create_elt(self, parent, name, value):
        """Create the value with its name in the object browser"""
        node = parent.node.add_node(name)
        elt = self.load(node)
        elt.line.store_type(self.compo_cls)
        elt.write_value(value)
        return elt

    def create_elt(self, parent, compo):
        """Create the value from user data"""
        return self._create_elt(parent, compo.name, compo.value)

    def copy_to(self, parent, elt):
        """Copy the value as a child of the given parent"""
        return self._create_elt(parent, elt.read_name(), elt.read_value())


class File(Factory):
    """A file factory
    """

    def __init__(self, elt_cls, sftype=ST.File):
        Factory.__init__(self)
        self._elt_cls = elt_cls
        self._sftype = sftype

    def load(self, node):
        """Load the file element from a given node"""
        sfile = self._sftype(node)
        return self._elt_cls(node, self.compo_cls, sfile)

    def _create_elt(self, parent, fname):
        """Create the file element"""
        node = parent.node.add_node(fname)
        sfile = self._sftype(node)
        sfile.store_type(self.compo_cls)
        sfile.write_fname(fname)
        return self._elt_cls(node, self.compo_cls, sfile)

    def create_elt(self, parent, compo):
        """Create the file element from user data"""
        return self._create_elt(parent, compo.fname)

    def copy_to(self, parent, felt):
        """Copy the file as a child of the given parent"""
        return self._create_elt(parent, felt.read_fname())


class Directory(Factory):
    """A directory factory
    """

    def __init__(self, name, elt_cls=AS.Directory):
        self._name = name
        self._elt_cls = elt_cls

    def load(self, node):
        """Load at the given node"""
        return self._elt_cls(node, self.compo_cls)

    def _create_elt(self, parent, dname):
        """Create the directory element in the Salomé object browser"""
        node = parent.node.add_node(self._name)
        elt = self.load(node)
        elt.line.store_type(self.compo_cls)
        elt.write_dname(dname)
        return elt

    def create_elt(self, parent, compo):
        """Create a directory element from user data"""
        return self._create_elt(parent, compo.dname)

    def copy_to(self, parent_elt, src_delt):
        """Copy the directory element as a child of the given parent"""
        return self._create_elt(parent_elt, src_delt.read_dname())


class InputData(object):
    """An input data building the Aster case.
    """

    def add_to(self, aster_case, study_case, elt):
        """Add its input data on the Aster case and may need to query
        the aster element or the study case"""
        raise NotImplementedError


class InputFile(File, InputData):
    """Input file building the Aster case
    """


class CommFile(InputFile):
    """Command file factory
    """

    def add_to(self, aster_case, study_case, felt):
        """Add the command file to the aster case"""
        aster_case.use(astk.CommFile(felt.read_fname()))


class MedFile(InputFile):
    """Med file factory
    """

    def add_to(self, aster_case, study_case, felt):
        """Add the med file to the aster case"""
        aster_case.use(astk.MedFile(felt.read_fname()))


class ExportFile(InputFile):
    """Export file factory
    """

    def add_to(self, aster_case, study_case, felt):
        """Add the command file to the aster case"""
        aster_case.load_export(felt.read_fname())


class ExportFname(InputFile):
    """The filename used for exporting the ASTK profil
    """

    def add_to(self, aster_case, study_case, felt):
        """Set the filename on the Aster case"""
        aster_case.use_fname(felt.read_fname())


class InputDirectory(Directory, InputData):
    """An input directory building the Aster case
    """


class WorkingDir(InputDirectory):
    """Working dir factory
    """

    def add_to(self, aster_case, study_case, delt):
        """Set the working directory on the aster case."""
        aster_case.use_working_dir(delt.read_dname())


class InputValue(Value, InputData):
    """An input value building the Aster case
    """

class InteractivFollowUp(InputValue):
    """Interactive follow up factory
    """

    def create_elt(self, parent, compo):
        """Create the element from user data"""
        return InputValue._create_elt(self, parent, "interactiv-follow-up", True)

    def add_to(self, aster_case, study_case, elt):
        """Add input data to Aster case"""
        aster_case.use(astk.InteractivFollowUp())


class RemoveRmed(InputValue):
    """Remove rmed file factory
    """

    def create_elt(self, parent, compo):
        """Create the element"""
        return InputValue._create_elt(self, parent, "has-rmed", True)

    def add_to(self, aster_case, study_case, elt):
        """Remove result med file from the list of results"""
        aster_case.remove(astk.RRMedFile)


class HasBaseResult(InputValue):
    """Add an ASTK base result to the Aster case results.
    """

    def create_elt(self, parent, compo):
        """Create the element"""
        return InputValue._create_elt(self, parent, "has-base-result", True)

    def add_to(self, aster_case, study_case, elt):
        """Add a base result entry to the Aster case"""
        aster_case.use(astk.Base())


class FileEntry(Factory, InputData):
    """An file entry factory
    """

    def __init__(self, src_cls, astk_type, elt_cls=AS.FileReference):
        self._src_cls = src_cls
        self._astk_type = astk_type
        self._elt_cls = elt_cls
        self._load_src_elt = FactoryStore().find(src_cls).load

    def load(self, node):
        """Load the element from a given node"""
        return self._elt_cls(node, self.compo_cls)

    def _create_elt(self, parent, src_elt):
        """Create the element from entry data"""
        node = parent.node.add_node(src_elt.read_name())
        elt = self.load(node)
        elt.line.store_type(self.compo_cls)
        elt.use_source(src_elt)
        return elt

    def create_elt(self, parent, compo):
        """Create the element from user data"""
        std = parent.give_aster_study()
        src_elt = std.load_elt_from_entry(compo.entry)
        if not issubclass(ST.load_cls(src_elt.node), self._src_cls):
            mess = "'%s' type expected for the source"
            raise TypeError(mess % self._src_cls.__name__)
        return self._create_elt(parent, src_elt)

    def copy_to(self, parent, ref_elt):
        """Copy the element as a child of the given parent"""
        src_elt = self._load_src_elt(ref_elt.node.give_source())
        return self._create_elt(parent, src_elt)

    def add_to(self, aster_case, study_case, elt):
        """Add the file to the aster case"""
        aster_case.use(self._astk_type(elt.read_fname()))


class SMeshEntry(Factory, InputData):
    """SMesh entry factory
    """
    pattern = "%s.mmed"
    _mess = "No working directory found for writting a MED file " \
            "for the '%s' mesh"

    def __init__(self, elt_cls=AS.SMeshReference):
        Factory.__init__(self)
        self._elt_cls = elt_cls

    def load(self, node):
        """Load the element from a given node"""
        mesh = ST.attach_mesh(node.give_source())
        return self._elt_cls(node, self.compo_cls, mesh)

    def _create_elt(self, parent, mesh):
        """Create the element SMesh reference from the given mesh"""
        mesh_name = mesh.read_name()
        node = parent.node.add_node(mesh_name)
        node.use_source(mesh.node)
        elt = self._elt_cls(node, self.compo_cls, mesh)
        elt.line.store_type(self.compo_cls)
        return elt

    def create_elt(self, parent, compo):
        """Create the element reference in the object browser"""
        std = parent.give_aster_study()
        mesh_node = std.sstd.build_node_from_entry(compo.entry)
        mesh = ST.attach_mesh(mesh_node)
        return self._create_elt(parent, mesh)

    def copy_to(self, parent, ref_elt):
        """Copy the element as a child of the given parent"""
        return self._create_elt(parent, ref_elt.mesh)

    def _find_working_dir(self, study_case, elt):
        """Find the working directory on the study case"""
        wdir = None
        wdir_elt = study_case.get(AC.WorkingDir)
        if wdir_elt:
            wdir = wdir_elt.read_dname()
        for compo in [AC.CommFile, AC.CommEntry]:
            comm = study_case.get(compo)
            if comm:
                wdir = osp.dirname(comm.read_fname())
                break
        if wdir is None:
            raise ValueError(self._mess % elt.read_name())
        return wdir

    def add_to(self, aster_case, study_case, elt):
        """Add the mesh to the aster case"""
        wdir = self._find_working_dir(study_case, elt)
        med_fname = osp.join(wdir, self.pattern % study_case.read_name())
        elt.mesh.dump_to(med_fname)
        aster_case.use(astk.MedFile(med_fname))


class AstkProfil(Factory, InputData):
    """Astk profil factory
    """

    def __init__(self, elt_cls=AS.AstkProfil):
        Factory.__init__(self)
        self._elt_cls = elt_cls

    def load(self, node):
        """Does nothing"""
        return self._elt_cls(node, self.compo_cls)

    def create_elt(self, parent, compo):
        """Create an element in the Salomé tree but keep the profil
        in Python memory"""
        node = parent.node.add_node("profil")
        elt = self._elt_cls(node, self.compo_cls)
        elt.line.store_type(self.compo_cls)
        elt.store_profil(compo.profil)
        return elt

    def copy_to(self, parent, elt):
        """Does nothing"""
        raise NotImplementedError

    def add_to(self, aster_case, study_case, elt):
        """Set the Astk profil on the Aster case"""
        aster_case.use_profil(elt.load_profil())


class JobId(Value):
    """Job id factory
    """

    def create_elt(self, parent, compo):
        """Create the element"""
        return Value._create_elt(self, parent, "job-id", compo.pid)


class OutputData(object):
    """Contract for a result
    """

    def create_elt_from(self, aster_case, parent_elt):
        """Create the element from the aster case and the parent element
        """
        raise NotImplementedError


class ResultFile(File, OutputData):
    """A result file factory
    """

    def __init__(self, astk_type, elt_cls, sftype=ST.File):
        self._astk_type = astk_type
        File.__init__(self, elt_cls, sftype)

    def create_elt_from(self, aster_case, parent):
        """Create element from the aster case"""
        res = aster_case.get_result(self._astk_type)
        if res:
            return self._create_elt(parent, res.fname)


class ResultDirectory(Directory, OutputData):
    """A result directory factory
    """

    def __init__(self, name, astk_type, elt_cls=AS.Directory):
        self._astk_type = astk_type
        Directory.__init__(self, name, elt_cls)

    def create_elt_from(self, aster_case, parent):
        """Create element from the aster case"""
        res = aster_case.get_result(self._astk_type)
        if res:
            return self._create_elt(parent, res.dname)


class VisuMedFile(ResultFile):
    """A med file seen in the VISU component
    """

    def __init__(self, astk_type, elt_cls, sftype=ST.VisuMedFile):
        ResultFile.__init__(self, astk_type, elt_cls, sftype)

    def create_elt_from(self, aster_case, parent):
        """Create element from the aster case and display the result in
        VISU component"""
        elt = ResultFile.create_elt_from(self, aster_case, parent)
        if elt:
            elt.sfile.show()
        return elt


class Section(Factory):
    """A section factory
    """

    def __init__(self, elt_cls):
        self._elt_cls = elt_cls

    def load(self, node):
        """Load the element from a given node"""
        return self._elt_cls(node, self.compo_cls)

    def _create_elt(self, parent_elt, name):
        """Create the section element"""
        node = parent_elt.node.add_node(name)
        elt = self.load(node)
        elt.line.store_type(self.compo_cls)
        return elt

    def create_elt(self, parent_elt, compo):
        """Create the section"""
        return self._create_elt(parent_elt, compo.name)

    def copy_to(self, parent_elt, src_elt):
        """Copy the section"""
        copy_elt = self._create_elt(parent_elt, src_elt.read_name())
        for elt in src_elt.get_all_elts():
            elt.copy_to(copy_elt)
        return copy_elt


class AstkParams(Section):
    """Astk parameters section
    """

    def __init__(self, elt_cls=AS.AstkParams):
        Section.__init__(self, elt_cls)

    def create_elt(self, parent_elt, compo):
        """Create the section"""
        elt = Section._create_elt(self, parent_elt, compo.name)
        elt.attach_cfg(compo.cfg)
        return elt

    def copy_to(self, parent_elt, src_elt):
        """Copy the section"""
        copy_elt = Section.copy_to(self, parent_elt, src_elt)
        copy_elt.attach_cfg(src_elt.get_cfg())
        return copy_elt


class ResultsSection(Section):
    """Results section factory
    """

    def __init__(self, res_types, elt_cls=AS.ResultsSection):
        Section.__init__(self, elt_cls)
        self.result_types = res_types

    def display_from(self, aster_case, elt):
        """Find results on the Aster study case (astk.Case)"""
        for rtype in self.result_types:
            find_factory(rtype).create_elt_from(aster_case, elt)


class Case(Section):
    """A case factory
    """

    def __init__(self, inputs, outputs, elt_cls):
        Section.__init__(self, elt_cls)
        self._inputs = inputs
        self._outputs = outputs

    def load(self, node):
        """Load the case from the given node"""
        elt = self._elt_cls(node, self.compo_cls, self._inputs, self._outputs)
        elt.data = elt.get(AC.DataSection)
        elt.results = elt.get(AC.ResultsSection)
        return elt

    def create_elt(self, parent, compo):
        """Create the case element"""
        elt = Section._create_elt(self, parent, compo.name)
        elt.data = AC.DataSection().build(elt)
        return elt

    def copy_to(self, parent_elt, src_elt):
        """Copy the case"""
        name = src_elt.read_name() + "-copy"
        copy_nb = src_elt.line.load_attr("copy_nb") or 0
        if copy_nb:
            name += "%i" % copy_nb
        copy_nb += 1
        src_elt.line.store_attr("copy_nb", copy_nb)

        copy = Section._create_elt(self, parent_elt, name)
        for elt in src_elt.get_all_elts():
            elt.copy_to(copy)

        copy.data = copy.get(AC.DataSection)
        copy.results = copy.get(AC.ResultsSection)
        return copy


class FromComm(Case):
    """A case factory from command file
    """

    def __init__(self, inputs, outputs):
        Case.__init__(self, inputs, outputs, AS.FromComm)

    def load(self, node):
        """Load the case from the given node"""
        elt = Case.load(self, node)
        elt.params = elt.get(AC.AstkParams)
        return elt

    def create_elt(self, parent, compo):
        """Create case element"""
        elt = Case.create_elt(self, parent, compo)
        elt.params = AC.AstkParams(astk.build_default_cfg()).build(elt)
        elt.write_name(compo.name)
        return elt

    def copy_to(self, parent_elt, src_elt):
        """Copy the case"""
        copy = Case.copy_to(self, parent_elt, src_elt)
        copy.params = copy.get(AC.AstkParams)
        return copy


def register_all():
    """Register all the factories"""
    reg = FactoryStore().register

    reg(AC.CommFile, CommFile(AS.File))
    reg(AC.MedFile, MedFile(AS.File))
    reg(AC.ExportFile, ExportFile(AS.File))
    reg(AC.ExportFname, ExportFname(AS.File))

    reg(AC.WorkingDir, WorkingDir("working-dir"))
    reg(AC.RemoveRmed, RemoveRmed())
    reg(AC.HasBaseResult, HasBaseResult())
    reg(AC.InteractivFollowUp, InteractivFollowUp())
    reg(AC.Value, Value())

    reg(AC.CommEntry, FileEntry(AC.CommFile, astk.CommFile))
    reg(AC.MedEntry, FileEntry(AC.MedFile, astk.MedFile))
    reg(AC.SMeshEntry, SMeshEntry())

    reg(AC.AstkProfil, AstkProfil())

    reg(AC.DataSection, Section(AS.DataSection))
    reg(AC.AstkParams, AstkParams())
    outputs = (
        AC.MessFile,
        AC.ResuFile,
        AC.RMedFile,
        AC.BaseResult,
        )
    reg(AC.ResultsSection, ResultsSection(outputs))

    reg(AC.JobId, JobId())
    reg(AC.MessFile, ResultFile(astk.MessFile, AS.File))
    reg(AC.ResuFile, ResultFile(astk.ResuFile, AS.File))
    reg(AC.RMedFile, VisuMedFile(astk.RMedFile, AS.File))
    reg(AC.BaseResult, ResultDirectory("base-result", astk.BaseResult))

    inputs = (
        AC.CommFile,
        AC.CommEntry,
        AC.MedFile,
        AC.MedEntry,
        AC.SMeshEntry,
        AC.WorkingDir,
        AC.RemoveRmed,
        AC.HasBaseResult,
        AC.InteractivFollowUp,
    )
    reg(AC.FromComm, FromComm(inputs, outputs))

    inputs = (
        AC.ExportFile,
    )
    reg(AC.FromExport, Case(inputs, outputs, AS.FromExport))

    inputs = (
        AC.AstkProfil,
        AC.ExportFname,
    )
    reg(AC.FromProfil, Case(inputs, outputs, AS.FromProfil))

