#!python3

from common.config import MODULES_MAP, BASE_FILE_HANDLER as fh
from common.loggingHandler import logger
from importlib import import_module

from Engines.gcloudSDKEngine import gcloudSDKEngine

CONF = fh.load_yaml(MODULES_MAP[__name__], subpath='gcloudSDKConnectors')
logger.debug("CONF: {}".format(CONF))
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']
UPD_FIELD_NAME = CONNECTOR_CONF['update_field']
DEFAULT_SCOPE = CONNECTOR_CONF['default_scope']
logger.debug("DEFAULT SCOPE: {}".format(DEFAULT_SCOPE))
MODELS = CONF['Models']

# Import the connector python module from google.cloud
CONNECTOR_CLASSNAME = CONNECTOR_CONF['name']
CONNECTOR_CLASS = import_module('google.cloud.{}'.format(CONNECTOR_CLASSNAME))

class gcloudComputeConnector(gcloudSDKEngine):

    def __init__(self, client=None, schema=SCHEMA_NAME, scopes=DEFAULT_SCOPE, models=MODELS, update_field=UPD_FIELD_NAME, connector_class=CONNECTOR_CLASS, **params):
        gcloudSDKEngine.__init__(self,
                    client=client,
                    schema=schema,
                    scopes=scopes,
                    models=models,
                    update_field=update_field,
                    connector_class=connector_class,
                    **params
                    )
