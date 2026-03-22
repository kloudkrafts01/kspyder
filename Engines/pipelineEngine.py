#!python

import sys
from importlib import import_module
import jmespath

from common.config import BASE_FILE_HANDLER as fh
from common.clientHandler import clientHandler
from common.loggingHandler import logger
from common.configModels import PipelineConfig
from common.protocols import DocumentStore, Extractor

class pipelineEngine:

    def __init__(self,**params):

        self.ch = clientHandler()
        self.schema = __name__

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
            'header': { 
                'operation': 'set_static_data',
                'count': len(data)
            },
            'data': data
        }

        logger.debug(f"Static data: {static_dataset}")

        return static_dataset

    def get_unique_key_list(self,input_data=None,key=None,datapath=None):

        values_list = jmespath.search(datapath,input_data)
        if values_list:
            output_data = [{key: value} for value in values_list]
        else:
            output_data = []

        # logger.debug("Extracted key-value list: {}".format(output_data))

        full_output_data ={
            'header': {
                'count': len(output_data)
            },
            'data': output_data
        }

        return full_output_data

    def get_data_to_mongo(self, input_data=[{}], from_worker=None, **params):
        """Shortcut method to get data from a connector and get the output to mongoDB directly.
        This method assumes model_name = collection_name."""

        worker_module: Extractor = self.ch.get_client(from_worker)
        full_dataset = worker_module.get_data(input_data=input_data, **params)

        mongo_module: DocumentStore = self.ch.get_client('mongoDB')
        mongo_module.upsert_dataset(input_data=full_dataset)

        return full_dataset

    def execute_pipeline_from_file(self, filename):

        pipeline_data = fh.load_yaml(filename, subpath='pipelines')
        pipeline = PipelineConfig(**pipeline_data)
        self.execute_pipeline(pipeline)

    def execute_pipeline(self, pipeline: PipelineConfig):

        datasets = {}

        for step in pipeline.Steps:

            step_input = jmespath.search(step.Input, datasets) if step.Input else None

            worker_module = self.ch.get_client(step.Worker) if step.Worker else self
            job_instance = getattr(worker_module, step.Job)
            logger.info("Executing step {} : Worker = {}, Job = {}".format(step.Name, worker_module.schema, step.Job))

            if step_input:
                result = job_instance(input_data=step_input, **step.Params)
            else:
                result = job_instance(**step.Params)

            step_output_name = step.Output or step.Name
            logger.info("Inserting result set {} in the pile.".format(step_output_name))
            datasets[step_output_name] = result
            logger.info("Current datasets in the processing pile: {}".format(list(datasets.keys())))

            # If the step conf specifies the result needs to be dumped into csv or json, proceed.
            # Order is important : csv first, then json
            results_count = result['header']['count']

            if results_count > 0:
                if step.DumpCSV:
                    result_dataset = fh.dump_csv(result, step.Worker, step_output_name)

                if step.DumpJSON:
                    result_dataset = fh.dump_json(result, step.Worker, step_output_name)


if __name__ == "__main__":

    pipeline_name = sys.argv[1]
    # input_filename = sys.argv[2]

    # input_data = fh.load_json(input_filename,input=TEMP_FOLDER)['data']

    engine = pipelineEngine()
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
