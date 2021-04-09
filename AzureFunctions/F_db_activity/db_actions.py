
#!python3

from importlib import import_module

from common.spLogging import logger
from Connectors.azureSQL import AzureSQLConnector

connectors = {
    'odoo': 'odooRPC',
    'prestashop': 'prestashopSQL'
}

def main(params: dict) -> dict:

    result = {
        'params': params
    }
    
    try:
        # params = orc_input['params']
        # body = orc_input['body']

        azconn = AzureSQLConnector.load_default()
        schema, connector_list, action = prepare_params(params)

        if action == 'build':
            created_tables = azconn.create_db(connector_list)
            result['results'] = created_tables

        elif action == 'destroy':
            deleted_tables = azconn.delete_db(schema_name=schema)
            result['results'] = deleted_tables

        elif action == 'examine':
            plans = {}
            for connector in connector_list:
                plans[connector.SCHEMA_NAME] = azconn.plan_changes(connector)
            result['results'] = plans

        elif action == 'apply':
            body = params['body']
            reports = {}
            for connector_name,plan in body.items():
                reports[connector_name] = azconn.apply_changes(plan)
            result['results'] = reports
        
        else:
            returnMsg = "F_db_activity :: Invalid value provided for 'action' parameter: {}".format(action)
            logger.warning(returnMsg)
            result['results'] = returnMsg

    except Exception as e:
        returnMsg = 'F_db_activity error :: {}'.format(e)
        logger.error(returnMsg)
        result['results'] = returnMsg

    return result

def prepare_params(params):

    connector_list = []
    schema = params['source']
    if schema:
        connector_list += import_module(connectors[schema]),
    else:
        for key,name in connectors.items():
            connector_list += import_module(name),
    action = params['action']

    return schema, connector_list, action
