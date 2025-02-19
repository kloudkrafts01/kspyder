
#!python3

from importlib import import_module
import traceback

from common.config import MODULES_MAP
from common.loggingHandler import logger
from Connectors.azureSQLConnector import azureSQLConnector

def main(params: dict) -> dict:

    result = {}
    
    try:
        
        azconn = azureSQLConnector.load_default()
        schema = params['source']
        schema_list = ([schema] if schema else list(MODULES_MAP.keys()))
        action = params['action']
        models = params['model']

        if action == 'build':
            result = azconn.create_db(schema_list)

        elif action == 'destroy':
            result = azconn.delete_db(schema_list)
        
        elif action =='drop':
            result = azconn.delete_tables(schema,models)

        elif action == 'examine':
            for schema in schema_list:
                result[schema] = azconn.plan_changes(schema)

        elif action == 'apply':
            for schema in schema_list:
                plan = azconn.plan_changes(schema)
                result[schema] = azconn.apply_changes(plan)
        
        else:
            returnMsg = "F_db_activity :: Invalid value provided for 'action' parameter: {}".format(action)
            logger.warning(returnMsg)
            result = returnMsg

    except Exception as e:
        returnMsg = 'F_db_activity error :: {}'.format(traceback.print_exc())
        logger.error(returnMsg)
        result = returnMsg

    return result
