import re
import jmespath
import requests
from urllib.parse import urljoin

from akamai.edgegrid import EdgeGridAuth, EdgeRc


from common.config import MODULES_MAP, BASE_FILE_HANDLER as fh
from common.spLogging import logger
from Engines.restExtractorEngine import RESTExtractor

CONF = fh.load_yaml(MODULES_MAP[__name__], subpath=__name__)

# mandatory connector config
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']
UPD_FIELD_NAME = CONNECTOR_CONF['update_field']

MODELS = CONF['Models']

class akamaiClient():

    def __init__(self):

        edgerc = EdgeRc('~/.edgerc')
        default_section = 'default'
        self.baseurl = 'https://{}'.format(edgerc.get(default_section, 'host'))

        self.session = requests.Session()
        self.session.auth = EdgeGridAuth.from_edgerc(edgerc, default_section)



class akamaiConnector(RESTExtractor):

    def __init__(self, scopes=None, schema=SCHEMA_NAME, models=MODELS, update_field = UPD_FIELD_NAME, **params):

        self.schema = schema
        self.models = models
        self.update_field = update_field
        self.scopes = scopes

        self.client = akamaiClient()
    
    def build_query(self,model,**params):

        # Get parameters with accepted keys
        valid_params = {}
        if 'accepted_inputs' in model.keys():
            valid_keys = (x for x in params.keys() if x in model['accepted_inputs'])
            valid_params_list = [ {k:params[k]} for k in valid_keys ]
            for param in valid_params_list:
                valid_params = { **valid_params, **param }
        else:
            valid_params = params

        logger.debug("Initial Valid Params: {}".format(valid_params))

        # build URL
        logger.debug("Now building Query URL...")
        path_expression = model['path']
        url_path = path_expression
        for key,value in valid_params.items():
            # Compile and search for the parameter key in the URL path expression
            pattern_string = '\{\$(%s)\}' % key
            var_pattern = re.compile(pattern_string,re.I)
            matches = re.search(var_pattern, path_expression).groups()
            for matched_item in matches:
                # if parameter was matched, pop it out of query params and sub the expression
                logger.debug("Matched following item in path: {}".format(matched_item))
                url_path = re.sub(var_pattern, str(value), url_path)
                # valid_params.pop(key)
        

        url = urljoin(self.client.baseurl, url_path)
        logger.debug("Query URL: {}".format(url))
        logger.debug("Final Valid Params: {}".format(valid_params))

        headers = model['headers']

        return url, headers, valid_params


    def read_query(self,model,start_token=None,**params):

        url, headers, valid_params = self.build_query(model,**params)
        response = self.client.session.get(url, headers = headers, params = valid_params)

        next_token = 'toto'
        # infer if is truncated from this, cause the natural field result_truncated ain't worth shit
        is_truncated = False

        result = response.status_code
        logger.debug("Result: {}".format(result))
        raw_response_data = response.json()
        response_data = []

        if result == 200:
            response_data = jmespath.search(model['datapath'], raw_response_data)
            # response_data = raw_response_data
            logger.debug("Successful response data: {}".format(response_data))

        else:
            logger.error("Encountered error in response: {}".format(response_data))

        return response_data, is_truncated, next_token
