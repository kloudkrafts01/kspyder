#!python3
import json
import azure.functions as func
import azure.durable_functions as df

from common.spLogging import logger


async def main(req: func.HttpRequest, starter: str) -> None:
    client = df.DurableOrchestrationClient(starter)

    instances = await client.get_status_all()
    instances_list = []

    # response = None

    try: 
        for instance in instances:
            # instances_list += instance.to_json(),
            logger.info(json.dumps(instance))
        # resp_body = json.dumps(instances_list)

        # response = func.HttpResponse(
        #     body = resp_body,
        #     status_code = 200,
        #     mimetype = 'application/json'
        # )

    except Exception as e:
        
        logger.error("F_get_runs :: {}".format(e))

    # return response