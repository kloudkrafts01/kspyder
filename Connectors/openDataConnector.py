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

    def postprocess_item(self, item, model=None, status_code=None, **params):

        count_key = model['count_key'] if 'count_key' in model.keys() else None
        is_truncated = False
        next_token = 0
        raw_response_data = item.json()

        metadata = {}
        data = []

        if status_code == 200:

            response_data = {}

            for key, value in model['fields'].items():
                response_data[key] = jmespath.search(value, raw_response_data)

            # response_data = jmespath.search(model['datapath'], raw_response_data) if self.iterate_output else [raw_response_data]
            # logger.debug("Successful response data: {}".format(response_data))

            data = response_data.pop('data')
            metadata = response_data

            logger.debug("Item metadata: {}".format(metadata))

            count = int(response_data['total_count']) if 'total_count' in response_data. keys() else len(data)
            total_count = int(response_data['total_count']) if 'total_count' in response_data.keys() else None
            next_token = response_data['next_token'] if 'next_token' in response_data.keys() else None
            
            # Determine if the current results are truncated or not, based on explicit fields if present, or on number counts
            if 'is_truncated' in response_data.keys():
                is_truncated = response_data['is_truncated']
            else:
                if next_token is not None:
                    is_truncated = (next_token != "")
                elif total_count is not None:
                    is_truncated = (count < total_count) and (count > 0)
                else: 
                    is_truncated = False

        else:
            logger.exception("Encountered error in response: {}".format(response_data))

        return data, metadata, is_truncated, next_token


    def read_query(self, model, start_token=None, batch_size:int = 10, **params):

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

        status_code = response.status_code
        logger.debug("Response Status code: {}".format(status_code))
        # logger.debug("Raw response data: {}".format(raw_response_data))

        data, metadata, is_truncated, next_token = self.postprocess_item(response, model = model, status_code = status_code)

        # If page-based pagination, replace whatever next_token value with pagenumber +1
        if (self.pagination_style == "pages") and is_truncated:
            next_token = start_token + 1

        return data, is_truncated, next_token
