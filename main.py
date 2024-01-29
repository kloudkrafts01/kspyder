#!python3

import json
import argparse
from re import search

from common.config import DEFAULT_TIMESPAN, MODULES_LIST
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
scopes = None
search_domain = None

params = {}


def fetch():

    result = fetch_data.main(params)
    logger.info(result)

    return result

def build_db():

    azconn = AzureSQLConnector.load_default()
    source_list = ([source] if source else None)
    azconn.create_db(source_list)

def destroy_db():

    azconn = AzureSQLConnector.load_default()
    azconn.delete_db(schema_name=source)

def extract():

    full_results = []

    for current_scope in scopes:
        
        logger.info("Instantiating Extractor {} with context : {}".format(source,current_scope))
        client = get_client(source, scope = current_scope)  
        
        for model_name in models:
            logger.info("Extracting schema: {} - model: {}".format(source,model_name))
            # scopedict = {'scope': scope}
            jsonpath,dataset = client.get_data(model_name,**params)
            full_results += {'jsonpath': jsonpath, 'dataset': dataset},
        
    return full_results

def get_to_mongo():

    results = extract()
    mgconn = MongoDBConnector()
    for result in results:
        try:
            mgconn.insert_dataset(result['dataset'])
        except Exception as e:
            logger.error("get_to_mongo :: Caught Exception: {}".format(e))
            continue


def insert_to_azure():
    
    azconn = AzureSQLConnector.load_default()
    azconn.insert_from_jsonfile(input_file)

def insert_to_mongo():

    mgconn = MongoDBConnector()
    mgconn.insert_from_jsonfile(input_file)

def pass_mongo_queries():
    mgconn = MongoDBConnector()
    mgconn.execute_queries(query_names=models,search_domain=search_domain)

def transform_xls():

    for model_name in models:
        pdxls = get_client(source,pipeline_def=model_name)
        dataframes = pdxls.apply_transforms()


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

def get_client(source, **kwargs):
    """Simple method to return a client from a given 'source' value.
        This method assumes that the 'source' given is valid, and corresponds to a callable module
        The module must provide a class named exactly like itself
        e.g. from azureRGConnector impor azureRGConnector"""
    # # get the names from config
    # connector_name = CONNECTOR_MAP[source]["connector"]
    # client_name = CONNECTOR_MAP[source]["client"]

    if source in MODULES_LIST:
        # import the right connector
        connector = import_module(source)

        # instantiate a connector client
        client_class = getattr(connector,source)
        client = client_class(**kwargs)

        return client
    
    else:
        raise ValueError('{} :: {} is not a valid source.\nAccepted sources are:\n{}'.format(__name__,source,MODULES_LIST))

if __name__ == "__main__":


    # Define Arg Parser
    parser = argparse.ArgumentParser()
    parser.add_argument('operation',action='store',type=str)
    parser.add_argument('-s','--source',action='store',type=str,dest=source)
    parser.add_argument('-k','--scope',action='store',type=str,nargs='+',dest=scopes)
    parser.add_argument('-m','--model',action='store',type=str,nargs='+',dest=model_name)
    parser.add_argument('-f','--file',action='store',type=str,dest=input_file)
    parser.add_argument('-t','--timespan',action='store',type=int,dest=last_days,default=DEFAULT_TIMESPAN)
    parser.add_argument('-a','--all',action='store_true',dest=fetch_all,default=False)
    parser.add_argument('-x','--action',action='store',type=str,dest=action)
    parser.add_argument('-d','--searchdomain',action='store',type=str,nargs=3,dest=search_domain)
    

    args = parser.parse_args()

    source = args.source
    fetch_all = args.all
    last_days = args.timespan
    models = args.model
    input_file = args.file
    action = args.action
    scopes = args.scope
    search_domain = args.searchdomain
    
    params = {
        'trigger': 'cli',
        'last_days': (None if fetch_all else last_days),
        'model': models,
        'search_domain': search_domain,
        'source': source,
        'action': action,
        'scope': scopes
    }

    print(params)

    function = locals()[args.operation]
    function()

