import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Define classes to get secrets information from Azure Key Vault
class AzureClient:

    def __init__(self):
        self.credential = DefaultAzureCredential()

# Azure Key Vault config
# AZURE_VAULT_NAME = os.environ['AZURE_VAULT_NAME']

# class AzureVaultClient(AzureClient):

#     def __init__(self,vault_name=AZURE_VAULT_NAME):
#         AzureClient.__init__(self)
#         self.vault_name = vault_name
#         self.vault_url = "https://{}.vault.azure.net/".format(vault_name)
#         self.secret_client = SecretClient(vault_url=self.vault_url, credential=self.credential)

# AZ_VAULT = AzureVaultClient()
# AZ_SECRETS = AZ_VAULT.secret_client