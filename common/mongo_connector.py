from re import match
from Connectors.azureResourceGraph import SCHEMA_NAME
import json
from pymongo import MongoClient

from common.config import APP_NAME, DUMP_JSON, load_conf
from common.utils import json_dump, csv_dump
from common.spLogging import logger

MONGO_QUERIES = load_conf("mongodb_queries",subfolder="manifests")
SCHEMA_NAME = APP_NAME

class MongoDBConnector():

    def __init__(self):
        self.client = MongoClient('localhost',27017)
        self.db = self.client[SCHEMA_NAME]

    def insert_dataset(self,dataset):

        header = dataset['header']
        schema_name = header['schema']
        model_name = header['model']
        line_count = header['count']
        data = dataset['data']

        logger.info("Inserting dataset to Mongo Collection: {}".format(model_name))

        collection = self.db[model_name]
        result = collection.insert_many(data)

        return result

    def insert_from_jsonfile(self,jsonpath):
        
        if jsonpath:
            with open(jsonpath,'r') as jf:
                json_data = json.load(jf)
                self.insert_dataset(json_data)

    def execute_queries(self, query_names=None, search_domain=None):
        
        queries = {}
        #extracting a subset of the MONGO_QUERIES dicitonary if query names were explicitly provided
        if query_names:
            queries = {query_name: MONGO_QUERIES[query_name] for query_name in set(query_names)}
        else:
            queries = MONGO_QUERIES

        for query_name,query_conf in queries.items():
            logger.info("Preparing Mongo Query {}: {}".format(query_name,query_conf))

            #if search domains were given, pile them up into a $match aggregation clause, with AND logic
            if search_domain:
                
                # matches = []

                # for sd in search_domains:
                sd = search_domain
                field = sd[0]
                operator = sd[1]
                value = sd[2]

                sd_conf = {}
                if operator == '=':
                    sd_conf = {field: value}
                elif operator == '~=':
                    sd_conf = { field: {'$regex': value} }
                else:
                    raise ValueError

                    # matches += sd_conf,

                match_conf = { '$match': sd_conf }

                old_conf = query_conf['operations']
                query_conf['operations'] = { **match_conf, **old_conf }

            result_dataset = self.execute_query(query_name,query_conf)

            if DUMP_JSON:
                json_dump(result_dataset,APP_NAME,query_name)

            if query_conf['dump_csv']:
                csv_dump(result_dataset['data'],APP_NAME,query_name)

    def execute_query(self,query_name,query_conf):

        model_name, queryPipeline = build_mongo_query(query_conf)
        collection = self.db[model_name]

        logger.info("Executing mongo Query on Collection {}: {}".format(model_name,queryPipeline))

        results = collection.aggregate(queryPipeline)
        results_list = list(results)

        logger.debug(results_list)

        result_dataset = {
            "header": {
                "schema": SCHEMA_NAME,
                "model": model_name,
                "query_name": query_name,
                "query_conf": query_conf,
                "count": len(results_list),
            },
            "data": results_list
        }

        return result_dataset

def build_mongo_query(query_conf):

    queryPipeline = []
    model_name = query_conf['collection']

    for operation_name,operation in query_conf['operations'].items():
        
        queryPipeline += {operation_name: operation},

    return model_name, queryPipeline
