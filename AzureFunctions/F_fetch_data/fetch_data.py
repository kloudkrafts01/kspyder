#!python3

import traceback

from common.spLogging import logger
from common.extract import get_data

from Connectors import odooRPC, prestashopSQL
from Connectors.azureSQL import AzureSQLConnector

VALID_SOURCES = {
    'odoo': odooRPC,
    'prestashop': prestashopSQL
}


def main(params: dict) -> dict:

    returnStr = ""
    
    try:
        # params = orc_input['params']
        source,last_days,models = format_params(params)
        trigger = params['trigger']
        results = {}
        
        azconn = AzureSQLConnector.load_default()

        initStr = "Fetch operation started. Trigger: {} Source: {} - Models: {} - LAST_DAYS={}".format(trigger,source,models,last_days)
        logger.info(initStr)

        for model_name in models:
            logger.info('Extracting data from Model: {}'.format(model_name))
            jsonpath,dataset = get_data(source,model_name,last_days=last_days)
            # push to Azure SQL
            result = azconn.insert_dataset(dataset)
            results[model_name] = result

        returnStr = "Fetch operation ended. Trigger: {} - Source: {} - LAST_DAYS={}\nRESULTS: {}".format(trigger,source,last_days,results)
        logger.info(returnStr)
        output_results = {
            'params': params,
            'results': results
        }

    except Exception as e:
        returnStr = 'F_fetch_data.fetch_data :: {}'.format(e)
        logger.error(e)

        output_results = {
            'params': params,
            'results': returnStr
        }

    return output_results

def format_params(params):

    source = None
    source_name = params['source']
    # get the right module from source_name, if valid
    if source_name in VALID_SOURCES:
        source = VALID_SOURCES[source_name]
    else:
        errmsg = "Invalid source name provided for fetch_data ! please provide a valid source name."
        raise ValueError(errmsg)
    
    # typecast last_days to 'int' if it has been provided
    last_days = params['last_days']
    if last_days is not None:
        last_days = int(last_days)

    # get the input model into a list
    model_name = params['model']
    models = []
    if model_name in source.MODELS_LIST:
        models = [model_name]
    elif model_name is None:
        # if no model name was provided as input, just iterate over all valid models for the source
        models = source.MODELS_LIST
    else:
        errmsg = "Fetch_data: Invalid Model name provided ! No data will be fetched."
        raise ValueError(errmsg)

    return source,last_days,models

