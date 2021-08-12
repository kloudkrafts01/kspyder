#!python3

import os
import json
import datetime
from bson import ObjectId

from .config import TEMP_FOLDER

class bJSONEncoder(json.JSONEncoder):

    def default(self,o):
        if isinstance(o,ObjectId):
            return str(o)
        return json.JSONEncoder.default(self,o)

def json_dump(dictData,schema,name):

    now = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    filename = '{}_{}-{}.json'.format(now,schema,name)
    filepath = os.path.join(TEMP_FOLDER,filename)

    encoded_json = bJSONEncoder().encode(dictData)
    loaded_json = json.loads(encoded_json)
    with open(filepath,'w') as f:
        json.dump(loaded_json,f)

    return filepath

