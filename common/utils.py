#!python3

import os
import json
import datetime

from .config import TEMP_FOLDER

def json_dump(dictData,schema,name):

    now = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    filename = '{}_{}-{}.json'.format(now,schema,name)
    filepath = os.path.join(TEMP_FOLDER,filename)
    with open(filepath,'w') as f:
        json.dump(dictData,f)

    return filepath

