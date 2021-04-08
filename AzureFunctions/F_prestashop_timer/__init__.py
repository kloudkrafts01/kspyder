#!python3

import azure
import azure.durable_functions as df

from common.spLogging import logger


async def main(mytimer: azure.functions.TimerRequest, starter: str):
    
    try:
        orchestrator_name = "F_orchestrator"
        client = df.DurableOrchestrationClient(starter)

        req_params = {
            'trigger': 'scheduled',
            'source': 'prestashop',
            'last_days': '1',
            'model': None,
            'action': None
        }

        req_body = {
            'status': 'TODO'
        }

        orc_input = {
            'params': req_params,
            'body': req_body
        }

        instance_id = await client.start_new(orchestrator_name, None, req_params)

        logger.info(f"Started orchestration with ID = '{instance_id}'.")


    except Exception as e:

        logger.error("F_odoo_timer :: {}".format(e))
