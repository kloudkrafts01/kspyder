import os
from importlib import import_module
from common.config import MODULES_MAP,CONF_FOLDER


class clientHandler:

    def __init__(self, modules=MODULES_MAP) -> None:
        self.modules = modules

    def get_client(self, source=None, profile_name=None, **kwargs):
        """Simple method to return a client from a given 'source' value.
            This method assumes that the 'source' given is valid, and corresponds to a callable module
            The module must provide a class named exactly like itself
            e.g. from azureRGConnector import azureRGConnector"""

        if source in self.modules.keys():
            # import the right connector
            connector = import_module(source)
            client_class = getattr(connector,source)

            connector_conf_folder = os.path.join(CONF_FOLDER,source)
            base_profile = "{}Profile".format(source)
            base_profilename = "{}.yml".format(base_profile)
            connector_base_profilepath = os.path.join(connector_conf_folder,base_profilename)

            if profile_name:
                # if Profile name was provided, load the corresponding instance
                client = client_class.from_profile(profile_name)

            elif os.path.isfile(connector_base_profilepath):
                # if default profile exists in the Connector conf folder, use it to instanciate
                client = client_class.from_profile(base_profile)

            else:
                # else just instanciate without specifying profile
                client = client_class(**kwargs)

            return client
        
        else:
            raise ValueError('{} :: {} is not a valid source.\nAccepted sources are:\n{}'.format(__name__,source,self.modules))
