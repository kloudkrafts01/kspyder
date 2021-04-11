
#!python3

from importlib import import_module
import traceback

from common.config import CONNECTOR_MAP
from common.spLogging import logger
from Connectors.azureSQL import AzureSQLConnector

def main(params: dict) -> dict:

    result = {}
    
    try:
        # params = orc_input['params']
        # body = orc_input['body']

        azconn = AzureSQLConnector.load_default()
        schema, connector_list, action, models = prepare_params(params)

        if action == 'build':
            result = azconn.create_db(connector_list)

        elif action == 'destroy':
            result = azconn.delete_db(schema_name=schema)
        
        elif action =='drop':
            plan = azconn.build_plan(schema_name=schema,to_delete=models)
            result = azconn.apply_changes(plan)

        elif action == 'examine':
            for connector in connector_list:
                result[connector.SCHEMA_NAME] = azconn.plan_changes(connector)

        elif action == 'apply':
            body = params['body']
            for connector_name,plan in body.items():
                result[connector_name] = azconn.apply_changes(plan)
        
        else:
            returnMsg = "F_db_activity :: Invalid value provided for 'action' parameter: {}".format(action)
            logger.warning(returnMsg)
            result = returnMsg

    except Exception as e:
        returnMsg = 'F_db_activity error :: {}'.format(traceback.print_exc())
        logger.error(returnMsg)
        result = returnMsg

    return result

def prepare_params(params):

    connector_list = []
    schema = params['source']
    if schema:
        connector_list += import_module(CONNECTOR_MAP[schema]),
    else:
        for key,name in CONNECTOR_MAP.items():
            connector_list += import_module(name),
    action = params['action']
    model_name = params['model']
    models = [model_name]

    return schema, connector_list, action, models
