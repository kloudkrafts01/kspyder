#!python3

import os, requests

from common.config import load_conf, AZ_PRICING_PROFILE
from common.spLogging import logger

MODELS = load_conf('azureRG_models', subfolder='manifests')
# UNPACKING = MODELS.pop('_UnpackingFields')
MODELS_LIST = list(MODELS.keys())

# mandatory connector config
SCHEMA_NAME = 'azureRetailPrices'
UPD_FIELD_NAME = 'write_date'

class AzurePricingConnector:

    def __init__(self, endpoint):
        self.endpoint = endpoint

def get_client(model_name):
    
    client = AzurePricingConnector(AZ_PRICING_PROFILE['url'])
    model = MODELS[model_name]

    return client, model

def get_count(client, model, search_domains=[]):

    total_count = 0

    return total_count

def read_query(client,model,search_domains=[],start_row=0):

    return 'TODO'


def forge_item(input_dict,model):
    '''TODO function to forge outputs from Azure Resource Graph API'''

    return input_dict

