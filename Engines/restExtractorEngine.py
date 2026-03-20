import datetime
import time
import re
import requests
import jmespath
from urllib.parse import urljoin

from common.config import DEFAULT_TIMESPAN, DUMP_JSON, BASE_FILE_HANDLER as fh
from common.loggingHandler import logger
from common.baseModels import DataGraph
from common.models import Dataset, DatasetHeader, DataPage, PageCursor
from common.configModels import APIConfig


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

    def get_data(self, model_name=None, last_days=DEFAULT_TIMESPAN, search_domains=[], input_data=[{}], **params):
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

        if last_days:
            now = datetime.datetime.now()
            delta = datetime.timedelta(days=last_days)
            yesterday = now - delta
            logger.info("UTC start datetime is {}".format(yesterday))
            search_domains += [self.update_field, '>=', yesterday],

        model = self.models[model_name]
        scopes = self.scopes if isinstance(self.scopes, list) else None

        dataset = Dataset(
            header=DatasetHeader(
                source_schema=self.schema,
                model_name=model_name,
                model=model,
                scopes=scopes,
                params=params,
            )
        )

        for input_item in input_data:
            logger.debug("Input item: {}".format(input_item))
            try:
                self.fetch_dataset(dataset, input_item, model, search_domains=search_domains, **params)
            except Exception as e:
                logger.exception(e)
                dataset.failed_items.append({'item': input_item})
                continue

        if not dataset:
            logger.info('no results were found.')
        else:
            if DUMP_JSON:
                fh.dump_json(dataset.to_json(), self.schema, model_name)

        return dataset

    def set_api_from_model(self,model):
        
        self.api_name = model['API']
        self.api = APIConfig(**self.apis[self.api_name])

        # Prepare response translation map
        base_response_map = self.api.response_map or {}
        response_map = model['response_map'] if 'response_map' in model.keys() else {}
        include_base_map = model['include_base_response_map'] if 'include_base_response_map' in model.keys() else True

        if include_base_map:
            # if include API base mapping is true, merge both dicts
            model['response_map'] = { **base_response_map, **response_map }

        self.response_map = model['response_map']
        if 'data' not in model['response_map'].keys():
            logger.exception("Model does not specify a 'data' path. No payload will be returned.")

        # prepare rate limit (expressed in seconds before new call)
        if self.api.rate_limit is not None:
            self.rate_limit = self.api.rate_limit


        self.iterate_output = model['iterable'] if 'iterable' in model.keys() else True

    def fetch_dataset(self, dataset: Dataset, input_item: dict, model, search_domains=[], **params):
        """Paginate over a single input_item and accumulate DataPages into the given Dataset."""

        self.set_api_from_model(model)
        merged_params = {**params, **input_item}
        logger.debug("Using this as input params for this round: {}".format(merged_params))

        for page in self.paginated_fetch(model, search_domains=search_domains, **merged_params):
            if page.count > 0:
                dataset.update(page.model_copy(update={'input_context': input_item}))

    def _build_cursor(self, next_token, is_truncated: bool) -> PageCursor | None:
        """Wrap the raw next_token into a typed PageCursor based on the API's pagination style."""
        if not is_truncated or next_token is None:
            return None
        if self.api.pagination_style == "pages":
            return PageCursor(next_page=int(next_token))
        if self.api.pagination_style == "offsets":
            return PageCursor(next_offset=int(next_token))
        return PageCursor(next_token=str(next_token))

    def paginated_fetch(self, model, search_domains=[], start_token=None, **params):

        is_truncated = True
        page_num = 0

        while is_truncated:

            results, is_truncated, next_token, current_token = self.read_query(
                model, search_domains=search_domains, start_token=start_token, **params)

            results_count = len(results)
            logger.debug("caught {} items starting from token {}".format(results_count, current_token))

            cursor = self._build_cursor(next_token, is_truncated)
            yield DataPage(
                page_num=page_num,
                count=results_count,
                data=results,
                is_last=not is_truncated,
                cursor=cursor,
            )

            page_num += 1
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

        logger.debug(f"Applying Response map: {self.response_map}")
        
        for key, value in self.response_map.items():
            # get all fields through JMESpath expressions, except if the keyword __ROOT__ is there.
            # if __ROOT__ is given in the model def, then just store the full response body in list type
            if value == "__ROOT__":
                translated_data[key] = response_data if type(response_data) is list else [response_data]
            else:
                translated_data[key] = jmespath.search(value, response_data)

        # pop out the dataset and keep the rest as metadata
        data = translated_data.pop('data')
        if data is None:
            data = []
        metadata = translated_data

        logger.debug(f"Translated metadata: {translated_data}")

        count = int(translated_data.get('count', len(data)))
        total_count = translated_data.get('total_count')
        total_count = int(total_count) if total_count else None
        next_token_key = self.api.next_token_key
        next_token = translated_data.get(next_token_key)
        logger.debug("next token: {}".format(next_token))
        
        # Determine if the current results are truncated or not 
        # If explicitly given in the response, then take it
        if 'is_truncated' in translated_data.keys():
            is_truncated = translated_data['is_truncated']
            logger.debug(f"is_truncated value found in response: {is_truncated}")

        # if not : explicit 'is_last' value > no next token > empty next token > count equals total
        else:
            if 'is_last' in translated_data.keys():
                is_last = bool(translated_data['is_last'])
                logger.debug("Is Last ? {}".format(is_last))
                is_truncated = not is_last

            elif next_token is None:
                is_truncated = False

            elif next_token is not None:
                is_truncated = (next_token != "")
                logger.debug(f"Is Truncated because there is a next token ? {is_truncated}")

                if total_count is not None:
                    logger.debug(f"Determining if truncated from count: {count}, total count: {total_count}")
                    is_truncated = (count < total_count) and (count > 0)

            else: 
                is_truncated = False

        logger.debug("Is response truncated? {}".format(is_truncated))

        # If page-based pagination, replace whatever next_token value with pagenumber + 1
        if (self.api.pagination_style == "pages") and is_truncated:
            logger.debug(f"Start Token: {start_token}")
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
        full_dataset['header']['count'] = graph.node_count
        full_dataset['header']['schema'] = self.schema

        if DUMP_JSON:
            full_dataset = fh.dump_json(full_dataset,self.schema,model_name)

        return full_dataset
