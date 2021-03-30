
#!python3

from importlib import import_module

from common.spLogging import logger
from Connectors.azureSQL import AzureSQLConnector

connectors = {
    'odoo': 'odooRPC',
    'prestashop': 'prestashopSQL'
}

def main(params: dict) -> dict:

    result = {}
    
    try:
        
        azconn = AzureSQLConnector.load_default()
        schema, connector_list, action = prepare_params(params)

        if action == 'build_db':
            azconn.create_db(connectors)

        elif action == 'destroy_db':
            azconn.delete_db(schema_name=schema)

        elif action == 'examine_db':
            for connector in connector_list:
                result[connector.SCHEMA_NAME] = azconn.plan_changes(connector)

        elif action == 'apply_db_changes':
            print("TODO")
            # azconn.apply_changes(input_body)
        
        else:
            raise ValueError("Invalid value provided for 'action' parameter.")

    except Exception as e:
        errorStr = '{}'.format(e)
        logger.error(errorStr)

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
