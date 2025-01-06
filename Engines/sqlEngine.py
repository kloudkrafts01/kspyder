# import pyodbc
import re
import urllib
from importlib import import_module

import sqlalchemy
from sqlalchemy import Column, String
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker


# automap_base is an extension of the sqlAlchemy declarative_base, 
# the main advantage being, it can load tables from the db and directly translate them in to ORM classes.
# for documentation on this : refer to https://docs.sqlalchemy.org/en/14/orm/extensions/automap.html
AutoBase = automap_base()

from common.loggingHandler import logger
from common.config import DUMP_JSON, BASE_FILE_HANDLER as fh

STR_PATTERN = re.compile('(String)\((\d+)\)')

class GenericSQLEngine():

    def __init__(self,dbtype,url,dbname,username,password):

        self.type = dbtype
        self.url = url
        self.dbname = dbname
        __username = username
        __password = password

        self.protocol = None
        self.port = None
        self.dbconn = None

        conn_url = None

        if self.type == 'mysql':
            self.protocol = 'mysql+pymysql'
            self.port = '3306'

            conn_url = '{protocol}://{user}:{pw}@{url}:{port}/{db}'\
                .format(protocol = self.protocol,
                    user = __username,
                    pw = __password,
                    url = self.url,
                    port = self.port,
                    db = self.dbname
                )

        if self.type == 'mssql':
            self.protocol = 'mssql+pyodbc'
            self.port = '1433'
            __driver= '{ODBC Driver 17 for SQL Server}'
            __cstring = 'DRIVER={};SERVER={};PORT={};DATABASE={};UID={};PWD={}'.format(
                __driver,
                self.url,
                self.port,
                self.dbname,
                __username,
                __password
            )
        
            # self.dbconn = pyodbc.connect(__cstring)
            __cstring_safe = urllib.parse.quote_plus(__cstring)
            conn_url = "{}:///?odbc_connect={}".format(self.protocol,__cstring_safe)

        # else:
        #     raise Exception

        self.engine = sqlalchemy.create_engine(conn_url)
        self.SessionFactory = sessionmaker(bind=self.engine)
              
    @classmethod
    def from_profile(cls,profile):
        
        return cls(
            profile['dbtype'],
            profile['url'],
            profile['dbname'],
            profile['username'],
            profile['password']
        )
    
    def update_from_json(self,dataset):

        header = dataset['header']
        schema = header['schema']
        model_name = header['model']

        result = None

        logger.info("Loading DB schema: {}".format(schema))
        # for documentation on this : refer to https://docs.sqlalchemy.org/en/14/orm/extensions/automap.html
        AutoBase = automap_base()
        AutoBase.prepare(engine=self.engine, schema=schema, reflect=True)
        logger.debug("loading modelObject")
        modelObject = getattr(AutoBase.classes,model_name)

        logger.debug("Opening Session")
        session = self.SessionFactory()
        # This is very important, so the data is inserted in the right schema
        session.connection(execution_options={
            "schema_translate_map": {schema : schema}
        })

        logger.info("Saving JSON file to {}".format(self.dbname))
        logger.debug("JSON Header: {}".format(header))
    
        try:
            for dict_item in dataset['data']:

                id = dict_item['Id']
                objectInstance = session.query(modelObject).filter(modelObject.Id == id).first()
                
                # if object not found in the db, create it
                if objectInstance is None:
                    logger.debug("Object {} with ID={} not found in DB. Creating.".format(model_name,id))
                    objectInstance = modelObject(**dict_item)
                    session.add(objectInstance)
                
                # if already present, update all its fields
                else:
                    logger.debug("Object {} with ID={} found in DB. Updating.".format(model_name,id))
                    id = dict_item.pop('Id')
                    for key,value in dict_item.items():
                        setattr(objectInstance,key,value)

                logger.debug("inserted record {}".format(dict_item.values()))
            
            logger.info("Committing...")
            session.commit()
            result = 'committed'
            
        except Exception as e:
            logger.error("SQL connector update_from_json: {}".format(e))
            session.rollback()
            result = 'rolled back'

        finally:
            session.close()
        
        return result

    def compare_schema(self,schema):
        """Loads all table definitions from the db schema, and compares it with the connector's model definitions taken from the connector's YAML manifest.
        Returns several sets of strings:

        - new_models: Model names that were given in the connector's manifest but not found in the database
        - deleted_models: Model names that were found in the database, but absent from the connector's current manifest
        - intersect_models: Model names that were found both in the database and in the connector's manifest
        - model_changes: dict object reflecting if some intersecting models were changed i.e.,
            if fields were added or deleted from the manifest, compared to the current database state)
            - new_fields: list of field names that were found in the model manifest but not in the corresponding database table
            - deleted_fields: list of field names present in the db table but absent from the model manifest
        """

        connector = import_module(schema)
        logger.info("Comparing DB schema {} with connector models: {}".format(schema,connector.__name__))
        # for documentation on this : refer to https://docs.sqlalchemy.org/en/14/orm/extensions/automap.html
        # AutoBase = automap_base()
        AutoBase.prepare(engine=self.engine, schema=schema, reflect=True)

        table_names = set(x.__table__.name for x in AutoBase.classes)
        model_names = set(connector.MODELS_LIST)

        new_models = model_names - table_names
        deleted_models = table_names - model_names
        intersect_models = table_names & model_names
        changed_models = set()

        logger.info("NEW models: {}".format(new_models))
        logger.info("DELETED models: {}".format(deleted_models))
        logger.info("Intersecting models: {}".format(intersect_models))

        model_changes = {}

        for model_name in intersect_models:

            # logger.debug("Comparing Model: {}".format(model_name))
            model = connector.MODELS[model_name]
            table_obj = getattr(AutoBase.classes,model_name)

            table_fields = set(x.name for x in table_obj.__table__.columns)
            table_field_objects = set(x for x in table_obj.__table__.columns)
            table_field_dict = {}
            for field in table_field_objects:
                table_field_dict[field.name] = {
                    'dbname'
                }

            model_fields = get_all_model_fields(connector,model_name)

            new_fields = model_fields - table_fields
            deleted_fields = table_fields - model_fields
            intersect_fields = table_fields & model_fields

            has_changed = len(new_fields)>0 or len(deleted_fields)>0
            if has_changed:
                changed_models.add(model_name)

            # logger.debug("HAS CHANGED: {}".format(has_changed))
            # logger.debug("NEW Fields: {}".format(new_fields))
            # logger.debug("DELETED Fields: {}".format(deleted_fields))
            # logger.debug("MATCHING Fields: {}".format(intersect_fields))

            model_changes[model_name] = {
                'has_changed': has_changed,
                'new_fields': list(new_fields),
                'deleted_fields': list(deleted_fields),
                'intersect_fields': list(intersect_fields)
            }

        logger.info("Models Comparison: {}".format(model_changes))

        return new_models, deleted_models, intersect_models, changed_models, model_changes

    def plan_changes(self,schema,create_new=True,delete_old=False,alter_changed=True):
        """Establishes a comparison between the current connector's manifest and the current db schema state,
        and produces a 'change plan' JSON file"""

        new, old, matching, changed, changes = self.compare_schema(schema)

        # Determine all models that need to be dropped from the schema
        to_delete = None
        if delete_old and alter_changed:
            to_delete = {*old, *changed}
        elif delete_old and not alter_changed:
            to_delete = old
        elif alter_changed and not delete_old:
            to_delete = changed
        else:
            to_delete = set()

        # Determine all models that need to be created, or re-created after deletion
        to_create = None
        if create_new and alter_changed:
            to_create = {*new, *changed}
        elif create_new and not alter_changed:
            to_create = new
        elif alter_changed and not create_new:
            to_create = changed
        else:
            to_create = set()

        # If relevant, add the detailed changes that need to occur on modified models
        changes_detail = {}
        for key,value in changes.items():
            if value['has_changed']:
                changes_detail[key] = value

        plan = {
            "schema": schema, 
            "delete": list(to_delete), 
            "create": list(to_create),
            "changes_detail": changes_detail
        }

        logger.debug("CHANGE PLAN FOR SCHEMA {}: {}".format(schema, plan))

        if DUMP_JSON:
            fh.dump_json(plan, schema, 'DB_CHANGE_PLAN')

        return plan

    def apply_changes(self,plan):
        """Applies the changes specified in a given 'plan' JSON file. This approach is pretty much inspired by Terraform, but applied to SQLAlchemy db models :)"""

        returnmsg = ""
        result = {}

        schema = plan['schema']
        to_delete = plan['delete']
        to_create = plan['create']

        deletion = len(to_delete)>0
        creation = len(to_create)>0

        if deletion or creation:
            logger.info("DB CHANGE: Applying change plan: {}".format(plan))
            
            try:
                
                # for documentation on this : refer to https://docs.sqlalchemy.org/en/14/orm/extensions/automap.html
                AutoBase.prepare(engine=self.engine, schema=schema, reflect=True)

                # if tables need to be dropped, use SQLAlchemy to drop them
                if deletion:
                    # delete_tables = list(x.__table__ for x in AutoBase.classes if x.__table__.name in to_delete)
                    self.delete_tables(schema, to_delete)
                    AutoBase.metadata.clear()

                # if tables need to be (re)-created, create them from the connector's manifest definition
                if creation:
                    self.create_models(schema,to_create)
                    AutoBase.metadata.clear()
                
                returnmsg = "Successfully applied changes to the DB."
                logger.info(returnmsg)

                result['status'] = 'success'

            except Exception as e:
                returnmsg = "DB CHANGE: Error {}".format(e)
                logger.error(returnmsg)
                result['status'] = 'error'

        else:
            returnmsg = "DB CHANGE: Nothing to change in the current plan. No action will be applied on the db."
            logger.info(returnmsg)
            result['status'] = 'not applied'

        result['message'] = returnmsg
        result['plan'] = plan
        return result

    def delete_tables(self,schema,to_delete):

        AutoBase.prepare(engine=self.engine, schema=schema, reflect=True)
        tables_list = list(x.__table__ for x in AutoBase.classes if x.__table__.name in to_delete)
        
        logger.info("DROPPING tables from schema {}: {}".format(schema,to_delete))
        
        AutoBase.metadata.drop_all(bind=self.engine,tables=tables_list)
        logger.info("Successfully dropped tables : {}".format(to_delete))

        result = {
            'schema': schema,
            'deleted': to_delete
        }

        return result
        
    def delete_db(self,schemas=[]):
        """ Drops all tables from the database within the specified schema. If no schema is specified, drops everything"""

        delete_tables = []

        # drops all tables at the SQL database level
        for schema in schemas:
            connector = import_module(schema)
            to_delete = connector.MODELS_LIST
            deleted = self.delete_tables(schema,to_delete)
            delete_tables.append(deleted)
        
        # clears up the intermediary MetaData definition python objects
        AutoBase.metadata.clear()

        result = {
            'delete_list': schemas,
            'deleted': '{}'.format(delete_tables)
        }

        return result

    def create_db(self,schemas=[]):
        """Creates all Table Metadata and db tables corresponding to the given connectors' models definitions"""

        for schema in schemas:
            self.create_models(schema)

        AutoBase.metadata.create_all(self.engine)
        tables_list = list(x.name for x in AutoBase.metadata.sorted_tables)
        logger.info("Successfully created database. Models: {}".format(tables_list))

        result = {
            'schemas': schemas,
            'created': tables_list
        }

        return result

    def create_models(self, schema, models_list=None):
        """Creates Tabls Metadata and db tables corresponding to the given connectors' models definitions"""

        connector = import_module(schema)

        if models_list is None:
            models_list = connector.MODELS_LIST

        logger.info("Creating MetadataClasses in schema {} from models: {}".format(schema, models_list))

        for model_name in models_list:
            ORMclass = create_ORM_class(schema, model_name, connector.MODELS[model_name], connector.UNPACKING)

        AutoBase.metadata.create_all(bind=self.engine)
        

def create_ORM_class(schema,model_name,model,unpack={}):
    """Constructs an sqlAlchemy ORM class definition on a declarative Base,
    that corresponds to a given model definition""" 

    logger.debug("START CREATION of ORM class {}. Schema: {}".format(model_name,schema))

    construct = {
        '__tablename__': model_name,
        '__table_args__': {'schema': schema}
    }

    for field_name,field in model['fields'].items():
        
        field_construct = construct_field(field_name,field,unpack)
        construct.update(field_construct)
    
    # logger.debug("SQLAlchemy Construct: {}".format(construct))

    ORMClass = type(model_name, (AutoBase,), construct)

    return ORMClass

def construct_field(field_name,field,unpack):
    """Builds a dict-like object that represents the field, and can be passed to the SQLAlchemy constructor"""

    field_construct = {}
    
    dbname = field['dbname']
    fieldtype_raw = field['type']
    fieldtype = translate_orm_type(fieldtype_raw)
    
    if ('primary_key' in field.keys()) and field['primary_key']:
        field_construct[dbname] = Column(fieldtype, primary_key=True, autoincrement=False)
    else:
        field_construct[dbname] = Column(fieldtype)

    # IF the field has to be 'unpacked', secondary fields may be added to the construct
    if (field_name in unpack) and (unpack[field_name] is not None):
        
        unpacked_fieldname = unpack[field_name]['dbname']
        unpacked_fieldtype_raw = unpack[field_name]['type']
        unpacked_fieldtype = translate_orm_type(unpacked_fieldtype_raw)

        field_construct[unpacked_fieldname] = Column(unpacked_fieldtype)

    return field_construct

def translate_orm_type(fieldtype_raw):
    """function to translate a 'raw' string into a valid sqlalchemy Data Type"""

    fieldtype = None
    match = re.search(STR_PATTERN,fieldtype_raw)
    if match:
        # define Cloumn as a String object with the desired max length
        fieldtype = String(match[2])
    else:
        fieldtype = getattr(sqlalchemy,fieldtype_raw)

    return fieldtype

def get_all_model_fields(connector,model_name):
    """Utility function to get the full list of field names from a model, 
    INCLUDING field names that are eventually derived fro mthe connector's UNPACKING list in the manifest."""

    model = connector.MODELS[model_name]
    unpacking = connector.UNPACKING

    base_model_fields = set(x['dbname'] for x in model['fields'].values())
    full_model_fields = base_model_fields
    
    # get teh list of fields that are in the model and potentially unpacked
    unpackable_fields = set(x for x in unpacking.keys() if x in model['fields'].keys())

    for fieldname in unpackable_fields:
        unpack = unpacking[fieldname]
        # if the field actually is unpacked into another field
        if unpack:
            full_model_fields.add(unpack['dbname'])

    return full_model_fields
