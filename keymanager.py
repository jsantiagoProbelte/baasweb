from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os

# DefaultAzureCredential is the key to access the vault
# See https://learn.microsoft.com/en-us/python/api/overview/
# azure/identity-readme?view=azure-python#getting-started
# Use az login for development

# For the setup in production:
# 1. Create a Managed Identity . Use the client_id
# 2. On the WebApp , go to Identity, User Assigned tab, and add the managed
#    identity
# 3. Add a variable AZURE_CLIENT_ID in Settings of the web app environment with
#    the client_id of the Managed Identity
# 4. On the Key Vault, add a Role to that managed identity as
#    'Key Vault Secrets User" to that managed identity


class KeyManager:
    def __init__(self):
        if "KEYVAULT-URL" in os.environ:
            keyVault = os.environ.get("KEYVAULT-URL")
        else:
            keyVault = 'https://baaskeys.vault.azure.net/'
        self.secret_client = SecretClient(
            vault_url=keyVault,
            credential=DefaultAzureCredential())

    def get_secret(self, secret_name):
        try:
            secret = self.secret_client.get_secret(secret_name)
            return secret.value
        except Exception as e:
            print(e)
            pass
        return os.environ.get(secret_name)
