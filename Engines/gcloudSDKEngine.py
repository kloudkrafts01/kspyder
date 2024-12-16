#!python3

from importlib import import_module
# Essential to serialize Google API types to dict
import proto

from Engines.restExtractorEngine import RESTExtractor
from common.spLogging import logger

class gcloudSDKEngine(RESTExtractor):

    def __init__(self, client=None, schema=None, scope=None, models=None, update_field=None,connector_class=None,**params):

        self.schema = schema
        self.scope = scope
        self.models = models
        self.params = params
        self.update_field = update_field
        self.connector_class = connector_class
        self.client = client

    def set_client_from_model(self, model):
        
        client_name = model['client_name']
        logger.debug("Client name: {}".format(client_name))
        client_class = getattr(self.connector_class, client_name)
        logger.debug("Imported client class: {}".format(client_class))
        self.client = client_class()

    def build_request(self,model):
        # Import request builder and instanciate a request in context
        request_builder = getattr(self.connector_class, model['request_builder'])
        request_params = model['request_params']

        logger.debug("request builder name: {}".format(model['request_builder']))
        logger.debug("request builder object: {}".format(request_builder))
        logger.debug("request builder params: {}".format(request_params))

        request = request_builder(**request_params)

        return request
    
    def fetch_dataset(self,model_name=None,search_domains=[],**params):
        """Supercharges the RESTExtractor method as Google Cloud client libraries
            provide a fancy shortcut to iterate over pagination"""

        output_docs = []
        total_count = 0
        model = self.models[model_name]

        # Instantiate the relevant API client class from google.cloud
        self.set_client_from_model(model)

        # Prepare Request object and load the method for calling the request
        request_object = self.build_request(model)
        query_gen = getattr(self.client,model['query_name'])

        # Generate request iterator
        response_iter = query_gen(request_object)

        for item in response_iter:
            
            data = proto.Message.to_dict(item)
            total_count += 1
            output_docs += data,
        
        return total_count,output_docs
