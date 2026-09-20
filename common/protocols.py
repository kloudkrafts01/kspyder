from typing import Any, Protocol, runtime_checkable

from common.models import Dataset


@runtime_checkable
class Extractor(Protocol):
    """Structural contract for any connector that extracts data into a Dataset.

    Satisfied by RESTExtractor and GenericRPCExtractor subclasses without
    any inheritance change — they already implement this surface."""

    schema: str

    def get_data(
        self,
        model_name: str | None = None,
        last_days: int | None = None,
        search_domains: list = [],
        input_data: list[dict[str, Any]] = [{}],
        **params: Any,
    ) -> Dataset: ...


@runtime_checkable
class DocumentStore(Protocol):
    """Structural contract for any connector that persists a Dataset.

    Satisfied by mongoDBConnector without any inheritance change."""

    schema: str

    def upsert_dataset(
        self,
        input_data: Dataset,
        collection: str | None = None,
        model: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...
