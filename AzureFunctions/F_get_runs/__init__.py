#!python3
import json
import azure.functions as func
import azure.durable_functions as df

from common.spLogging import logger


async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    client = df.DurableOrchestrationClient(starter)

    instances = await client.get_status_all()

    for instance in instances:
        logger.info(json.dumps(instance))

    response = func.HttpResponse(
        body = json.dumps(instances),
        status_code = 200,
        mimetype = 'application/json'
    )

    return response