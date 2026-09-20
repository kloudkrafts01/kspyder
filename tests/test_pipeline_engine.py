import jmespath

from common.configModels import PipelineConfig
from Engines.pipelineEngine import pipelineEngine
from tests.conftest import FakeDocumentStore, FakeExtractor


def make_engine():
    return pipelineEngine()


def test_apply_filters():
    engine = make_engine()
    input_data = [
        {"name": "a", "kind": "x"},
        {"name": "b", "kind": "y"},
        {"name": "c", "kind": "x"},
    ]

    result = engine.apply_filters(input_data=input_data, filters={"kind": "x"})

    assert result["header"] == {"operation": "apply_filters"}
    assert result["data"] == [{"name": "a", "kind": "x"}, {"name": "c", "kind": "x"}]


def test_set_static_data():
    engine = make_engine()
    data = [{"name": "a"}, {"name": "b"}]

    result = engine.set_static_data(data=data)

    assert result["header"]["operation"] == "set_static_data"
    assert result["header"]["count"] == 2
    assert result["data"] == data


def test_get_unique_key_list():
    engine = make_engine()
    input_data = {"items": [{"id": 1}, {"id": 2}, {"id": 3}]}

    result = engine.get_unique_key_list(input_data=input_data, key="id", datapath="items[].id")

    assert result["header"]["count"] == 3
    assert result["data"] == [{"id": 1}, {"id": 2}, {"id": 3}]


def test_execute_pipeline_chains_steps_via_input():
    engine = make_engine()

    pipeline = PipelineConfig(Steps=[
        {
            "Name": "raw",
            "Job": "set_static_data",
            "Params": {"data": [
                {"name": "a", "kind": "x"},
                {"name": "b", "kind": "y"},
            ]},
        },
        {
            "Name": "filtered",
            "Job": "apply_filters",
            "Input": "raw.data",
            "Params": {"filters": {"kind": "x"}},
        },
    ])

    datasets = {}
    for step in pipeline.Steps:
        step_input = jmespath.search(step.Input, datasets) if step.Input else None
        job_instance = getattr(engine, step.Job)
        result = job_instance(input_data=step_input, **step.Params) if step_input else job_instance(**step.Params)
        datasets[step.Output or step.Name] = result

    assert datasets["raw"]["data"] == [
        {"name": "a", "kind": "x"},
        {"name": "b", "kind": "y"},
    ]
    assert datasets["filtered"]["data"] == [{"name": "a", "kind": "x"}]


def test_get_data_to_mongo_with_protocol_doubles(monkeypatch):
    engine = make_engine()

    fake_extractor = FakeExtractor()
    fake_store = FakeDocumentStore()

    def fake_get_client(source=None, profile_name=None, **kwargs):
        return fake_extractor if source != "mongoDB" else fake_store

    monkeypatch.setattr(engine.ch, "get_client", fake_get_client)

    input_data = [{"id": 1}, {"id": 2}]
    full_dataset = engine.get_data_to_mongo(input_data=input_data, from_worker="someExtractor")

    assert full_dataset.data == input_data
    assert len(fake_store.upserted) == 1
    assert fake_store.upserted[0] is full_dataset
