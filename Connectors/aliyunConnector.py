import os, re
from importlib import import_module
import jmespath

from Engines.restExtractorEngine import RESTExtractor
from common.config import MODULES_MAP, PAGE_SIZE, BASE_FILE_HANDLER as fh
from common.loggingHandler import logger

from alibabacloud_tea_openapi.models import Config
from alibabacloud_tea_util.models import RuntimeOptions

CONF = fh.load_yaml(MODULES_MAP[__name__], subpath=__name__)
logger.debug("CONF: {}".format(CONF))
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']
DEFAULT_RATE = CONNECTOR_CONF['default_rate_limit']

APIS = CONF['APIs']
MODELS = CONF['Models']

ALIYUN_MAX_PAGE_SIZE = 100

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

    def __init__(self, profile=None, schema=SCHEMA_NAME, models=MODELS, apis=APIS, scopes=None, rate_limit=DEFAULT_RATE, batch_size=ALIYUN_MAX_PAGE_SIZE, **params):

        self.schema = schema
        self.models = models
        self.apis = apis
        self.scopes = scopes
        self.params = params
        self.profile = profile
        self.rate_limit = rate_limit
        self.batch_size = batch_size

        # All the fields below are set at each query context
        self.api_name = None
        self.api = None
        self.convert_case = False
        self.is_truncated_key = None
        self.next_token_key = None
        self.last_request_key = None
        self.update_field = None
        self.client = None
        self.source_models = None
        self.runtime_options = None

    def convert_to_camelcase(self,string):
        
        if string:
            old_string = string

            # using regex to split string at every underscore
            temp = re.split('_+', string)
            # using lambda function to convert first letter of every word to uppercase
            string = ''.join(map(lambda x: x.title(), temp))
            
            logger.debug("Converted field {} to {}".format(old_string, string))

        return string



    def build_request(self, model, **params):

        request_builder = None
        request_context = []

        # Instanciate a request object with the sdk module needed arguments
        request_params = {}
        # if start_token:
        #     request_params[ self.next_token_key ] = start_token
        # if hasattr(self.api, 'batch_size_key') and self.api.batch_size_key in model['accepted_inputs']:
        #     request_params[ self.max_results_key ] = min( PAGE_SIZE, 100 )

        # add base keys from API definition
        base_keys = (
            self.api.next_token_key,
            self.api.batch_size_key
        )
        if hasattr(self.api, 'is_truncated_key'):
            base_keys += self.api.is_truncated_key,
        if hasattr(self.api, 'total_count_key'):
            base_keys += self.api.total_count_key,
    
        for key in (x for x in params.keys() if x in base_keys):
            request_params[key] = params[key]

        if 'accepted_inputs' in model.keys():
            valid_keys = (x for x in params.keys() if x in model['accepted_inputs'])
            for key in valid_keys:
                request_params[key] = params[key]

        if 'request_builder' in model.keys():
            # Import request builder and instanciate a request object
            request_builder = getattr(self.source_models, model['request_builder'])
            logger.debug("request builder name: {}".format(model['request_builder']))
            logger.debug("request builder object: {}".format(request_builder))
            logger.debug("request builder params: {}".format(request_params))

            request = request_builder(**request_params)
            
            # Add the request to request context (mandatory)
            request_context.append(request)

        else:
            # if no request builder class is provided, just pass on the valid key-value params
            request_context.append(request_params)
        
        # If the API requires a header (e.g. ContainerServices API), add it
        if hasattr(self.api, 'header'):
            request_context.append(self.api.header)
        
        # Add RuntimeOptions (mandatory)
        request_context.append(self.runtime_options)

        logger.debug("Request context: {}".format(request_context))
        return request_context

    def read_query(self,model,search_domains=[],start_token=None,batch_size=None,query_args=[],**params):
        
        data = []
        metadata = {}
        is_truncated = False
        next_token = None

        # Instantiate a new AliyunClient and set it to current client
        aliyun_client = AliyunClient.from_env(api_name = self.api.name)
        self.client = aliyun_client.client
        self.source_models = aliyun_client.source_models
        self.runtime_options = RuntimeOptions()

        preprocessed_params = self.preprocess_params(params,start_token=start_token,batch_size=batch_size)

        # Build a request context for the current client API
        request_context = self.build_request( model, **preprocessed_params )
        
        # Send a query with the request context built before
        query = getattr(self.client, model['query_name'])
        response = query( *request_context )

        # Parse response and retrieve relevant data
        raw_response_data = response.body.to_map()
        logger.debug("Response dict keys: {}".format(raw_response_data.keys()))

        data, metadata, is_truncated, next_token = self.postprocess_response(raw_response_data, model = model, start_token = start_token)
        logger.debug("Next token: {}".format(next_token))

        return data, is_truncated, next_token, start_token