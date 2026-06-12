from uuid import UUID

import pytest
from pydantic import ValidationError

from common.models import Dataset, DatasetHeader, DataPage, PageCursor


def make_header(**overrides):
    defaults = dict(source_schema="testSchema", model_name="testModel", model={"name": "testModel"})
    return DatasetHeader(**{**defaults, **overrides})


def test_dataset_header_defaults():
    header = make_header()
    assert isinstance(header.run_id, UUID)
    assert header.params == {}
    assert header.scopes is None
    assert header.json_dump is None
    assert header.csv_dump is None


def test_data_page_defaults():
    page = DataPage(page_num=0, count=2, data=[{"a": 1}, {"a": 2}])
    assert page.input_context == {}
    assert page.is_last is False
    assert page.cursor is None


def test_page_cursor_is_frozen():
    cursor = PageCursor(next_token="abc")
    with pytest.raises(ValidationError):
        cursor.next_token = "def"


def test_empty_dataset_is_falsy():
    dataset = Dataset(header=make_header())
    assert bool(dataset) is False
    assert dataset.data == []
    assert dataset.count == 0


def test_update_appends_page_and_aggregates():
    dataset = Dataset(header=make_header())

    dataset.update(DataPage(page_num=0, count=2, data=[{"a": 1}, {"a": 2}]))
    dataset.update(DataPage(page_num=1, count=1, data=[{"a": 3}], is_last=True))

    assert bool(dataset) is True
    assert dataset.count == 3
    assert dataset.data == [{"a": 1}, {"a": 2}, {"a": 3}]


def test_getitem_shim():
    header = make_header()
    dataset = Dataset(header=header)
    dataset.update(DataPage(page_num=0, count=1, data=[{"a": 1}]))
    dataset.failed_items.append({"item": {"a": "bad"}})

    assert dataset["data"] == [{"a": 1}]
    assert dataset["failed_items"] == [{"item": {"a": "bad"}}]

    legacy_header = dataset["header"]
    assert legacy_header["schema"] == "testSchema"
    assert legacy_header["model_name"] == "testModel"
    assert legacy_header["count"] == 1
    assert legacy_header["run_id"] == str(header.run_id)

    with pytest.raises(KeyError):
        dataset["not_a_real_key"]


def test_to_json_shape():
    dataset = Dataset(header=make_header())
    dataset.update(DataPage(page_num=0, count=1, data=[{"a": 1}]))

    json_data = dataset.to_json()

    assert set(json_data.keys()) == {"header", "data", "failed_items"}
    assert json_data["data"] == [{"a": 1}]
    assert json_data["failed_items"] == []
    assert json_data["header"]["schema"] == "testSchema"
