import datetime
import traceback

from common.config import DEFAULT_TIMESPAN, DUMP_JSON, BASE_FILE_HANDLER as fh
from common.loggingHandler import logger

class GenericRPCExtractor():

    def __init__(self,**kwargs):
        self.client = "This is an empty client from the GenericRPCExtractor interface. Please instantiate an actual Class over it"
        self.schema = "Empty schema from the GenericRPCExtractor interface"
        self.scopes = "Empty scope from the GenericRPCExtractor interface"
        self.update_field = "Empty update_field from the GenericRPCExtractor interface"
        self.models = [{"default": "Empty schema from the GenericRPCExtractor interface"}]

    def get_count(self,**kwargs):
        ValueError("This method was called from the GenericRPCExtractor interface. Please instantiate an actual Class over it")

    def read_query(self,**kwargs):
        ValueError("This method was called from the GenericRPCExtractor interface. Please instantiate an actual Class over it")

    def forge_item(self,item,model_name,**kwargs):
        ValueError("This method was called from the GenericRPCExtractor interface. Please instantiate an actual Class over it")

    def get_data(self,model_name=None,last_days=DEFAULT_TIMESPAN,search_domains=[],**params):

        logger.debug("Extractor object: {}".format(self.__dict__))

        # sd = []
        model = self.models[model_name]

        if last_days:
            now = datetime.datetime.utcnow()
            delta = datetime.timedelta(days=last_days)
            yesterday = now - delta

            logger.info("UTC start datetime is {}".format(yesterday))
            search_domains += [self.update_field,'>=',yesterday],

        count, dataset = self.fetch_dataset(model=model,search_domains=search_domains,**params)

        full_dataset = {
                'header': {
                    'schema': self.schema,
                    'scopes': self.scopes,
                    'model_name': model_name,
                    'model': model,
                    'count': count,
                    'params': params,
                    'json_dump': None,
                    'csv_dump': None
                },
                'data': dataset
            }
        
        if dataset == []:
            logger.info('no results were found.')
        
        else: 
            if DUMP_JSON:
                full_dataset = fh.dump_json(full_dataset,self.schema,model_name)

        
        return full_dataset

    def fetch_dataset(self,model=None,search_domains=[],**params):

        output_rows = []    
        total_count = self.get_count(model,search_domains=search_domains,**params)

        if total_count > 0:    
            
            logger.info('Found a total of {} items.'.format(total_count))        
            ex_iter = self.batch_fetch(model,search_domains=search_domains,batch_size=total_count,**params)

            for results in ex_iter:

                for row in results:
                    # logger.debug('raw item: {}'.format(row))
                    try:
                        # cleaning and formatting the item for the dataset
                        new_row = self.forge_item(row,model,**params)
                        # logger.debug("forged item : {}".format(new_row))
                        output_rows += new_row,

                    except Exception as ie:
                        logger.exception(traceback.format_exc())
                        continue
        
        return total_count,output_rows

    def batch_fetch(self,model,search_domains=[],start_row=0,batch_size=None,**params):

        while batch_size > 0:

            results = self.read_query(model,search_domains=search_domains,start_row=start_row,**params)

            how_many = len(results)
            logger.debug("caught {} items starting at row = {}".format(how_many,start_row))
            yield results
            
            start_row += how_many
            batch_size = batch_size - how_many
            print("{} more to go.".format(batch_size))


class DirectExtractor(GenericRPCExtractor):
    # child Interface bypassing the 'forge item' step
    def forge_item(self,item,model_name,**kwargs):
        return item