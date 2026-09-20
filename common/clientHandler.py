import os
from importlib import import_module
from typing import Any
from common.config import CONF_FOLDER
from common.protocols import Extractor, DocumentStore


class clientHandler:

    def get_client(self, source: str | None = None, profile_name: str | None = None, **kwargs: Any) -> Extractor | DocumentStore:
        """Return an instantiated connector for the given source name.
        source must match a sub-package name under Connectors/ (e.g. 'aliyun', 'mongoDB').
        Each connector package exposes its class as 'connector' in its __init__.py."""

        try:
            module = import_module(f"Connectors.{source}")
        except ImportError:
            raise ValueError(
                f"{__name__} :: '{source}' is not a valid connector. "
                f"Expected a package at Connectors/{source}/__init__.py"
            )

        client_class = module.connector

        connector_conf_folder = os.path.join(CONF_FOLDER, source)
        base_profile = f"{source}Profile"
        base_profilepath = os.path.join(connector_conf_folder, f"{base_profile}.yml")

        if profile_name:
            client = client_class.from_profile(profile_name)
        elif os.path.isfile(base_profilepath):
            client = client_class.from_profile(base_profile)
        else:
            client = client_class(**kwargs)

        return client
