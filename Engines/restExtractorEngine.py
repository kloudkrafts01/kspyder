import datetime
import traceback
import re
from urllib.parse import urljoin

from common.config import DEFAULT_TIMESPAN, DUMP_JSON, BASE_FILE_HANDLER as fh
from common.loggingHandler import logger

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

class RESTExtractor():

    def __init__(self,**kwargs):
        self.client = "This is an empty client from the RESTExtractor interface. Please instantiate an actual Class over it"
        self.schema = "Empty schema from the RESTExtractor interface"
        self.scopes = "Empty scope from the RESTExtractor interface"
        self.update_field = "Empty update_field from the RESTExtractor interface"
        self.models = [{"default": "Empty schema from the RESTExtractor interface"}]

    def read_query(self,**kwargs):
        ValueError("This method was called from the RESTExtractor interface. Please instantiate an actual Class over it")

    def build_request(self,model,baseurl=None,**params):
        """Method to build valid URL, parameters and headers for a python request call from a model definition."""

        # Only keep parameters with accepted keys
        valid_params = {}
        if 'accepted_inputs' in model.keys():
            valid_keys = (x for x in params.keys() if x in model['accepted_inputs'])
            for key in valid_keys:
                valid_params[key] = params[key]
        else:
            # If nothing specified, just keep any parameters passed
            valid_params = params

        logger.debug("Initial Valid Params: {}".format(valid_params))

        # build URL
        logger.debug("Now building Query URL...")
        path_expression = model['path']
        url_path = path_expression
        params_to_pop = []

        for key,value in valid_params.items():
            
            # Compile and search for the parameter key in the URL path expression
            pattern_string = '\{\$(%s)\}' % key
            var_pattern = re.compile(pattern_string,re.I)
            matches = re.search(var_pattern, path_expression).groups()

            for matched_item in matches:
                # if parameter was matched, sub the expression
                logger.debug("Matched following item in path: {}".format(matched_item))
                url_path = re.sub(var_pattern, str(value), url_path)
                params_to_pop.append(key)

        # pop out any parameter used to build the URL so there's no duplicate in request parameters
        for key in params_to_pop:
            valid_params.pop(key)
        
        url = urljoin(baseurl, url_path)
        logger.debug("Query URL: {}".format(url))
        logger.debug("Final Valid Params: {}".format(valid_params))

        headers = model['headers'] if 'headers' in model.keys() else {}
        logger.debug("Request headers: {}".format(headers))

        return url, headers, valid_params

    def get_data(self,model_name=None,last_days=DEFAULT_TIMESPAN,search_domains=[],input_data=[{}],**params):
        """Get Data from the connector.
        
        INPUTS :
        
         - model_name : Name of the model of data wanted
         - last_days : number of days of data to get
         - search_domains : triplets for search query parameters
        search_domain are given in the form of a 3-element list: [ 'field', 'operation', 'value' ]
        
         - input_data : a given array of input key-values
        Each key-value needs to be fed as input to a query, and aggregated.
        This method assumes the input in the form of a list of 
        one-level key-value dicts, with consistent keys ie :
        inputs = [ 
                    {
                        "key01": "value01", 
                        "key02": "value02"
                    },
                    {
                        "key01": "value03",
                        "key02": "value04"
                    }
                ]

         - **params : additional keyword arguments
        """

        # logger.debug("Extractor object: {}".format(self.__dict__))

        if last_days:
            now = datetime.datetime.utcnow()
            delta = datetime.timedelta(days=last_days)
            yesterday = now - delta

            logger.info("UTC start datetime is {}".format(yesterday))
            search_domains += [self.update_field,'>=',yesterday],

        count = 0
        dataset = []
        failed_items = []
        model = self.models[model_name]

        for input_item in input_data:
            
            logger.debug("Input item: {}".format(input_item))

            item_params = {**params, **input_item}
            logger.debug("Using this as input params for this round: {}".format(item_params))

            try:
                result_count, plain_dataset = self.fetch_dataset(model,search_domains=search_domains,**item_params)
                
                count += result_count
                # Only add the result dataset if not empty
                if result_count > 0:
                    result_dataset = [{**input_item, **result_item} for result_item in plain_dataset]
                    dataset.extend(result_dataset)
            
            except Exception as e:
                logger.exception(e)
                failed_items += {
                    'item': input_item,
                    'reason': e
                },
                continue
        
        full_dataset = {
                'header': {
                    'schema': self.schema,
                    'model_name': model_name,
                    'model': model,
                    'count': count,
                    'json_dump': None,
                    'csv_dump': None,
                    'scopes': self.scopes,
                    'params': params
                },
                'failed_items': failed_items,
                'data': dataset
            }
            
        if dataset == []:
            logger.info('no results were found.')
        else: 
            if DUMP_JSON:
                full_dataset = fh.dump_json(full_dataset,self.schema,model_name)

        return full_dataset

    def fetch_dataset(self,model,search_domains=[],**params):

        output_docs = []
        total_count = 0

        ex_iter = self.paginated_fetch(model,search_domains=search_domains,**params)

        for results_count, results in ex_iter:
            
            total_count += results_count
            output_docs.extend(results)
        
        return total_count,output_docs

    def paginated_fetch(self,model,search_domains=[],start_token=None,**params):

        results_count = 0
        is_truncated = True

        while is_truncated:

            results, is_truncated, next_token = self.read_query(model,search_domains=search_domains,start_token=start_token,**params)
            
            results_count = len(results)
            logger.debug("caught {} items starting from token {}".format(results_count,start_token))

            yield results_count, results

            # set for the next query iteration
            start_token = next_token
            
    def postprocess_item(self,item,model=None,**params):
        """Placeholder method ; if the API returns elements that need postprocessing
        (e.g. if return payload is not directly serializable), run the item through this.
        
        Child classes inheriting from the REST Extractor interface can supercharge this method if necessary.
        By default, just returns the item unchanged."""

        return item
        

    def discover_data(self,model_name=None,input_data=[{}],**params):
        """Recursiverly discovers REST data, depth-first, starting from a given root element"""

        model = self.models[model_name]

        # initiate graph with root-level node
        graph = ElementGraph(
            name = model_name,
            node_key = model['node_key'],
            parent_key = model['parent_key']
            )
        
        root_element = input_data.pop(0)
        if len(input_data) > 0:
            logger.warning("Graph discovery only takes the first input into account. All subsequent elements will be ignored: {}".format(input_data))
        
        if 'level' not in root_element.keys():
            root_element['level'] = 0

        graph.describe_graph(
            start_node = root_element,
            fetch_method = getattr( self.client, model['query_name'] ),
            postprocess_method = self.postprocess_item
            )

        full_dataset = graph.to_dict()
        # Adding model specification for interop compliance with mongo insert and json dump methods
        full_dataset['header']['model'] = model

        if DUMP_JSON:
            full_dataset = fh.dump_json(full_dataset,self.schema,model_name)

        return full_dataset
