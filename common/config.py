import os,sys,re
import yaml
from .azure_utils import AZ_SECRETS


# default number of days' history to be fetched and page size for source queries
# DEFAULT_TIMESPAN = 1
# PAGE_SIZE = 500

# specify which config you want to apply. The config files will be looked up in th 'CONF_${USE_CONFIG}' folder.
USE_CONFIG = os.environ["KSPYDER_CONF"]

# Python path config
COMMONS_FOLDER = os.path.dirname(__file__)
ROOT_FOLDER = os.path.abspath(os.path.join(COMMONS_FOLDER,'..'))
CONF_FOLDER = os.path.join(ROOT_FOLDER,'kspyder-{}-conf'.format(USE_CONFIG))
FUNCTIONS_FOLDER = os.path.join(ROOT_FOLDER,'AzureFunctions')
CONNECTORS_FOLDER = os.path.join(ROOT_FOLDER,'Connectors')
TEMP_FOLDER = os.path.join(ROOT_FOLDER,'temp')
LOG_FOLDER = os.path.join(ROOT_FOLDER,'log')

sys.path.insert(0,COMMONS_FOLDER)
sys.path.insert(0,CONF_FOLDER)
sys.path.insert(0,ROOT_FOLDER)
sys.path.insert(0,FUNCTIONS_FOLDER)
sys.path.insert(0,CONNECTORS_FOLDER)
sys.path.insert(0,TEMP_FOLDER)
sys.path.insert(0,LOG_FOLDER)


# source db profiles config
SOURCE_PROFILES = os.path.join(CONF_FOLDER,'source_profiles.yml')

def load_profile(profile,profilepath=SOURCE_PROFILES,secrets=AZ_SECRETS):
    """Loads a YAML file and returns the db or API client definition named '$profile' as a dict, retrieving passwords from Azure Key Vault"""

    with open(profilepath,'r') as conf:
        profile = yaml.full_load(conf)[profile]
        password = secrets.get_secret(profile['secretkey']).value
        profile['password'] = password

    return profile

def load_conf(name,folder=CONF_FOLDER,subfolder=None):
    """Simply Loads a YAML file and passes the result as a dict"""

    if subfolder:
        folder = os.path.join(folder,subfolder)
    
    # Add the .yml extension to the conf name if not already present
    yml_ext = re.compile('(\.yml|\.yaml)$')
    if re.search(yml_ext, name) is None:
        name = '{}.yml'.format(name)

    conf_path = os.path.join(folder,name)

    with open(conf_path,'r') as conf:
        conf_dict = yaml.full_load(conf)

    return conf_dict

BASE_CONFIG = load_conf('baseconfig')
print(BASE_CONFIG)
ENV = os.environ['KSPYDER_ENVIRONMENT']

# Set global, environment-independant variables
DEFAULT_TIMESPAN = BASE_CONFIG['DEFAULT_TIMESPAN']
PAGE_SIZE = BASE_CONFIG['PAGE_SIZE']

# Sets the global variables depending on the environment : Local dev machine, Dev/test cloud environment, or PROD cloud environment
DUMP_JSON = BASE_CONFIG[ENV]['DUMP_JSON']
log_key = BASE_CONFIG[ENV]['LOG_CONFIG']
LOG_CONFIG = load_conf(log_key)

odoo_key = BASE_CONFIG[ENV]['ODOO_PROFILE']
ODOO_PROFILE = load_profile(odoo_key)

ps_key = BASE_CONFIG[ENV]['PS_PROFILE']
PS_PROFILE = load_profile(ps_key)

azure_key = BASE_CONFIG[ENV]['AZURE_PROFILE']
AZURE_PROFILE = load_profile(azure_key)
