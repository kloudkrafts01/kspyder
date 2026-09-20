#!python3

import os,json
from typing import Any

from Engines.sqlEngine import GenericSQLEngine
from common.config import CONF_FOLDER
from common.profileHandler import profileHandler

CONNECTOR_CONF_PATH = os.path.join(CONF_FOLDER, 'azureSQL')
DEFAULT_PROFILE = 'azureSQLProfile'

class azureSQLConnector(GenericSQLEngine):

    @classmethod
    def load_default(cls) -> "azureSQLConnector":

        ph = profileHandler(input_folder=CONNECTOR_CONF_PATH)
        profile = ph.load_profile(profile_name=DEFAULT_PROFILE)
        return cls.from_profile(profile)

    def insert_from_jsonfile(self, jsonpath: str) -> None:

        if jsonpath:
            with open(jsonpath,'r') as jf:
                json_data = json.load(jf)
                self.insert_dataset(json_data)

    def insert_dataset(self, dataset: dict) -> Any:

        result = self.update_from_json(dataset)

        return result
