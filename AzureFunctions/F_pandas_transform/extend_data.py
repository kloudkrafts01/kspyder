#!python3

import os

from common.config import CONF_FOLDER, BASE_FILE_HANDLER as fh
from common.loggingHandler import logger
from Connectors.pandasSQL import PandasSQLConnector

TRANSFORMS_DIR = os.path.join(CONF_FOLDER,'transforms')

def main(params: dict) -> dict:

    returnStr = ""
    
    try:
        # params = orc_input['params']
        pdconn = PandasSQLConnector.load_default()
        schema = params['source']
        trigger = params['trigger']

        results = {}
  
        initStr = "Extend Data Table operation started. Trigger : {} - Schema: {}".format(trigger,schema)
        logger.info(initStr)

        for filename in os.listdir(TRANSFORMS_DIR):
            
            transform_def = fh.load_yaml(filename, subpath='transforms')
            
            if transform_def['Source'] == schema:
                logger.info("Applying pandas transforms from manifest: {}".format(filename))
                df = pdconn.apply_transforms(transform_def)
                results[filename] = 'applied'
            
            else:
                logger.info("Skipping filtered schema : {}".format(transform_def))
                results[filename] = 'skipped'

        returnStr = "Extend Data Table ended. Results: {}".format(results)
        logger.info(returnStr)

        output_results = {
            'params': params,
            'results': results
        }

    except Exception as e:
        returnStr = '{}'.format(e)
        logger.error(e)

        output_results = {
            'params': params,
            'results': returnStr
        }

    return output_results
