#!python3

from common.config import MODULES_MAP, BASE_FILE_HANDLER as fh
from common.spLogging import logger

from Engines.aliyunSDKEngine import AliyunClient,AliyunRESTConnector

CONF = fh.load_yaml(MODULES_MAP[__name__], subpath=__name__)
logger.debug("CONF: {}".format(CONF))
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']
UPD_FIELD_NAME = CONNECTOR_CONF['update_field']
MODELS = CONF['Models']


class aliyunCSConnector(AliyunRESTConnector):

    def __init__(self, profile=None, schema=SCHEMA_NAME, models=MODELS, update_field=UPD_FIELD_NAME, scope=None, **params):
        
        aliyun_client = AliyunClient.from_env(
            connector_name=CONNECTOR_CONF['name']
            )
        
        AliyunRESTConnector.__init__(
            self,
            aliyun_client,
            profile=profile,
            schema=schema,
            models=models,
            update_field=update_field,
            scope=scope,
            connector_conf=CONNECTOR_CONF,
            **params
            )
        
        # self.client = AliyunClient.from_env().client
        # self.runtime_options = RuntimeOptions()

        # self.schema = schema
        # self.models = models
        # self.scope = scope
        # self.params = params
    
    # def load_conf(self):
    #     self.conf = fh.load_yaml(MODULES_MAP[__name__], subpath=__name__)


    # def read_query(self,model,search_domains=[],start_token=None,**params):

    #     # Import request builder and instanciate a request in context
    #     request_params = {}
    #     request_builder = getattr(SourceModels, model['request_builder'])
    #     request = request_builder(**request_params)

    #     # Build and send a query with the request context
    #     query = getattr(self.client, model['query_name'])
    #     headers = {}
    #     response = query(
    #         request,
    #         headers,
    #         self.runtime_options
    #     )

    #     # Parse response and retrieve relevant data
    #     response_dict = response.body.to_map()
    #     results = []

    #     if model['datapath'] == '$root':
    #         results = response_dict
    #     else:
    #         datapath = jmespath.compile(model['datapath'])
    #         results = datapath.search(response_dict)
        
    #     is_truncated = response_dict[IS_TRUNCATED_KEY] if IS_TRUNCATED_KEY in response_dict.keys() else None
    #     next_token = response_dict[NEXT_TOKEN_KEY] if NEXT_TOKEN_KEY in response_dict.keys() else None

    #     return results, is_truncated, next_token