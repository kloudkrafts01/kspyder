import datetime
import time
import re
import requests
import jmespath
from urllib.parse import urljoin

from common.config import DEFAULT_TIMESPAN, DUMP_JSON, BASE_FILE_HANDLER as fh
from common.loggingHandler import logger
from common.baseModels import DataGraph

class GenericMap():

    def __init__(self, payload={}):
        for key,value in payload.items():
            setattr(self,key,value)


class RESTExtractor():

    def __init__(self,**kwargs):
        self.client = "This is an empty client from the RESTExtractor interface. Please instantiate an actual Class over it"
        self.schema = "Empty schema from the RESTExtractor interface"
        self.scopes = "Empty scope from the RESTExtractor interface"
        self.update_field = "Empty update_field from the RESTExtractor interface"
        self.models = [{"default": "Empty schema from the RESTExtractor interface"}]
        self.apis = [{"default": "Empty schema from the RESTExtractor interface"}]
        self.iterate_output = True
        self.rate_limit = None
        self.response_map = {}

    def read_query(self, model, start_token:int = 1, batch_size:int = 100, **params):

        data = []
        metadata = {}
        is_truncated = False
        next_token = None

        params, start_token, batch_size = self.preprocess_params(params,start_token=start_token,batch_size=batch_size)

        url, headers, valid_params = self.build_request(model, baseurl = self.api.base_url, **params)
        
        # pass the request, get http status and response payload
        response = requests.get(url, headers = headers, params = valid_params)
        raw_response_data = response.json()
        status_code = response.status_code
        logger.debug("Response Status code: {}".format(status_code))
        # logger.debug("Raw response data: {}".format(raw_response_data))

        if status_code == 200:
            data, metadata, is_truncated, next_token = self.postprocess_response(raw_response_data, model = model, start_token = start_token)

        else:
            logger.exception("Encountered error in response: {}".format(raw_response_data))

        return data, is_truncated, next_token, start_token
    
    def build_url_path(self,path_expression,valid_params={}):
        
        url_path = path_expression
        params_to_pop = []

        for key,value in valid_params.items():
            
            # Compile and search for the parameter key in the URL path expression
            pattern_string = r'\{\$(%s)\}' % key
            var_pattern = re.compile(pattern_string,re.I)
            matches = re.search(var_pattern, path_expression)
            match_groups = matches.groups() if matches else []

            for matched_item in match_groups:
                # if parameter was matched, sub the expression
                logger.debug("Matched following item in path: {}".format(matched_item))
                url_path = re.sub(var_pattern, str(value), url_path)
                params_to_pop.append(key)

        # pop out any parameter used to build the URL so there's no duplicate in request parameters
        for key in params_to_pop:
            valid_params.pop(key)
        
        return url_path, valid_params

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
        url_path, valid_params = self.build_url_path(path_expression,valid_params=valid_params)

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
                    'item': input_item
                    # 'reason': e
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

    def set_api_from_model(self,model):
        
        self.api_name = model['API']
        self.api = GenericMap(payload = self.apis[self.api_name])

        # Prepare response translation map
        base_response_map = self.api.response_map if hasattr(self.api, 'response_map') else {}
        response_map = model['response_map'] if 'response_map' in model.keys() else {}
        include_base_map = model['include_base_response_map'] if 'include_base_response_map' in model.keys() else True
        
        if include_base_map:
            # if include API base mapping is true, merge both dicts
            model['response_map'] = { **base_response_map, **response_map }

        self.response_map = model['response_map']
        if 'data' not in model['response_map'].keys():
            logger.exception("Model does not specify a 'data' path. No payload will be returned.")

        # prepare rate limit (expressed in seconds before new call)
        self.rate_limit = self.api.rate_limit if hasattr(self.api, 'rate_limit') else self.rate_limit


        self.iterate_output = model['iterable'] if 'iterable' in model.keys() else True

    def fetch_dataset(self,model,search_domains=[],**params):

        output_docs = []
        total_count = 0

        self.set_api_from_model(model)

        ex_iter = self.paginated_fetch(model,search_domains=search_domains,**params)

        for results_count, results in ex_iter:
            
            total_count += results_count
            output_docs.extend(results)
        
        return total_count,output_docs

    def paginated_fetch(self,model,search_domains=[],start_token=None,**params):

        results_count = 0
        is_truncated = True

        while is_truncated:

            results, is_truncated, next_token, current_token = self.read_query(model,search_domains=search_domains,start_token=start_token,**params)
            
            results_count = len(results)
            logger.debug("caught {} items starting from token {}".format(results_count,current_token))

            yield results_count, results

            # set for the next query iteration
            start_token = next_token

            if self.rate_limit:
                time.sleep(self.rate_limit)

    def preprocess_params(self,params,start_token=None,batch_size=None):
        """Process and add up query parameters for pagination, according to the API's pagination style"""

        # mandatory: put start and batch size into query parameters entry
        actual_start_token = start_token
        actual_batch_size = int(batch_size) if batch_size else self.batch_size

        logger.debug("Pagination style is: {}".format(self.api.pagination_style))
        
        if self.api.pagination_style == "pages":
            actual_start_token = int(start_token) if start_token else 1

        if self.api.pagination_style == "offsets":
            actual_start_token = int(start_token) if start_token else 0
        
        params[self.api.next_token_key] = actual_start_token
        params[self.api.batch_size_key] = actual_batch_size
        logger.debug("Preprocessed Params: {}".format(params))

        return actual_start_token, params

    def postprocess_response(self, response_data, start_token=None, **params):

        translated_data = {}
        metadata = {}
        data = []
        is_truncated = False
        next_token = None

        for key, value in self.response_map.items():
            translated_data[key] = jmespath.search(value, response_data)

        # logger.debug("Translated response data: {}".format(translated_data))

        # pop out the dataset and keep the rest as metadata
        data = translated_data.pop('data')
        metadata = translated_data

        logger.debug("Item metadata: {}".format(metadata))

        count = int(translated_data['count']) if 'count' in translated_data.keys() else len(data)
        total_count = int(translated_data['total_count']) if 'total_count' in translated_data.keys() else None
        next_token = translated_data['next_token'] if 'next_token' in translated_data.keys() else None
        logger.debug("next token: {}".format(next_token))
        
        # Determine if the current results are truncated or not, based on explicit fields if present, or on number counts
        if 'is_truncated' in translated_data.keys():
            is_truncated = translated_data['is_truncated']
        else:
            if 'is_last' in translated_data.keys():
                is_last = bool(translated_data['is_last'])
                logger.debug("Is Last ? {}".format(is_last))
                is_truncated = not is_last
            elif next_token is not None:
                is_truncated = (next_token != "")
            elif total_count is not None:
                is_truncated = (count < total_count) and (count > 0)
            else: 
                is_truncated = False

        logger.debug("Is response truncated? {}".format(is_truncated))

        # If page-based pagination, replace whatever next_token value with pagenumber + 1
        if (self.api.pagination_style == "pages") and is_truncated:
            next_token = start_token + 1
        
        # If offset-based pagination, replace whatever next_token value with offset + results size
        if (self.api.pagination_style == "offsets") and is_truncated:
            next_token = start_token + len(data)

        return data, metadata, is_truncated, next_token
        

    def discover_data(self,model_name=None,input_data=[{}],**params):
        """Recursiverly discovers REST data, depth-first, starting from a given root element"""

        model = self.models[model_name]

        # initiate graph with root-level node
        graph = DataGraph(
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
