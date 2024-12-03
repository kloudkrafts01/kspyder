import datetime
import traceback

from common.config import DEFAULT_TIMESPAN, DUMP_JSON, BASE_FILE_HANDLER as fh
from common.spLogging import logger

class RESTExtractor():

    def __init__(self,**kwargs):
        self.client = "This is an empty client from the RESTExtractor interface. Please instantiate an actual Class over it"
        self.schema = "Empty schema from the RESTExtractor interface"
        self.scope = "Empty scope from the RESTExtractor interface"
        self.update_field = "Empty update_field from the RESTExtractor interface"
        self.models = [{"default": "Empty schema from the RESTExtractor interface"}]

    # def get_count(self,**kwargs):
    #     ValueError("This method was called from the RESTExtractor interface. Please instantiate an actual Class over it")

    def read_query(self,**kwargs):
        ValueError("This method was called from the RESTExtractor interface. Please instantiate an actual Class over it")

    # def forge_item(self,item,model_name,**kwargs):
    #     ValueError("This method was called from the RESTExtractor interface. Please instantiate an actual Class over it")

    def get_data(self,model_name=None,last_days=DEFAULT_TIMESPAN,search_domains=[],**params):

        logger.debug("Extractor object: {}".format(self.__dict__))

        # sd = []

        if last_days:
            now = datetime.datetime.utcnow()
            delta = datetime.timedelta(days=last_days)
            yesterday = now - delta

            logger.info("UTC start datetime is {}".format(yesterday))
            search_domains += [self.update_field,'>=',yesterday],

        count, dataset = self.fetch_dataset(model_name=model_name,search_domains=search_domains,**params)

        if dataset == []:
            logger.info('no results were found.')

        full_dataset = {
            'header': {
                'schema': self.schema,
                'scope': self.scope,
                'model': model_name,
                'count': count,
                'params': params
            },
            'data': dataset
        }

        jsonpath = None
        if DUMP_JSON:
            jsonpath = fh.dump_json(full_dataset,self.schema,"{}_{}".format(self.scope,model_name))

        return jsonpath,full_dataset

    def fetch_dataset(self,model_name=None,search_domains=[],**params):

        output_docs = []
        total_count = 0
        model = self.models[model_name]

        ex_iter = self.page_fetch(model,search_domains=search_domains,**params)

        for results_count, results in ex_iter:
            
            total_count += results_count

            for doc in results:
                # logger.debug('raw item: {}'.format(doc))
                output_docs += doc,
                # try:
                #     # cleaning and formatting the item for the dataset
                #     new_row = self.forge_item(row,model,**params)
                #     # logger.debug("forged item : {}".format(new_row))
                #     output_docs += new_row,

                # except Exception as ie:
                #     logger.error(traceback.format_exc())
                #     continue
    
        return total_count,output_docs

    def page_fetch(self,model,search_domains=[],start_token=None,**params):

        results_count = 0
        is_truncated = True

        while is_truncated:

            results, is_truncated, next_token = self.read_query(model,search_domains=search_domains,start_token=start_token,**params)
            
            how_many = len(results)
            results_count += how_many
            logger.debug("caught {} items starting from token {}".format(how_many,next_token))
            yield results_count, results

            start_token = next_token
            
            print("Fetching from next token: {}".format(next_token))
