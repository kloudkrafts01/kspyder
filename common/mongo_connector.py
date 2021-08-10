import json
from pymongo import MongoClient

from common.spLogging import logger

class MongoDBConnector():

    def __init__(self):
        self.client = MongoClient('localhost',27017)

    def insert_dataset(self,dataset):

        header = dataset['header']
        schema_name = header['schema']
        model_name = header['model']
        line_count = header['count']
        data = dataset['data']

        logger.info("Inserting dataset to Mongo Collection: {}".format(model_name))

        db = self.client.database
        collection = db[model_name]
        result = collection.insert_many(data)


    def insert_from_jsonfile(self,jsonpath):
        
        if jsonpath:
            with open(jsonpath,'r') as jf:
                json_data = json.load(jf)
                self.insert_dataset(json_data)