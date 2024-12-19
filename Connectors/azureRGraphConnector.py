# import os
import jmespath

from azure.identity import DefaultAzureCredential
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest,QueryRequestOptions
from azure.mgmt.subscription import SubscriptionClient

from common.config import PAGE_SIZE, CONF_FOLDER, BASE_FILE_HANDLER as fh
from common.profileHandler import profileHandler
from common.spLogging import logger
from Engines.restExtractorEngine import RESTExtractor

CONF = fh.load_yaml('azureRGraphModels', subpath=__name__)
# CONNECTOR_CONF_FOLDER = os.path.join(CONF_FOLDER,__name__)

# mandatory connector config
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']
UPD_FIELD_NAME = CONNECTOR_CONF['update_field']
DEFAULT_FIELDS = CONNECTOR_CONF['default_fields']
DEFAULT_CLASS = CONNECTOR_CONF['default_class']

MODELS = CONF['Models']

class azureRGraphClient(ResourceGraphClient):

    def __init__(self):

        self.credential = DefaultAzureCredential()
        # Instantiate Azure Resource Graph Client with Credential
        ResourceGraphClient.__init__(
            self,
            credential = self.credential
        )

    def get_subscriptions(self):

        # Instantiate azure Subscriptions Client
        sub_client = SubscriptionClient( 
            credential = self.credential
        )
        sub_iter = sub_client.subscriptions.list()
        subscriptions = []

        for sub in sub_iter:
            subscriptions += sub.__dict__,

        return subscriptions


class azureRGraphConnector(RESTExtractor):

    def __init__(self, scopes=None, schema=SCHEMA_NAME, models=MODELS, update_field = UPD_FIELD_NAME, **params):

        self.schema = schema
        self.models = models
        self.update_field = update_field

        self.client = azureRGraphClient()

        self.subscriptions = self.client.get_subscriptions()
        # set the subscription IDs and scope names from the scopes specified in the request,
        # or all subscription IDs if no scope was specified
        self.scopes = None
        self.subscription_ids = None
        self.set_scopes_and_subscription_ids(scopes)
    
    def set_scopes_and_subscription_ids(self,scopes=None):
        
        subscription_ids = []
        print(scopes)

        if scopes:
            logger.debug("setting subscription Ids from names: {}".format(scopes))
            self.scopes = scopes
            subscription_ids = [x['subscription_id'] for x in self.subscriptions if x['display_name'] in scopes]
        else:
            logger.debug("setting all subscription Ids")
            # Explicitly set all scopes names for clarity and logging
            all_scopes = jmespath.search('[].display_name', self.subscriptions)
            self.scopes = all_scopes
            subscription_ids = jmespath.search('[].subscription_id', self.subscriptions)

        # logger.debug("Final Scope names: {}".format(self.scopes))
        # logger.debug("Final Subscription Ids: {}".format(subscription_ids))

        self.subscription_ids = subscription_ids

    def read_query(self,model,start_token=None,**params):

        request = self.build_request(model,start_token=start_token)
        query_response = self.client.resources(request)

        # the base Azure object spits out 'true' or 'false' in string format.
        # which is the dumbest thing ever. Have to convert it to boolean like that
        is_truncated = (query_response.result_truncated == True)

        next_token = query_response.skip_token
        result = query_response.data

        return result, is_truncated, next_token


    def build_request(self, model, start_token=None, page_size=PAGE_SIZE, **params):

        class_scope = model['class'] if 'class' in model.keys() else DEFAULT_CLASS
        base_name = model['base_name']
        fieldnames = model['fields'] if 'fields' in model.keys() else DEFAULT_FIELDS

        query_string = "{} | where type =~ '{}' | project {}".format(class_scope, base_name, fieldnames)
        logger.debug("QUERY STRING : {}".format(query_string))

        request_params = { 'skip_token': start_token } if start_token else {}

        request_options = QueryRequestOptions(
            top = page_size,
            **request_params
        )

        # Instantiate request object
        request = QueryRequest(
                query=query_string,
                subscriptions = self.subscription_ids,
                options = request_options
            )

        return request


