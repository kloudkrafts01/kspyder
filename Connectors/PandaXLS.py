import os
import pandas as pd
from common.panda_pipelines import PandaPipeline
from common.config import DATA_FOLDER, TEMP_FOLDER


class PandaXLSConnector(PandaPipeline):

    def __init__(self,target_filename='pandas_output.xlsx',target_folder=TEMP_FOLDER,pipeline_def=''):

        self.source_type = ['csv','excel']
        self.target_type = ['excel']
        self.dataframes = {}
        self.to_save = {}
        self.target_file = os.path.join(target_folder,target_filename)
        self.xlswriter = pd.ExcelWriter(self.target_file)

        self.load_transforms(pipeline_def)

    def load_tables(self,file_list,source=DATA_FOLDER):
        
        for filename in file_list:
            filepath = os.path.join(source,filename)
            tablename, extname = os.path.splitext(filename)
            print("Pandas loading file: {}".format(filepath))
            self.dataframes[tablename] = pd.read_excel(filepath)

    def save(self,df,sheetname):
        
        if df.empty:
            print("PandasSQL: Dataframe {} to be saved is Empty. Not saving.".format(sheetname))
            return
        df.to_excel(self.xlswriter,sheet_name=sheetname,index=True,index_label=df.index.name)
