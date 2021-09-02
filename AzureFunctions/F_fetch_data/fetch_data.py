#!python3

import traceback
from importlib import import_module

from common.spLogging import logger
from common.utils import get_client
from common.config import CONNECTOR_MAP

# from Connectors import odooRPC, prestashopSQL, azureResourceGraph
from Connectors.azureSQL import AzureSQLConnector


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

        client = get_client(source)

        for model_name in models:
            logger.info('Extracting data from Model: {}'.format(model_name))
            jsonpath,dataset = client.get_data(model_name,last_days=last_days)
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
    if source_name in CONNECTOR_MAP.keys():
        source = import_module(CONNECTOR_MAP[source_name])
    else:
        errmsg = "Invalid source name provided for fetch_data ! please provide a valid source name."
        raise ValueError(errmsg)
    
    # typecast last_days to 'int' if it has been provided
    last_days = (int(params['last_days']) if params['last_days'] is not None else None)

    # get the input model into a list, take all the connector's models if None provided
    models = (source.MODELS_LIST if params['model'] is None else params['model'])
    
    return source,last_days,models

