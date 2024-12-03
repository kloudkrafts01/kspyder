#!python3

from Engines.rpcExtractorEngine import DirectExtractor
import os,sys
from typing import List

from alibabacloud_ram20150501.client import Client as Ram20150501Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ram20150501 import models as ram_20150501_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

from common.config import PAGE_SIZE, load_conf
from common.spLogging import logger

CONF = load_conf('aliyunRAM_models', subfolder='manifests') 

# mandatory connector config
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']
UPD_FIELD_NAME = CONNECTOR_CONF['update_field']

MODELS = CONF['Models']
MODELS_LIST = list(MODELS.keys())
UNPACKING = CONF['UnpackingFields']

class AliyunRAMClient:

    def __init__(self, access_key_id:str, access_key_secret:str):

        config = open_api_models.Config(
            # Required, your AccessKey ID,
            access_key_id=access_key_id,
            # Required, your AccessKey secret,
            access_key_secret=access_key_secret
        )
        # See https://api.alibabacloud.com/product/Ram.
        config.endpoint = f'ram.aliyuncs.com'

        self.client = Ram20150501Client(config)

    @classmethod
    def from_env(cls):
        env = os.environ
        return cls(
            env['ALIBABACLOUD_ACCESS_KEY_ID'],
            env['ALIBABACLOUD_ACCESS_KEY_SECRET']
        )

class AliyunRAMConnector(DirectExtractor):

    def __init__(self, profile=None, schema=SCHEMA_NAME, models=MODELS, update_field=UPD_FIELD_NAME,**params):

        self.client = AliyunRAMClient.from_env().client

    def read_query(self,model,search_domains=[],start_row=0):

        request_gen = getattr(ram_20150501_models,model['class'])
        request = request_gen()

        runtime = util_models.RuntimeOptions()
        # Copy the code to run, please print the return value of the API by yourself.
        method_gen = getattr(self.client,model['base_name'])
        results = method_gen(request, runtime)

        return results