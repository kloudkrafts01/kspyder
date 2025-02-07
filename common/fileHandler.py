#!python3

import os, re
import json, yaml, csv, datetime
from bson import ObjectId
from importlib import import_module


class bJSONEncoder(json.JSONEncoder):

    def default(self,o):
        if isinstance(o,ObjectId):
            return str(o)
        json.JSONEncoder.default(self,o)


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
            dict_data = json.load(conf)
        
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
    
    def dump_json(self,dataset,schema,name):

        now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = "{}_{}-{}.json".format(now,schema,name)
        filepath = os.path.join(self.output_folder,filename)

        # Specify the path of json dump into the dataset's header. 
        # Creates the header if not existing.
        dataset['header']['json_dump'] = filepath

        encoder = bJSONEncoder()
        encoded_json = encoder.encode(dataset)
        loaded_json = json.loads(encoded_json)
        with open(filepath,"w") as f:
            json.dump(loaded_json,f)

        return dataset

    def dump_csv(self,dataset,schema,name):

        dict_data = dataset['data']

        now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = "{}_{}-{}.csv".format(now,schema,name)
        filepath = os.path.join(self.output_folder,filename)

        fieldnameset = set()

        for i in range(0,min(1000,len(dict_data))):
            fieldset = set(dict_data[i].keys())
            fieldnameset |= fieldset
        
        fieldnames = sorted(list(fieldnameset), key=str.lower)
        print("FIELDNAMES: {}".format(fieldnames))

        with open(filepath,"w") as f:
            writer = csv.DictWriter(f,fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(dict_data)
        
        # Specify the path of csv dump into the dataset's header. 
        # Creates the header if not existing.
        dataset['header']['csv_dump'] = filepath

        return dataset