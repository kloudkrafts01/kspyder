#!python3

import os
import requests

from common.config import BASE_FILE_HANDLER as fh
from common.loggingHandler import logger
from Engines.restExtractorEngine import RESTExtractor

_DIR = os.path.dirname(__file__)
CONF = fh.load_yaml('models', input=_DIR)

CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']
UPD_FIELD_NAME = CONNECTOR_CONF['update_field']

APIS = CONF['APIs']
MODELS = CONF['Models']

API_VERSION = '2023-01-01-preview'


class AzureRetailPricesConnector(RESTExtractor):

    def __init__(self, schema=SCHEMA_NAME, models=MODELS, apis=APIS, update_field=UPD_FIELD_NAME, **params):

        self.schema = schema
        self.models = models
        self.apis = apis
        self.update_field = update_field
        self.scopes = None
        self.iterate_output = True
        self.rate_limit = None

    def read_query(self, model, search_domains=[], start_token=None, batch_size=None, **params):

        # N>1 requests: start_token is the full NextPageLink URL — delegate to base engine
        if start_token and str(start_token).startswith('https://'):
            return super().read_query(model, start_token=start_token, batch_size=batch_size, **params)

        # First request: build URL normally and inject the required api-version query param
        url, headers, valid_params = self.build_request(model, baseurl=self.api.base_url, **params)
        valid_params['api-version'] = API_VERSION
        response = requests.get(url, headers=headers, params=valid_params)

        status_code = response.status_code
        logger.debug("Response Status code: {}".format(status_code))

        if status_code == 200:
            raw_response_data = response.json()
            data, metadata, is_truncated, next_token = self.postprocess_response(
                raw_response_data, model=model, start_token=start_token)
        else:
            logger.exception("Encountered error in response: {}".format(response.text))
            data, is_truncated, next_token = [], False, None

        return data, is_truncated, next_token, start_token
