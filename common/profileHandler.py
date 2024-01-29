import os

from .secret_utils import secretsHandler
from .utils import FileHandler

USE_CONFIG = os.environ["KSPYDER_CONF"]
ENV_CONFIG = os.path.abspath(USE_CONFIG)


class profileHandler(FileHandler,secretsHandler):

    def __init__(self, input_folder=ENV_CONFIG, output_folder="."):
        FileHandler.__init__(self,input_folder=input_folder,output_folder=output_folder)
        secretsHandler.__init__(self)


    def load_profile(self,profile_name,scope='default'):
        """Loads a YAML file and returns the db or API client definition named '$profile' as a dict, retrieving passwords from Azure Key Vault"""

        # with open(profilepath,'r') as conf:
        profile_conf = self.load_yaml(profile_name)
        profile_data = []
        profile = {}

        # get common fields, if any
        profile_data = profile_conf.pop('common','default')

        # aggregate the profile data for common values and the wanted profile values
        if scope in profile_conf.keys():
            profile_data = [ *profile_data, *profile_conf[scope] ]

        for field_definition in profile_data:

            key = field_definition['name']
            value = field_definition['value']

            # If secret value, decode it with the Secrets client
            if field_definition['type'] == 'secret':
                decoded_value = self.secrets_client.get_secret(field_definition['value'])
                value = decoded_value
            
            # Insert the decoded key/value pair into the profile dict
            profile[key] = value

        return profile
