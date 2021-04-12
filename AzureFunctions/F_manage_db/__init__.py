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

    result = yield context.call_activity('db_activity', orc_input)
    
    return result

main = df.Orchestrator.create(orchestrator_function)