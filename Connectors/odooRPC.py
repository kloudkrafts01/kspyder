#!python3

from common.profileHandler import profileHandler
from common.extract import GenericExtractor
import xmlrpc.client
import ssl

from common.config import ODOO_PROFILE, PAGE_SIZE, BASE_FILE_HANDLER as fh


# Load the Connector's config
# CONF = load_conf('odoo_models', subfolder='manifests')
CONF = fh.load_yaml('odooRPCModels', subfolder=__name__)
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']
UPD_FIELD_NAME = CONNECTOR_CONF['update_field']
UNPACKING = CONF['UnpackingFields']
MODELS = CONF['Models']
MODELS_LIST = list(MODELS.keys())

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
    def from_profile(cls,profile_name):

        ph = profileHandler(input_folder=CONF)
        profile = ph.load_profile(profile_name=profile_name)

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


class OdooRPCConnector(GenericExtractor):

    def __init__(self, profile=ODOO_PROFILE, schema=SCHEMA_NAME, models=MODELS, update_field=UPD_FIELD_NAME,**params):

        # instantiate an Odoo XML-RPC client
        self.client = OdooClient.from_profile(profile)

        self.schema = schema
        self.models = models
        self.update_field = update_field

    def get_count(self, model=None, search_domains=[]):

        total_count = self.client.get_records_count(model=model,search_domains=search_domains)
        return total_count

    def read_query(self,model=None,search_domains=[],start_row=0):

        results = self.client.search_read(model=model,search_domains=search_domains,offset=start_row)
        return results


    def forge_item(self,odoo_dict,model=None):
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

