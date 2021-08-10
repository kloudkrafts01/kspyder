#!python3

import json
import argparse
from importlib import import_module

from common.extract import get_data
from common.config import CONNECTOR_MAP, DEFAULT_TIMESPAN
from common.spLogging import logger

from common.mongo_connector import MongoDBConnector
from Connectors.azureSQL import AzureSQLConnector


from AzureFunctions.F_fetch_data import fetch_data
from AzureFunctions.F_pandas_transform import extend_data
from AzureFunctions.F_db_activity import db_actions


operation = 'operation'
source = None
model_name = None
input_file = 'file'
last_days = None
fetch_all = None
action = None

params = {}


def fetch():

    orc_input = {
        'params': params,
        'body': 'TODO'
    }

    result = fetch_data.main(params)
    logger.info(result)

    return result

def build_db():

    azconn = AzureSQLConnector.load_default()
    source_list = ([source] if source else None)
    azconn.create_db(source_list)

def destroy_db():

    azconn = AzureSQLConnector.load_default()
    azconn.delete_db(schema=source)

def extract():

    connector = import_module(CONNECTOR_MAP[source])

    full_results = []
    
    for model_name in models:
        logger.info("Extracting schema: {} - models: {}".format(source,model_name))
        jsonpath,dataset = get_data(connector,model_name,last_days=params['last_days'])
        full_results += {'jsonpath': jsonpath, 'dataset': dataset},
    
    return full_results

def insert_to_azure():
    
    azconn = AzureSQLConnector.load_default()
    azconn.insert_from_jsonfile(input_file)

def insert_to_mongo():

    mgconn = MongoDBConnector()
    mgconn.insert_from_jsonfile(input_file)

def pass_mongo_queries():
    mgconn = MongoDBConnector()
    mgconn.execute_queries()

def expand():

    result = extend_data.main(params)
    logger.info(result)

def examine_db():

    azconn = AzureSQLConnector.load_default()
    json_plan = azconn.plan_changes(source)
    return json_plan

def apply_db_changes():

    with open(input_file, 'r') as f:
        plan = json.load(f)
    
    azconn = AzureSQLConnector.load_default()
    azconn.apply_changes(plan)

def manage_db():
    result = db_actions.main(params)
    return result

if __name__ == "__main__":


    # Define Arg Parser
    parser = argparse.ArgumentParser()
    parser.add_argument('operation',action='store',type=str)
    parser.add_argument('-s','--source',action='store',type=str,dest=source)
    parser.add_argument('-m','--model',action='store',type=str,nargs='+',dest=model_name)
    parser.add_argument('-f','--file',action='store',type=str,dest=input_file)
    parser.add_argument('-t','--timespan',action='store',type=int,dest=last_days,default=DEFAULT_TIMESPAN)
    parser.add_argument('-a','--all',action='store_true',dest=fetch_all,default=False)
    parser.add_argument('-x','--action',action='store',type=str,dest=action)

    args = parser.parse_args()

    source = args.source
    fetch_all = args.all
    last_days = args.timespan
    models = args.model
    input_file = args.file
    action = args.action
    
    params = {
        'trigger': 'cli',
        'last_days': (None if fetch_all else last_days),
        'model': models,
        'source': source,
        'action': action
    }

    print(params)

    function = locals()[args.operation]
    function()

