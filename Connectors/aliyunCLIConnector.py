#!python3

import subprocess

from common.extract import GenericExtractor
from common.spLogging import logger

from common.config import PAGE_SIZE, BASE_FILE_HANDLER as fh


# Load the Connector's config
CONF = fh.load_yaml('aliyunCLIModels', subpath=__name__)
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

        command = ['aliyun', model['class']]
        # build the basics : 'scope' is supposed to be one type of query that fits the model
        if scope in model['scopes']:
            command += scope,
        else:
            errmsg_tmpl = '{} :: {} is not a valid scope for the {} model.\nAccepted scopes are: {}'
            errmsg = errmsg_tmpl.format(__name__, scope, model['base_name'], model['scopes'])
            logger.error(errmsg)
            raise ValueError(errmsg)

        # add search filters if any
        for domain in search_domains:
            # if there was a given start_time, the syntax is a bit different
            if domain[0] == self.update_field:
                timefilter = [
                    '--Filter.1.Key',
                    domain[0],
                    '--Filter.1.Value',
                    domain[2]
                ]
                command = command + timefilter
            else:
                command = command + [f'--{domain[0]}', domain[2]]
        
        logger.debug('{} :: Aliyun command: {}'.format(__name__, command))

        return command

    def get_records_count(self,model,scope,search_domains=[]):
        
        command = self.build_command(model,scope,search_domains=search_domains)
        result = subprocess.run(command)
        return result['TotalCount']

    def search_read(self,model,scope,search_domains=[],offset=None,limit=PAGE_SIZE):

        # fields = model['fields']
        # pkeys = [x for x in fields.keys() if 'primary_key' in fields[x].keys()]
        # paramsDict = {'fields': fields, 'order': pkeys[0]}

        # add_params = []

        if limit:
            # for AliyunCLI pafge size is strictly limited to 100
            capped_limit = limit if limit < 100 else 100
            # paramsDict['limit'] = capped_limit
            search_domains += ['--PageSize', '=', capped_limit],

            if offset:
                # paramsDict['offset'] = offset
                # in AliyunCLI the offset is given as a page number
                pageno = offset / capped_limit + 1
                search_domains += ['--PageNumber', '=', pageno],

        # Build the command and add up the offset and page size params
        command = self.build_command(model,scope,search_domains=search_domains)
        result = subprocess.run(command)

        base_name = model['base_name']
        basename_plural = base_name + 's'

        dataset = result[basename_plural][base_name]

        return dataset


class aliyunCLIConnector(GenericExtractor):

    def __init__(self, schema=SCHEMA_NAME, models=MODELS, update_field=UPD_FIELD_NAME,**params):

        self.schema = schema
        self.models = models
        self.update_field = update_field
        self.client = aliyunCLIClient(update_field)

    def get_count(self, model, scopes=['default'], search_domains=[]):

        total_count = 0
        
        if scopes == ['default']:
            scopes = model['scopes']

        for scope in scopes:
            result = self.client.get_records_count(model,scope,search_domains)
            total_count += result['TotalCount']
        
        return total_count

    def read_query(self, model, scopes=['default'], search_domains=[], start_row=0):

        if scopes == ['default']:
            scopes = model['scopes']

        for scope in scopes:
            results = self.client.search_read(model,scope,search_domains=search_domains,offset=start_row)
            dataset = dataset + results

        return results


    def forge_item(self,dictitem,model):
        '''function to split Odoo dict objects that contain two-value list as values, as it can happen when getting stuff from the Odoo RPC API.
        The values are split into two distinct fields, and if needed the second field can be dropped (e.g. when it contains PII we don't want to keep).'''

        new_dict = {}
        fields = model['fields']

        for key,value in dictitem.items():

            isInFieldMap = (key in fields)

            if isInFieldMap:
                
                new_key = fields[key]['dbname']
                new_dict[new_key] = value

            # for now, filter out elements not in the model target fields
            # else:
            #     new_dict[key] = value

        return new_dict

