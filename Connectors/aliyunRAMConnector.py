#!python3

import os
from typing import List
from importlib import import_module
import jmespath

from Engines.restExtractorEngine import RESTExtractor
from common.config import BASE_FILE_HANDLER as fh

# Load the Connector's config
CONF = fh.load_yaml('aliyunRAMmodels', subpath=__name__)
CONNECTOR_CONF = CONF['Connector']
CONNECTOR_NAME = CONNECTOR_CONF['name']
SCHEMA_NAME = CONNECTOR_CONF['schema']
UPD_FIELD_NAME = CONNECTOR_CONF['update_field']
IS_TRUNCATED_KEY = CONNECTOR_CONF['is_truncated_key']
NEXT_TOKEN_KEY = CONNECTOR_CONF['next_token_key']
LAST_REQUEST_KEY = CONNECTOR_CONF['last_request_key']

# Load models config
MODELS = CONF['Models']
MODELS_LIST = list(MODELS.keys())

# Import the connector's modules
SourceClient = import_module('{}.client'.format(CONNECTOR_NAME))
SourceModels = import_module('{}.models'.format(CONNECTOR_NAME))
from alibabacloud_tea_openapi.models import Config
from alibabacloud_tea_util.models import RuntimeOptions

class AliyunClient:

    def __init__(self, access_key_id:str, access_key_secret:str, region_id:str):

        config = Config(
            # Required, your AccessKey ID,
            access_key_id=access_key_id,
            # Required, your AccessKey secret,
            access_key_secret=access_key_secret,
            # your Region ID
            region_id = region_id
        )
        Client = getattr(SourceClient,'Client')
        self.client = Client(config)

    @classmethod
    def from_env(cls):
        env = os.environ
        return cls(
            env['ALIBABACLOUD_ACCESS_KEY_ID'],
            env['ALIBABACLOUD_ACCESS_KEY_SECRET'],
            'cn-shanghai'
        )

class aliyunRAMConnector(RESTExtractor):

    def __init__(self, profile=None, schema=SCHEMA_NAME, models=MODELS, update_field=UPD_FIELD_NAME,scope=None,**params):

        self.client = AliyunClient.from_env().client
        self.runtime_options = RuntimeOptions()

        self.schema = schema
        self.models = models
        self.scope = scope
        self.params = params

    def read_query(self,model,search_domains=[],start_token=None,**params):

        # Import request builder and instanciate a request in context
        kwargs = {
            str.lower(NEXT_TOKEN_KEY): start_token
        }
        request_builder = getattr(SourceModels, model['request_builder'])
        request = request_builder(**kwargs)

        # Build and send a query with the request context
        query = getattr(self.client, model['query_name'])
        response = query(
            request,
            self.runtime_options
        )

        # Parse response and retrieve relevant data
        response_dict = response.body.to_map()

        datapath = jmespath.compile(model['datapath'])
        results = datapath.search(response_dict)
        is_truncated = response_dict[IS_TRUNCATED_KEY]
        next_token = response_dict[NEXT_TOKEN_KEY] if NEXT_TOKEN_KEY in response_dict.keys() else None

        return results, is_truncated, next_token