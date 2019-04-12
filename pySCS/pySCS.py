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
    df['comments'] = df['comments'].fillna('')
    # convert source and target to classses
    # df['source'] = df['source'].apply(lambda x: str_to_class(x))
    # df['target'] = df['target'].apply(lambda x: str_to_class(x))
    # Create temporary dictionary with ID as key
    temp_dict = df.to_dict('id')
    # Update global threatlist
    Threats.update(temp_dict)

#from pytm.threats import Threats
# Initialize threatlist

# addThreatList('gdpr.csv')

# STUB - test to load model.py
exec(open("models/stub/model.py").read())

# STUB - show threat dictionary
import pprint
for key, value in Threats.items() :
    print (value)