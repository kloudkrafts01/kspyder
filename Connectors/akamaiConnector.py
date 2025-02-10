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

        self.client = akamaiClient()


    def read_query(self,model,start_token=None,**params):

        url, headers, valid_params = self.build_request(model, baseurl = self.client.baseurl, **params)
        response = self.client.session.get(url, headers = headers, params = valid_params)

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
