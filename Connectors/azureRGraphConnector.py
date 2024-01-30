import os

from azure.identity import DefaultAzureCredential
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest

from common.config import PAGE_SIZE, CONF_FOLDER, BASE_FILE_HANDLER as fh
from common.spLogging import logger
from common.profileHandler import profileHandler
from common.extract import GenericExtractor

# build config folder path from module's name
CONF_PATH = os.path.join(CONF_FOLDER,__name__)
CONF = fh.load_yaml('azureRGraphModels', subpath=__name__)

# mandatory connector config
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']
UPD_FIELD_NAME = CONNECTOR_CONF['update_field']

MODELS = CONF['Models']
MODELS_LIST = list(MODELS.keys())
UNPACKING = CONF['UnpackingFields']


class azureRGraphConnector(GenericExtractor):

    def __init__(self, scope='default', schema=SCHEMA_NAME, models=MODELS, update_field = UPD_FIELD_NAME):

        self.scope = scope
        self.schema = schema
        self.models = models
        self.update_field = update_field

        self.credential = DefaultAzureCredential()

        # initialize Azure Resource Graph Client from profile info
        ph = profileHandler(input_folder=CONF_PATH)
        self.profile = ph.load_profile('azureRGraphProfile', scope=self.scope)
        self.subscription_id = self.profile['id']
        
        logger.debug("{} PROFILE OBJ: {}".format(__name__,self.profile))
        
        self.client = ResourceGraphClient(
            credential = self.credential,
            subscription_id = self.subscription_id
        )

    def get_count(self, model, search_domains=[]):

        queryStr = self.build_query(model, count=True)

        query = QueryRequest(
                query=queryStr,
                subscriptions = [self.subscription_id]
            )
        query_response = self.client.resources(query)

        total_count = query_response.data[0]['Count']

        return total_count

    def read_query(self,model,search_domains=[],start_row=0):

        queryStr = self.build_query(model)
        
        query = QueryRequest(
                query=queryStr,
                subscriptions = [self.subscription_id]
            )
        query_response = self.client.resources(query)

        return query_response.data


    def build_query(self, model, page_size=PAGE_SIZE, count=False):

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

