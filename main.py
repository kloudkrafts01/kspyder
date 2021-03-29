#!python3

import json
import argparse
import logging

from common.extract import get_data
from common.config import DEFAULT_TIMESPAN
from common.spLogging import logger

from Connectors import odooRPC, prestashopSQL
from Connectors.azureSQL import AzureSQLConnector

from AzureFunctions.F_fetch_data import fetch_data
from AzureFunctions.F_pandas_transform import extend_data


operation = 'operation'
env = 'env'
source = None
model_name = None
input_file = 'file'
last_days = None
fetch_all = None

CONNECTORS = {
    'odoo': odooRPC,
    'prestashop': prestashopSQL
}

def get_connectors():

    result = []
    if source:
        result += CONNECTORS[source], 
    else:
        result = CONNECTORS.values()

    return result

def fetch():

    params = {
        'last_days': (None if fetch_all else last_days),
        'model': model_name,
        'source': source
    }
    result = fetch_data.main(params)
    logger.info(result)

    return result

def build_db():

    azconn = AzureSQLConnector.load_default()
    connectors = get_connectors()

    azconn.create_db(connectors)

def destroy_db():

    azconn = AzureSQLConnector.load_default()
    azconn.delete_db(schema_name=source)

def extract_from_odoo():

    logger.info('Extracting Odoo Model: {}'.format(model_name))

    if fetch_all:
        jsonpath,dataset = get_data(odooRPC,model_name,last_days=None)
    else:
        jsonpath,dataset = get_data(odooRPC,model_name,last_days=last_days)

    return jsonpath,dataset

def extract_from_ps():

    logger.info('Extracting PS Model: {}'.format(model_name))

    if fetch_all:
        jsonpath,dataset = get_data(prestashopSQL,model_name,last_days=None)
    else:
        jsonpath,dataset = get_data(prestashopSQL,model_name,last_days=last_days)

    return jsonpath,dataset

def insert_to_azure():
    
    azconn = AzureSQLConnector.load_default()
    azconn.insert_from_jsonfile(input_file)

def expand():

    params = {
        'source': source
    }
    result = extend_data.main(params)
    logger.info(result)

def examine_db():

    azconn = AzureSQLConnector.load_default()
    connectors = get_connectors()
    for connector in connectors:
        json_plan = azconn.plan_changes(connector)

def apply_db_changes():

    with open(input_file, 'r') as f:
        plan = json.load(f)
    
    azconn = AzureSQLConnector.load_default()
    azconn.apply_changes(plan)


if __name__ == "__main__":


    # Define Arg Parser
    parser = argparse.ArgumentParser()
    parser.add_argument('operation',action='store',type=str)
    parser.add_argument('-s','--source',action='store',type=str,dest=source)
    parser.add_argument('-m','--model',action='store',type=str,dest=model_name)
    parser.add_argument('-f','--file',action='store',type=str,dest=input_file)
    parser.add_argument('-e','--env',action='store',type=str,dest=env)
    parser.add_argument('-t','--timespan',action='store',type=int,dest=last_days,default=DEFAULT_TIMESPAN)
    parser.add_argument('-a','--all',action='store_true',dest=fetch_all,default=False)

    args = parser.parse_args()

    logging.info(args)

    source = args.source
    fetch_all = args.all
    last_days = args.timespan
    model_name = args.model
    input_file = args.file
    env = args.env
    
    function = locals()[args.operation]
    function()

