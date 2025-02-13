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
PAGE_SIZE = CONNECTOR_CONF['default_batch_size']

APIS = CONF['APIs']
MODELS = CONF['Models']



class openDataConnector(RESTExtractor):

    def __init__(self, scopes=None, schema=SCHEMA_NAME, models=MODELS, apis=APIS, update_field = UPD_FIELD_NAME, batch_size=PAGE_SIZE, **params):

        self.schema = schema
        self.models = models
        self.apis = apis
        self.update_field = update_field
        self.scopes = scopes
        self.api_name = None
        self.base_url = None
        self.iterate_output = True
        self.rate_limit = None
        self.batch_size = batch_size

    def read_query(self, model, start_token:int = 1, batch_size:int = 100, **params):

        params, start_token, batch_size = self.preprocess_params(params,start_token=start_token,batch_size=batch_size)

        url, headers, valid_params = self.build_request(model, baseurl = self.api.base_url, **params)
        
        # pass the request, get http status and response payload
        response = requests.get(url, headers = headers, params = valid_params)
        raw_response_data = response.json()
        status_code = response.status_code
        logger.debug("Response Status code: {}".format(status_code))
        # logger.debug("Raw response data: {}".format(raw_response_data))

        if status_code == 200:
            data, metadata, is_truncated, next_token = self.postprocess_response(raw_response_data, model = model, start_token = start_token)

        else:
            logger.exception("Encountered error in response: {}".format(raw_response_data))

        return data, is_truncated, next_token, start_token
