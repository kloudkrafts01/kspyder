import datetime
import traceback

# from .utils import dump_json
from .config import DEFAULT_TIMESPAN, DUMP_JSON, BASE_FILE_HANDLER as fh
from .spLogging import logger

class GenericExtractor():

    def __init__(self,**kwargs):
        self.client = "This is an empty client from the GenericExtractor interface. Please instantiate an actual Class over it"
        self.schema = "Empty schema from the GenericExtractor interface"
        self.scope = "Empty scope from the GenericExtractor interface"
        self.models = [{"default": "Empty schema from the GenericExtractor interface"}]

    def get_count(self,model_name):
        ValueError("This method was called from the GenericExtractor interface. Please instantiate an actual Class over it")

    def read_query(self,model_name):
        ValueError("This method was called from the GenericExtractor interface. Please instantiate an actual Class over it")

    def forge_item(self,item,model_name):
        ValueError("This method was called from the GenericExtractor interface. Please instantiate an actual Class over it")

    def get_data(self,model_name,last_days=DEFAULT_TIMESPAN,**params):

        logger.debug("Extractor object: {}".format(self.__dict__))

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


class DirectExtractor(GenericExtractor):
    # child Interface bypassing the 'forge item' step
    def forge_item(self,item,model_name):
        return item