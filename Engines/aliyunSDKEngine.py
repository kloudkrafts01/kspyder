#!python3

import os
from typing import List
from importlib import import_module
import jmespath

from Engines.restExtractorEngine import RESTExtractor
from common.config import MODULES_MAP, BASE_FILE_HANDLER as fh
from common.loggingHandler import logger

from alibabacloud_tea_openapi.models import Config
from alibabacloud_tea_util.models import RuntimeOptions

class AliyunClient:

    def __init__(self, access_key_id:str, access_key_secret:str, region_id:str, connector_name=None, **kwargs):
        
        config = Config(
            # Required, your AccessKey ID,
            access_key_id = access_key_id,
            # Required, your AccessKey secret,
            access_key_secret = access_key_secret,
            # The Region Id. Required in some cases depending on the actual client
            region_id = region_id
        )

        # Import the connector's modules
        self.source_client = import_module('{}.client'.format(connector_name))
        self.source_models = import_module('{}.models'.format(connector_name))

        Client = getattr(self.source_client,'Client')
        self.client = Client(config)

    @classmethod
    def from_env(cls,connector_name=None):
        env = os.environ
        return cls(
            env['ALIBABACLOUD_ACCESS_KEY_ID'],
            env['ALIBABACLOUD_ACCESS_KEY_SECRET'],
            env['ALIBABACLOUD_REGION_ID'],
            connector_name=connector_name
        )

class AliyunRESTConnector(RESTExtractor):

    def __init__(self, aliyun_client:AliyunClient, profile=None, schema=None, models=None, update_field=None,scope=None,connector_conf=None,**params):

        self.schema = schema
        self.models = models
        self.scope = scope
        self.params = params
        self.update_field = update_field
        self.profile = profile

        # Load the Connector's config
        self.is_truncated_key = connector_conf['is_truncated_key']
        self.next_token_key = connector_conf['next_token_key']
        self.last_request_key = connector_conf['last_request_key']

        self.client = aliyun_client.client
        self.source_models = aliyun_client.source_models
        self.runtime_options = RuntimeOptions()

    def build_request(self,model,**request_params):
        # Import request builder and instanciate a request in context
        request_builder = getattr(self.source_models, model['request_builder'])
        logger.debug("request builder name: {}".format(model['request_builder']))
        logger.debug("request builder object: {}".format(request_builder))
        logger.debug("request builder params: {}".format(request_params))
        request = request_builder(**request_params)

        return request

    def read_query(self,model,search_domains=[],start_token=None,query_args=[],**params):

        # Build and send a query with the request context
        query = getattr(self.client, model['query_name'])
        response = query(*query_args)

        # Parse response and retrieve relevant data
        response_dict = response.body.to_map()
        results = []

        if model['datapath'] == '$root':
            results = response_dict
        else:
            datapath = jmespath.compile(model['datapath'])
            results = datapath.search(response_dict)
        
        is_truncated = response_dict[self.is_truncated_key] if self.is_truncated_key in response_dict.keys() else None
        next_token = response_dict[self.next_token_key] if self.next_token_key in response_dict.keys() else None

        return results, is_truncated, next_token