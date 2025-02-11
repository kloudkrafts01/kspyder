from common.loggingHandler import logger

class DataGraph():

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
                'model_name': self.name,
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
            element['is_leaf'] = False
            if child_count == 0:
                element['is_leaf'] = True
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