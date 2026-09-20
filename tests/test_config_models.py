import pytest
from pydantic import ValidationError

from common.configModels import APIConfig, PipelineConfig, PipelineStepConfig


def test_api_config_defaults():
    api = APIConfig()
    assert api.name is None
    assert api.base_url is None
    assert api.pagination_style is None
    assert api.convert_response_case is False
    assert api.response_map is None


def test_api_config_accepts_valid_pagination_style():
    for style in ("pages", "offsets", "tokens", "urls"):
        api = APIConfig(pagination_style=style)
        assert api.pagination_style == style


def test_api_config_rejects_invalid_pagination_style():
    with pytest.raises(ValidationError):
        APIConfig(pagination_style="not_a_real_style")


def test_pipeline_step_config_requires_name_and_job():
    with pytest.raises(ValidationError):
        PipelineStepConfig(Job="get_data")

    with pytest.raises(ValidationError):
        PipelineStepConfig(Name="step1")


def test_pipeline_step_config_optional_defaults():
    step = PipelineStepConfig(Name="step1", Job="get_data")
    assert step.Worker is None
    assert step.Input is None
    assert step.Output is None
    assert step.Params == {}
    assert step.DumpJSON is None
    assert step.DumpCSV is None


def test_pipeline_config_validates_steps_list():
    pipeline = PipelineConfig(Steps=[
        {"Name": "step1", "Job": "get_data", "Worker": "azureRetailPrices"},
        {"Name": "step2", "Job": "set_static_data", "Input": "step1.data"},
    ])

    assert len(pipeline.Steps) == 2
    assert all(isinstance(step, PipelineStepConfig) for step in pipeline.Steps)
    assert pipeline.Steps[0].Worker == "azureRetailPrices"
    assert pipeline.Steps[1].Input == "step1.data"
