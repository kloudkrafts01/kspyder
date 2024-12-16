#!python

import sys,re
from importlib import import_module

from common.config import TEMP_FOLDER,DUMP_JSON,BASE_FILE_HANDLER as fh
from common.clientHandler import clientHandler
from common.spLogging import logger


EACH_PATTERN = re.compile("(\$each)\.(.+)")

def execute_pipeline_from_file(filename,input=[]):

    pipeline_data = fh.load_yaml(filename, subpath='orchestrator')
    execute_pipeline(pipeline_data,input=input)

def execute_pipeline(pipeline,input=[]):

    ch = clientHandler()
    datasets = {}

    for step in pipeline['Steps']:

        step_name = step['Name']
        worker_name = step['Worker']
        job_name = step['Job']
        logger.debug("Preparing step {} : Worker = {}, Job = {}".format(step_name, worker_name, job_name))

        worker_module = ch.get_client(worker_name)
        job_instance = getattr(worker_module,job_name)
        
        # prepare job input
        step_input_name = step['Input'] if 'Input' in step.keys() else None
        step_input = datasets[step_input_name] if step_input_name else None
        # logger.debug("Step Input: {}".format(step_input))
        step_params = step['Params'] if 'Params' in step.keys() else {}
        
        if step_input:
            result = job_instance(step_input,**step_params)
        else:
            result = job_instance(**step_params)

        step_output_name = step['Output'] if 'Output' in step.keys() else step_name
        logger.debug("Inserting result set {} in the pile.".format(step_output_name))
        logger.debug("Current datasets in the processing pile: {}".format(list(datasets.keys())))
        datasets[step_output_name] = result


        # for input_item in input :
        
        #     logger.debug("INPUT ITEM: {}".format(input_item))
        #     # Unfold input parameters for the job execution
        #     params = {}
        #     for key, value in step_params.items():
        #         match = re.match(EACH_PATTERN,value)
        #         if match:
        #             new_key = match.group(2)
        #             logger.debug("matched the $each pattern: {}\nReplacing with: {}".format(value, new_key))
        #             # If a Step param has the '$each' key prefix, replace it for every input item
        #             params[key] = input_item[new_key]
        #         else:
        #             logger.debug("Did not match the $each pattern: {}".format(value))
        #             # Else just pass the param as specified in the Step definition
        #             params[key] = value

        #     # Execute the job instance
        #     logger.debug("orchestrator :: launching job {} from Worker module {}".format(job_name,worker_name))
        #     logger.debug("orchestrator :: job params : {}".format(params))
        #     jsonpath, dataset = job_instance(**params)

            # if DUMP_JSON:
            #     fh.dump_json(dataset,worker_name,jsonpath)




if __name__ == "__main__":

    pipeline_name = sys.argv[1]
    # input_filename = sys.argv[2]

    # input_data = fh.load_json(input_filename,input=TEMP_FOLDER)['data']

    execute_pipeline_from_file(pipeline_name)