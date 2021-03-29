#!python3

import xmlrpc.client
import ssl

from common.config import ODOO_PROFILE, PAGE_SIZE, load_conf

MODELS = load_conf('odoo_models', subfolder='manifests')
UNPACKING = MODELS.pop('_UnpackingFields')
MODELS_LIST = list(MODELS.keys())

# mandatory connector config
SCHEMA_NAME = 'odoo'
UPD_FIELD_NAME = 'write_date'


class OdooClient:
    """Simple class to instanciate an XML-RPC client connected to the Odoo API and provide querying methods"""

    def __init__(self,url,dbname,username, password):
        
        self.url = url
        self.dbname = dbname
        self.__username = username
        self.__password = password

        self.common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(self.url),context=ssl._create_unverified_context())
        self.uid = self.common.authenticate(self.dbname, self.__username, self.__password, {})
        self.models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self.url),context=ssl._create_unverified_context())

    @classmethod
    def from_profile(cls,profile):
        return cls(
            profile['url'],
            profile['dbname'],
            profile['username'],
            profile['password']
        )

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


def get_client(model_name):

    # instantiate an Odoo XML-RPC client
    client = OdooClient.from_profile(ODOO_PROFILE)
    model = MODELS[model_name]

    return client, model

def get_count(client, model, search_domains=[]):

    total_count = client.get_records_count(model,search_domains=search_domains)
    return total_count

def read_query(client,model,search_domains=[],start_row=0):

    results = client.search_read(model,search_domains=search_domains,offset=start_row)
    return results


def forge_item(odoo_dict,model):
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

