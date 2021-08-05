from sqlalchemy.orm import query_expression
from Connectors.azureResourceGraph import read_query
import json
from pymongo import MongoClient

from common.config import APP_NAME, load_conf
from common.spLogging import logger

MONGO_QUERIES = load_conf("mongodb_queries",subfolder="manifests")

class MongoDBConnector():

    def __init__(self):
        self.client = MongoClient('localhost',27017)
        self.db = self.client[APP_NAME]

    def insert_dataset(self,dataset):

        header = dataset['header']
        schema_name = header['schema']
        model_name = header['model']
        line_count = header['count']
        data = dataset['data']

        logger.info("Inserting dataset to Mongo Collection: {}".format(model_name))

        # db = self.client[APP_NAME]
        collection = self.db[model_name]
        result = collection.insert_many(data)

        return result

    def insert_from_jsonfile(self,jsonpath):
        
        if jsonpath:
            with open(jsonpath,'r') as jf:
                json_data = json.load(jf)
                self.insert_dataset(json_data)

    def execute_queries(self):

        for query_name,query_conf in MONGO_QUERIES.items():
            logger.info("Preparing Mongo Query: {}".format(query_conf))
            result = self.read_query(query_conf)
    
    def read_query(self,query_conf):

        model_name, queryPipeline = build_mongo_query(query_conf)
        collection = self.db[model_name]

        logger.info("Executing mongo Query on Collection {}: {}".format(model_name,queryPipeline))

        results = collection.aggregate(queryPipeline)
        for result in results:
            logger.debug(result)

        return results

def build_mongo_query(query_conf):

    queryPipeline = []
    model_name = query_conf['collection']

    for operation_name,operation in query_conf['operations'].items():
        
        opsKey = '${}'.format(operation_name)
        logger.debug("opsKey: {}".format(opsKey))
        logger.debug("operation: {}".format(operation))
        opsDict = {}

        for key,name in operation.items():
            opsDict[key] = '${}'.format(name)

        queryPipeline += {opsKey: opsDict},

    return model_name, queryPipeline
