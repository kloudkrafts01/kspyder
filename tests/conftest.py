import os
from typing import Any

# Several modules under test (common.clientHandler, Engines.pipelineEngine) read
# common.config attributes at import time, which now lazily resolves KSPYDER_CONF
# (see common/config.py). Default to the existing local conf so the suite is
# runnable without extra setup, without overriding a developer's own env var.
os.environ.setdefault("KSPYDER_CONF", "local")

from common.models import Dataset, DatasetHeader, DataPage


class FakeExtractor:
    """Duck-typed test double satisfying the Extractor Protocol — no inheritance."""

    schema = "fakeExtractor"

    def get_data(
        self,
        model_name: str | None = None,
        last_days: int | None = None,
        search_domains: list = [],
        input_data: list[dict[str, Any]] = [{}],
        **params: Any,
    ) -> Dataset:
        dataset = Dataset(
            header=DatasetHeader(
                source_schema=self.schema,
                model_name=model_name or "fakeModel",
                model={},
            )
        )
        dataset.update(DataPage(page_num=0, count=len(input_data), data=input_data, is_last=True))
        return dataset


class FakeDocumentStore:
    """Duck-typed test double satisfying the DocumentStore Protocol — no inheritance."""

    schema = "fakeDocumentStore"

    def __init__(self) -> None:
        self.upserted: list[Dataset] = []

    def upsert_dataset(
        self,
        input_data: Dataset,
        collection: str | None = None,
        model: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.upserted.append(input_data)
        return {"upserted_count": input_data.count, "collection": collection}
