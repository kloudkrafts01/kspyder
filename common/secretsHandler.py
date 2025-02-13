import os
from .fileHandler import FileHandler

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

VAULT_TYPE = os.environ["KSPYDER_VAULT_TYPE"]
VAULT_NAME = os.environ["KSPYDER_VAULT_NAME"]

VAULT_CLIENTS = {
    'azure_keyvault': 'AzureKeyVaultClient',
    'local': 'LocalSecretsParser'
}


class AzureKeyVaultClient():

    def __init__(self,vault_name:str):
        
        self.credential = DefaultAzureCredential()
        self.vault_name = vault_name
        self.vault_url = "https://{}.vault.azure.net/".format(vault_name)
        self.secrets_client = SecretClient(vault_url=self.vault_url, credential=self.credential)

class LocalSecret:

    def __init__(self, name:str, value:str) -> None:
        self.name = name
        self.value = value
        self.properties = {
            'secret_type': 'local',
            'secure': False
        }

class LocalSecretsParser(FileHandler):
    """WARNING : This is a dummy class to emulate secret fetching methods.
    It is only here for use in local development and not secure at all. Use at your own risk"""


    def __init__(self,store:str) -> None:
    
        self.input_folder = os.path.abspath(store)
        self.output_folder = os.path.abspath(store)

    def get_secret(self,secret_key:str,secrets_filename=None) -> any:
        """WARNING : This is a dummy class method to emulate secret fetching locally.
        It is only here for use in local development and not secure at all. Use at your own risk"""
        
        # secrets_filepath = os.path.join(self.storepath,secrets_filename) if secrets_filename else self.storepath
        secrets_dict = self.load_json(secrets_filename)

        if secret_key in secrets_dict.keys():
            return LocalSecret(secret_key, secrets_dict[secret_key])
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
            self.keyvault_client = AzureKeyVaultClient(self.vault_name)
            self.secrets_client = self.keyvault_client.secrets_client
        else:
            raise KeyError(f'Unrecognized {self.vault_type} for {__name__}')
        

