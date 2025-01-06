# from google.cloud.resourcemanager import FoldersClient,ListFoldersRequest
import proto

from common.config import MODULES_MAP, DUMP_JSON, BASE_FILE_HANDLER as fh
from common.loggingHandler import logger
from importlib import import_module

# from google.cloud import resourcemanager

from Engines.gcloudSDKEngine import gcloudSDKEngine

CONF = fh.load_yaml('gcloudRMmodels', subpath='gcloudSDKConnectors')
logger.debug("CONF: {}".format(CONF))
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']
UPD_FIELD_NAME = CONNECTOR_CONF['update_field']
MODELS = CONF['Models']

# Import the connector python module from google.cloud
CONNECTOR_CLASSNAME = CONNECTOR_CONF['name']
CONNECTOR_CLASS = import_module('google.cloud.{}'.format(CONNECTOR_CLASSNAME))


class gcloudResourceManagerConnector(gcloudSDKEngine):

    def __init__(self, client=None, schema=SCHEMA_NAME, models=MODELS, update_field=UPD_FIELD_NAME, connector_class=CONNECTOR_CLASS, **params):
        gcloudSDKEngine.__init__(self,
                    client=client,
                    schema=schema,
                    models=models,
                    update_field=update_field,
                    connector_class=connector_class,
                    **params
                    )
        
    def postprocess_item(self, item, model=None, **params):
        """Run returned items through JSON serialization"""
        return proto.Message.to_dict(item)
    
    def discover_data(self, model_name=None, root_element=None, **params):
        
        model = self.models[model_name]
        # Instantiate the relevant API client class from google.cloud
        self.set_client_from_model(model)
        
        return super().discover_data(model_name, root_element, **params)
