from importlib import import_module
from common.config import MODULES_MAP

class clientHandler:

    def __init__(self, modules=MODULES_MAP) -> None:
        self.modules = modules

    def get_client(self, source, *args, **kwargs):
        """Simple method to return a client from a given 'source' value.
            This method assumes that the 'source' given is valid, and corresponds to a callable module
            The module must provide a class named exactly like itself
            e.g. from azureRGConnector impor azureRGConnector"""

        if source in self.modules.keys():
            # import the right connector
            connector = import_module(source)

            # instantiate a connector client
            client_class = getattr(connector,source)
            client = client_class(**kwargs)

            return client
        
        else:
            raise ValueError('{} :: {} is not a valid source.\nAccepted sources are:\n{}'.format(__name__,source,self.modules))
