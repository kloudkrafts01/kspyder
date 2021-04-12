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
        returnStr = 'F_fetch_data.fetch_data :: {}'.format(traceback.print_exc())
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
    models_raw = params['model']
    models = (source.MODELS_LIST if models_raw is None else models_raw )
    
    return source,last_days,models

