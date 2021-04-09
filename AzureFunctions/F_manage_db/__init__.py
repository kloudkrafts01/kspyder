# This function is not intended to be invoked directly. Instead it will be
# triggered by an HTTP starter function.
# Before running this sample, please:
# - create a Durable activity function (default name is "Hello")
# - create a Durable HTTP starter function
# - add azure-functions-durable to requirements.txt
# - run pip install -r requirements.txt

import azure.functions as func
import azure.durable_functions as df

from common.spLogging import logger

def orchestrator_function(context: df.DurableOrchestrationContext):
    
    orc_input = context.get_input()
    logger.info("Orchestration Input : {}".format(orc_input))
    action = orc_input['action']

    if action == 'apply':
        # first, run an examine action and get the change plan
        examine_input = orc_input
        examine_input['action'] = 'examine'
        result1 = yield context.call_activity('db_activity', examine_input)
        
        # then apply changes with the change plan as input body
        apply_input = orc_input
        apply_input['body'] = result1['results']
        result = yield context.call_activity('db_activity', apply_input)

    else:
        result = yield context.call_activity('db_activity', orc_input)
    
    return result

main = df.Orchestrator.create(orchestrator_function)