import os
from os import path
import sys
from sys import stderr, exit
import argparse
from re import match
from weakref import WeakKeyDictionary
from hashlib import sha224
from re import sub
import string
import pandas

# Main loader of the framework
# This contains descriptions of the elements and will parse the model.py on the provided folder location

# You should at least provide the folder location of the model you want to process. The model should be named model.py.
# The following parameters can be provided:
# --debug		print debug messages
# --dfd 		output DFD (default)
# --report		output report using the named template file (sample template file is under templates/template_sample.md
# --exclude		specify control IDs to be ignored
# --seq 		output sequential diagram
# --list		list known controls
# --describe	describe the contents of a given element


# Descriptors
# The base for this (descriptors instead of properties) has been shamelessly lifted from
# https://nbviewer.jupyter.org/urls/gist.github.com/ChrisBeaumont/5758381/raw/descriptor_writeup.ipynb
# By Chris Beaumont

class varString(object):
    # A descriptor that returns strings but won't allow writing
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
            raise ValueError(
                "expecting a String value, got a {}".format(type(value)))
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
            raise ValueError(
                "expecting a Boundary value, got a {}".format(type(value)))
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
            raise ValueError(
                "expecting a boolean value, got a {}".format(type(value)))
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
            raise ValueError(
                "expecting an integer value, got a {}".format(type(value)))
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
            raise ValueError(
                "expecting an Element (or inherited) value, got a {}".format(type(value)))
        try:
            self.data[instance]
        except (NameError, KeyError):
            self.data[instance] = value


def _setColor(element):
    if element.inScope is True:
        return "black"
    else:
        return "grey69"


def _debug(args, msg):
    if args.debug is True:
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


def addControlList(csv_file):
        # adds controls to list based on csv files in folder /controllists
        # csv files should contain following structure
        # ID;description;source;target;condition;comments
    local_dir = path.dirname(__file__)
    dict_path = 'controls'
    control_csv = os.path.join(local_dir, dict_path, csv_file)
    df = pandas.read_csv(control_csv, sep=';', index_col=0)
    # convert all headers to lowercase (just to be sure)
    df.columns = df.columns.str.lower()
    # fill NaN for source and target with default value 'Element'
    df[['source', 'target']] = df[['source', 'target']].fillna('Element')
    # remove NaN from empty comments
    df['mitigation'] = df['mitigation'].fillna('not provided')
    # convert source and target to classses
    df['source'] = df['source'].apply(lambda x: str_to_class(x))
    df['target'] = df['target'].apply(lambda x: str_to_class(x))
    # Create temporary dictionary with ID as key
    temp_dict = df.to_dict('id')
    # Update global controllist
    Controls.update(temp_dict)

# Element definitions


class SCS():
    ''' Describes the control model administratively, and holds all details during a run '''
    BagOfFlows = []
    BagOfElements = []
    BagOfControls = []
    BagOfFindings = []
    BagOfBoundaries = []
    _controlsExcluded = []
    _sf = None
    description = varString("")

    def __init__(self, name):
        self.name = name
        self._sf = SuperFormatter()
        Control.load()

    def resolve(self):
        for e in (SCS.BagOfElements):
            if e.inScope is True:
                for t in SCS.BagOfControls:
                    if t.apply(e) is True:
                        SCS.BagOfFindings.append(
                            Finding(e.name, t.description))

    def check(self):
        if self.description is None:
            raise ValueError(
                "Every control model should have at least a brief description of the system being modeled.")
        for e in (SCS.BagOfElements + SCS.BagOfFlows):
            e.check()

    def dfd(self):
        print(
            "digraph scs {\n\tgraph [\n\tfontname = Arial;\n\tfontsize = 14;\n\t]")
        print(
            "\tnode [\n\tfontname = Arial;\n\tfontsize = 14;\n\trankdir = lr;\n\t]")
        print(
            "\tedge [\n\tshape = none;\n\tfontname = Arial;\n\tfontsize = 12;\n\t]")
        print('\tlabelloc = "t";\n\tfontsize = 20;\n\tnodesep = 1;\n')
        for b in SCS.BagOfBoundaries:
            b.dfd()
        for e in SCS.BagOfElements:
            #  Boundaries draw themselves
            if type(e) != Boundary and e.inBoundary == None:
                e.dfd()
        print("}")

    def seq(self):
        print("@startuml")
        for e in SCS.BagOfElements:
            if type(e) is Actor:
                print("actor {0} as \"{1}\"".format(
                    _uniq_name(e.name), e.name))
            elif type(e) is Datastore:
                print("database {0} as \"{1}\"".format(
                    _uniq_name(e.name), e.name))
            elif type(e) is not Dataflow and type(e) is not Boundary:
                print("entity {0} as \"{1}\"".format(
                    _uniq_name(e.name), e.name))

        ordered = sorted(SCS.BagOfFlows, key=lambda flow: flow.order)
        for e in ordered:
            print("{0} -> {1}: {2}".format(_uniq_name(e.source.name),
                                           _uniq_name(e.sink.name), e.name))
            if e.note != "":
                print("note left\n{}\nend note".format(e.note))
        print("@enduml")

    def report(self, *args, **kwargs):
        with open(self._template) as file:
            template = file.read()

        print(self._sf.format(template, scs=self, dataflows=self.BagOfFlows, controls=self.BagOfControls,
                              findings=self.BagOfFindings, elements=self.BagOfElements, boundaries=self.BagOfBoundaries))

    def process(self):
        self.check()
        if args.seq is True:
            self.seq()
        if args.dfd is True:
            self.dfd()
        if args.report is not None:
            self.resolve()
            self.report()


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
                tt = Control(
                    t, Controls[t]["description"], Controls[t]["condition"], Controls[t]["target"])
                SCS.BagOfControls.append(tt)
        _debug(args, "{} control(s) loaded\n".format(len(SCS.BagOfControls)))
#        print(SCS.BagOfControls)

    def apply(self, target):
        if type(self.target) is tuple:
            if type(target) not in self.target:
                return None
        else:
            if type(target) is not self.target:
                return None
        return eval(self.condition)


class Finding():
    ''' This class represents a Finding - the element in question and a description of the finding '''

    def __init__(self, element, description):
        self.target = element
        self.description = description


class Element():
    name = varString("")
    description = varString("")
    inBoundary = varBoundary(None)
    inScope = varBool(True)

    def __init__(self, name):
        self.name = name
        SCS.BagOfElements.append(self)

    def check(self):
        return True
        ''' makes sure it is good to go '''
        # all minimum annotations are in place
        if self.description == "" or self.name == "":
            raise ValueError(
                "Element {} needs a description and a name.".format(self.name))

    def dfd(self):
        print("%s [\n\tshape = square;" % _uniq_name(self.name))
        print(
            '\tlabel = <<table border="0" cellborder="0" cellpadding="2"><tr><td><b>{0}</b></td></tr></table>>;'.format(self.name))
        print("]")


class Boundary(Element):
    def __init__(self, name):
        super().__init__(name)
        if name not in SCS.BagOfBoundaries:
            SCS.BagOfBoundaries.append(self)

    def dfd(self):
        print("subgraph cluster_{0} {{\n\tgraph [\n\t\tfontsize = 10;\n\t\tfontcolor = firebrick2;\n\t\tstyle = dashed;\n\t\tcolor = firebrick2;\n\t\tlabel = <<i>{1}</i>>;\n\t]\n".format(
            _uniq_name(self.name), self.name))
        _debug(args, "Now drawing boundary " + self.name)
        for e in SCS.BagOfElements:
            if type(e) == Boundary:
                continue  # Boundaries are not in boundaries
            if e.inBoundary == self:
                _debug(args, "Now drawing content " + e.name)
                e.dfd()
        print("\n}\n")


class Actor(Element):
    isAdmin = varBool(False)
    isTrusted = varBool(False)

    def __init__(self, name):
        super().__init__(name)

    def dfd(self):
        print("%s [\n\tshape = square;" % _uniq_name(self.name))
        print(
            '\tlabel = <<table border="0" cellborder="0" cellpadding="2"><tr><td><b>{0}</b></td></tr></table>>;'.format(self.name))
        print("]")


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
        SCS.BagOfFlows.append(self)

    def __set__(self, instance, value):
        print("Should not have gotten here.")

    def check(self):
        ''' makes sure it is good to go '''
        # all minimum annotations are in place
        # then add itself to BagOfFlows
        pass

    def dfd(self):
        print("\t{0} -> {1} [".format(_uniq_name(self.source.name),
                                      _uniq_name(self.sink.name)))
        color = _setColor(self)
        if self.order >= 0:
            print('\t\tcolor = {2};\n\t\tlabel = <<table border="0" cellborder="0" cellpadding="2"><tr><td><font color="{2}"><b>({0}) {1}</b></font></td></tr></table>>;'.format(self.order, self.name, color))
        else:
            print('\t\tcolor = {1};\n\t\tlabel = <<table border="0" cellborder="0" cellpadding="2"><tr><td><font color ="{1}"><b>{0}</b></font></td></tr></table>>;'.format(self.name, color))
        print("\t]")


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

    def dfd(self):
        color = _setColor(self)
        print("{0} [\n\tshape = circle\n\tcolor = {1}".format(
            _uniq_name(self.name), color))
        print('\tlabel = <<table border="0" cellborder="0" cellpadding="2"><tr><td><b>{}</b></td></tr></table>>;'.format(self.name))
        print("]")


class Server(System):

    def __init__(self, name):
        super().__init__(name)

    def dfd(self):
        color = _setColor(self)
        print("{0} [\n\tshape = circle\n\tcolor = {1}".format(
            _uniq_name(self.name), color))
        print('\tlabel = <<table border="0" cellborder="0" cellpadding="2"><tr><td><b>{}</b></td></tr></table>>;'.format(self.name))
        print("]")


class Lambda(System):

    def __init__(self, name):
        super().__init__(name)

    def dfd(self):
        color = _setColor(self)
        local_dir = path.dirname(__file__)
        img_path = 'images'
        img_file = 'lambda.png'
        img_source = os.path.join(local_dir, img_path, img_file)
        print('{0} [\n\tshape = none\n\tfixedsize=shape\n\timage="{2}"\n\timagescale=true\n\tcolor = {1}'.format(
            _uniq_name(self.name), color, img_source))
        print('\tlabel = <<table border="0" cellborder="0" cellpadding="2"><tr><td><b>{}</b></td></tr></table>>;'.format(self.name))
        print("]")


class ExternalEntity(System):

    def __init__(self, name):
        super().__init__(name)


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
        color = _setColor(self)
        print("{0} [\n\tshape = none;\n\tcolor = {1};".format(
            _uniq_name(self.name), color))
        print(
            '\tlabel = <<table sides="TB" cellborder="0" cellpadding="2"><tr><td><font color="{1}"><b>{0}</b></font></td></tr></table>>;'.format(self.name, color))
        print("]")


class Process(System):
    codeType = varString("Unmanaged")
    implementsCommunicationProtocol = varBool(False)
    dataType = varString("")
    tracksExecutionFlow = varBool(False)

    def __init__(self, name):
        super().__init__(name)

    def dfd(self):
        color = _setColor(self)
        print("{0} [\n\tshape = circle;\n\tcolor = {1};\n".format(
            _uniq_name(self.name), color))
        print(
            '\tlabel = <<table border="0" cellborder="0" cellpadding="2"><tr><td><font color="{1}"><b>{0}</b></font></td></tr></table>>;'.format(self.name, color))
        print("]")


class SetOfProcesses(Process):
    def __init__(self, name):
        super().__init__(name)

    def dfd(self):
        color = _setColor(self)
        print("{0} [\n\tshape = doublecircle;\n\tcolor = {1};\n".format(
            _uniq_name(self.name), color))
        print(
            '\tlabel = <<table border="0" cellborder="0" cellpadding="2"><tr><td><font color="{1}"><b>{0}</b></font></td></tr></table>>;'.format(self.name, color))
        print("]")

# Program start


# First parse arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    'folder', help='required; folder containing the model.py to process')
parser.add_argument('--file', help='alternative filename (default = model.py')
parser.add_argument('--dfd', action='store_true', help='output DFD')
parser.add_argument('--seq', action='store_true',
                    help='output sequential diagram')
parser.add_argument(
    '--report', help='output report using the specified template file')
parser.add_argument('--list', action='store_true',
                    help='list controls used in model')
parser.add_argument('--listfull', action='store_true',
                    help='same as --list but with full descriptions')
#parser.add_argument('--exclude', help='specify control IDs to be ignored')
parser.add_argument(
    '--describe', help='describe the contents of a given class (use dummy foldername)')
parser.add_argument('--debug', action='store_true',
                    help='print debug messages')

args = parser.parse_args()

if args.dfd is True and args.seq is True:
    stderr.write(
        "Cannot produce DFD and sequential diagrams in the same run.\n")
    exit(0)

if args.describe is not None:
    try:
        one_word = args.describe.split()[0]
        c = eval(one_word)
    except Exception:
        stderr.write("No such class to describe: {}\n".format(args.describe))
        exit(-1)
    print(args.describe)
    [print("\t{}".format(i))
     for i in dir(c) if not callable(i) and match("__", i) is None]
    exit(0)

# check provided folder location
model_location = args.folder
if os.path.exists(model_location) == False:
    stderr.write("Folder not found.")
    exit(-1)

# check if alternative filename is provided
if args.file is not None:
    model_name = args.file
else:
    model_name = "model.py"

# load reporting template if provided
if args.report is not None:
    SCS._template = args.report

# parse model
model_file = os.path.join(model_location, model_name)
stderr.write("Processing: {l}\n".format(l=model_file))
# try:
# 	exec(open(model_file).read())
# except Exception:
# 	stderr.write("File {m} not found.\n".format(m=model_file))
# 	exit(-1)
exec(open(model_file).read())

# list used controls in model (either in short or full description)
if args.list is True:
    for key, value in Controls.items():
        print("{i} - {d}".format(i=key, d=Controls[key]["description"]))
if args.listfull is True:
    for key, value in Controls.items():
        print("{i} - {d} \n  from\t{s} \n  to\t{t} \n  when\t{c}\n  Mitigation: {m}".format(i=key,
                                                                                            d=Controls[key]["description"], s=Controls[key]["source"], t=Controls[key]["target"], c=Controls[key]["condition"], m=Controls[key]["mitigation"]))


# FIXME BEGIN

# if args.exclude is not None:
#     TM._controlsExcluded = args.exclude.split(",")
# FIXME END
