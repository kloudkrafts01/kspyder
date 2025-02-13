import jmespath
import requests

from akamai.edgegrid import EdgeGridAuth, EdgeRc


from common.config import MODULES_MAP, BASE_FILE_HANDLER as fh
from common.loggingHandler import logger
from Engines.restExtractorEngine import RESTExtractor

CONF = fh.load_yaml(MODULES_MAP[__name__], subpath=__name__)

# mandatory connector config
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']
UPD_FIELD_NAME = CONNECTOR_CONF['update_field']

MODELS = CONF['Models']
APIS = CONF['APIs']

class akamaiClient():

    def __init__(self):

        edgerc = EdgeRc('~/.edgerc')
        default_section = 'default'
        self.baseurl = 'https://{}'.format(edgerc.get(default_section, 'host'))

        self.session = requests.Session()
        self.session.auth = EdgeGridAuth.from_edgerc(edgerc, default_section)


class akamaiConnector(RESTExtractor):

    def __init__(self, scopes=None, schema=SCHEMA_NAME, models=MODELS, apis=APIS, update_field = UPD_FIELD_NAME, **params):

        self.schema = schema
        self.models = models
        self.apis = apis
        self.update_field = update_field
        self.scopes = scopes
        self.iterate_output = True
        self.rate_limit = None
        self.response_map = {}

        self.client = akamaiClient()


    def read_query(self, model, start_token:int = 1, batch_size:int = 100, **params):

        data = []
        metadata = {}
        is_truncated = False
        next_token = None

        params, start_token, batch_size = self.preprocess_params(params,start_token=start_token,batch_size=batch_size)

        url, headers, valid_params = self.build_request(model, baseurl = self.client.baseurl, **params)
        
        # pass the request, get http status and response payload
        response = self.client.session.get(url, headers = headers, params = valid_params)
        raw_response_data = response.json()
        status_code = response.status_code
        logger.debug("Response Status code: {}".format(status_code))
        # logger.debug("Raw response data: {}".format(raw_response_data))

        if status_code == 200:
            data, metadata, is_truncated, next_token = self.postprocess_response(raw_response_data, model = model, start_token = start_token)

        else:
            logger.exception("Encountered error in response: {}".format(raw_response_data))

        return data, is_truncated, next_token, start_token
