#!python3

import os,yaml

from common.config import load_conf, CONF_FOLDER
from common.spLogging import logger
from Connectors.pandasSQL import PandasSQLConnector

TRANSFORMS_DIR = os.path.join(CONF_FOLDER,'transforms')

def main(params: dict) -> str:

    returnStr = ""
    
    try:
        
        pdconn = PandasSQLConnector.load_default()
        schema = params['source']
        
        results = {}
  
        initStr = "Extend Data Table operation started."
        logger.info(initStr)

        for filename in os.listdir(TRANSFORMS_DIR):
            
            transform_def = load_conf(filename, subfolder='transforms')
            
            if transform_def['Source'] == schema:
                logger.info("Applying pandas transforms from manifest: {}".format(filename))
                df = pdconn.apply_transforms(transform_def)
                results[filename] = 'applied'
            
            else:
                logger.info("Skipping filtered schema : {}".format(schema))
                results[filename] = 'skipped'

        returnStr = "Extend Data Table ended. Results: {}".format(results)
        logger.info(returnStr)

    except Exception as e:
        returnStr = '{}'.format(e)
        logger.error(e)

    return returnStr
