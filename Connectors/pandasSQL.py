import pandas as pd

from common.sql_connector import GenericSQLConnector
from common.config import AZURE_PROFILE
from common.spLogging import logger


class PandasSQLConnector(GenericSQLConnector):

    @classmethod
    def load_default(cls):
        return cls.from_profile(AZURE_PROFILE)

    def load_tables(self,schema,table_list):
        
        dfs = {} 
        for table in table_list:
            dfs[table] = pd.read_sql_table(table,self.engine,schema=schema,index_col='Id')
        return dfs

    def save(self,df,schema,table):
        
        if df.empty:
            logger.warning("PandasSQL: Dataframe {} to be saved is Empty. Not saving.".format(table))
            return
        df.to_sql(table,self.engine,schema=schema,if_exists='replace',index=True,index_label=df.index.name)

    def apply_transforms(self,transforms):

        source = transforms['Source']
        table_list = transforms['Tables']
        dataframes = self.load_tables(source,table_list)

        df = None

        for step in transforms['Steps']:
            
            step_name = step['Step']
            logger.debug("STEP: {}".format(step))

            try:
                logger.info("{}::{} - Executing Step".format(source, step_name))
                operation = step['type']
                params = step['params']
                output_name = step['output']

                # replace the dataframe names by the actual dataframes in the params
                input_name = step['input']
                params['origin_df'] = dataframes[input_name]
                
                if 'right_input' in step.keys():
                    right_name = step['right_input']
                    params['right_df'] = dataframes[right_name]
                
                logger.debug("STEP PARAMS: {}".format(params))
                # retrieve the right function to apply and pass the parameters as dict
                function = getattr(self,operation)
                df = function(**params) 

                logger.debug(df.head(10))

                # store the output in the buffer_dfs for further chaining
                dataframes[output_name] = df

                if 'save' in step.keys() and (step['save']):
                    logger.info("Saving dataframe {}::{}".format(source, output_name))
                    self.save(df, source, output_name)

            except Exception as e:
                errmsg = "{}::{} error: {}".format(source, step_name, e)
                logger.error(errmsg)
                continue
        
        return df
    
    def merge_fields(self,origin_df,how='inner',left_key='Id',left_fields=None,right_df=None,right_key='Id',right_fields=None,prefix=None):

        map = {}
        base_df = origin_df
        extend_df = right_df

        # if we only want to keep a subset of fields from the left dataframe
        if left_fields:

            left_fields += left_key,
            drop_cols = (x for x in origin_df.columns if x not in left_fields)
            base_df = origin_df.drop(drop_cols, axis=1)

        # if we only want to keep a subset of fields from the right dataframe, and rename those fields before merging
        if right_fields:

            if prefix:
                for field_name in right_fields:
                    map[field_name] = '{}_{}'.format(prefix,field_name)

            right_fields += right_key,
            drop_cols = (x for x in right_df.columns if x not in right_fields)
            extend_df = right_df.drop(drop_cols, axis=1)
            extend_df = extend_df.rename(map, axis=1)

        # build a dict with the join parameters for pandas
        joinparams = {
            'how': how
        }
        if left_key == base_df.index.name:
            joinparams['left_index'] = True
        else:
            joinparams['left_on'] = left_key
        
        if right_key == extend_df.index.name:
            joinparams['right_index'] = True
        else:
            joinparams['right_on'] = right_key

        # and here we go
        df = pd.merge(base_df, extend_df, **joinparams)

        return df

    def group_compute(self,origin_df,group_by,map=None):
        
        values = list(set(map.keys()))
        df = pd.pivot_table(origin_df,index=group_by, values=values, aggfunc=map)
        # flatten the df index, to avoid ugly column names if saved to the database
        df.columns = df.columns.map('_'.join).str.strip('_')

        return df

