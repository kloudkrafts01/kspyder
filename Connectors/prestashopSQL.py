#!python3

import datetime,decimal

from common.sql_connector import GenericSQLConnector
from Engines.rpcExtractorEngine import GenericRPCExtractor
from common.config import PS_PROFILE, PAGE_SIZE, load_conf
from common.spLogging import logger

MODELS = load_conf('ps_models', subfolder='manifests')

MODELS_LIST = list(MODELS.keys())

# Load the Connector's config
CONF = load_conf('ps_models', subfolder='manifests')
CONNECTOR_CONF = CONF['Connector']
SCHEMA_NAME = CONNECTOR_CONF['schema']
UPD_FIELD_NAME = CONNECTOR_CONF['update_field']
UNPACKING = CONF['UnpackingFields']
MODELS = CONF['Models']

MODELS_LIST = list(MODELS.keys())
MODELS_TO_UPDATE = list(x for x in MODELS.keys() if MODELS[x]['update'])
CATALOGS = list(x for x in MODELS.keys() if MODELS[x]['update'] is False)

class prestashopSQLExtractor(GenericRPCExtractor,GenericSQLConnector):
        
    def __init__(self, profile=PS_PROFILE, schema=SCHEMA_NAME, models=MODELS, update_field=UPD_FIELD_NAME):

        presta_conn = GenericSQLConnector.from_profile(profile)
        self.client = presta_conn.engine.connect()

        self.schema = schema
        self.model = models
        self.update_field = update_field

    def get_count(self, model, search_domains=[]):

        countStr = 'SELECT COUNT(*)' + self.build_domain_query( model, search_domains=search_domains )
        logger.debug('Applying count query string: {}'.format(countStr))
        total_count = self.client.execute(countStr).fetchone()[0]

        return total_count

    def read_query(self,model,search_domains=[],start_row=None):

        queryStr = self.build_read_query( model, search_domains=search_domains, offset=start_row )
        logger.debug('Applying the following queryStr: {}'.format(queryStr))
        results = self.client.execute(queryStr).fetchall()

        return results

    def build_read_query(self, model, search_domains=[], offset=None, limit=PAGE_SIZE):

        # table_name = model['ps_table']
        fields = model['fields']

        # building the first part of the 'read' query
        queryStr = 'SELECT '
        for fieldname,value in fields.items():
            queryStr += "c.{}, ".format(fieldname)
        # remove the last trailing comma and space
        queryStr = queryStr[0:-2]

        queryStr += self.build_domain_query(model, search_domains=search_domains, offset=offset, limit=limit)

        return queryStr

    def build_domain_query(self, model, search_domains=[], offset=None, limit=None):

        table_name = model['ps_table']
        order_by = model['order_by']

        # determines if the model has a parent table. 
        # If yes, then the parent table is the one with the built-in 'date_upd' field that we need to get differential results
        has_parent = ('parent' in model.keys())

        # building the full name of the table that is to be queried : the table itself or the join with its parent table
        full_name = "{} as c".format(table_name)
        if has_parent:
            parent_table = model['parent']['table']
            key = model['parent']['key']
            full_name = "{} as p JOIN {} as c ON p.{}=c.{}".format(
                parent_table,
                table_name,
                key,
                key
            )
        domainStr = ' FROM {}'.format(full_name)

        count = 0
        if model in MODELS_TO_UPDATE:
            for domain in search_domains:
                domainStr += " {} {}.{} {} '{}'".format(
                    ('WHERE' if count==0 else 'AND'),
                    ('p' if has_parent else 'c'),
                    domain[0],
                    domain[1],
                    domain[2]
                )
                count += 1

        for key,value in order_by.items():
            domainStr += ' ORDER BY c.{} {}'.format(key,value)

        if limit:
            domainStr += ' LIMIT {}'.format(limit)

        if offset:
            domainStr += ' OFFSET {}'.format(offset)
        
        domainStr += ';'

        return domainStr

    def forge_item(self,row,model):

        output = {}
        count = 0    
        
        fields = model['fields']

        for in_fieldname,field in fields.items():

            out_fieldname = field['dbname']
            field_value = row[count]
            if isinstance(field_value, (datetime.date, datetime.datetime)):
                field_value = field_value.isoformat()
            elif isinstance(field_value, decimal.Decimal):
                field_value = float(field_value)
            output[out_fieldname] = field_value
            count += 1

        return output
