#!python3

from Engines.restExtractorEngine import RESTExtractor
import os
from typing import List
from common.config import PAGE_SIZE, BASE_FILE_HANDLER as fh

from alibabacloud_ram20150501.client import Client
from alibabacloud_ram20150501.models import ListUsersRequest
from alibabacloud_tea_openapi.models import Config
from alibabacloud_tea_util.models import RuntimeOptions


# Load the Connector's config
CONF = fh.load_yaml('aliyunRAMmodels', subpath=__name__)
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']
UPD_FIELD_NAME = CONNECTOR_CONF['update_field']

MODELS = CONF['Models']
MODELS_LIST = list(MODELS.keys())

class AliyunRAMClient:

    def __init__(self, access_key_id:str, access_key_secret:str):

        config = Config(
            # Required, your AccessKey ID,
            access_key_id=access_key_id,
            # Required, your AccessKey secret,
            access_key_secret=access_key_secret
        )

        self.client = Client(config)

    @classmethod
    def from_env(cls):
        env = os.environ
        return cls(
            env['ALIBABACLOUD_ACCESS_KEY_ID'],
            env['ALIBABACLOUD_ACCESS_KEY_SECRET']
        )

class aliyunRAMConnector(RESTExtractor):

    def __init__(self, profile=None, schema=SCHEMA_NAME, models=MODELS, update_field=UPD_FIELD_NAME,scope=None,**params):

        self.client = AliyunRAMClient.from_env().client
        # self.request = ListUsersRequest()
        self.runtime_options = RuntimeOptions()

        self.schema = schema
        self.models = models
        self.scope = scope
        self.params = params

    def read_query(self,model,search_domains=[],start_token=None,**params):

        next_request = ListUsersRequest(marker = start_token)
        response = self.client.list_users_with_options(next_request, self.runtime_options)

        response_dict = response.body.to_map()

        results = response_dict['Users']['User']
        is_truncated = response_dict['IsTruncated']
        next_token = response_dict['Marker'] if 'Marker' in response_dict.keys() else None

        return results, is_truncated, next_token