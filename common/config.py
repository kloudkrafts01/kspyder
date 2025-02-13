import os,sys

from .fileHandler import FileHandler

# load environment variables
USE_CONFIG = os.getenv("KSPYDER_CONF")

# Python path config
COMMONS_FOLDER = os.path.dirname(__file__)
ROOT_FOLDER = os.path.abspath(os.path.join(COMMONS_FOLDER,'..'))
CONF_FOLDER = os.path.join(ROOT_FOLDER,'kspyder-{}-conf'.format(USE_CONFIG))
LOG_CONFIG_FOLDER = os.path.join(CONF_FOLDER,'logging')
FUNCTIONS_FOLDER = os.path.join(ROOT_FOLDER,'AzureFunctions')
ENGINES_FOLDER = os.path.join(ROOT_FOLDER,'Engines')
CONNECTORS_FOLDER = os.path.join(ROOT_FOLDER,'Connectors')
TEMP_FOLDER = os.path.join(ROOT_FOLDER,'temp')
LOG_FOLDER = os.path.join(ROOT_FOLDER,'log')
DATA_FOLDER = os.path.join(ROOT_FOLDER,'inputs')

sys.path.insert(0,ROOT_FOLDER)
sys.path.insert(0,COMMONS_FOLDER)
sys.path.insert(0,CONF_FOLDER)
sys.path.insert(0,FUNCTIONS_FOLDER)
sys.path.insert(0,CONNECTORS_FOLDER)
sys.path.insert(0,ENGINES_FOLDER)
sys.path.insert(0,TEMP_FOLDER)
sys.path.insert(0,LOG_FOLDER)
sys.path.insert(0,DATA_FOLDER)

BASE_FILE_HANDLER = FileHandler(input_folder=CONF_FOLDER,output_folder=TEMP_FOLDER)

# Load baseline config from yaml
BASE_CONFIG = BASE_FILE_HANDLER.load_yaml("baseconfig")

DEFAULT_TIMESPAN = BASE_CONFIG["DEFAULT_TIMESPAN"]
PAGE_SIZE = BASE_CONFIG["PAGE_SIZE"]
APP_NAME = BASE_CONFIG["APP_NAME"]
MODULES_MAP = BASE_CONFIG['Modules']

DUMP_JSON = BASE_CONFIG["DUMP_JSON"]
# DUMP_CSV = BASE_CONFIG["DUMP_CSV"]

# load specified logger configuration
log_config_key = BASE_CONFIG["LOG_CONFIG"]
LOG_CONFIG = BASE_FILE_HANDLER.load_yaml(log_config_key,subpath=LOG_CONFIG_FOLDER)

# TODO get rid of this with KWI-30
PLACEHOLDER_PROFILE = {
    'dbtype': 'stub',
    'url': 'http://localhost',
    'dbname': 'stub',
    'username': 'stub_user',
    'password': 'blah'
}

ODOO_PROFILE = PLACEHOLDER_PROFILE
PS_PROFILE = PLACEHOLDER_PROFILE
AZURE_PROFILE = PLACEHOLDER_PROFILE
