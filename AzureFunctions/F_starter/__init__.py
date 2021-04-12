# This function an HTTP starter function for Durable Functions.
# Before running this sample, please:
# - create a Durable orchestration function
# - create a Durable activity function (default name is "Hello")
# - add azure-functions-durable to requirements.txt
# - run pip install -r requirements.txt

import json
import azure.functions as func
import azure.durable_functions as df

from common.spLogging import logger

async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    
    try:
        client = df.DurableOrchestrationClient(starter)

        logger.info("request parameters: {}".format(req.params))

        expected_params = [
            'last_days',
            'source',
            'model',
            'action'
        ]

        # req_params = dict(req.params)
        params = {}
        # req_body = req.get_body()
        req_body = {
            'status': 'TODO'
        }

        for key in expected_params:
            params[key] = (req.params[key] if key in req.params.keys() else None)
        
        params['trigger'] = 'http'
        models_raw = params['model']
        params['model'] = (models_raw.split(',') if models_raw else None)

        orc_input = {
            'params': params,
            'body': req_body
        }

        instance_id = await client.start_new(req.route_params["functionName"], None, params)

        logger.info(f"Started orchestration with ID = '{instance_id}'.")

        return client.create_check_status_response(req, instance_id)

    except Exception as e:

        logger.error("F_starter :: {}".format(e))