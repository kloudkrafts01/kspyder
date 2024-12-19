import datetime
import traceback

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


    def get_data(self,model_name=None,last_days=DEFAULT_TIMESPAN,search_domains=[],input_data=[{}],**params):
        """Variation of the get_data method when given an array of input key-values.
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
                    'scopes': self.scopes,
                    'model': model_name,
                    'count': count,
                    'params': params,
                    'json_dump': None,
                    'csv_dump': None,
                    'failed_items': failed_items
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
            
            logger.debug("Fetching from next token: {}".format(next_token))
