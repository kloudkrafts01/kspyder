#!python

import sys
from importlib import import_module
import jmespath

from common.config import BASE_FILE_HANDLER as fh
from common.clientHandler import clientHandler
from common.loggingHandler import logger

class documentPipelineEngine:

    def __init__(self,**params):

        self.schema = "documentPipelineEngine"
        self.ch = clientHandler()

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

    def set_static_data(self, data=None):

        static_dataset = {
            'header': { 'operation': 'set_static_data' },
            'data': data
        }

        return static_dataset

    def get_unique_key_list(self,input_data=None,key=None,datapath=None):

        values_list = jmespath.search(datapath,input_data)
        if values_list:
            output_data = [{key: value} for value in values_list]
        else:
            output_data = []

        logger.debug("Extracted key-value list: {}".format(output_data))

        return output_data

    def get_data_to_mongo(self,input_data=[{}],from_worker=None,**params):
        """Shortcut method to get data from a connector and get the output to mongoDB directly
        This method assumes model_name = collection_name"""

        worker_module = self.ch.get_client(from_worker)
        full_dataset = worker_module.get_data(input_data=input_data,**params)

        mongo_module = self.ch.get_client('mongoDBConnector')
        insertion_result = mongo_module.upsert_dataset(input_data=full_dataset)

        return full_dataset

    def execute_pipeline_from_file(self,filename,input=[]):

        pipeline_data = fh.load_yaml(filename, subpath='orchestrator')
        self.execute_pipeline(pipeline_data,input=input)

    def execute_pipeline(self,pipeline,input=[]):

        # ch = clientHandler()
        datasets = {}

        for step in pipeline['Steps']:

            # Mandatory Step definition fields
            step_name = step['Name']
            job_name = step['Job']

            # prepare job input
            step_input_name = step['Input'] if 'Input' in step.keys() else None
            step_input = jmespath.search(step_input_name, datasets) if step_input_name else None
            # logger.debug("Step Input: {}".format(step_input))
            step_params = step['Params'] if 'Params' in step.keys() else {}
            
            # If no Worker name is given in the Step definition,
            # It is assumed that the job is one of documentPipelineEngine's own methods
            step_worker_name = step['Worker'] if 'Worker' in step.keys() else __name__
            worker_module = self.ch.get_client(step_worker_name) if 'Worker' in step.keys() else self
            job_instance = getattr(worker_module,job_name)
            logger.debug("Executing step {} : Worker = {}, Job = {}".format(step_name, worker_module.schema, job_name))

            if step_input:
                result = job_instance(input_data=step_input,**step_params)
            else:
                result = job_instance(**step_params)

            # Store Output
            step_output_name = step['Output'] if 'Output' in step.keys() else step_name
            logger.debug("Inserting result set {} in the pile.".format(step_output_name))
            datasets[step_output_name] = result
            logger.debug("Current datasets in the processing pile: {}".format(list(datasets.keys())))

            # If the step conf specifies the result needs to be dumped into csv or json, proceed.
            # Order is important : csv first, then json
            dump_json = step['DumpJSON'] if 'DumpJSON' in step.keys() else None
            dump_csv = step['DumpCSV'] if 'DumpCSV' in step.keys() else None
            results_count = result['header']['count']

            if results_count > 0:
                if dump_csv:
                    result_dataset = fh.dump_csv(result,step['Worker'],step_output_name)

                if dump_json:
                    result_dataset = fh.dump_json(result,step['Worker'],step_output_name)


if __name__ == "__main__":

    pipeline_name = sys.argv[1]
    # input_filename = sys.argv[2]

    # input_data = fh.load_json(input_filename,input=TEMP_FOLDER)['data']

    engine = documentPipelineEngine()
    engine.execute_pipeline_from_file(pipeline_name)

    # client = gRM.FoldersGraphClient(scope='christiandior.com',org_id = "organizations/68618737410")
    # folders_graph = client.get_all_folders()

    # full_dataset = {
    #     'header':{
    #         folders_graph['graph_metadata']
    #     },
    #     'data': folders_graph['data']
    # }

    # # if DUMP_JSON:
    # fh.dump_json(dataset = folders_graph, schema="gcloudRMConnector", name='GCloudFolders')
