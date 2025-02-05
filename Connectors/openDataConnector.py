import jmespath
import requests

from common.config import MODULES_MAP, BASE_FILE_HANDLER as fh
from common.loggingHandler import logger
from Engines.restExtractorEngine import RESTExtractor

CONF = fh.load_yaml(MODULES_MAP[__name__], subpath=__name__)

# mandatory connector config
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']
UPD_FIELD_NAME = CONNECTOR_CONF['update_field']

APIs = CONF['APIs']
MODELS = CONF['Models']



class openDataConnector(RESTExtractor):

    def __init__(self, scopes=None, schema=SCHEMA_NAME, models=MODELS, update_field = UPD_FIELD_NAME, **params):

        self.schema = schema
        self.models = models
        self.update_field = update_field
        self.scopes = scopes
        self.api_name = None
        self.base_url = None
        self.iterate_output = True
        self.rate_limit = None

    def set_api_from_model(self,model):
        
        self.api_name = model['API']
        api_def = APIs[self.api_name]
        self.base_url = api_def['base_url']
        self.rate_limit = api_def['rate_limit'] if 'rate_limit' in api_def.keys() else None
        self.iterate_output = model['iterable'] if 'iterable' in model.keys() else True
        

    def read_query(self,model,start_token=None,**params):

        self.set_api_from_model(model)
        
        url, headers, valid_params = self.build_request(model, baseurl = self.base_url, **params)
        response = requests.get(url, headers = headers, params = valid_params)

        next_token = 'toto'
        # infer if is truncated from this, cause the natural field result_truncated ain't worth shit
        is_truncated = False

        result = response.status_code
        logger.debug("Result: {}".format(result))
        raw_response_data = response.json()
        logger.debug("Raw response data: {}".format(raw_response_data))

        response_data = []

        if result == 200:
            response_data = jmespath.search(model['datapath'], raw_response_data) if self.iterate_output else [raw_response_data]
            # logger.debug("Successful response data: {}".format(response_data))

        else:
            logger.exception("Encountered error in response: {}".format(response_data))

        return response_data, is_truncated, next_token
