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



class aliyunRAMConnector(AliyunRESTConnector):

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
        
    def read_query(self, model, search_domains=..., start_token=None, **params):
        
        # Instanciate a request object with the sdk module needed arguments
        request_params = {
            str.lower(self.next_token_key): start_token
        } if start_token else {}

        if 'accepted_inputs' in model.keys():
            accepted_inputs = (x['key'] for x in model['accepted_inputs'])
            # mandatory_inputs = (x['key'] for x in model['accepted_inputs'] if x['mandatory'])
            valid_params = (x for x in params.keys() if x in accepted_inputs)
            
            for key in valid_params:
                request_params[key] = params[key]

        request = self.build_request(
            model,
            **request_params
            )
        
        # Prepare the arguments for the query builder
        query_args = [
            request,
            self.runtime_options
        ]

        # Execute the query using the interface's method
        return super().read_query(model, search_domains, start_token, query_args, **params)
        