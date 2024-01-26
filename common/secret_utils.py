import os
from .utils import FileHandler

class Secret:

    def __init__(self, secret_key:str, secret_value:str) -> None:
        self.key = secret_key
        self.value = secret_value

class SecretParser:
    """WARNING : This is a dummy class to emulate secret fetching methods.
    It is only here for use in local development and not secure at all. Use at your own risk"""

    storepath:str

    def __init__(self,store:str) -> None:
    
        self.storepath = os.path.abspath(store)

    def get_secret(self,secret_key:str) -> str:
        """WARNING : This is a dummy class method to emulate secret fetching locally.
        It is only here for use in local development and not secure at all. Use at your own risk"""

        fh = FileHandler(input_folder=self.storepath)
        secrets_dict = fh.load_yaml('secrets')
        if secret_key in secrets_dict:
            return Secret(
                secret_key=secret_key,
                secret_value=secrets_dict[secret_key]
                )
        else:
            raise KeyError(f'{secret_key} not found in {self.storepath}')
