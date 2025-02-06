#!python

import sys
from importlib import import_module
import jmespath

from common.config import BASE_FILE_HANDLER as fh
from common.clientHandler import clientHandler
from common.loggingHandler import logger
from common.baseModels import Dataset

SCHEMA_NAME = 'pipelineEngine'

class pipelineEngine:

    def __init__(self,**params):

        self.ch = clientHandler()
        self.schema = SCHEMA_NAME

    def apply_filters(self,input_data=None,filters=None):

        filtered_data = input_data
        logger.debug("apply_filters :: INPUT DATA : {}".format(input_data))

        for filter_key, filter_value in filters.items():
            logger.debug("Applying filter : {} = {}".format(filter_key, filter_value))
            filtered_data = [x for x in filtered_data if x[filter_key] == filter_value]

        logger.debug("Filtered {} records.".format(len(filtered_data)))

        filtered_dataset = {
            'header': { 'operation': 'apply_filters' },
            'data': filtered_data
        }

        return filtered_dataset

    def set_static_data(self, data=None, index_keys=[], output=None, **params):

        params = {
            'operation': 'set_static_data'
        }
        model_name = output
        model = {
            'index_keys': index_keys
        }
        static_dataset = Dataset(SCHEMA_NAME,model_name,model,count=len(data),params=params)

        return static_dataset

    def get_unique_key_list(self,input_data=None,key=None,datapath=None):

        values_list = jmespath.search(datapath,input_data)
        if values_list:
            output_data = [{key: value} for value in values_list]
        else:
            output_data = []

        logger.debug("Extracted key-value list: {}".format(output_data))

        return output_data

    def get_data_to_mongo(self,from_worker=None,**params):
        """Shortcut method to get data from a connector and get the output to mongoDB directly
        This method assumes model_name = collection_name"""

        worker_module = self.ch.get_client(from_worker)
        dataset = worker_module.get_data(**params)

        mongoDBConnector = self.ch.get_client('mongoDBConnector')
        mongoDBConnector.upsert_dataset(dataset)

        return dataset

    def execute_pipeline_from_file(self,filename):

        pipeline_data = fh.load_yaml(filename, subpath='pipelines')
        self.execute_pipeline(pipeline_data)

    def execute_pipeline(self,pipeline):

        datasets = {}

        for step in pipeline['Steps']:
            
            # Mandatory Step definition fields
            step_name = step['Name']
            job_name = step['Job']
            step_output_name = step['Output']

            # prepare job input
            step_input_name = step['Input'] if 'Input' in step.keys() else None
            step_input = jmespath.search(step_input_name, datasets) if step_input_name else None
            step_params = step['Params'] if 'Params' in step.keys() else {}
            step_params.update({'output': step_output_name})
            if step_input:
                step_params.update({'input': step_input})
            
            # If no Worker name is given in the Step definition,
            # It is assumed that the job is one of pipelineEngine's own methods
            step_worker_name = step['Worker'] if 'Worker' in step.keys() else __name__
            worker_module = self.ch.get_client(step_worker_name) if 'Worker' in step.keys() else self
            job_instance = getattr(worker_module,job_name)
            logger.debug("Executing step {} : Worker = {}, Job = {}".format(step_name, worker_module.schema, job_name))
            logger.debug("Step Params: {}".format(step_params))

            dataset = job_instance(**step_params)

            # Store Output
            logger.debug("Inserting result set {} in the pile.".format(step_output_name))
            datasets[step_output_name] = dataset.to_json()
            logger.debug("Current datasets in the processing pile: {}".format(list(datasets.keys())))

            # If the step conf specifies the result needs to be dumped into csv or json, proceed.
            # Order is important : csv first, then json
            dump_json = step['DumpJSON'] if 'DumpJSON' in step.keys() else None
            dump_csv = step['DumpCSV'] if 'DumpCSV' in step.keys() else None
            results_count = dataset.count

            if results_count > 0:
                if dump_csv:
                    dataset = fh.dump_csv(dataset)

                if dump_json:
                    dataset = fh.dump_json(dataset)
            
            # "destroy" the dataset before next iteration
            logger.debug("Deleting job instance: {} - and dataset: {}".format(job_instance,dataset))
            del job_instance
            del dataset
            logger.debug("deletion done.")


if __name__ == "__main__":

    pipeline_name = sys.argv[1]
    engine = pipelineEngine()
    engine.execute_pipeline_from_file(pipeline_name)
