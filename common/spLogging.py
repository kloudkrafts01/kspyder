import yaml
import logging
import logging.config

from .config import LOG_CONFIG


logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger('bgspyder')
