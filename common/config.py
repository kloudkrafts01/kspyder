import os
import sys
from functools import lru_cache
from typing import Any

from .fileHandler import FileHandler

# Python path config (no I/O, no env dependency beyond computing paths)
COMMONS_FOLDER = os.path.dirname(__file__)
ROOT_FOLDER = os.path.abspath(os.path.join(COMMONS_FOLDER, '..'))

sys.path.insert(0, ROOT_FOLDER)

# Names that are resolved lazily on first access via __getattr__ (PEP 562),
# once KSPYDER_CONF is known to be valid.
_LAZY_KEYS = {
    'USE_CONFIG',
    'CONF_FOLDER',
    'LOG_CONFIG_FOLDER',
    'TEMP_FOLDER',
    'LOG_FOLDER',
    'DATA_FOLDER',
    'BASE_FILE_HANDLER',
    'BASE_CONFIG',
    'DEFAULT_TIMESPAN',
    'PAGE_SIZE',
    'APP_NAME',
    'DUMP_JSON',
    'LOG_CONFIG',
    'PLACEHOLDER_PROFILE',
    'ODOO_PROFILE',
    'PS_PROFILE',
    'AZURE_PROFILE',
}


@lru_cache(maxsize=1)
def _load_config() -> dict[str, Any]:
    """Resolve KSPYDER_CONF, load baseconfig.yml and the logging config.

    Deferred until first access so that an unset/invalid KSPYDER_CONF raises
    a clear error here instead of an obscure FileNotFoundError at import time."""

    use_config = os.getenv("KSPYDER_CONF")
    if not use_config:
        raise RuntimeError(
            "KSPYDER_CONF environment variable is not set. "
            "Set it to the suffix of your config folder, e.g. KSPYDER_CONF=local "
            "for kspyder-local-conf."
        )

    conf_folder = os.path.join(ROOT_FOLDER, 'kspyder-{}-conf'.format(use_config))
    if not os.path.isdir(conf_folder):
        raise RuntimeError(
            "KSPYDER_CONF={!r} does not match an existing config folder: {}".format(
                use_config, conf_folder)
        )

    log_config_folder = os.path.join(conf_folder, 'logging')
    temp_folder = os.path.join(ROOT_FOLDER, 'temp')

    base_file_handler = FileHandler(input_folder=conf_folder, output_folder=temp_folder)
    base_config = base_file_handler.load_yaml("baseconfig")

    log_config_key = base_config["LOG_CONFIG"]
    log_config = base_file_handler.load_yaml(log_config_key, subpath=log_config_folder)

    # TODO get rid of this with KWI-30
    placeholder_profile = {
        'dbtype': 'stub',
        'url': 'http://localhost',
        'dbname': 'stub',
        'username': 'stub_user',
        'password': 'blah',
    }

    return {
        'USE_CONFIG': use_config,
        'CONF_FOLDER': conf_folder,
        'LOG_CONFIG_FOLDER': log_config_folder,
        'TEMP_FOLDER': temp_folder,
        'LOG_FOLDER': os.path.join(ROOT_FOLDER, 'log'),
        'DATA_FOLDER': os.path.join(ROOT_FOLDER, 'inputs'),
        'BASE_FILE_HANDLER': base_file_handler,
        'BASE_CONFIG': base_config,
        'DEFAULT_TIMESPAN': base_config["DEFAULT_TIMESPAN"],
        'PAGE_SIZE': base_config["PAGE_SIZE"],
        'APP_NAME': base_config["APP_NAME"],
        'DUMP_JSON': base_config["DUMP_JSON"],
        'LOG_CONFIG': log_config,
        'PLACEHOLDER_PROFILE': placeholder_profile,
        'ODOO_PROFILE': placeholder_profile,
        'PS_PROFILE': placeholder_profile,
        'AZURE_PROFILE': placeholder_profile,
    }


def __getattr__(name: str) -> Any:
    if name in _LAZY_KEYS:
        return _load_config()[name]
    raise AttributeError("module {!r} has no attribute {!r}".format(__name__, name))
