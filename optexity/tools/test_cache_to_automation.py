import pytest
from pydantic import ValidationError

from optexity.tools.cache_to_automation import build_automation, build_node
from optexity.tools.models import CachedStep


def make_step(**overrides) -> CachedStep:
    base = dict(
        step_index=0,
        action_name="input_text",
        dom_index=12,
        resolved_selector="Full Name",
        resolved_selector_strategy="label",
        accessible_name=None,
        value="myname",
        page_url_before="https://example.com",
        success=True,
        timestamp=0.0,
    )
    base.update(overrides)
    return CachedStep(**base)


def test_normal_path_builds_valid_input_text_node():
    node = build_node(make_step())
    assert node["interaction_action"]["input_text"]["command"] == 'get_by_label("Full Name")'
    assert node["interaction_action"]["input_text"]["input_text"] == "myname"


def test_dedup_case_keeps_only_last_value_for_same_field():
    from optexity.tools.filter import filter_redundant

    steps = [
        make_step(step_index=0, value="wrong"),
        make_step(step_index=1, value="myname"),
    ]
    kept = filter_redundant(steps)
    assert len(kept) == 1
    assert kept[0].value == "myname"


def test_xpath_fallback_case():
    step = make_step(
        resolved_selector_strategy="xpath",
        resolved_selector="//input[@id='city']",
    )
    node = build_node(step)
    assert node["interaction_action"]["input_text"]["xpath"] == "//input[@id='city']"
    assert node["interaction_action"]["input_text"]["command"] is None


def test_build_automation_validates_against_real_schema():
    automation = build_automation("https://example.com", [make_step()])
    assert automation.url == "https://example.com"
    assert len(automation.nodes) == 1

def test_build_automation_validation_failure():
    step = make_step()
    node = build_node(step)
    del node["interaction_action"]["input_text"]
    automation_dict = {
        "url": "https://example.com",
        "parameters": {"input_parameters": {}, "generated_parameters": {}},
        "nodes": [node],
    }
    from optexity.schema.automation import Automation
    with pytest.raises(ValidationError):
        Automation.model_validate(automation_dict)
