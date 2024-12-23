#!python

import sys
from importlib import import_module
import jmespath

from common.config import BASE_FILE_HANDLER as fh
from common.clientHandler import clientHandler
from common.spLogging import logger

from Connectors import gcloudResourceManagerConnector as gRM
# from gcloudResourceManagerConnector import gcloudResourceClient

class documentPipelineEngine:

    def __init__(self,**params):

        self.schema = "documentPipelineEngine"

    def get_unique_key_list(self,input_data=None,key=None,datapath=None,filters=None):

        values_list = jmespath.search(datapath,input_data)
        output_data = [{key: value} for value in values_list]

        if filters:
            for filter_key, filter_value in filters.items():
                output_data = [x for x in output_data if x[filter_key] == filter_value]

        logger.debug("Extracted key-value list: {}".format(output_data))

        return output_data

    def execute_pipeline_from_file(self,filename,input=[]):

        pipeline_data = fh.load_yaml(filename, subpath='orchestrator')
        self.execute_pipeline(pipeline_data,input=input)

    def execute_pipeline(self,pipeline,input=[]):

        ch = clientHandler()
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
            worker_module = ch.get_client(step['Worker']) if 'Worker' in step.keys() else self
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
