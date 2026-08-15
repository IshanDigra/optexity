"""Tests for the cache -> automation pipeline.

Every case here is a bug that actually occurred while building this, kept as a regression guard:
selectors collapsing a whole form into one node, xpaths landing in a field nothing reads, and
locators that match more than one element.
"""

import json

import pytest
from pydantic import ValidationError

from optexity.schema.automation import Automation
from optexity.tools.cache_to_automation import (
    DEFAULT_END_SLEEP_TIME,
    NAVIGATION_END_SLEEP_TIME,
    build_automation,
    build_node,
    plan_nodes,
)
from optexity.tools.filter import filter_redundant
from optexity.tools.models import CachedStep

SEED = Automation.model_validate(
    {
        "url": "https://example.com",
        "parameters": {"input_parameters": {}, "generated_parameters": {}},
        "nodes": [
            {
                "type": "action_node",
                "interaction_action": {
                    "agentic_task": {"task": "do the thing", "max_steps": 10}
                },
            }
        ],
    }
)


def make_step(**overrides) -> CachedStep:
    base = dict(
        step_index=0,
        action_name="input",
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


def only_node(step: CachedStep) -> dict:
    """Run one step through the planner so tests exercise the real path."""
    return build_node(plan_nodes("https://example.com", [step])[0])


# --- locator construction -------------------------------------------------------------------


def test_normal_path_builds_valid_input_text_node():
    action = only_node(make_step())["interaction_action"]["input_text"]
    assert action["command"] == 'get_by_label("Full Name").first'
    assert action["input_text"] == "myname"
    assert action["prompt_instructions"]


def test_role_command_includes_accessible_name():
    step = make_step(
        resolved_selector_strategy="role", resolved_selector="textbox", accessible_name="City"
    )
    command = only_node(step)["interaction_action"]["input_text"]["command"]
    assert command == 'get_by_role("textbox", name="City").first'


def test_quotes_in_selector_are_escaped():
    command = only_node(make_step(resolved_selector='say "hi"'))["interaction_action"][
        "input_text"
    ]["command"]
    assert command == 'get_by_label("say \\"hi\\"").first'


def test_xpath_becomes_a_command_not_the_xpath_field():
    """Nothing under optexity/inference reads BaseAction.xpath, so a node carrying only an xpath
    has no locator at replay and falls through to the LLM."""
    step = make_step(resolved_selector_strategy="xpath", resolved_selector="//input[@id='city']")
    action = only_node(step)["interaction_action"]["input_text"]
    assert action["command"] == 'locator("xpath=//input[@id=\'city\']").first'
    assert "xpath" not in action


def test_relative_xpath_is_made_absolute():
    """browser-use reports paths without a leading slash; Playwright treats those as relative."""
    step = make_step(
        resolved_selector_strategy="xpath", resolved_selector="html/body/header/div/div[1]"
    )
    command = only_node(step)["interaction_action"]["input_text"]["command"]
    assert command == 'locator("xpath=/html/body/header/div/div[1]").first'


def test_unresolved_step_yields_no_command():
    step = make_step(resolved_selector=None, resolved_selector_strategy="unknown")
    action = only_node(step)["interaction_action"]["input_text"]
    assert action["command"] is None
    assert action["prompt_instructions"]


# --- action mapping -------------------------------------------------------------------------


def test_navigate_maps_to_go_to_url():
    step = make_step(action_name="navigate", value="https://example.com/page")
    node = only_node(step)
    assert node["interaction_action"]["go_to_url"] == {"url": "https://example.com/page"}


def test_unmappable_action_is_reported():
    with pytest.raises(ValueError, match="No mapping"):
        only_node(make_step(action_name="send_keys"))


# --- filtering ------------------------------------------------------------------------------


def test_dedup_keeps_only_last_value_for_same_field():
    kept = filter_redundant(
        [make_step(step_index=0, value="wrong"), make_step(step_index=1, value="myname")]
    )
    assert [s.value for s in kept] == ["myname"]


def test_dedup_does_not_collapse_distinct_fields_sharing_a_role():
    """The role strategy reports the ARIA role, so every text input on a form shares the selector
    'textbox'. Only the accessible name tells them apart."""
    steps = [
        make_step(
            step_index=i,
            resolved_selector_strategy="role",
            resolved_selector="textbox",
            accessible_name=name,
            value=value,
        )
        for i, (name, value) in enumerate(
            [("Full Name", "myname"), ("Address 1", "xyz"), ("Address 2", "abc"), ("City", "SF")]
        )
    ]
    assert [s.value for s in filter_redundant(steps)] == ["myname", "xyz", "abc", "SF"]


def test_failed_and_non_replayable_steps_are_dropped():
    steps = [
        make_step(step_index=0, success=False, value="typo"),
        make_step(step_index=1, action_name="scroll", resolved_selector=None),
        make_step(step_index=2, action_name="done", resolved_selector=None),
        make_step(step_index=3, action_name="evaluate", resolved_selector=None),
        make_step(step_index=4, value="myname"),
    ]
    assert [s.value for s in filter_redundant(steps)] == ["myname"]


# --- navigation detection -------------------------------------------------------------------


def test_step_that_changes_the_url_gets_a_longer_settle_time():
    steps = [
        make_step(step_index=0, action_name="click", page_url_before="https://example.com"),
        make_step(step_index=1, action_name="click", page_url_before="https://example.com/next"),
    ]
    nodes = [build_node(p) for p in plan_nodes("https://example.com", steps)]
    assert nodes[0]["end_sleep_time"] == NAVIGATION_END_SLEEP_TIME
    # The last step has no successor to compare against, so it keeps the default.
    assert nodes[1]["end_sleep_time"] == DEFAULT_END_SLEEP_TIME


def test_opening_navigation_to_the_start_url_is_dropped():
    steps = [
        make_step(step_index=0, action_name="navigate", value="https://example.com"),
        make_step(step_index=1, value="myname"),
    ]
    planned = plan_nodes("https://example.com", steps)
    assert [p.optexity_action for p in planned] == ["input_text"]


# --- seed inheritance -----------------------------------------------------------------------


def test_build_automation_validates_against_real_schema():
    automation = build_automation(SEED, [make_step()])
    assert automation.url == "https://example.com"
    assert len(automation.nodes) == 1
    # The 5s schema default would otherwise dominate the replay-latency comparison.
    assert automation.nodes[0].end_sleep_time == DEFAULT_END_SLEEP_TIME


def test_seed_parameters_and_downloads_are_inherited():
    """The cached automation is triggered exactly like the agentic one, so undeclared parameters
    would be stripped by the local override in child_process.py."""
    seed = Automation.model_validate(
        {
            "url": "https://example.com",
            "expected_downloads": 1,
            "parameters": {
                "input_parameters": {"connection_key": ["ishan"]},
                "generated_parameters": {},
            },
            "nodes": SEED.model_dump(mode="json")["nodes"],
        }
    )
    automation = build_automation(seed, [make_step()])
    assert automation.expected_downloads == 1
    assert automation.parameters.input_parameters == {"connection_key": ["ishan"]}


def test_url_override_wins_over_the_seed():
    automation = build_automation(SEED, [make_step()], url="https://other.example")
    assert automation.url == "https://other.example"


def test_build_automation_rejects_a_malformed_node():
    node = only_node(make_step())
    del node["interaction_action"]["input_text"]
    with pytest.raises(ValidationError):
        Automation.model_validate(
            {
                "url": "https://example.com",
                "parameters": {"input_parameters": {}, "generated_parameters": {}},
                "nodes": [node],
            }
        )


def test_generated_automation_round_trips_through_json():
    """What is written to disk has to survive being read back by the inference server."""
    automation = build_automation(SEED, [make_step()])
    dumped = json.dumps(automation.model_dump(mode="json", exclude_none=True))
    assert Automation.model_validate(json.loads(dumped)).nodes
