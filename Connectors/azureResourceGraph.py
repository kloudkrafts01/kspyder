#!python3

from common.extract import GenericExtractor
import os

from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest

from common.config import AZURE_CLIENT, PAGE_SIZE, CONF_FOLDER, BASE_FILE_HANDLER as fh
from common.spLogging import logger
from common.profileHandler import profileHandler

# build config folder path from module's name
CONF_PATH = os.path.join(CONF_FOLDER,__name__)
CONF = fh.load_yaml('azureRGraphModels', subpath=__name__)

# mandatory connector config
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONF['schema']
UPD_FIELD_NAME = CONF['update_field']

MODELS = CONF['Models']
MODELS_LIST = list(MODELS.keys())
UNPACKING = CONF['UnpackingFields']

# def format_azprofiles(input=None):

#     raw_profiles = load_conf(input,folder='local_only')
#     output_dict = {}
#     for profile in raw_profiles:
#         name = profile['name']
#         output_dict[name] = profile
    
#     return output_dict

# # DEFAULT_SCOPE = os.environ.get("AZURE_SUBSCRIPTION_ID", None)
# AZURE_PROFILES = format_azprofiles('azure_subs')
# AZURE_SCOPES = list(AZURE_PROFILES.keys())
# DEFAULT_PROFILE = [x for x in AZURE_PROFILES.values() if x['isDefault']][0]



class AzureRGConnector(GenericExtractor):

    def __init__(self, scope, schema=SCHEMA_NAME, models=MODELS, update_field = UPD_FIELD_NAME):

        self.scope = scope
        self.schema = schema
        self.models = models
        self.update_field = update_field

        # initialize Azure Resource Graph Client from profile info
        ph = profileHandler(input_folder=CONF_PATH)
        self.profile = ph.load_profile('azureRGraphProfile', scope=self.scope)
        self.subscription_id = self.profile['id']
        
        logger.debug("{} PROFILE OBJ: {}".format(__name__,self.profile))
        
        self.client = ResourceGraphClient(
            credential = AZURE_CLIENT.credential,
            subscription_id = self.subscription_id
        )

    def get_count(self, model, search_domains=[]):

        queryStr = self.forge_query(model, count=True)

        query = QueryRequest(
                query=queryStr,
                subscriptions = [self.scope_id]
            )
        query_response = self.client.resources(query)

        total_count = query_response.data[0]['Count']

        return total_count

    def read_query(self,model,search_domains=[],start_row=0):

        queryStr = self.forge_query(model)
        
        query = QueryRequest(
                query=queryStr,
                subscriptions = [self.scope_id]
            )
        query_response = self.client.resources(query)

        return query_response.data


    def forge_query(self, model, page_size=PAGE_SIZE, count=False):

        class_scope = None
        if 'class' in model.keys():
            class_scope = model['class']
        else:
            class_scope = 'Resources'

        base_name = model['base_name']
        fieldnames = ''
        for key in model['fields'].keys():
            fieldnames += key + ","
        #remove trailing comma
        fieldnames = fieldnames[0:-1]

        queryStr = "{} | where type =~ '{}' | project {}".format(class_scope, base_name, fieldnames)
        if count:
            queryStr += " | count"
        else:
            queryStr += " | limit {}".format(page_size)

        logger.debug("QUERY STR : {}".format(queryStr))

        return queryStr

    def forge_item(self,input_dict,model):
        '''TODO function to forge outputs from Azure Resource Graph API'''

        return input_dict

