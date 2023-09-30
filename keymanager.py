from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os


class KeyManager:
    def __init__(self):
        # Use the DefaultAzureCredential to automatically use Managed Identity
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
