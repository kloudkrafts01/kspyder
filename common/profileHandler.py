import os

from .azure_utils import AzureClient, AzureVaultClient
from .secret_utils import SecretParser
from .utils import FileHandler

# from .config import USE_AZKV, LOCAL_SECRETS


USE_AZKV = os.environ["KSPYDER_USE_AZ_KEYVAULT"]
LOCAL_SECRETS = os.environ["KSPYDER_LOCAL_SECRETS"]
SOURCE_PROFILES = "source_profiles"
AZURE_CLIENT = None
AZ_VAULT = None
SECRETS_HANDLER = None

if USE_AZKV:
    AZURE_CLIENT = AzureClient()
    AZ_VAULT = AzureVaultClient()
    SECRETS_HANDLER = AZ_VAULT.secret_client
else:
    SECRETS_HANDLER = SecretParser(store=LOCAL_SECRETS)

fh = FileHandler()

def load_profile(profile,profilepath=SOURCE_PROFILES,secret_handler=SECRETS_HANDLER):
    """Loads a YAML file and returns the db or API client definition named '$profile' as a dict, retrieving passwords from Azure Key Vault"""

    # with open(profilepath,'r') as conf:
    profile = fh.load_yaml(profilepath)[profile]
    if 'secretkey' in profile.keys():
        password = secret_handler.get_secret(profile['secretkey']).value
        profile['password'] = password

    if 'config' in profile.keys():
        profile_conf = fh.load_yaml(profile['config'],folder='local_only')
        print("Profile conf: {}".format(profile_conf))
        
    return profile