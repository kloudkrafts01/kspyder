#!python3


import json

import common.sql_connector as sc
from common.sql_connector import GenericSQLConnector
from common.config import AZURE_PROFILE
from common.spLogging import logger


class AzureSQLConnector(GenericSQLConnector):

    @classmethod
    def load_default(cls):
        return cls.from_profile(AZURE_PROFILE)

    def insert_from_jsonfile(self,jsonpath):
        
        if jsonpath:
            with open(jsonpath,'r') as jf:
                json_data = json.load(jf)
                self.insert_dataset(json_data)

    def insert_dataset(self,dataset):

        result = self.update_from_json(dataset)

        return result

