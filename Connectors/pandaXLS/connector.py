import os
import pandas as pd
from Engines.pandasEngine import PandaPipeline
from common.config import DATA_FOLDER, TEMP_FOLDER
from common.loggingHandler import logger


class pandaXLSConnector(PandaPipeline):

    def __init__(self, target: str = 'pandas_output.xlsx', target_folder: str = TEMP_FOLDER, pipeline_def: str = '') -> None:

        self.source_type = ['csv','excel']
        self.target_type = ['excel']
        self.dataframes = {}
        self.to_save = {}
        self.target = os.path.join(target_folder,target)
        self.engine = pd.ExcelWriter(self.target)

        self.load_transforms(pipeline_def)

    def load_tables(self, file_list: list[str], source: str = DATA_FOLDER) -> None:

        for filename in file_list:
            filepath = os.path.join(source,filename)
            tablename, extname = os.path.splitext(filename)
            logger.debug("Pandas loading file: {}".format(filepath))
            self.dataframes[tablename] = pd.read_excel(filepath)

    def save(self, df: pd.DataFrame, tablename: str) -> None:

        if df.empty:
            logger.info("PandasSQL: Dataframe {} to be saved is Empty. Not saving.".format(tablename))
            return
        df.to_excel(self.engine,sheet_name=tablename,index=True,index_label=df.index.name)

    def close_engine(self) -> None:
        self.engine.close()

    
