import datetime
import traceback

from .utils import json_dump
from .config import DEFAULT_TIMESPAN, DUMP_JSON
from .spLogging import logger

def get_data(connector,model_name,last_days=DEFAULT_TIMESPAN):

    sd = []
    if last_days:
        today = datetime.datetime.utcnow()
        delta = datetime.timedelta(days=last_days)
        yesterday = today - delta

        logger.info("UTC start datetime is {}".format(yesterday))
        sd += [connector.UPD_FIELD_NAME,'>=',yesterday],

    dataset = fetch_dataset(connector,model_name,search_domains=sd)

    if dataset == []:
        logger.info('no results were found.')

    full_dataset = {
        'header': {
            'schema': connector.SCHEMA_NAME,
            'model': model_name
        },
        'data': dataset
    }

    jsonpath = None
    if DUMP_JSON:
        jsonpath = json_dump(full_dataset,connector.SCHEMA_NAME,model_name)

    return jsonpath,full_dataset

def fetch_dataset(connector,model_name,search_domains=[]):

    output_rows = []    
    client, model = connector.get_client(model_name)
    total_count = connector.get_count(client,model,search_domains)

    if total_count > 0:    
        
        logger.info('Found a total of {} items.'.format(total_count))        
        ex_iter = batch_fetch(connector,client,model,search_domains=search_domains,batch_size=total_count)

        for results in ex_iter:

            for row in results:
                logger.debug('raw item: {}'.format(row))
                try:
                    # cleaning and formatting the item for the dataset
                    new_row = connector.forge_item(row,model)
                    logger.debug("forged item : {}".format(new_row))
                    output_rows += new_row,

                except Exception as ie:
                    logger.error(traceback.format_exc())
                    continue
    
    return output_rows

def batch_fetch(connector,client,model,search_domains=[],start_row=0,batch_size=None):

    while batch_size > 0:

        results = connector.read_query(client,model,search_domains=search_domains,start_row=start_row)

        how_many = len(results)
        logger.debug("caught {} items starting at row = {}".format(how_many,start_row))
        yield results
        
        start_row += how_many
        batch_size = batch_size - how_many
        print("{} more to go.".format(batch_size))
