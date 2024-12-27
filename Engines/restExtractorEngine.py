import datetime
import traceback
import re
from urllib.parse import urljoin

from common.config import DEFAULT_TIMESPAN, DUMP_JSON, BASE_FILE_HANDLER as fh
from common.spLogging import logger

class RESTExtractor():

    def __init__(self,**kwargs):
        self.client = "This is an empty client from the RESTExtractor interface. Please instantiate an actual Class over it"
        self.schema = "Empty schema from the RESTExtractor interface"
        self.scopes = "Empty scope from the RESTExtractor interface"
        self.update_field = "Empty update_field from the RESTExtractor interface"
        self.models = [{"default": "Empty schema from the RESTExtractor interface"}]

    def read_query(self,**kwargs):
        ValueError("This method was called from the RESTExtractor interface. Please instantiate an actual Class over it")

    def build_query(self,model,baseurl=None,**params):
        """Method to build valid URL, parameters and headers for a python request call from a model definition."""

        # Only keep parameters with accepted keys
        valid_params = {}
        if 'accepted_inputs' in model.keys():
            valid_keys = (x for x in params.keys() if x in model['accepted_inputs'])
            valid_params_list = [ {k:params[k]} for k in valid_keys ]
            for param in valid_params_list:
                valid_params = { **valid_params, **param }
        else:
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
        # failed_items = []

        for input_item in input_data:
            
            logger.debug("Input item: {}".format(input_item))

            item_params = {**params, **input_item}
            logger.debug("Using this as input params for this round: {}".format(item_params))

            # try:
            result_count, plain_dataset = self.fetch_dataset(model_name=model_name,search_domains=search_domains,**item_params)
            
            count += result_count
            # Only add the result dataset if not empty
            if result_count > 0:
                result_dataset = [{**input_item, **result_item} for result_item in plain_dataset]
                dataset.extend(result_dataset)
            
            # except Exception as e:
            #     logger.error(e.)
            #     failed_items += {
            #         'item': input_item,
            #         'reason': e.__str__
            #     },
            #     continue
            
        if dataset == []:
            logger.info('no results were found.')
            return {}
        
        else: 
            full_dataset = {
                'header': {
                    'schema': self.schema,
                    'model': model_name,
                    'count': count,
                    'json_dump': None,
                    'csv_dump': None,
                    'scopes': self.scopes,
                    'params': params
                },
                'data': dataset
            }

            if DUMP_JSON:
                full_dataset = fh.dump_json(full_dataset,self.schema,model_name)

            return full_dataset

    def fetch_dataset(self,model_name=None,search_domains=[],**params):

        output_docs = []
        total_count = 0
        model = self.models[model_name]

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
            
