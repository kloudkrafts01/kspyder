#!python3

import subprocess
import json

from common.extract import DirectExtractor
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

# specific formatting expected by Aliyun CLI when filtering over a datetime
DATETIME_FORMAT = '%Y-%m-%dT%H:%mZ'

class aliyunCLIClient:
    """Class to process the raw output of an Aliyun CLI command, because the python sdk sucks.
    This WILL NOT set or authenticate to your Aliyun context, you have to run locally 'aliyun configure'"""

    def __init__(self, update_field=UPD_FIELD_NAME):
        
        self.update_field = update_field
    
    def build_command(self,model=None,query_domain=None,search_domains=[]):

        command = ['aliyun', model['class']]
        # build the basics : 'query_domain' is supposed to be one type of query that fits the model
        if query_domain in model['query_domains']:
            command += query_domain,
        else:
            errmsg_tmpl = '{} :: {} is not a valid query_domain for the {} model.\nAccepted query_domain are: {}'
            errmsg = errmsg_tmpl.format(__name__, query_domain, model['base_name'], model['query_domains'])
            logger.error(errmsg)
            raise ValueError(errmsg)

        # add search filters if any
        for domain in search_domains:
            # if there was a given start_time, the syntax is a bit different
            if domain[0] == self.update_field:
                time_str = domain[2].strftime(DATETIME_FORMAT)
                timefilter = [
                    '--Filter.1.Key',
                    self.update_field,
                    '--Filter.1.Value',
                    time_str
                ]
                command = command + timefilter
            else:
                command = command + [f'--{domain[0]}', domain[2]]
        
        # # add the tabular formatting cmdlets
        # command = self.add_tabular_cmdlets(command,model)

        logger.debug('{} :: Aliyun command: {}'.format(__name__, command))

        return command

    def add_tabular_cmdlet(self,command,model=None):
        # add the tabular formatting cmdlets
        base_name = model['base_name']
        rows_cmdlet = 'rows="{}s.{}[*]"'.format(base_name,base_name)
        cols_string = ''
        for field_name,field_data in model['fields'].items():
            cols_string = cols_string + field_name + ","
        # remove last trailing comma
        cols_string = cols_string[:-1]
        cols_cmdlet = 'cols="{}"'.format(cols_string)

        output_cmd = ['--output', rows_cmdlet, cols_cmdlet]
        command = command + output_cmd

        return command

    def execute_command(self,command):

        output = None 

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                encoding='utf-8'
                )
            output = json.JSONDecoder().decode(result.stdout)
        except Exception as e:
            logger.error(e)

        return output


    def get_records_count(self,model=None,query_domain=None,search_domains=[]):
        
        command = self.build_command(model=model,query_domain=query_domain,search_domains=search_domains)
        output = self.execute_command(command)

        return output['TotalCount']

    def search_read(self,model=None,query_domain=None,search_domains=[],offset=None,limit=PAGE_SIZE):

        # Build the command and add up the offset and page size params
        command = self.build_command(model=model,query_domain=query_domain,search_domains=search_domains)

        if limit:
            # AliyunCLI page size is strictly limited to 100
            capped_limit = limit if limit < 100 else 100
            command = command + ['--PageSize',str(capped_limit)]
            # calculate page number
            pageno = int(offset / capped_limit) + 1 if offset else 1
            command = command + ['--PageNumber', str(pageno)]
            
        logger.debug('{} :: Final Aliyun command: {}'.format(__name__, command))
        output = self.execute_command(command)
        
        modelname = model['base_name']
        modelnames = modelname + 's'

        # only return the list of objects
        dataset = output[modelnames][modelname]

        # logger.debug('{} :: search_read dataset output:\n{}'.format(__name__, dataset))

        return dataset


class aliyunCLIConnector(DirectExtractor):

    def __init__(self, schema=SCHEMA_NAME, models=MODELS, update_field=UPD_FIELD_NAME, scope=None, **params):

        self.schema = schema
        self.models = models
        self.update_field = update_field
        self.client = aliyunCLIClient(update_field)
        self.params = params
        self.scope = scope

    def get_count(self, model=None, query_domain=None, search_domains=[],**params):

        total_count = 0
        # default to the first item in the model's query domains list
        query_domain = query_domain if query_domain else model['query_domains'][0]
        total_count = self.client.get_records_count(model,query_domain=query_domain,search_domains=search_domains)            
        return total_count

    def read_query(self, model=None, query_domain=None, search_domains=[], start_row=0,**params):

        # default to the first item in the model's query domains list
        query_domain = query_domain if query_domain else model['query_domains'][0]
        dataset = self.client.search_read(model=model,query_domain=query_domain,search_domains=search_domains,offset=start_row)
        return dataset


    # def forge_item(self,dictitem,model=None,**params):
        
    #     new_dict = {}
    #     fields = model['fields']

    #     for key,value in dictitem.items():

    #         isInFieldMap = (key in fields.keys())

    #         if isInFieldMap:
    #             new_key = fields[key]['dbname']
    #             new_dict[new_key] = value

    #         # for now, filter out elements not in the model target fields
    #         else:
    #             new_dict[key] = value

    #     return new_dict

