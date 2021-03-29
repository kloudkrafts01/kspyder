#!python3

import azure

from common.spLogging import logger
from common.extract import get_data

from odoo_rpc import odooRPC
from azure_sql.azureSQL import AzureSQLConnector


def main(mytimer: azure.functions.TimerRequest):

    azconn = AzureSQLConnector.load_default()

    for model_name in odooRPC.MODELS_LIST:
        logger.info('Extracting Odoo Model: {}'.format(model_name))
        jsonpath,dataset = get_data(odooRPC,model_name)
        # push to Azure SQL
        azconn.insert_dataset(dataset)
