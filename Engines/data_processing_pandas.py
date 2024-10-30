#!python3
import pandas as pd

def sub_value(row,idx=None,new_value=None):
    new_row = row
    new_row[idx] = new_value
    return new_row

def split_rows_by_stringvalue(row,separator=";",column=None):

    output_rows = []

    old_value = row[column]
    new_values = old_value.split(separator)
    for new_value in new_values:
        output_rows += sub_value(row,idx=column,new_value=new_value),

    return pd.DataFrame(output_rows)