from uuid import UUID, uuid4
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field


class PageCursor(BaseModel):
    """Ephemeral pagination state used internally by extractors to drive iteration.
    Never leaves the extraction loop — discarded once is_last is True on the produced DataPage.
    Stored optionally on DataPage.cursor to enable future resumability."""

    model_config = ConfigDict(frozen=True)

    next_page: int | None = None
    next_offset: int | None = None
    next_token: str | None = None
    next_url: str | None = None


class DataPage(BaseModel):
    """One page of extracted data — the atomic unit of extraction output.
    Pages share a common header/lineage via their parent Dataset.
    Designed to be independently processable and queueable."""

    page_num: int
    count: int
    data: list[dict[str, Any]]
    input_context: dict[str, Any] = Field(default_factory=dict)
    is_last: bool = False
    cursor: PageCursor | None = None  # cursor that produced this page; None until resumability is implemented


class DatasetHeader(BaseModel):
    """Metadata and lineage for a Dataset.

    Note: field is named source_schema (not schema) to avoid shadowing
    Pydantic v2's deprecated .schema() classmethod."""

    source_schema: str
    model_name: str
    model: dict[str, Any]
    run_id: UUID = Field(default_factory=uuid4)
    params: dict[str, Any] = Field(default_factory=dict)
    scopes: list[Any] | None = None
    json_dump: str | None = None
    csv_dump: str | None = None


class Dataset(BaseModel):
    """Accumulated extraction result composed of DataPages sharing the same header/lineage.

    .data and .count are computed properties that provide a flat view across all pages.

    The __getitem__ shim preserves backwards compatibility with legacy dict-style access
    patterns in pipelineEngine (result['data'], result['header']['count'], etc.) during
    the migration period."""

    header: DatasetHeader
    pages: list[DataPage] = Field(default_factory=list)
    failed_items: list[dict[str, Any]] = Field(default_factory=list)

    @computed_field
    @property
    def data(self) -> list[dict[str, Any]]:
        return [item for page in self.pages for item in page.data]

    @computed_field
    @property
    def count(self) -> int:
        return sum(p.count for p in self.pages)

    def update(self, page: DataPage) -> None:
        """Append a DataPage to this Dataset."""
        self.pages.append(page)

    def __bool__(self) -> bool:
        return len(self.pages) > 0

    def __getitem__(self, key: str) -> Any:
        """Backwards compatibility shim for legacy dict-style access.
        To be removed once pipelineEngine is fully migrated to typed Dataset access."""
        if key == 'data':
            return self.data
        if key == 'failed_items':
            return self.failed_items
        if key == 'header':
            return {
                'schema': self.header.source_schema,
                'model_name': self.header.model_name,
                'model': self.header.model,
                'count': self.count,
                'run_id': str(self.header.run_id),
                'params': self.header.params,
                'scopes': self.header.scopes,
                'json_dump': self.header.json_dump,
                'csv_dump': self.header.csv_dump,
            }
        raise KeyError(f"Dataset has no key '{key}'")

    def to_json(self) -> dict[str, Any]:
        """Serialise to the legacy {{'header': {{...}}, 'data': [...]}} dict format.
        Used by fileHandler for JSON/CSV dumps."""
        return {
            'header': self['header'],
            'data': self.data,
            'failed_items': self.failed_items,
        }
