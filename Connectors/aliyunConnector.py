import os, re
from importlib import import_module
import jmespath

from Engines.apiExtractorEngine import RESTExtractor
from common.config import MODULES_MAP, PAGE_SIZE, BASE_FILE_HANDLER as fh
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

    def set_current_client_from_model(self, model):

        # Get the API config from the chosen Model
        api_id = model['API']
        self.api_conf = APIS_CONF[api_id]
        self.api_name = self.api_conf['name']
        logger.debug("Setting client from API conf: {}".format(self.api_conf))

        self.update_field = self.api_conf['update_field']

        # Initiate all fields that can be useful for pagination
        self.convert_case = self.api_conf['convert_response_case'] if 'convert_response_case' in self.api_conf.keys() else False
        self.is_truncated_key = self.api_conf['is_truncated_key'] if 'is_truncated_key' in self.api_conf.keys() else None
        self.next_token_key = self.api_conf['next_token_key'] if 'next_token_key' in self.api_conf.keys() else None
        self.last_request_key = self.api_conf['last_request_key'] if 'last_request_key' in self.api_conf.keys() else None
        self.max_results_key = self.api_conf['max_results_key'] if 'max_results_key' in self.api_conf.keys() else None
        self.page_number_key = self.api_conf['page_number_key'] if 'page_number_key' in self.api_conf.keys() else None
        self.page_size_key = self.api_conf['page_size_key'] if 'page_size_key' in self.api_conf.keys() else None


        # Instantiate a new AliyunClient and set it to current client
        aliyun_client = AliyunClient.from_env(api_name = self.api_name)
        self.client = aliyun_client.client
        self.source_models = aliyun_client.source_models
        self.runtime_options = RuntimeOptions()


    def build_request(self, model, start_token=None, **params):

        request_builder = None
        request_context = []

        # Instanciate a request object with the sdk module needed arguments
        request_params = {}
        if start_token:
            request_params[ self.next_token_key ] = start_token
        if self.max_results_key and self.max_results_key in model['accepted_inputs']:
            request_params[ self.max_results_key ] = min( PAGE_SIZE, 100 )

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
            
            # Add the request to request context
            request_context.append(request)

            # Add RuntimeOptions (mandatory)
            request_context.append(self.runtime_options)

        else:
            # if no request builder class is provided, just pass on the valid key-value params
            request_context.append(request_params)

        # If the API requires a header (e.g. ContainerServices API), add it
        if 'header' in self.api_conf.keys():
            request_context.append(self.api_conf['header'])

        logger.debug("Request context: {}".format(request_context))
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

        logger.debug("Response dict keys: {}".format(response_dict.keys()))

        if model['datapath'] == '$root':
            results = response_dict
        else:
            datapath = jmespath.compile(model['datapath'])
            results = datapath.search(response_dict)
        
        response_next_token_key = self.next_token_key
        response_max_results = self.max_results_key
        response_is_truncated_key = self.is_truncated_key
        response_page_size_key = self.page_size_key
        response_page_number_key = self.page_number_key

        # If specified in the API conf, convert field name to CamelCase to look for the needed fields in the response dict
        if self.convert_case:
            response_next_token_key = self.convert_to_camelcase(response_next_token_key)
            response_max_results = self.convert_to_camelcase(response_max_results)
            response_is_truncated_key = self.convert_to_camelcase(response_is_truncated_key)
            response_page_size_key = self.convert_to_camelcase(response_page_size_key)
            response_page_number_key = self.convert_to_camelcase(response_page_number_key)

        next_token = response_dict[response_next_token_key] if response_next_token_key in response_dict.keys() else ''
        # logger.debug("Next Token: {}".format(next_token))

        is_next_token = next_token != ''
        # logger.debug("Is Next Token ? {}".format(is_next_token))
        is_truncated_key = response_is_truncated_key in response_dict.keys()
        # determine whether pagination should continue : if response explicitly tells so, relay the info. If not, see if a "next" token exists
        is_truncated = response_dict[response_is_truncated_key] if is_truncated_key else is_next_token
        logger.debug("Is response truncated ? {}".format(is_truncated))

        return results, is_truncated, next_token