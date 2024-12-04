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
        