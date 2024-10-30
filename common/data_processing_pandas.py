#!python3
import pandas as pd

def sub_value(row,idx=None,new_value=None):
    new_row = row
    new_row[idx] = new_value

    # print("=========== NEW ROW ===========")
    # print(new_row)
    return new_row

def split_rows_by_stringvalue(row,separator=";",column=None):

    # df = pd.DataFrame(columns=row.index)
    # print(df)
    output = []

    # print("=========== OLD ROW ===========")
    # print(row)

    old_value = row[column]
    new_values = old_value.split(separator)

    for new_value in new_values:
        subbed_row = sub_value(row,idx=column,new_value=new_value).to_dict()
        output += subbed_row,
    
    df = pd.DataFrame(output)

    return df