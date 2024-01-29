import os, yaml
from importlib import import_module

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

VAULT_TYPE = os.environ["KSPYDER_VAULT_TYPE"]
VAULT_NAME = os.environ["KSPYDER_VAULT_NAME"]

VAULT_CLIENTS = {
    'azure_keyvault': 'AzureKeyVaultClient',
    'local': 'LocalSecretsParser'
}

# Define classes to get secrets information from Azure Key Vault
class AzureClient:

    def __init__(self):
        self.credential = DefaultAzureCredential()


class AzureKeyVaultClient(AzureClient):

    def __init__(self,vault_name:str):
        AzureClient.__init__(self)
        self.vault_name = vault_name
        self.vault_url = "https://{}.vault.azure.net/".format(vault_name)
        self.secret_client = SecretClient(vault_url=self.vault_url, credential=self.credential)

class LocalSecretsParser:
    """WARNING : This is a dummy class to emulate secret fetching methods.
    It is only here for use in local development and not secure at all. Use at your own risk"""

    storepath:str

    def __init__(self,store:str) -> None:
    
        self.storepath = os.path.abspath(store)

    def get_secret(self,secret_key:str) -> str:
        """WARNING : This is a dummy class method to emulate secret fetching locally.
        It is only here for use in local development and not secure at all. Use at your own risk"""
        with open(self.storepath,'r') as sp:
            secrets_dict = yaml.full_load(sp)
            
        if secret_key in secrets_dict.keys():
            return secrets_dict[secret_key]
        else:
            raise KeyError(f'{secret_key} not found in {self.storepath}')
        
class secretsHandler():

    def __init__(self, vault_type=VAULT_TYPE, vault_name=VAULT_NAME) -> None:
        self.vault_type = vault_type
        self.vault_name = vault_name
        
        client_classname = VAULT_CLIENTS[self.vault_type]
        # this_module = import_module('.')
        # self.secrets_client = getattr(this_module, client_classname).__init__(vault_name)
        self.secrets_client = None
        if self.vault_type == 'local':
            self.secrets_client = LocalSecretsParser(self.vault_name)
        elif self.vault_type == 'azure_keyvault':
            self.secrets_client = AzureKeyVaultClient(self.vault_name)
        else:
            raise KeyError(f'Unrecognized {self.vault_type} for {__name__}')

