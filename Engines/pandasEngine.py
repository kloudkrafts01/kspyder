import pandas as pd
import numpy as np
from importlib import import_module
from typing import Any, cast

from common.config import BASE_FILE_HANDLER as fh

class PandaPipeline():

    # set by subclasses (e.g. export_to_json usage) — never assigned in this base class
    schema: str
    scope: str

    def __init__(self) -> None:

        self.dataframes: dict = {}
        self.transforms: dict = {}
        # placeholder object for instanciated child classes
        self.engine = None

    def close_engine(self) -> None:
        """Placeholder method. Each child class will have to instanciate its own engine."""
        return None

    def load_tables(self, table_list: list[str], source: str | None = None) -> dict:
        """Placeholder method. Each child class implements its own table-loading strategy (SQL, XLS, etc.)."""
        raise NotImplementedError

    def save(self, df: pd.DataFrame, *args: Any, **kwargs: Any) -> None:
        """Placeholder method. Each child class implements its own save strategy (SQL, XLS, etc.)."""
        raise NotImplementedError

    def load_transforms(self, pipeline_def: str) -> None:

        self.transforms = fh.load_yaml(pipeline_def,subpath=__name__)

    def apply_transforms(self) -> dict:

        table_list = self.transforms['Tables']
        source = self.transforms['Source']
        table_list = self.transforms['Tables']
        
        self.load_tables(table_list,source=source)

        df = None

        for step in self.transforms['Steps']:
            
            step_name = step['Step']

            # try:
            print("{} - Executing Step".format(step_name))
            operation = step['type']
            params = (step['params'] if 'params' in step.keys() else {})
            output_name = step['output']

            # replace the dataframe names by the actual dataframes in the params
            input_name = step['input']
            params['origin_df'] = self.dataframes[input_name]
            
            if 'right_input' in step.keys():
                right_name = step['right_input']
                params['right_df'] = self.dataframes[right_name]
            
            print("STEP PARAMS: {}".format(params))
            # retrieve the right function to apply and pass the parameters as dict
            function = getattr(self,operation)
            df = function(**params) 

            print(df.head(10))

            # store the output in the buffer_dfs for further chaining
            self.dataframes[output_name] = df

            if 'save' in step.keys() and (step['save']):
                print("Saving dataframe {}".format(output_name))
                self.save(df, output_name)

        self.close_engine()

        return self.dataframes

    def passthrough(self, origin_df: pd.DataFrame) -> pd.DataFrame:
            return origin_df

    def export_to_json(self, origin_df: pd.DataFrame, model_name: str, **params: Any) -> None:

        dataset = origin_df.to_json(orient='records')

        full_dataset = {
            'header': {
                'schema': self.schema,
                'scope': self.scope,
                'model': model_name,
                'count': origin_df.size,
                'params': params
            },
            'data': dataset
        }

        fh.dump_json(full_dataset,self.schema,model_name)

    def reduce_df_axis(self, origin_df: pd.DataFrame) -> Any:

        df = origin_df.iloc[0]
        for i in range(1,origin_df.shape[0]):
            df = pd.concat([df,origin_df.iloc[i]])

        return df

    def series_from_set(self, origin_df: pd.DataFrame, import_from: str | None = None, import_value: str | None = None) -> pd.Series:

        module = import_module(name=cast(str, import_from))
        imported_set = getattr(module, cast(str, import_value))

        datalist = list(imported_set)
        series = pd.Series(datalist)

        return series

    def apply_func_on_df(self, origin_df: pd.DataFrame, func_name: str | None = None, import_from: str = '.', **fargs: Any) -> pd.DataFrame:

        module = import_module(name=import_from)
        func = getattr(module, cast(str, func_name))
        df = func(origin_df,**fargs)

        return df

    def apply_func_on_axis(self, origin_df: pd.DataFrame, func_name: str | None = None, axis: int = 1, import_from: str = '.', import_pkg: str | None = None, **fargs: Any) -> pd.DataFrame:

        module = import_module(name=import_from,package=import_pkg)
        func = getattr(module, cast(str, func_name))
        df = origin_df.apply(func,axis=axis,**fargs)

        return df

    def merge_fields(self, origin_df: pd.DataFrame, how: str = 'inner', left_key: str = 'Id', left_index: bool = False, left_fields: list | None = None, right_df: pd.DataFrame | None = None, right_key: str | None = None, right_index: bool = False, right_fields: list | None = None, prefix: str | None = None) -> pd.DataFrame:

        map: dict = {}
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
            drop_cols = (x for x in cast(pd.DataFrame, right_df).columns if x not in right_fields)
            extend_df = cast(pd.DataFrame, right_df).drop(drop_cols, axis=1)
            extend_df = extend_df.rename(map, axis=1)

        # build a dict with the join parameters for pandas
        joinparams: dict = {
            'how': how
        }
        if (left_index or (left_key == base_df.index.name)):
            joinparams['left_index'] = True
        else:
            joinparams['left_on'] = left_key

        if (right_index or (right_key == cast(pd.DataFrame, extend_df).index.name)):
            joinparams['right_index'] = True
        elif right_key is None:
            # if no right key is provided, join on the same key as left
            joinparams['right_on'] = left_key
        else:
            joinparams['right_on'] = right_key

        # and here we go
        df = pd.merge(base_df, extend_df, **joinparams)

        return df

    def group_compute(self, origin_df: pd.DataFrame, group_by: str | list, map: dict | None = None, unstack: Any = None, slug_index: bool = False, fillna: bool = True) -> pd.DataFrame:
        
        values = list(set(cast(dict, map).keys()))
        df = pd.pivot_table(origin_df,index=group_by, values=values, aggfunc=map)

        if unstack:
            df = df.unstack(unstack)

        if slug_index:
            # flatten the df index, to avoid ugly column names if saved to the database
            df.columns = df.columns.map('_'.join).str.strip('_')

        if fillna:
            df = df.fillna(0.0)

        return df

    def transpose(self, origin_df: pd.DataFrame, copy: bool = True) -> pd.DataFrame:

        df = origin_df.transpose(copy=copy)

        return df

    def reindex(self, origin_df: pd.DataFrame, **params: Any) -> pd.DataFrame:

        df = origin_df.reindex(**params)

        return df

    def rename_columns(self, origin_df: pd.DataFrame, separator: str = "|", column_map: dict = {}, dropcolumns: bool = False, flatten_columns: bool = False) -> pd.DataFrame:

        df = origin_df

        if flatten_columns:
            df.columns = df.columns.map(separator.join).str.strip(separator)
            df = df.reindex(columns=column_map.keys())

        if dropcolumns:
            drop_cols = (x for x in df.columns if x not in column_map.keys())
            df.drop(drop_cols, axis=1, inplace=True)
        
        df.rename(column_map, axis=1, inplace=True)

        return df

    def sort_values(self, origin_df: pd.DataFrame, sort_by: str | list, **params: Any) -> pd.DataFrame:

        df = origin_df.sort_values(sort_by,**params)
        return df

    def group_rank(self, origin_df: pd.DataFrame, rank_by: str, name: str | None = None, group_by: str | list | None = None, method: str = 'dense', ascending: bool = False) -> pd.DataFrame:

        if group_by:
            series = origin_df.groupby(group_by).rank(method=method,ascending=ascending)[rank_by]
        else:
            series = origin_df.rank(method=method,ascending=ascending)[rank_by]

        if name is None:
            name = rank_by

        df = pd.DataFrame({name: series})

        return df

    def deduplicate(self, origin_df: pd.DataFrame, by: str | list | None = None) -> pd.DataFrame:

        df = origin_df.drop_duplicates(subset=by,keep='first')

        return df

    def add_datetimes(self, origin_df: pd.DataFrame, datecol: str, dayfirst: bool = True) -> pd.DataFrame:

        df = origin_df
        df.loc[:,'datetime'] = pd.to_datetime(df.loc[:,datecol], dayfirst=dayfirst)
        df['date_'] = df.loc[:,'datetime'].dt.date
        df.loc[:,'year'] = df.loc[:,'datetime'].dt.year
        df.loc[:,'month'] = df.loc[:,'datetime'].dt.month
        df.loc[:,'day'] = df.loc[:,'datetime'].dt.day

        return df

    def filter(self, origin_df: pd.DataFrame, filter_map: list) -> pd.DataFrame:

        fdef = filter_map.pop(0)
        
        if fdef['right_type'] == 'str':
            query_str = "({} {} '{}')"
        else:
            query_str = "({} {} {})"
            
        query_str = query_str.format(fdef['left'], fdef['op'], fdef['right'])

        for fdef in filter_map:
            if fdef['right_type'] == 'str':
                query_step = " and ({} {} '{}')"
            else:
                query_step = " and ({} {} {})"

            query_str = query_str + query_step.format(fdef['left'], fdef['op'], fdef['right'])
        
        df = origin_df.query(query_str)

        return df

    def hash_columns(self, origin_df: pd.DataFrame, columns: list) -> pd.DataFrame:

        hashcol = np.zeros(origin_df.shape[0])

        for col in columns:
            hashcol += df[col].apply(lambda x: hash(x))  # type: ignore[has-type, used-before-def]

        df = origin_df
        df['hash'] = hashcol
        return df

    def concat(self, origin_df: pd.DataFrame, df_list: list = []) -> pd.DataFrame:

        dataframes = [origin_df]

        for df_name in df_list:
            dataframes += self.dataframes[df_name],

        return pd.concat(dataframes)

    def cast_dtypes(self, origin_df: pd.DataFrame, typemap: dict) -> pd.DataFrame:

            df = origin_df.astype(typemap)
            return df

    def addup_columns(self, origin_df: pd.DataFrame, output_name: str, origin_column: str, add_columns: list = []) -> pd.DataFrame:

        df = origin_df
        df[output_name] = df[origin_column]
        for colname in add_columns:
            df[output_name] = df[output_name].add(df[colname],fill_value=0.0)

        return df

    def substitute_str(self, origin_df: pd.DataFrame, colnames: list, strmaps: list) -> pd.DataFrame:
        
        df = origin_df
        for colname in colnames:
            for strmap in strmaps:
                df[colname] = df[colname].str.replace(strmap['old'],strmap['new'])
        
        return df

    def add_fill_column(self, origin_df: pd.DataFrame, fill_columns: list) -> pd.DataFrame:

        df = origin_df
        for item in fill_columns:
            df[item['colname']] = item['fill_value']

        return df

    def filter_duplicates(self, origin_df: pd.DataFrame, colnames: list, sort_by: str | list, keep: str = 'first') -> pd.DataFrame:

        sorted_df = origin_df.reset_index().sort_values(by=sort_by)
        filtered_df = sorted_df.duplicated(subset=colnames,keep=keep)
        mask = sorted_df.loc[filtered_df].index

        df = sorted_df.drop(mask)

        return df