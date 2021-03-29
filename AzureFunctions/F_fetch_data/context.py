import os,sys

HERE = os.path.dirname(__file__)
ROOT_FOLDER = os.path.abspath(os.path.join(HERE,'..'))
CONF_FOLDER = os.path.abspath(os.path.join(ROOT_FOLDER,'common'))

sys.path.insert(0,ROOT_FOLDER)
sys.path.insert(0,CONF_FOLDER)

import common.config