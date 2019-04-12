# Main loader of the framework
# This contains descriptions of the elements and will parse the model.py on the provided folder location

# You should at least provide the folder location of the model you want to process. The model should be named model.py.
# The following parameters can be provided:
# --debug		print debug messages
# --dfd 		output DFD (default)
# --report		output report using the named template file (sample template file is under templates/template_sample.md
# --exclude		specify threat IDs to be ignored
# --seq 		output sequential diagram
# --list		list known threats
# --describe	describe the contents of a given element

import os
from  os import path
import sys
from sys import stderr, exit
import argparse


def str_to_class(classname):
    sumelements = []
    for item in classname.split(", "):
        sumelements.append(getattr(sys.modules[__name__], item))
    return (sumelements)

import pandas
def addThreatList(csv_file):
# adds threats to threalist based on csv files in folder /threatlists
# csv files should contain following structure
# ID;description;source;target;condition;comments
    local_dir = path.dirname(__file__)
    dict_path = 'controls'
    threat_csv = os.path.join(local_dir, dict_path, csv_file)
    df = pandas.read_csv(threat_csv, sep = ';', index_col = 0)
    # convert all headers to lowercase (just to be sure)
    df.columns = df.columns.str.lower()
    # fill NaN for source and target with default value 'Element'
    df[['source','target']] = df[['source','target']].fillna('Element')
    # remove NaN from empty comments
    df['mitigation'] = df['mitigation'].fillna('not provided')
    # convert source and target to classses
    # df['source'] = df['source'].apply(lambda x: str_to_class(x))
    # df['target'] = df['target'].apply(lambda x: str_to_class(x))
    # Create temporary dictionary with ID as key
    temp_dict = df.to_dict('id')
    # Update global threatlist
    Threats.update(temp_dict)


# Program start

# First parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('folder', help='required; folder containing the model.py to process')
parser.add_argument('--file', help='alternative filename (default = model.py')
parser.add_argument('--dfd', action='store_true', help='output DFD')
parser.add_argument('--seq', action='store_true', help='output sequential diagram')
parser.add_argument('--report', help='output report using the specified template file')
parser.add_argument('--list', action='store_true', help='list controls used in model')
parser.add_argument('--listfull', action='store_true', help='same as --list but with full descriptions')
parser.add_argument('--exclude', help='specify threat IDs to be ignored')
parser.add_argument('--describe', help='describe the contents of a given class')
parser.add_argument('--debug', action='store_true', help='print debug messages')

args = parser.parse_args()

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

# parse model
model_file = os.path.join(model_location, model_name)
print("Processing: {l}".format(l=model_file))
try:
	exec(open(model_file).read())
except Exception:
	stderr.write("Model {m} not found.".format(m=model_name))
	exit(-1)

# list used controls in model (either in short or full description)
if args.list is True:
	for key, value in Threats.items() :
		print("{i} - {d}".format(i=key, d=Threats[key]["description"]))
if args.listfull is True:
	for key, value in Threats.items() :
		print("{i} - {d} \n  from\t{s} \n  to\t{t} \n  when\t{c}\n  Mitigation: {m}".format(i=key, d=Threats[key]["description"], s=Threats[key]["source"], t=Threats[key]["target"], c=Threats[key]["condition"], m=Threats[key]["mitigation"]))

# FIXME BEGIN
# if args.dfd is True and _args.seq is True:
#     stderr.write("Cannot produce DFD and sequential diagrams in the same run.\n")
#     exit(0)
# if args.report is not None:
#     TM._template = args.report
# if args.exclude is not None:
#     TM._threatsExcluded = args.exclude.split(",")
# if args.describe is not None:
#     try:
#         one_word = args.describe.split()[0]
#         c = eval(one_word)
#     except Exception:
#         stderr.write("No such class to describe: {}\n".format(args.describe))
#         exit(-1)
#     print(args.describe)
#     [print("\t{}".format(i)) for i in dir(c) if not callable(i) and match("__", i) is None]
# FIXME END
