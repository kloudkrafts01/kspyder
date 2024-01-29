#!python3

from common.extract import GenericExtractor
import pandas as pd
import os,re

from common.config import DATA_FOLDER, load_conf


# Load the Connector's config
CONF = load_conf('xls_models', subfolder='manifests')
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']
UPD_FIELD_NAME = CONNECTOR_CONF['update_field']
UNPACKING = CONF['UnpackingFields']
MODELS = CONF['Models']
MODELS_LIST = list(MODELS.keys())


class XLSConnector(GenericExtractor):

    def __init__(self, schema=SCHEMA_NAME, models=MODELS, update_field=UPD_FIELD_NAME,**params):

        self.schema = schema
        self.models = models
        self.update_field = update_field
        self.dataframes = self.load_tables()

    def load_tables(self,source_folder=DATA_FOLDER):
        '''Loads all excel files in the input folder whose names match one Model name in the schema's YML config'''

        file_list = os.listdir(source_folder)
        models_list = list(x['base_name'] for x in self.models)
        dataframes = {}

        for filename in file_list:
            
            tablename, extname = os.path.splitext(filename)
            if re.match(re.compile("(xls)|(xlsx)$",re.I),extname) and tablename in models_list:
                tablenames += tablename,
                filepath = os.path.join(source_folder,filename)
                dataframes[tablename] = pd.read_excel(filepath)
        
        return dataframes

    def get_count(self, model, search_domains=[]):

        df = self.dataframes[model['base_name']]
        total_count = len(df)
        return total_count

    def read_query(self,model,search_domains=[],start_row=0):
        
        df = self.dataframes[model['base_name']]
        results = df.to_json(orient='records')
        return results


    def forge_item(self,input_dict,model):
        '''Passthrough function because it has to be here to work with the GenericExtractor flow. No added value in the case of this specific connector.'''

        new_dict = input_dict

        return new_dict

