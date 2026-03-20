from typing import Any, Literal

from pydantic import BaseModel, Field


class APIConfig(BaseModel):
    name: str | None = None
    base_url: str | None = None
    pagination_style: Literal["pages", "offsets", "tokens"] | None = None
    next_token_key: str | None = None
    batch_size_key: str | None = None
    total_count_key: str | None = None
    is_truncated_key: str | None = None
    last_request_key: str | None = None
    update_field: str | None = None
    rate_limit: float | None = None
    response_map: dict[str, str] | None = None
    convert_response_case: bool = False
    default_headers: dict[str, str] | None = None
    header: dict[str, str] | None = None


class PipelineStepConfig(BaseModel):
    Name: str
    Job: str
    Worker: str | None = None
    Input: str | None = None
    Output: str | None = None
    Params: dict[str, Any] = Field(default_factory=dict)
    DumpJSON: bool | None = None
    DumpCSV: bool | None = None


class PipelineConfig(BaseModel):
    Steps: list[PipelineStepConfig]
