#!python3

from google.cloud.resourcemanager import FoldersClient,ProjectsClient

from common.config import MODULES_MAP, BASE_FILE_HANDLER as fh
from common.spLogging import logger
from importlib import import_module

from google.cloud import resourcemanager

from Engines.gcloudSDKEngine import gcloudSDKEngine

CONF = fh.load_yaml(MODULES_MAP[__name__], subpath='gcloudSDKConnectors')
logger.debug("CONF: {}".format(CONF))
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']
UPD_FIELD_NAME = CONNECTOR_CONF['update_field']
DEFAULT_SCOPE = CONNECTOR_CONF['default_scope']
logger.debug("DEFAULT SCOPE: {}".format(DEFAULT_SCOPE))
MODELS = CONF['Models']

# Import the connector python module from google.cloud
CONNECTOR_CLASSNAME = CONNECTOR_CONF['name']
CONNECTOR_CLASS = import_module('google.cloud.{}'.format(CONNECTOR_CLASSNAME))

SAMPLE_GRAPH_NODES = [
    {
        'level': 0,
        'parent_id': None,
        'name': 'christiandior.com',
        'id': '237459',
        'described': True,
        'children': 2
    },
    {
        'level': 1,
        'parent_id': '237459',
        'name': 'prd',
        'id': 'prod999990',
        'described': True,
        'children': 3
    },
    {
        'level': 2,
        'parent_id': 'prod999990',
        'name': 'ShopInDior-PRD',
        'id': 'SIDprd',
        'described': True,
        'children': 0
    }
]

SAMPLE_PILE = [
    {
        'level': 1,
        'parent_id': '237459',
        'name': 'non-prd',
        'id': 'nonprd909876'
    },
    {
        'level': 2,
        'parent_id': 'prod999990',
        'name': 'Bespoke-PRD',
        'id': 'BSPKprod'
    },
    {
        'level': 2,
        'parent_id': 'prod999990',
        'name': 'Dataiku-PRD',
        'id': 'DTKprod'
    }
]

SAMPLE_CHILDREN = [
    {
        'parent_id': 'DTKprod',
        'name': 'DataikuStudio-PRD',
        'id': 'DTKstudioPRD'
    },
    {
        'parent_id': 'nonprd909876',
        'name': 'Bespoke-NONPRD',
        'id': 'bspkNONPRD'
    },
    {
        'parent_id': 'nonprd909876',
        'name': 'Dataiku-NONPRD',
        'id': 'DTKnonPRD'
}
]


class ElementGraph():

    def __init__(self,name):
        
        self.name = name
        self.described = False
        self.depth = 0
        self.node_count = 0
        self.leaf_count = 0
        self.nodes = []

    def add_node(self,element):
        
        self.nodes.append(element)
        self.node_count += 1

        if element['level'] > self.depth:
            self.depth = element['level']
        
        if element['children'] == 0:
            self.leaf_count += 1


class gcloudResourceClient():

    def __init__(self,org_id=None):
        
        self.org_id = org_id
        self.folder_client = FoldersClient()
        self.projects_client = ProjectsClient()

    def get_all_folders(self):
        
        parent = self.org_id

        sample_graph = ElementGraph('sample_graph')
        sample_graph.depth = 2
        sample_graph.node_count = 3
        sample_graph.leaf_count = 1
        sample_graph.nodes = SAMPLE_GRAPH_NODES

        print("INITIAL SAMPLE:")
        for item in sample_graph.nodes:
            print(item)

        process_pile = SAMPLE_PILE 
        print("PROCESS PILE:")
        for item in process_pile:
            print(item)
        
        # Depth-first graph building
        while not sample_graph.described:

            # pop lowest element in the pile and visit it
            element = process_pile.pop()
            print("popped element: {}".format(element))
            child_count = 0
            children = self.get_folders(
                parent = element['id']
            )
            for child in children:
                # append each found child to the queue
                child_count += 1
                # child_element = proto.Message.to_dict(child)
                child_element = child
                child_element['level'] = element['level'] + 1
                print("--- child found: {}".format(child_element))
                process_pile.append(child_element)

            # When all children are added to queue, complete element and store it to graph
            element['children'] = child_count
            element['described'] = True
            if child_count == 0:
                print("Element {} is a Leaf.".format(element['name']))

            sample_graph.add_node(element)
            # Re-revaluate if queue is empty - therefore if graph completely described
            sample_graph.described = (len(process_pile) == 0)
    
        print("FINAL SAMPLE DESCRIBED: {}".format(sample_graph.described))
        print("--- DEPTH = {}".format(sample_graph.depth))
        print("--- NODES = {}".format(sample_graph.node_count))
        print("--- LEAVES = {}".format(sample_graph.leaf_count))
        for item in sample_graph.nodes:
            print(item)

    def get_folders(self, parent=None):

        print("PARENT_ID = {}".format(parent))
        # Dummy code
        children = [x for x in SAMPLE_CHILDREN if x['parent_id'] == parent]
        return children

class gcloudResourceManagerConnector(gcloudSDKEngine):

    def __init__(self, client=None, schema=SCHEMA_NAME, models=MODELS, update_field=UPD_FIELD_NAME, connector_class=CONNECTOR_CLASS, **params):
        gcloudSDKEngine.__init__(self,
                    client=client,
                    schema=schema,
                    models=models,
                    update_field=update_field,
                    connector_class=connector_class,
                    **params
                    )
