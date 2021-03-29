#!python3

import azure

from common.extract import get_data
from common.spLogging import logger

from prestashop_sql import prestashopSQL
from azure_sql.azureSQL import AzureSQLConnector


def main(mytimer: azure.functions.TimerRequest):

    azconn = AzureSQLConnector.load_default()

    for model_name in prestashopSQL.MODELS_LIST:
        logger.info('Extracting Prestashop Model: {}'.format(model_name))
        jsonpath,dataset = get_data(prestashopSQL,model_name)
        # push to Azure SQL
        azconn.insert_dataset(dataset)
