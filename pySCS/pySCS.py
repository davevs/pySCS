import os
from  os import path
import sys
from sys import stderr, exit
import argparse
from re import match
from weakref import WeakKeyDictionary
from hashlib import sha224
from re import sub
import string
import pandas
import pydot

# Descriptors
# The base for this (descriptors instead of properties) has been shamelessly lifted from    
# https://nbviewer.jupyter.org/urls/gist.github.com/ChrisBeaumont/5758381/raw/descriptor_writeup.ipynb
# By Chris Beaumont

class varString(object):
    #A descriptor that returns strings but won't allow writing
    def __init__(self, default):
        self.default = default
        self.data = WeakKeyDictionary()

    def __get__(self, instance, owner):
        # when x.d is called we get here
        # instance = x
        # owner = type(x)
        return self.data.get(instance, self.default)

    def __set__(self, instance, value):
        # called when x.d = val
        # instance = x
        # value = val
        if not isinstance(value, str):
            raise ValueError("expecting a String value, got a {}".format(type(value)))
        try:
            self.data[instance]
        except (NameError, KeyError):
            self.data[instance] = value

class varBoundary(object):
    def __init__(self, default):
        self.default = default
        self.data = WeakKeyDictionary()

    def __get__(self, instance, owner):
        return self.data.get(instance, self.default)

    def __set__(self, instance, value):
        if not isinstance(value, Boundary):
            raise ValueError("expecting a Boundary value, got a {}".format(type(value)))
        try:
            self.data[instance]
        except (NameError, KeyError):
            self.data[instance] = value

class varBool(object):
    def __init__(self, default):
        self.default = default
        self.data = WeakKeyDictionary()

    def __get__(self, instance, owner):
        return self.data.get(instance, self.default)

    def __set__(self, instance, value):
        if not isinstance(value, bool):
            raise ValueError("expecting a boolean value, got a {}".format(type(value)))
        try:
            self.data[instance]
        except (NameError, KeyError):
            self.data[instance] = value

class varInt(object):
    def __init__(self, default):
        self.default = default
        self.data = WeakKeyDictionary()

    def __get__(self, instance, owner):
        return self.data.get(instance, self.default)

    def __set__(self, instance, value):
        if not isinstance(value, int):
            raise ValueError("expecting an integer value, got a {}".format(type(value)))
        try:
            self.data[instance]
        except (NameError, KeyError):
            self.data[instance] = value

class varElement(object):
    def __init__(self, default):
        self.default = default
        self.data = WeakKeyDictionary()

    def __get__(self, instance, owner):
        return self.data.get(instance, self.default)

    def __set__(self, instance, value):
        if not isinstance(value, Element):
            raise ValueError("expecting an Element (or inherited) value, got a {}".format(type(value)))
        try:
            self.data[instance]
        except (NameError, KeyError):
            self.data[instance] = value

def _setColor(element):
    if element.inScope is True:
        return "black"
    else:
        return "grey69"

def _debug(_args, msg):
    if _args.debug is True:
        stderr.write("DEBUG: {}\n".format(msg))

def _uniq_name(s):
    ''' transform name in a unique(?) string '''
    h = sha224(s.encode('utf-8')).hexdigest()
    return sub(r'[0-9]', '', h)

# World's simplest Template engine.
# shamelessly lifted from https://makina-corpus.com/blog/metier/2016/the-worlds-simplest-python-template-engine
class SuperFormatter(string.Formatter):

    def format_field(self, value, spec):
        if spec.startswith('repeat'):
            template = spec.partition(':')[-1]
            if type(value) is dict:
                value = value.items()
            return ''.join([template.format(item=item) for item in value])
        elif spec == 'call':
            return value()
        elif spec.startswith('if'):
            return (value and spec.partition(':')[-1]) or ''
        else:
            return super(SuperFormatter, self).format_field(value, spec)

# csv parsers
def str_to_class(classname):
    sumelements = []
    for item in classname.split(", "):
        sumelements.append(getattr(sys.modules[__name__], item))
    return (sumelements)

def import_control_list(csv_file):
	# adds controls to list based on csv files in folder /controllists
	# csv files should contain following structure
	# ID;description;source;target;condition;comments
    local_dir = path.dirname(__file__)
    dict_path = 'controls'
    control_csv = os.path.join(local_dir, dict_path, csv_file)
    df = pandas.read_csv(control_csv, sep = ';', index_col = 0)
    # convert all headers to lowercase (just to be sure)
    df.columns = df.columns.str.lower()
    # fill NaN for source and target with default value 'Any'
    df[['source','target']] = df[['source','target']].fillna('Any')
    # remove NaN from empty comments
    df['mitigation'] = df['mitigation'].fillna('not provided')
    # convert source and target to classses
    df['source'] = df['source'].apply(lambda x: str_to_class(x))
    df['target'] = df['target'].apply(lambda x: str_to_class(x))
    # Create temporary dictionary with ID as key
    temp_dict = df.to_dict('id')
    # Update global controllist
    Controls.update(temp_dict)
    _debug(_args, Controls)


# DFD creation functions
def initialize_dfd():
    global dfd_in_progress
    global boundary_dfd

    # graph properties
    dip_name = "DFD"
    dip_graph_type = "digraph"
    dip_labelloc = "t"
    dip_nodesep = "1"
    dip_font = "Arial"
    dip_font_size = "20"

    # default node properties
    dip_font_node = "Arial"
    dip_font_node_size = "14"
    dip_node_rank = "LR"

    # default edge properties
    dip_font_edge = "Arial"
    dip_font_edge_size = "12"
    dip_edge_shape_default = "none"        

    # create graph
    dfd_in_progress = pydot.Dot(name=dip_name, graph_type=dip_graph_type, labelloc = dip_labelloc, nodesep = dip_nodesep)
    dfd_in_progress.set_graph_defaults(fontname = dip_font, fontsize = dip_font_size)
    dfd_in_progress.set_node_defaults(fontname = dip_font_node, fontsize = dip_font_node_size, rankdir = dip_node_rank)
    dfd_in_progress.set_edge_defaults(shape = dip_edge_shape_default, fontname = dip_font_edge, fontsize = dip_font_edge_size)

    boundary_dfd = {}


def add_boundary_to_dfd(element):
    if type(element) == Boundary:
        boundary_label = element.name
        boundary_id = _uniq_name(element.name) 
        _debug(_args, "Adding boundary {b} with id {i} to dfd".format(b=boundary_label, i=boundary_id))
        boundary_dfd[boundary_id] = pydot.Cluster(boundary_id, label=boundary_label, style = "dashed", color = "firebrick2", fontsize="10", fontcolor="firebrick2", fontname="Arial italic")
        dfd_in_progress.add_subgraph(boundary_dfd[boundary_id])

def add_element_to_dfd(element, color="black", shape="none", fontname="Arial", fontsize="14", rank=""):
    if type(element) != Boundary:
        if element.inBoundary != None:
            # determine boundary to add element to
            boundary_id = _uniq_name(element.inBoundary.name) 
            _debug(_args, "Adding element {e} to boundary {b}".format(e=element.name, b=boundary_id))
            node_id = _uniq_name(element.name)
            node_to_add = pydot.Node(node_id, label=element.name, shape=shape, color=color, fontname=fontname, fontsize=fontsize, rank=rank)
            # boundary_to_use = boundary_dfd[boundary_id]
            boundary_dfd[boundary_id].add_node(node_to_add)
            _debug(_args, "Node {n} added to boundary {b}".format(n=node_to_add, b=boundary_dfd[boundary_id]))
        else:
            # elements without boundary are just added to the dfd
            _debug(_args, "Adding element {e} to dfd".format(e=element.name))
            node_id = _uniq_name(element.name)
            node_to_add = pydot.Node(node_id, label=element.name, shape=shape, color=color, fontname=fontname, fontsize=fontsize, rank=rank)
            dfd_in_progress.add_node(node_to_add)
            _debug(_args, "Node {n} added DFD".format(n=node_to_add))

def add_dataflow_to_dfd(description, source, sink):
    source_id = _uniq_name(source)
    sink_id = _uniq_name(sink)
    dataflow_to_add = pydot.Edge(source_id, sink_id, label=description)
    dfd_in_progress.add_edge(dataflow_to_add)


# Element definitions

class SCS():
    # Describes the control model administratively, and holds all details during a run
    ListOfFlows = []
    ListOfElements = []
    ListOfControls = []
    ListOfFindings = []
    ListOfBoundaries = []
    _controlsExcluded = []
    _sf = None
    description = varString("")

    def __init__(self, name):
        self.name = name
        self._sf = SuperFormatter()
        Control.load()

    def process(self):
        self.check()
        # don't create a dfd, seq diagram, and report if we just want to have the list of controls
        if _args.list is False and _args.listfull is False:
            self.dfd()
        if _args.seq is True:
            self.seq()
        if _args.report is not None:
            self.resolve()
            self.report()


    def check(self):
        if self.description is None:
            raise ValueError("Every control model should have at least a brief description of the system being modeled.")
        for e in (SCS.ListOfElements + SCS.ListOfFlows):
            e.check()

    def dfd(self):
        for e in SCS.ListOfElements:
            e.dfd()

    def seq(self):
        print("@startuml")
        for e in SCS.ListOfElements:
            if type(e) is Actor:
                print("actor {0} as \"{1}\"".format(_uniq_name(e.name), e.name))
            elif type(e) is Datastore:
                print("database {0} as \"{1}\"".format(_uniq_name(e.name), e.name))
            elif type(e) is not Dataflow and type(e) is not Boundary:
                print("entity {0} as \"{1}\"".format(_uniq_name(e.name), e.name))

        ordered = sorted(SCS.ListOfFlows, key=lambda flow: flow.order)
        for e in ordered:
            print("{0} -> {1}: {2}".format(_uniq_name(e.source.name), _uniq_name(e.sink.name), e.name))
            if e.note != "":
                print("note left\n{}\nend note".format(e.note))
        print("@enduml")

    def report(self, *_args, **kwargs):
        with open(self._template) as file:
            template = file.read()

        print(self._sf.format(template, scs=self, dataflows=self.ListOfFlows, controls=self.ListOfControls, findings=self.ListOfFindings, elements=self.ListOfElements, boundaries=self.ListOfBoundaries))

    def resolve(self):
        for e in (SCS.ListOfElements):
            _debug(_args, "Scope for {}: {}".format(e, e.inScope))
            if e.inScope is True:
                for t in SCS.ListOfControls:
                    if t.apply(e) is True:
                        SCS.ListOfFindings.append(Finding(e.name, t.description))


class Control():
    id = varString("")
    description = varString("")
    condition = varString("")
    target = ()

    ''' Represents a possible control '''
    def __init__(self, id, description, condition, target):
        self.id = id
        self.description = description
        self.condition = condition
        self.target = target

    @classmethod
    def load(self):
        for t in Controls.keys():
            if t not in SCS._controlsExcluded:
                tt = Control(t, Controls[t]["description"], Controls[t]["condition"], Controls[t]["target"])
                SCS.ListOfControls.append(tt)
        _debug(_args, "{} control(s) loaded\n".format(len(SCS.ListOfControls)))
#        print(SCS.ListOfControls)

    def apply(self, target):
        _debug(_args, "Type detected: {}".format(type(self.target)))
        if type(self.target) is tuple:
            # This branch is never used
            if type(target) not in self.target:
                return None
        else:
            # changed this to tuple evaluation to get it to work. No clue why ....
            # if type(target) is not self.target:
            if type(target) not in self.target:
                return None
            _debug(_args, "Target type: {}".format(type(target)))
            _debug(_args, "Self type: {}".format(self.target))
            _debug(_args, "Evaluation: {}".format(type(target) not in self.target))
            _debug(_args, "Condition eval {}".format(eval(self.condition)))
        return eval(self.condition)


class Element():
    name = varString("")
    description = varString("")
    inBoundary = varBoundary(None)
    inScope = varBool(True)

    def __init__(self, name):
        self.name = name
        SCS.ListOfElements.append(self)
        _debug(_args, "Element {} of type {} loaded\n".format(self.name, type(self)))

    def check(self):
        return True
        ''' makes sure it is good to go '''
        # all minimum annotations are in place
        if self.description == "" or self.name == "":
            raise ValueError("Element {} needs a description and a name.".format(self.name))

    def dfd(self):
        add_element_to_dfd(self)


class Actor(Element):
    isAdmin = varBool(False)
    isTrusted = varBool(False)

    def __init__(self, name):
        super().__init__(name)

    def dfd(self):
        add_element_to_dfd(self, shape="square")


class Any(Element):
    # Dummy element; necessary for add_control_to_list
    def __init__(self, name):
        super().__init__(name)


class System(Element):
    OS = varString("")
    runsAsRoot = varBool(False)
    onAWS = varBool(False)
    isHardened = varBool(False)
    isResilient = varBool(False)
    handlesResources = varBool(False)
    handlesResourceConsumption = varBool(False)
    definesConnectionTimeout = varBool(False)
    handlesInterruptions = varBool(False)
    handlesCrashes = varBool(False)
    hasAccessControl = varBool(False)
    implementsAuthenticationScheme = varBool(False)
    authenticationScheme = varString("")
    authenticatesSource = varBool(False)
    authenticatesDestination = varBool(False)
    authorizesSource = varBool(False)
    providesConfidentiality = varBool(False)
    providesIntegrity = varBool(False)
    sanitizesInput = varBool(False)
    encodesOutput = varBool(False)
    implementsNonce = varBool(False)
    implementsCSRFToken = varBool(False)

    def __init__(self, name):
        super().__init__(name)


class Server(System):

    def __init__(self, name):
        super().__init__(name)

    def dfd(self):
        add_element_to_dfd(self, shape="square")

class Lambda(System):

    def __init__(self, name):
        super().__init__(name)

    def dfd(self):
        add_element_to_dfd(self, shape="Mcircle")


class ExternalEntity(System):

    def __init__(self, name):
        super().__init__(name)

    def dfd(self):
        add_element_to_dfd(self, shape="underline")


class Datastore(System):
    onRDS = varBool(False)
    storesLogData = varBool(False)
    storesPII = varBool(False)
    storesSensitiveData = varBool(False)
    isEncrypted = varBool(False)
    isSQL = varBool(True)
    isShared = varBool(False)
    hasWriteAccess = varBool(False)

    def __init__(self, name):
        super().__init__(name)

    def dfd(self):
        add_element_to_dfd(self, shape="none")


class Process(System):
    codeType = varString("Unmanaged")
    implementsCommunicationProtocol = varBool(False)
    dataType = varString("")
    tracksExecutionFlow = varBool(False)

    def __init__(self, name):
        super().__init__(name)

    def dfd(self):
        add_element_to_dfd(self, shape="circle")


class SetOfProcesses(Process):
    def __init__(self, name):
        super().__init__(name)

    def dfd(self):
        add_element_to_dfd(self, shape="doublecircle")


class Dataflow(Element):
    source = varElement(None)
    sink = varElement(None)
    data = varString("")
    protocol = varString("")
    dstPort = varInt(0)
    authenticatedWith = varBool(False)
    order = varInt(-1)
    implementsCommunicationProtocol = varBool(False)
    isEncrypted = varBool(False)
    note = varString("")

    def __init__(self, source, sink, name):
        self.source = source
        self.sink = sink
        self.name = name
        super().__init__(name)
        SCS.ListOfFlows.append(self)

    def __set__(self, instance, value):
        print("Should not have gotten here.")

    def check(self):
        ''' makes sure it is good to go '''
        # all minimum annotations are in place
        # then add itself to ListOfFlows
        pass

    def dfd(self):
        # TODO: add order 
        add_dataflow_to_dfd(self.name, self.source.name, self.sink.name)


class Boundary(Element):
    def __init__(self, name):
        super().__init__(name)
        if name not in SCS.ListOfBoundaries:
            SCS.ListOfBoundaries.append(self)

    def dfd(self):
        _debug(_args, "Found boundary " + self.name)
        add_boundary_to_dfd(self)


class Finding():
    ''' This class represents a Finding - the element in question and a description of the finding '''
    def __init__(self, element, description):
        self.target = element
        self.description = description


# Program start
# Initialize global variables
Controls = {}

# initialize dfd
initialize_dfd()

# First parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('folder', help='required; folder containing the model.py to process')
parser.add_argument('--file', help='alternative filename (default = model.py')
# parser.add_argument('--dfd', action='store_true', help='output DFD')
parser.add_argument('--seq', action='store_true', help='output sequential diagram')
parser.add_argument('--report', help='output report using the specified template file')
parser.add_argument('--list', action='store_true', help='list controls used in model')
parser.add_argument('--listfull', action='store_true', help='same as --list but with full descriptions')
#parser.add_argument('--exclude', help='specify control IDs to be ignored')
parser.add_argument('--describe', help='describe the contents of a given class (use dummy foldername)')
parser.add_argument('--debug', action='store_true', help='print debug messages')

_args = parser.parse_args()

if _args.describe is not None:
    try:
        one_word = _args.describe.split()[0]
        c = eval(one_word)
    except Exception:
        stderr.write("No such class to describe: {}\n".format(_args.describe))
        exit(-1)
    print(_args.describe)
    [print("\t{}".format(i)) for i in dir(c) if not callable(i) and match("__", i) is None]
    exit(0)
# check provided folder location
model_location = _args.folder
if os.path.exists(model_location) == False:
	stderr.write("Folder not found.")
	exit(-1)	

# check if alternative filename is provided
if _args.file is not None:
	model_name = _args.file
else:
	model_name = "model.py"

# load reporting template if provided
if _args.report is not None:
	SCS._template = _args.report

# parse model
model_file = os.path.join(model_location, model_name)
stderr.write("Processing: {l}\n".format(l=model_file))
exec(open(model_file).read())

# list used controls in model (either in short or full description)
if _args.list is True:
    for key, value in Controls.items() :
        print("{i} - {d}".format(i=key, d=Controls[key]["description"]))
    exit(0)
if _args.listfull is True:
    for key, value in Controls.items() :
        print("{i} - {d} \n  from\t{s} \n  to\t{t} \n  when\t{c}\n  Mitigation: {m}".format(i=key, d=Controls[key]["description"], s=Controls[key]["source"], t=Controls[key]["target"], c=Controls[key]["condition"], m=Controls[key]["mitigation"]))
    exit(0)

# Write output files
dfd_name = "dfd.png"
dfd_file = os.path.join(model_location, dfd_name)
dfd_in_progress.write_png(dfd_file)

#DEBUG SECTION
_debug(_args, "DFD generated:\n")
_debug(_args, "{}".format(dfd_in_progress))

import webbrowser
webbrowser.open(dfd_file)
# FIXME BEGIN

# if _args.exclude is not None:
#     TM._controlsExcluded = _args.exclude.split(",")
# FIXME END