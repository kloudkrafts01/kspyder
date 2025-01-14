from importlib import import_module
# Essential to serialize Google API types to dict
import proto
from google.api.client import services
from google.auth.exceptions import TransportError

from common.config import BASE_FILE_HANDLER as fh

from Engines.restExtractorEngine import RESTExtractor
from common.loggingHandler import logger

CONF = fh.load_yaml('gcloudModels', subpath=__name__)
logger.debug("CONF: {}".format(CONF))
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']
APIS_CONF = CONF['APIs']
MODELS = CONF['Models']

class gcloudConnector(RESTExtractor):

    def __init__(self, client=None, schema=SCHEMA_NAME, scopes=None, models=MODELS, update_field=None,connector_class=None,**params):

        self.schema = schema
        self.scopes = scopes
        self.models = models
        self.params = params
        self.update_field = update_field
        self.connector_class = connector_class
        self.client = client

    def set_current_client_from_model(self, model):

        # Get the API config from the chosen Model
        api_ref = model['API']
        self.api_conf = APIS_CONF[api_ref]
        self.api_name = self.api_conf['name'] if 'name' in self.api_conf.keys() else api_ref
        logger.debug("Setting client from API conf: {}".format(self.api_conf))

        # set API-level fields and import the GCP SDK module
        self.update_field = self.api_conf['update_field']
        self.connector_class = import_module('google.cloud.{}'.format(self.api_name))

        # Set client from model conf
        client_name = model['client_name']
        logger.debug("Client name: {}".format(client_name))

        client_class = getattr(self.connector_class, client_name)
        logger.debug("Imported client class: {}".format(client_class))
        self.client = client_class()

    def postprocess_item(self, item, model=None, **params):
        """Run returned items through JSON serialization"""

        if isinstance(item, proto.Message):
            data = proto.Message.to_dict(item)
        elif isinstance(item, dict):
            data = item
        else:
            logger.error("postprocess_item: item {} is not of type dict or protobuf. Item type = {}".format(item,type(item)))
            data = {}
        return data

        # return proto.Message.to_dict(item)
    
    def discover_data(self, model_name=None, input_data=None, **params):
        
        model = self.models[model_name]
        # Instantiate the relevant API client class from google.cloud
        self.set_current_client_from_model(model)
        
        return super().discover_data(model_name, input_data=input_data, **params)
    
    def build_request(self,model,**params):

        # Import request builder and instanciate a request in context, if provided
        request_builder_name = model['request_builder'] if 'request_builder' in model.keys() else None
        request_builder = getattr(self.connector_class, request_builder_name) if request_builder_name else None

        # Only keep parameters with accepted keys
        valid_params = {}
        if 'accepted_inputs' in model.keys():
            valid_keys = (x for x in params.keys() if x in model['accepted_inputs'])
            for key in valid_keys:
                valid_params[key] = params[key]
        else:
            # If nothing specified, just keep any parameters passed
            valid_params = params

        logger.debug("Initial Valid Params: {}".format(valid_params))

        logger.debug("request builder name: {}".format(request_builder_name))
        logger.debug("request builder object: {}".format(request_builder))
        logger.debug("request builder params: {}".format(valid_params))

        request = request_builder(**valid_params) if request_builder_name else None

        return valid_params, request
    
    def fetch_dataset(self,model=None,search_domains=[],**params):
        """Supercharges the RESTExtractor method as Google Cloud client libraries
            provide a fancy shortcut to iterate over pagination"""

        output_docs = []
        total_count = 0

        # Instantiate the relevant API client class from google.cloud
        self.set_current_client_from_model(model)
        # Prepare Request object and load the method for calling the request
        valid_params, request_object = self.build_request(model,**params)

        query_gen = getattr(self.client,model['query_name'])

        # Generate request iterator. If Requerst type object was built, pass it as argument, else pass keyword args directly
        response_iter = query_gen(request_object) if request_object else query_gen(**valid_params)

        for item in response_iter:

            data = self.postprocess_item(item)
            total_count += 1
            output_docs += data,

        return total_count,output_docs
