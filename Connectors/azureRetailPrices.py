#!python3

from Engines.rpcExtractorEngine import GenericRPCExtractor
import os, requests

from common.config import load_conf, AZ_PRICING_PROFILE
from common.loggingHandler import logger

MODELS = load_conf('azureRG_models', subfolder='manifests')
MODELS_LIST = list(MODELS.keys())

# mandatory connector config
SCHEMA_NAME = 'azureRetailPrices'
UPD_FIELD_NAME = 'write_date'

class AzurePricingConnector(GenericRPCExtractor):

    def __init__(self, endpoint, schema=SCHEMA_NAME, models=MODELS, update_field=UPD_FIELD_NAME):

        self.endpoint = endpoint
        self.client = AzurePricingConnector(AZ_PRICING_PROFILE['url'])
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

