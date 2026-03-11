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

MODELS = CONF['Models']
APIS = CONF['APIs']

class AzurePricingConnector(RESTExtractor):

    def __init__(self, endpoint, schema=SCHEMA_NAME, models=MODELS, update_field=UPD_FIELD_NAME):

        self.endpoint = endpoint
        self.client = RetailPriceClient(AZ_PRICING_PROFILE['url'])
        self.schema = schema
        self.models = models
        self.update_field = update_field

    def get_count(self, model, search_domains=[]):

        total_count = 0

        return total_count

    def read_query(self,model,search_domains=[],start_row=0):

        return 'TODO'


    def forge_item(self,input_dict,model):
        '''TODO function to forge outputs from Azure Resource Graph API'''

        return input_dict

