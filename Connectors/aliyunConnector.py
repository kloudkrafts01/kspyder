import os
from importlib import import_module
import jmespath

from Engines.restExtractorEngine import RESTExtractor
from common.config import MODULES_MAP, BASE_FILE_HANDLER as fh
from common.loggingHandler import logger

from alibabacloud_tea_openapi.models import Config
from alibabacloud_tea_util.models import RuntimeOptions

CONF = fh.load_yaml(MODULES_MAP[__name__], subpath=__name__)
logger.debug("CONF: {}".format(CONF))
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']

APIS_CONF = CONF['APIs']
MODELS = CONF['Models']

class AliyunClient:

    def __init__(self, access_key_id:str, access_key_secret:str, region_id:str, api_name=None, **kwargs):
        
        config = Config(
            # Required, your AccessKey ID,
            access_key_id = access_key_id,
            # Required, your AccessKey secret,
            access_key_secret = access_key_secret,
            # The Region Id. Required in some cases depending on the actual client
            region_id = region_id
        )

        # Import the connector's modules
        self.source_client = import_module('{}.client'.format(api_name))
        self.source_models = import_module('{}.models'.format(api_name))

        Client = getattr(self.source_client,'Client')
        self.client = Client(config)

    @classmethod
    def from_env(cls,api_name=None):
        env = os.environ
        return cls(
            env['ALIBABACLOUD_ACCESS_KEY_ID'],
            env['ALIBABACLOUD_ACCESS_KEY_SECRET'],
            env['ALIBABACLOUD_REGION_ID'],
            api_name = api_name
        )

class aliyunConnector(RESTExtractor):

    def __init__(self, profile=None, schema=SCHEMA_NAME, models=MODELS, scopes=None, **params):

        self.schema = schema
        self.models = models
        self.scopes = scopes
        self.params = params
        self.profile = profile

        # All the fields below are set at each query context
        self.api_name = None
        self.api_conf = None
        self.is_truncated_key = None
        self.next_token_key = None
        self.last_request_key = None
        self.update_field = None
        self.client = None
        self.source_models = None
        self.runtime_options = None

    def set_current_client_from_model(self, model):

        # Get the API config from the chosen Model
        api_id = model['API']
        self.api_conf = APIS_CONF[api_id]
        self.api_name = self.api_conf['name']
        logger.debug("Setting client from API conf: {}".format(self.api_conf))

        self.update_field = self.api_conf['update_field']
        self.is_truncated_key = self.api_conf['is_truncated_key']
        self.next_token_key = self.api_conf['next_token_key']
        self.last_request_key = self.api_conf['last_request_key']

        # Instantiate a new AliyunClient and set it to current client
        aliyun_client = AliyunClient.from_env(api_name = self.api_name)
        self.client = aliyun_client.client
        self.source_models = aliyun_client.source_models
        self.runtime_options = RuntimeOptions()


    def build_request(self, model, start_token=None, **params):

        request_context = []

        # Instanciate a request object with the sdk module needed arguments
        request_params = {
            str.lower(self.next_token_key): start_token
        } if start_token else {}

        if 'accepted_inputs' in model.keys():
            # accepted_inputs = (x['key'] for x in model['accepted_inputs'])
            valid_keys = (x for x in params.keys() if x in model['accepted_inputs'])
            for key in valid_keys:
                request_params[key] = params[key]

        # Import request builder and instanciate a request object
        request_builder = getattr(self.source_models, model['request_builder'])
        logger.debug("request builder name: {}".format(model['request_builder']))
        logger.debug("request builder object: {}".format(request_builder))
        logger.debug("request builder params: {}".format(request_params))
        request = request_builder(**request_params)
        # Add the request to request context
        request_context.append(request)

        # If the API requires a header (e.g. ContainerServices API), add it
        if 'header' in self.api_conf.keys():
            request_context.append(self.api_conf['header'])

        # Add RuntimeOptions (mandatory)
        request_context.append(self.runtime_options)

        return request_context

    def read_query(self,model,search_domains=[],start_token=None,query_args=[],**params):

        # First, set the current client to the model's API
        self.set_current_client_from_model(model)

        # Second, build a request context for the current client API
        request_context = self.build_request( model, start_token = start_token, **params )
        
        # Send a query with the request context built before
        query = getattr(self.client, model['query_name'])
        response = query( *request_context )

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