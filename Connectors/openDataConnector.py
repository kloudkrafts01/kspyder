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

    def set_api_from_model(self,model):
        
        self.api_name = model['API']
        self.base_url = APIs[self.api_name]['base_url']

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
        # logger.debug("Raw response data: {}".format(raw_response_data))

        response_data = []

        if result == 200:
            response_data = jmespath.search(model['datapath'], raw_response_data)
            # logger.debug("Successful response data: {}".format(response_data))

        else:
            logger.error("Encountered error in response: {}".format(response_data))

        return response_data, is_truncated, next_token
