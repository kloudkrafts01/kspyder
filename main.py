#!python3

import json
import argparse
# from re import search

from common.config import DEFAULT_TIMESPAN
from common.loggingHandler import logger
from common.clientHandler import clientHandler

from Connectors.mongoDBConnector import mongoDBConnector
from Connectors.azureSQLConnector import azureSQLConnector

from AzureFunctions.F_fetch_data import fetch_data
from AzureFunctions.F_pandas_transform import extend_data
from AzureFunctions.F_db_activity import db_actions

from Engines.pipelineEngine import pipelineEngine

operation = 'operation'
source = None
model_name = None
input_file = 'file'
last_days = None
fetch_all = None
action = None
scopes = None
search_domain = None
# query_domain = None
input_data = [{}]

params = {}

ch = clientHandler()
    

def fetch():

    result = fetch_data.main(params)
    logger.info(result)

    return result

def build_db():

    azconn = azureSQLConnector.load_default()
    source_list = ([source] if source else None)
    azconn.create_db(source_list)

def destroy_db():

    azconn = azureSQLConnector.load_default()
    azconn.delete_db(schema_name=source)

def extract():

    full_results = []

    logger.info("Instantiating Extractor {} with scopes : {}".format(source,scopes))
    client = ch.get_client(source=source, scopes=scopes)  
    
    for model_name in models:
        logger.info("Extracting schema: {} - model: {}".format(source,model_name))
        dataset = client.get_data(model_name=model_name,search_domains=[search_domain],**params)
        full_results += dataset,
        
    return full_results

def pipelines():

    p_engine = pipelineEngine()
    for model_name in models:
        p_engine.execute_pipeline_from_file(model_name)

def get_to_mongo():

    results = extract()
    mgconn = mongoDBConnector()
    for result in results:
        try:
            collection_name = result['header']['model']
            mgconn.insert_dataset(input_data=result['data'], collection = collection_name)
        except Exception as e:
            logger.error("get_to_mongo :: Caught Exception: {}".format(e))
            continue


def insert_to_azure():
    
    azconn = azureSQLConnector.load_default()
    azconn.insert_from_jsonfile(input_file)

def insert_to_mongo():

    mgconn = mongoDBConnector()
    mgconn.insert_from_jsonfile(input_file)

def pass_mongo_queries():
    mgconn = mongoDBConnector()
    mgconn.execute_queries(query_names=models,search_domain=search_domain)

def transform_xls():

    for model_name in models:
        pdxls = ch.get_client(source,pipeline_def=model_name)
        dataframes = pdxls.apply_transforms()


def expand():

    result = extend_data.main(params)
    logger.info(result)

def examine_db():

    azconn = azureSQLConnector.load_default()
    json_plan = azconn.plan_changes(source)
    return json_plan

def apply_db_changes():

    with open(input_file, 'r') as f:
        plan = json.load(f)
    
    azconn = azureSQLConnector.load_default()
    azconn.apply_changes(plan)

def manage_db():
    result = db_actions.main(params)
    return result

class KwargsParse(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, dict())
        for value in values:
            key, value = value.split('=')
            getattr(namespace, self.dest)[key] = value


if __name__ == "__main__":


    # Define Arg Parser
    parser = argparse.ArgumentParser(prog='kspyder')
    parser.add_argument('operation',action='store',type=str)
    parser.add_argument('-s','--source',action='store',type=str,dest=source)
    parser.add_argument('-k','--scopes',action='store',type=str,nargs='+',dest=scopes)
    parser.add_argument('-m','--model',action='store',type=str,nargs='+',dest=model_name)
    parser.add_argument('-f','--file',action='store',type=str,dest=input_file)
    parser.add_argument('-t','--timespan',action='store',type=int,dest=last_days,default=DEFAULT_TIMESPAN)
    parser.add_argument('-a','--all',action='store_true',dest=fetch_all,default=False)
    parser.add_argument('-x','--action',action='store',type=str,dest=action)
    parser.add_argument('-d','--searchdomain',action='store',type=str,nargs=3,dest=search_domain)
    # parser.add_argument('-q','--querydomain',action='store',type=str,nargs=1,dest=query_domain)
    parser.add_argument('-i', '--inputs', action=KwargsParse, nargs='*', default={})

    args = parser.parse_args()

    source = args.source
    fetch_all = args.all
    last_days = args.timespan
    models = args.model
    input_file = args.file
    action = args.action
    scopes = args.scopes
    search_domain = args.searchdomain
    # query_domain = args.querydomain
    input_data = [args.inputs]
    
    params = {
        'trigger': 'cli',
        'last_days': (None if fetch_all else last_days),
        'models': models,
        'search_domain': search_domain,
        # 'query_domain': query_domain,
        'source': source,
        'action': action,
        'scopes': scopes,
        'input_data': input_data
    }

    print(params)

    function = locals()[args.operation]
    function()

