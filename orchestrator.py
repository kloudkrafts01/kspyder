#!python

import sys
from importlib import import_module
import jmespath

from common.config import BASE_FILE_HANDLER as fh
from common.clientHandler import clientHandler
from common.spLogging import logger

def extract_key_list(dataset,key=None,datapath=None):

    values_list = jmespath.search(datapath,dataset)
    output_data = [{key: value} for value in values_list]

    logger.debug("Extracted key-value list: {}".format(output_data))

    return output_data

def execute_pipeline_from_file(filename,input=[]):

    pipeline_data = fh.load_yaml(filename, subpath='orchestrator')
    execute_pipeline(pipeline_data,input=input)

def execute_pipeline(pipeline,input=[]):

    ch = clientHandler()
    datasets = {}


    for step in pipeline['Steps']:

        step_name = step['Name']

        # prepare job input
        step_input_name = step['Input'] if 'Input' in step.keys() else None
        step_input = jmespath.search(step_input_name, datasets) if step_input_name else None
        # logger.debug("Step Input: {}".format(step_input))
        step_params = step['Params'] if 'Params' in step.keys() else {}

        if step_name == '$GetUniqueKeyList':
            
            logger.debug("Executing special job : get Key list")
            result = extract_key_list(step_input,**step_params)
        
        else:
            worker_name = step['Worker']
            job_name = step['Job']
            logger.debug("Preparing step {} : Worker = {}, Job = {}".format(step_name, worker_name, job_name))

            worker_module = ch.get_client(worker_name)
            job_instance = getattr(worker_module,job_name)
            
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

    execute_pipeline_from_file(pipeline_name)