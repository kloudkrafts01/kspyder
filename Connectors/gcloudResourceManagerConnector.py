# from google.cloud.resourcemanager import FoldersClient,ListFoldersRequest
import proto

from common.config import MODULES_MAP, DUMP_JSON, BASE_FILE_HANDLER as fh
from common.spLogging import logger
from importlib import import_module

# from google.cloud import resourcemanager

from Engines.gcloudSDKEngine import gcloudSDKEngine

CONF = fh.load_yaml('gcloudRMmodels', subpath='gcloudSDKConnectors')
logger.debug("CONF: {}".format(CONF))
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']
UPD_FIELD_NAME = CONNECTOR_CONF['update_field']
MODELS = CONF['Models']

# Import the connector python module from google.cloud
CONNECTOR_CLASSNAME = CONNECTOR_CONF['name']
CONNECTOR_CLASS = import_module('google.cloud.{}'.format(CONNECTOR_CLASSNAME))


class ElementGraph():

    def __init__(self,name=None,node_key=None,parent_key=None):
        
        self.name = name
        self.node_key = node_key
        self.parent_key = parent_key
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

    def to_dict(self):

        dict_graph = {
            'header': {
                'name': self.name,
                'node_key': self.node_key,
                'parent_key': self.parent_key,
                'described': self.described,
                'depth': self.depth,
                'node_count': self.node_count,
                'leaf_count': self.leaf_count,
            },
            'data': self.nodes
        }

        return dict_graph

    def describe_graph(self, start_node=None, fetch_method=None, postprocess_method=None):

        # Create a processing pile with starting node
        process_pile = [ start_node ]

        # Depth-first graph building
        while not self.described:

            # pop lowest element in the pile and visit it
            element = process_pile.pop()
            logger.debug("popped element: {}".format(element))
            child_count = 0
            fetch_args = {
                self.parent_key: element[self.node_key]
            }
            children = fetch_method( **fetch_args )
            for child in children:
                # append each found child to the queue
                child_count += 1
                child_element = postprocess_method(child)
                # child_element = child
                child_element['level'] = element['level'] + 1
                logger.debug("--- child found: {}".format(child_element))
                process_pile.append(child_element)

            # When all children are added to queue, complete element and store it to graph
            element['children'] = child_count
            element['described'] = True
            if child_count == 0:
                logger.debug("Element {} is a Leaf.".format(element[self.node_key]))

            self.add_node(element)
            # Re-revaluate if queue is empty - therefore if graph completely described
            self.described = (len(process_pile) == 0)
    
        logger.debug("FINAL GRAPH DESCRIBED: {}".format(self.described))
        logger.debug("--- DEPTH = {}".format(self.depth))
        logger.debug("--- NODES = {}".format(self.node_count))
        logger.debug("--- LEAVES = {}".format(self.leaf_count))
        # for item in sample_graph.nodes:
        #     print(item)



# SAMPLE_GRAPH_NODES = [
#     {
#         'level': 0,
#         'parent': None,
#         'display_name': 'christiandior.com',
#         'name': '237459',
#         'described': True,
#         'children': 2
#     },
#     {
#         'level': 1,
#         'parent': '237459',
#         'display_name': 'prd',
#         'name': 'prod999990',
#         'described': True,
#         'children': 3
#     },
#     {
#         'level': 2,
#         'parent': 'prod999990',
#         'display_name': 'ShopInDior-PRD',
#         'name': 'SIDprd',
#         'described': True,
#         'children': 0
#     }
# ]

# SAMPLE_GRAPH = ElementGraph('sample_graph')
# SAMPLE_GRAPH.depth = 2
# SAMPLE_GRAPH.node_count = 3
# SAMPLE_GRAPH.leaf_count = 1
# SAMPLE_GRAPH.nodes = SAMPLE_GRAPH_NODES

# SAMPLE_PILE = [
#     {
#         'level': 1,
#         'parent': '237459',
#         'disaply_name': 'non-prd',
#         'name': 'nonprd909876'
#     },
#     {
#         'level': 2,
#         'parent': 'prod999990',
#         'display_name': 'Bespoke-PRD',
#         'name': 'BSPKprod'
#     },
#     {
#         'level': 2,
#         'parent': 'prod999990',
#         'disaply_name': 'Dataiku-PRD',
#         'name': 'DTKprod'
#     }
# ]

# SAMPLE_CHILDREN = [
#     {
#         'parent': 'DTKprod',
#         'display_name': 'DataikuStudio-PRD',
#         'name': 'DTKstudioPRD'
#     },
#     {
#         'parent': 'nonprd909876',
#         'display_name': 'Bespoke-NONPRD',
#         'name': 'bspkNONPRD'
#     },
#     {
#         'parent': 'nonprd909876',
#         'display_name': 'Dataiku-NONPRD',
#         'name': 'DTKnonPRD'
#     }
# ]

# class FoldersGraphClient():

#     def __init__(self,org_id=None,scope=None):
        
#         self.org_id = org_id
#         self.scope = scope
#         self.client = FoldersClient()

#         # initiate graph with root-level node
#         self.graph = ElementGraph(
#             name = self.scope,
#             node_key = 'name',
#             parent_key = 'parent'
#             )

#     def get_all_folders(self):
        
#         parent = self.org_id
#         root_element = {
#             'level': 0,
#             'parent': None,
#             'display_name': self.scope,
#             'name': self.org_id,
#             'described': False
#         }

#         self.graph.describe_graph(
#             start_node = root_element,
#             fetch_method = getattr( self.client, "list_folders" ),
#             postprocess_method = getattr( proto.Message, "to_dict" )
#             )

#         return self.graph.to_dict()

#     def get_folders(self, parent=None):

#         print("PARENT_ID = {}".format(parent))
#         # Dummy code
#         # children = [x for x in SAMPLE_CHILDREN if x['parent_id'] == parent]

#         request = ListFoldersRequest( parent = parent )
#         response = self.folder_client.list_folders(request)

#         return response

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

    def discover_data(self,model_name=None,root_element=None,**params):
        """Recursiverly discovers REST data, depth-first, starting from a given root element"""

        model = self.models[model_name]

        # initiate graph with root-level node
        graph = ElementGraph(
            name = model_name,
            node_key = model['node_key'],
            parent_key = model['parent_key']
            )

        # Instantiate the relevant API client class from google.cloud
        self.set_client_from_model(model)

        graph.describe_graph(
            start_node = root_element,
            fetch_method = getattr( self.client, model['query_name'] ),
            postprocess_method = getattr( proto.Message, "to_dict" )
            )

        full_dataset = graph.to_dict()

        if DUMP_JSON:
            full_dataset = fh.dump_json(full_dataset,self.schema,model_name)

        return full_dataset
