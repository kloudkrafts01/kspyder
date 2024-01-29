import os,sys,re
import yaml,json
from .utils import FileHandler
# from .azure_utils import AzureClient, AzureVaultClient
# from .secret_utils import SecretParser

# AZURE_CLIENT = None
# AZ_VAULT = None
# SECRETS = None

# load environment variables
env = os.environ

# ENV = env["KSPYDER_ENVIRONMENT"]
# USE_AZKV = env["KSPYDER_USE_AZ_KEYVAULT"]
# LOCAL_SECRETS = env["KSPYDER_LOCAL_SECRETS"]
# specify which config you want to apply. The config files will be looked up in the 'CONF_${USE_CONFIG}' folder.
USE_CONFIG = env["KSPYDER_CONF"]

# if USE_AZKV:
#     AZURE_CLIENT = AzureClient()
#     AZ_VAULT = AzureVaultClient()
#     SECRETS = AZ_VAULT.secret_client
# else:
#     SECRETS = SecretParser(store=LOCAL_SECRETS)
    

# Python path config
COMMONS_FOLDER = os.path.dirname(__file__)
ROOT_FOLDER = os.path.abspath(os.path.join(COMMONS_FOLDER,'..'))
CONF_FOLDER = os.path.join(ROOT_FOLDER,'kspyder-{}-conf'.format(USE_CONFIG))
LOG_CONFIG_FOLDER = os.path.join(CONF_FOLDER,'spLogging')
FUNCTIONS_FOLDER = os.path.join(ROOT_FOLDER,'AzureFunctions')
CONNECTORS_FOLDER = os.path.join(ROOT_FOLDER,'Connectors')
TEMP_FOLDER = os.path.join(ROOT_FOLDER,'temp')
LOG_FOLDER = os.path.join(ROOT_FOLDER,'log')
DATA_FOLDER = os.path.join(ROOT_FOLDER,'inputs')

sys.path.insert(0,COMMONS_FOLDER)
sys.path.insert(0,CONF_FOLDER)
sys.path.insert(0,ROOT_FOLDER)
sys.path.insert(0,FUNCTIONS_FOLDER)
sys.path.insert(0,CONNECTORS_FOLDER)
sys.path.insert(0,TEMP_FOLDER)
sys.path.insert(0,LOG_FOLDER)
sys.path.insert(0,DATA_FOLDER)

BASE_FILE_HANDLER = FileHandler(input_folder=CONF_FOLDER,output_folder=TEMP_FOLDER)

BASE_CONFIG = BASE_FILE_HANDLER.load_yaml("baseconfig")

DEFAULT_TIMESPAN = BASE_CONFIG["DEFAULT_TIMESPAN"]
# CONNECTOR_MAP = BASE_CONFIG["CONNECTOR_MAP"]
PAGE_SIZE = BASE_CONFIG["PAGE_SIZE"]
APP_NAME = BASE_CONFIG["APP_NAME"]
MODULES_LIST = BASE_CONFIG['Modules']

DUMP_JSON = BASE_CONFIG["DUMP_JSON"]
# DUMP_CSV = BASE_CONFIG["DUMP_CSV"]

# load specified logger configuration
log_config_key = BASE_CONFIG["LOG_CONFIG"]
LOG_CONFIG = BASE_FILE_HANDLER.load_yaml(log_config_key,subpath=LOG_CONFIG_FOLDER)

# source db profiles config
# SOURCE_PROFILES = os.path.join(CONF_FOLDER,'source_profiles.yml')

# def load_profile(profile,profilepath=SOURCE_PROFILES,secrets=SECRETS):
#     """Loads a YAML file and returns the db or API client definition named '$profile' as a dict, retrieving passwords from Azure Key Vault"""

#     with open(profilepath,'r') as conf:
#         profile = yaml.full_load(conf)[profile]
#         if 'secretkey' in profile.keys():
#             password = secrets.get_secret(profile['secretkey']).value
#             profile['password'] = password

#         if 'config' in profile.keys():
#             profile_conf = BASE_FILE_HANDLER.load_yaml(profile['config'],folder='local_only')
            

#     return profile

# def load_conf(name,type="yaml",folder=CONF_FOLDER,subfolder=None):
#     """Simply Loads a YAML file and passes the result as a dict"""

#     conf_dict = {}

#     if subfolder:
#         folder = os.path.join(folder,subfolder)
    
#     if type=="json":
#         json_ext = re.compile('(\.yml)$')
#         if re.search(json_ext, name) is None:
#             name = '{}.json'.format(name)
        
#         conf_path = os.path.join(folder,name)

#         with open(conf_path,'r') as conf:
#             conf_dict = json.loads(conf)

#     elif type=="yaml":
#         # Add the .yml extension to the conf name if not already present
#         yml_ext = re.compile('(\.yml|\.yaml)$')
#         if re.search(yml_ext, name) is None:
#             name = '{}.yml'.format(name)

#         conf_path = os.path.join(folder,name)

#         with open(conf_path,'r') as conf:
#             conf_dict = yaml.full_load(conf)
    
#     else:
#         ValueError("common.config :: Invalid value provided for Config Type ! Valid options are 'json' or 'yaml'.")

#     return conf_dict


# azprice_key = BASE_CONFIG[ENV]['AZ_PRICING_PROFILE']
# AZ_PRICING_PROFILE = load_profile(azprice_key)


# odoo_key = BASE_CONFIG[ENV]['ODOO_PROFILE']
# ODOO_PROFILE = load_profile(odoo_key)

# odoo_key = BASE_CONFIG[ENV]['ODOO_PROFILE']
# ODOO_PROFILE = load_profile(odoo_key)

# ps_key = BASE_CONFIG[ENV]['PS_PROFILE']
# PS_PROFILE = load_profile(ps_key)

# azure_key = BASE_CONFIG[ENV]['AZURE_PROFILE']
# AZURE_PROFILE = load_profile(azure_key)

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
