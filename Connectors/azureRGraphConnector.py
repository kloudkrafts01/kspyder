from azure.identity import DefaultAzureCredential
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest,QueryRequestOptions

from common.config import PAGE_SIZE, BASE_FILE_HANDLER as fh
from common.spLogging import logger
from Engines.restExtractorEngine import RESTExtractor

CONF = fh.load_yaml('azureRGraphModels', subpath=__name__)

# mandatory connector config
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']
UPD_FIELD_NAME = CONNECTOR_CONF['update_field']
DEFAULT_FIELDS = CONNECTOR_CONF['default_fields']
DEFAULT_CLASS = CONNECTOR_CONF['default_class']

MODELS = CONF['Models']

class azureRGraphConnector(RESTExtractor):

    def __init__(self, scope='default', schema=SCHEMA_NAME, models=MODELS, update_field = UPD_FIELD_NAME):

        self.scope = scope
        self.schema = schema
        self.models = models
        self.update_field = update_field

        self.credential = DefaultAzureCredential()
        self.subscription_id = scope
        
        self.client = ResourceGraphClient(
            credential = self.credential
            # subscription_id = self.subscription_id
        )


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

        request = QueryRequest(
                query=query_string,
                subscriptions = [self.subscription_id],
                options = request_options
            )

        return request


