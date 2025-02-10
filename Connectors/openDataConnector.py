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

APIS = CONF['APIs']
MODELS = CONF['Models']



class openDataConnector(RESTExtractor):

    def __init__(self, scopes=None, schema=SCHEMA_NAME, models=MODELS, apis=APIS, update_field = UPD_FIELD_NAME, **params):

        self.schema = schema
        self.models = models
        self.apis = apis
        self.update_field = update_field
        self.scopes = scopes
        self.api_name = None
        self.base_url = None
        self.iterate_output = True
        self.rate_limit = None


    def read_query(self, model, start_token=None, batch_size:int = 50, **params):

        if start_token is None:
            start_token = 1

        if self.next_token_key:
            start_param = { self.next_token_key : start_token }
            params = { **params, **start_param }

        if self.batch_size_key:
            size_param = { self.batch_size_key : batch_size }
            params = { **params, **size_param }

        logger.debug("Params: {}".format(params))

        url, headers, valid_params = self.build_request(model, baseurl = self.base_url, **params)
        response = requests.get(url, headers = headers, params = valid_params)

        result = response.status_code
        logger.debug("Result: {}".format(result))
        raw_response_data = response.json()
        # logger.debug("Raw response data: {}".format(raw_response_data))

        count_key = model['count_key'] if 'count_key' in model.keys() else None
        is_truncated = False
        next_token = 0

        response_data = []

        if result == 200:
            response_data = jmespath.search(model['datapath'], raw_response_data) if self.iterate_output else [raw_response_data]
            # logger.debug("Successful response data: {}".format(response_data))

            count = len(response_data) 
            total_count = int(jmespath.search(count_key, raw_response_data)) if count_key else count

            if (count < total_count) and (count > 0):
                is_truncated = True

            next_token = start_token + 1

        else:
            logger.exception("Encountered error in response: {}".format(response_data))

        return response_data, is_truncated, next_token
