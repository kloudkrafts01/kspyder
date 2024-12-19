import os

from .secretsHandler import secretsHandler
from .fileHandler import FileHandler

USE_CONFIG = os.environ["KSPYDER_CONF"]
CONF_FOLDER = 'kspyder-{}-conf'.format(USE_CONFIG)
ENV_CONFIG = os.path.abspath(CONF_FOLDER)


class profileHandler(FileHandler,secretsHandler):

    def __init__(self, input_folder=ENV_CONFIG, output_folder="."):
        FileHandler.__init__(self,input_folder=input_folder,output_folder=output_folder)
        secretsHandler.__init__(self)


    def load_profile(self,profile_name,subpath=None,scope='default'):
        """Loads a YAML file and returns the db or API client definition named '$profile' as a dict, retrieving passwords from Azure Key Vault"""

        # with open(profilepath,'r') as conf:
        profile_conf = self.load_yaml(profile_name,subpath=subpath)
        profile_data = []
        profile = {}

        # get common fields, if any
        profile_data = profile_conf.pop('common','default')
        # get the vault associated to the profile's secrets, if any. It must be in the Common section
        profile_vault = profile_data['vault'] if 'vault' in profile_data.keys() else None

        # aggregate the profile data for common values and the wanted profile values
        if scope in profile_conf.keys():
            profile_data = [ *profile_data, *profile_conf[scope] ]

        for field_definition in profile_data:

            key = field_definition['name']
            field_type = field_definition['type']
            raw_value = field_definition['value']
            value = self.decode_secret(raw_value,profile_vault) if field_type == 'secret' else raw_value
            
            # Insert the decoded key/value pair into the profile dict
            profile[key] = value

        return profile

    def decode_secret(self,encoded_value):

        secret = self.secrets_client.get_secret(encoded_value)

        return secret.value