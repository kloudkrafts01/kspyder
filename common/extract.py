import datetime
import traceback

from .utils import json_dump
from .config import DEFAULT_TIMESPAN, DUMP_JSON
from .spLogging import logger

class GenericExtractor():

    def __init__(self):
        self.client = "This is an empty client from the GenericExtractor interface. Please instantiate an actual Class over it"
        self.schema = "Empty schema from the GenericExtractor interface"
        self.models = {"default": "Empty schema from the GenericExtractor interface"}

    def get_count(self,model_name):
        ValueError("This method was called from the GenericExtractor interface. Please instantiate an actual Class over it")

    def read_query(self,model_name):
        ValueError("This method was called from the GenericExtractor interface. Please instantiate an actual Class over it")

    def forge_item(self,model_name):
        ValueError("This method was called from the GenericExtractor interface. Please instantiate an actual Class over it")


    def get_data(self,model_name,last_days=DEFAULT_TIMESPAN):

        sd = []
        if last_days:
            today = datetime.datetime.utcnow()
            delta = datetime.timedelta(days=last_days)
            yesterday = today - delta

            logger.info("UTC start datetime is {}".format(yesterday))
            sd += [self.update_field,'>=',yesterday],

        count, dataset = self.fetch_dataset(model_name,search_domains=sd)

        if dataset == []:
            logger.info('no results were found.')

        full_dataset = {
            'header': {
                'schema': self.schema,
                'model': model_name,
                'count': count
            },
            'data': dataset
        }

        jsonpath = None
        if DUMP_JSON:
            jsonpath = json_dump(full_dataset,self.schema,model_name)

        return jsonpath,full_dataset

    def fetch_dataset(self,model_name,search_domains=[]):

        output_rows = []    
        model = self.models[model_name]
        total_count = self.get_count(model,search_domains)

        if total_count > 0:    
            
            logger.info('Found a total of {} items.'.format(total_count))        
            ex_iter = self.batch_fetch(model,search_domains=search_domains,batch_size=total_count)

            for results in ex_iter:

                for row in results:
                    # logger.debug('raw item: {}'.format(row))
                    try:
                        # cleaning and formatting the item for the dataset
                        new_row = self.forge_item(row,model)
                        # logger.debug("forged item : {}".format(new_row))
                        output_rows += new_row,

                    except Exception as ie:
                        logger.error(traceback.format_exc())
                        continue
        
        return total_count,output_rows

    def batch_fetch(self,model,search_domains=[],start_row=0,batch_size=None):

        while batch_size > 0:

            results = self.read_query(model,search_domains=search_domains,start_row=start_row)

            how_many = len(results)
            logger.debug("caught {} items starting at row = {}".format(how_many,start_row))
            yield results
            
            start_row += how_many
            batch_size = batch_size - how_many
            print("{} more to go.".format(batch_size))
