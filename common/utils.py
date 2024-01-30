#!python3

import os, re
import json, yaml, csv, datetime
# from bson import ObjectId
from importlib import import_module

# from .config import TEMP_FOLDER,CONNECTOR_MAP

class bJSONEncoder(json.JSONEncoder):

    def default(self,o):
        # if isinstance(o,ObjectId):
        #     return str(o)
        # return 
        json.JSONEncoder.default(self,o)

# def json_dump(dictData,schema,name):

#     now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
#     filename = "{}_{}-{}.json".format(now,schema,name)
#     filepath = os.path.join(TEMP_FOLDER,filename)

#     encoded_json = bJSONEncoder().encode(dictData)
#     loaded_json = json.loads(encoded_json)
#     with open(filepath,"w") as f:
#         json.dump(loaded_json,f)

#     return filepath

# def csv_dump(dictData,schema,name):

#     now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
#     filename = "{}_{}-{}.csv".format(now,schema,name)
#     filepath = os.path.join(TEMP_FOLDER,filename)

#     fieldnameset = set()

#     for i in range(0,min(1000,len(dictData))):
#         fieldset = set(dictData[i].keys())
#         fieldnameset |= fieldset
    
#     fieldnames = sorted(list(fieldnameset), key=str.lower)
#     print("FIELDNAMES: {}".format(fieldnames))

#     with open(filepath,"w") as f:
#         writer = csv.DictWriter(f,fieldnames=fieldnames)
#         writer.writeheader()
#         writer.writerows(dictData)

#     return filepath

# def get_client(source, **kwargs):

#     # get the names from config
#     connector_name = CONNECTOR_MAP[source]["connector"]
#     client_name = CONNECTOR_MAP[source]["client"]

#     # import the right connector
#     connector = import_module(connector_name)

#     # instantiate a connector client
#     client_class = getattr(connector,client_name)
#     client = client_class(**kwargs)

#     return client

class FileHandler():

    def __init__(self,input_folder=".",output_folder=".",**kwargs):
        
        self.input_folder = os.path.abspath(input_folder)
        self.output_folder = os.path.abspath(output_folder)

        
    def load_json(self,name,subpath=None,input=None):
        """Simply Loads a JSON file and passes the result as a dict"""

        dict_data = {}

        input_folder = (input if input else self.input_folder)
        folder = (os.path.join(input_folder,subpath) if subpath else input_folder)
    
        json_ext = re.compile('(\.json)$')
        if re.search(json_ext, name) is None:
            name = '{}.json'.format(name)
        
        conf_path = os.path.join(folder,name)

        with open(conf_path,'r') as conf:
            dict_data = json.loads(conf)
        
        return dict_data

    def load_yaml(self,name,subpath=None,input=None):
        """Simply Loads a YAML file and passes the result as a dict"""

        dict_data = {}
        
        input_folder = (input if input else self.input_folder)
        folder = (os.path.join(input_folder,subpath) if subpath else input_folder)

        # Add the .yml extension to the conf name if not already present
        yml_ext = re.compile('(\.yml|\.yaml)$')
        if re.search(yml_ext, name) is None:
            name = '{}.yml'.format(name)

        conf_path = os.path.join(folder,name)

        with open(conf_path,'r') as conf:
            dict_data = yaml.full_load(conf)
        
        return dict_data
    
    def dump_json(self,dictData,schema,name):

        now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = "{}_{}-{}.json".format(now,schema,name)
        filepath = os.path.join(self.output_folder,filename)

        encoded_json = bJSONEncoder().encode(dictData)
        loaded_json = json.loads(encoded_json)
        with open(filepath,"w") as f:
            json.dump(loaded_json,f)

        return filepath

    def dump_csv(self,dictData,schema,name):

        now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = "{}_{}-{}.csv".format(now,schema,name)
        filepath = os.path.join(self.output_folder,filename)

        fieldnameset = set()

        for i in range(0,min(1000,len(dictData))):
            fieldset = set(dictData[i].keys())
            fieldnameset |= fieldset
        
        fieldnames = sorted(list(fieldnameset), key=str.lower)
        print("FIELDNAMES: {}".format(fieldnames))

        with open(filepath,"w") as f:
            writer = csv.DictWriter(f,fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(dictData)

        return filepath