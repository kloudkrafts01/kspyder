import datetime
import traceback
from typing import Any, Iterator

from common.config import DEFAULT_TIMESPAN, DUMP_JSON, BASE_FILE_HANDLER as fh
from common.loggingHandler import logger
from common.models import Dataset, DatasetHeader, DataPage, PageCursor

class GenericRPCExtractor():

    def __init__(self, **kwargs: Any) -> None:
        self.client = "This is an empty client from the GenericRPCExtractor interface. Please instantiate an actual Class over it"
        self.schema = "Empty schema from the GenericRPCExtractor interface"
        self.scopes = "Empty scope from the GenericRPCExtractor interface"
        self.update_field = "Empty update_field from the GenericRPCExtractor interface"
        self.models = [{"default": "Empty schema from the GenericRPCExtractor interface"}]

    def get_count(self, **kwargs: Any) -> int:
        raise NotImplementedError("This method was called from the GenericRPCExtractor interface. Please instantiate an actual Class over it")

    def read_query(self, **kwargs: Any) -> list:
        raise NotImplementedError("This method was called from the GenericRPCExtractor interface. Please instantiate an actual Class over it")

    def forge_item(self, item: Any, model_name: Any, **kwargs: Any) -> dict:
        raise NotImplementedError("This method was called from the GenericRPCExtractor interface. Please instantiate an actual Class over it")

    def get_data(self, model_name: str | None = None, last_days: int | None = DEFAULT_TIMESPAN, search_domains: list = [], input_data: list[dict] = [{}], **params: Any) -> Dataset:

        logger.debug("Extractor object: {}".format(self.__dict__))

        if last_days:
            now = datetime.datetime.now(datetime.timezone.utc)
            delta = datetime.timedelta(days=last_days)
            yesterday = now - delta
            logger.info("UTC start datetime is {}".format(yesterday))
            search_domains += [self.update_field, '>=', yesterday],

        model = self.models[model_name]
        scopes = self.scopes if isinstance(self.scopes, list) else None

        dataset = Dataset(
            header=DatasetHeader(
                source_schema=self.schema,
                model_name=model_name,
                model=model,
                scopes=scopes,
                params=params,
            )
        )

        for input_item in input_data:
            logger.debug("Input item: {}".format(input_item))
            try:
                self.fetch_dataset(dataset, input_item, model, search_domains=search_domains, **params)
            except Exception as e:
                logger.exception(e)
                dataset.failed_items.append({'item': input_item})
                continue

        if not dataset:
            logger.info('no results were found.')
        else:
            if DUMP_JSON:
                fh.dump_json(dataset.to_json(), self.schema, model_name)

        return dataset

    def fetch_dataset(self, dataset: Dataset, input_item: dict, model: Any, search_domains: list = [], **params: Any) -> None:

        merged_params = input_item | params
        logger.debug("Using this as input params for this round: {}".format(merged_params))

        total_count = self.get_count(model, search_domains=search_domains, **merged_params)
        if total_count == 0:
            return

        logger.info('Found a total of {} items.'.format(total_count))
        ex_iter = self.batch_fetch(model, search_domains=search_domains, batch_size=total_count, **merged_params)

        accumulated = 0
        for page_num, results in enumerate(ex_iter):
            forged_rows = []
            for row in results:
                try:
                    forged_rows.append(self.forge_item(row, model, **merged_params))
                except Exception:
                    logger.exception(traceback.format_exc())
                    continue

            accumulated += len(forged_rows)
            if forged_rows:
                is_last = accumulated >= total_count
                dataset.update(DataPage(
                    page_num=page_num,
                    count=len(forged_rows),
                    data=forged_rows,
                    input_context=input_item,
                    is_last=is_last,
                    cursor=PageCursor(next_offset=accumulated) if not is_last else None,
                ))

    def batch_fetch(self, model: Any, search_domains: list = [], start_row: int = 0, batch_size: int | None = None, **params: Any) -> Iterator[list]:

        while batch_size > 0:

            results = self.read_query(model,search_domains=search_domains,start_row=start_row,**params)

            how_many = len(results)
            logger.debug("caught {} items starting at row = {}".format(how_many,start_row))
            yield results
            
            start_row = start_row + how_many
            batch_size = batch_size - how_many
            logger.info("{} more to go.".format(batch_size))


class DirectExtractor(GenericRPCExtractor):
    # child Interface bypassing the 'forge item' step
    def forge_item(self, item: Any, model_name: Any, **kwargs: Any) -> Any:
        return item