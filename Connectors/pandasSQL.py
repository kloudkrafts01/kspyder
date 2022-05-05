import pandas as pd

from common.panda_pipelines import PandaPipeline
from common.sql_connector import GenericSQLConnector
from common.config import AZURE_PROFILE
from common.spLogging import logger


class PandasSQLConnector(GenericSQLConnector,PandaPipeline):

    @classmethod
    def load_default(cls):
        return cls.from_profile(AZURE_PROFILE)

    def load_tables(self,table_list,source=None):
        
        dfs = {} 
        for table in table_list:
            dfs[table] = pd.read_sql_table(table,self.engine,schema=source,index_col='Id')
        return dfs

    def save(self,df,schema,table):
        
        if df.empty:
            logger.warning("PandasSQL: Dataframe {} to be saved is Empty. Not saving.".format(table))
            return
        df.to_sql(table,self.engine,schema=schema,if_exists='replace',index=True,index_label=df.index.name)
