import os
from typing import Any
import jmespath
import requests

from common.config import BASE_FILE_HANDLER as fh
from common.loggingHandler import logger
from Engines.restExtractorEngine import RESTExtractor

_DIR = os.path.dirname(__file__)
CONF = fh.load_yaml('models', input=_DIR)

# mandatory connector config
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']
UPD_FIELD_NAME = CONNECTOR_CONF['update_field']
PAGE_SIZE = CONNECTOR_CONF['default_batch_size']
RATE_LIMIT = CONNECTOR_CONF['default_rate_limit']

APIS = CONF['APIs']
MODELS = CONF['Models']


class openDataConnector(RESTExtractor):

    def __init__(self, scopes: list[str] | None = None, schema: str = SCHEMA_NAME, models: dict = MODELS, apis: dict = APIS, update_field: str = UPD_FIELD_NAME, batch_size: int = PAGE_SIZE, rate_limit: int | None = RATE_LIMIT, **params: Any) -> None:

        self.schema = schema
        self.models = models
        self.apis = apis
        self.update_field = update_field
        self.scopes = scopes
        self.api_name = None
        self.base_url = None
        self.iterate_output = True
        self.rate_limit = rate_limit
        self.batch_size = batch_size

    def read_query(self, model: dict, start_token: Any = None, batch_size: int | None = None, **params: Any) -> tuple[list, bool, Any, Any]:

        actual_start_token, preprocessed_params = self.preprocess_params(params,start_token=start_token,batch_size=batch_size)

        url, headers, valid_params = self.build_request(model, baseurl = self.api.base_url, **preprocessed_params)

        # pass the request, get http status and response payload
        response = requests.get(url, headers = headers, params = valid_params)
        raw_response_data = response.json()
        status_code = response.status_code
        logger.debug("Response Status code: {}".format(status_code))

        if status_code == 200:
            data, metadata, is_truncated, next_token = self.postprocess_response(raw_response_data, model = model, start_token = actual_start_token)

        else:
            logger.exception("Encountered error in response: {}".format(raw_response_data))

        return data, is_truncated, next_token, actual_start_token
