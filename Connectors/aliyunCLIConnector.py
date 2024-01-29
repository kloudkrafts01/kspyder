#!python3

import subprocess

from common.extract import GenericExtractor
from common.spLogging import logger

from common.config import ODOO_PROFILE, PAGE_SIZE, BASE_FILE_HANDLER as fh


# Load the Connector's config
# CONF = load_conf('odoo_models', subfolder='manifests')
CONF = fh.load_yaml('aliyunCLIModels', subfolder=__name__)
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']
UPD_FIELD_NAME = CONNECTOR_CONF['update_field']
UNPACKING = CONF['UnpackingFields']
MODELS = CONF['Models']
MODELS_LIST = list(MODELS.keys())

class aliyunCLIClient:
    """Class to process the raw output of an Aliyun CLI command, because the python sdk sucks.
    This WILL NOT set or authenticate to your Aliyun context, you have to run locally 'aliyun configure'"""

    def __init__(self, update_field=UPD_FIELD_NAME):
        
        self.update_field = update_field
    
    def build_command(self,model,scope,search_domains=[]):

        command_str = ''
        # build the basics : 'scope' is supposed to be one type of query that fits the model
        if scope in model['scopes']:
            command_str = 'aliyun {} {} '.format(model['class'], scope)
        else:
            errmsg_tmpl = '{} :: {} is not a valid scope for the {} model.\nAccepted scopes are: {}'
            errmsg = errmsg_tmpl.format(__name__, scope, model, model['scopes'])
            logger.error(errmsg)
            raise ValueError(errmsg)

        # add search filters if any
        for domain in search_domains:
            if domain[0] == self.update_field:
                last_time = 
                timefilter = '--Filter.1.Key {} --Filter.1.Value {} '.format(self.update_field, last_time)
                command_str += timefilter
            command_str += '--{} {} '.format(domain[0], domain[2])
        


        return command_str




    def get_records_count(self,model,search_domains=[]):
        
        result = self.models.execute_kw(
            self.dbname, self.uid, self.__password,
            model['odoo_name'], 'search_count',
            [search_domains]
        )
        return result

    def search_read(self,model,search_domains=[],offset=None,limit=PAGE_SIZE):

        fields = model['fields']
        paramsDict = {'fields': fields, 'order': 'id'}

        if offset:
            paramsDict['offset'] = offset

        if limit:
            paramsDict['limit'] = limit

        result = self.models.execute_kw(
            self.dbname, self.uid, self.__password,
            model['odoo_name'], 'search_read',
            [search_domains],
            paramsDict
        )
        return result


class aliyunCLIConnector(GenericExtractor):

    def __init__(self, profile=ODOO_PROFILE, schema=SCHEMA_NAME, models=MODELS, update_field=UPD_FIELD_NAME,**params):

        # instantiate an Odoo XML-RPC client
        self.client = aliyunCLIClient()
        self.schema = schema
        self.models = models
        self.update_field = update_field

    def get_count(self, model, search_domains=[]):

        total_count = self.client.get_records_count(model,search_domains=search_domains)
        return total_count

    def read_query(self,model,search_domains=[],start_row=0):

        results = self.client.search_read(model,search_domains=search_domains,offset=start_row)
        return results


    def forge_item(self,odoo_dict,model):
        '''function to split Odoo dict objects that contain two-value list as values, as it can happen when getting stuff from the Odoo RPC API.
        The values are split into two distinct fields, and if needed the second field can be dropped (e.g. when it contains PII we don't want to keep).'''

        new_dict = {}
        fields = model['fields']

        for key,value in odoo_dict.items():

            isInFieldMap = (key in fields)
            isInUnpack = (key in UNPACKING)

            if isInFieldMap and isInUnpack and value:

                new_key = fields[key]['dbname']
                new_dict[new_key] = value[0]
                additional_field = UNPACKING[key]
                
                if additional_field is not None:
                    additional_key = additional_field['dbname']
                    new_dict[additional_key] = value[1]

            elif isInFieldMap:
                
                new_key = fields[key]['dbname']
                new_dict[new_key] = value

            else:
                new_dict[key] = value

        return new_dict
