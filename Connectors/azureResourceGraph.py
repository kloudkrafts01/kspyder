#!python3

import os

from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest

from common.config import AZURE_CLIENT, PAGE_SIZE, load_conf

MODELS = load_conf('azureRG_models', subfolder='manifests')
# UNPACKING = MODELS.pop('_UnpackingFields')
MODELS_LIST = list(MODELS.keys())

# mandatory connector config
SCHEMA_NAME = 'azureRG'
UPD_FIELD_NAME = 'write_date'


def get_client(model_name):

    # If "SUBSCRIPTION_ID" is not set in the environment variable, you need to set it manually: export SUBSCRIPTION_ID="{SUBSCRIPTION_ID}"
    SUBSCRIPTION_ID = os.environ.get("AZURE_SUBSCRIPTION_ID", None)

    # Create client
    # For other authentication approaches, please see: https://pypi.org/project/azure-identity/
    client = ResourceGraphClient(
        credential=AZURE_CLIENT.credential,
        subscription_id=SUBSCRIPTION_ID
    )

    model = MODELS[model_name]

    return client, model

def get_count(client, model, search_domains=[]):

    queryStr = forge_query(model)
    queryStr += " | count"

    query = QueryRequest(
            query=queryStr,
            subscriptions=client.subscription_id
        )
    query_response = client.resources(query)

    total_count = query_response['data'][0]['Count']
    return total_count

def read_query(client,model,search_domains=[],start_row=0):

    queryStr = forge_query(model)
    
    query = QueryRequest(
            query=queryStr,
            subscriptions=client.subscription_id
        )
    query_response = client.resources(query)
    print("Basic query :\n{}".format(query_response))

    return query_response


def forge_query(model, page_size=PAGE_SIZE):

    class_scope = None
    if 'class' in model.keys():
        class_scope = model['class']
    else:
        class_scope = 'Resources'

    base_name = model['base_name']
    fieldnames = model['fields'].keys()

    queryStr = "{} | type =~ {} | project {} | limit {}".format(class_scope, base_name, fieldnames, page_size)

    return queryStr

def forge_item(input_dict,model):
    '''TODO function to forge outputs from Azure Resource Graph API'''

    return input_dict

