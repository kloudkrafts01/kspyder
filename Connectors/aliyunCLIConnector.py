#!python3

import subprocess
import json, jmespath

from Engines.rpcExtractorEngine import DirectExtractor
from common.loggingHandler import logger

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
GET_TABULAR_OUTPUT = False

class aliyunCLIClient:
    """Class to process the raw output of an Aliyun CLI command, because the python sdk sucks.
    This WILL NOT set or authenticate to your Aliyun context, you have to run locally 'aliyun configure'"""

    def __init__(self, update_field=UPD_FIELD_NAME):
        
        self.update_field = update_field
    
    def build_command(self,model=None,query_domain=None,search_domains=[],**params):

        command = ['aliyun', model['class']]
        # build the basics : 'query_domain' is supposed to be one type of query that fits the model
        if query_domain in model['query_domains']:
            command += query_domain,
        else:
            errmsg_tmpl = '{} is not a valid query_domain for the {} model.\nAccepted query_domain are: {}'
            errmsg = errmsg_tmpl.format(query_domain, model['base_name'], model['query_domains'])
            logger.error(errmsg)
            raise ValueError(errmsg)

        # add search filters if any
        for domain in search_domains:
            if domain:
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

        for key,value in params:
            command = command + [f'--{key}', value]
        
        if GET_TABULAR_OUTPUT:
            # add the tabular formatting cmdlets
            command = self.add_tabular_cmdlet(command,model)

        logger.debug('Aliyun command: {}'.format(command))

        return command

    def add_tabular_cmdlet(self,command,model=None):
        # add the tabular formatting cmdlets
        base_name = model['base_name']
        rows_cmdlet = 'rows="{}"'.format(model['datapath'])
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
            logger.exception(e)

        return output

    def get_records_count(self,model=None,query_domain=None,search_domains=[]):

        count = 0

        command = self.build_command(model=model,query_domain=query_domain,search_domains=search_domains)
        output = self.execute_command(command)
        total_count_key = model['total_count_key'] if 'total_count_key' in model.keys() else 'TotalCount'

        if output:
            if total_count_key in output.keys():
                count = output[total_count_key]
            else:
                count = len(output)
                # logger.error("Model is not RPC-based. Switch this config to a REST-based connector instead.") 

        return count

    def search_read(self,model=None,query_domain=None,search_domains=[],offset=None,limit=PAGE_SIZE):

        # Build the command and add up the offset and page size params
        command = self.build_command(model=model,query_domain=query_domain,search_domains=search_domains)
        
        paginate = model['paginated'] if 'paginated' in model.keys() else True
        
        if paginate:
            # AliyunCLI page size is strictly limited to 100
            capped_limit = min(limit,100)
            command = command + ['--PageSize',str(capped_limit)]
            # calculate page number
            pageno = int(offset / capped_limit) + 1 if offset else 1
            command = command + ['--PageNumber', str(pageno)]
            
        logger.debug('Final Aliyun command: {}'.format(command))
        output = self.execute_command(command)
        
        datapath = model['datapath']
        dataset = jmespath.search(datapath,output)

        return dataset


class aliyunCLIConnector(DirectExtractor):

    def __init__(self, schema=SCHEMA_NAME, models=MODELS, update_field=UPD_FIELD_NAME, scopes=None, **params):

        self.schema = schema
        self.models = models
        self.update_field = update_field
        self.client = aliyunCLIClient(update_field)
        self.params = params
        self.scopes = scopes

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

