```markdown
# Test and Validation Plan

## 1. Functional parity check

Run `test_automation_cached.json` (Phase 4 output) against `https://www.roboform.com/filling-test-all-fields` and assert the resulting field values match the original task's intent exactly:

```python
def test_roboform_cached_automation_fills_correct_values(page):
    run_automation_locally("test_automation_cached.json")
    assert page.locator("input[name='fullname']").input_value() == "myname"  # adjust selector to real field
    assert page.locator("input[name='address1']").input_value() == "xyz"
    assert page.locator("input[name='address2']").input_value() == "abc"
    assert page.locator("input[name='city']").input_value() == "SF"

```

(Selector names are placeholders — fill in from what Phase 2's cache actually resolved for each field.)

## 2. Performance comparison

Use the `run_and_measure` harness from `02_implementation_plan.md` Phase 5. Record both runs' `elapsed_seconds` and `llm_calls` and report the delta — this is the number the "latency/performance" evaluation criterion is scored on. Target: `llm_calls == 0` for the cached run, and a large (expect >50%) reduction in `elapsed_seconds`.

## 3. Idempotency / regression check

Run `test_automation_cached.json` **twice in a row** and confirm both runs produce identical results with no dependency on state left over from the first run (this catches accidental reliance on browser session state that an agentic run might tolerate but a deterministic replay shouldn't).

## 4. Unit tests for the converter

`optexity/tools/test_cache_to_automation.py`, three fixtures:

```python
import pytest
from cache_to_automation import build_automation, build_node
from models import CachedStep

def make_step(**overrides) -> CachedStep:
    base = dict(
        step_index=0, action_name="input_text", dom_index=12,
        resolved_selector="Full Name", resolved_selector_strategy="label",
        accessible_name=None, value="myname",
        page_url_before="[https://example.com](https://example.com)", success=True, timestamp=0.0,
    )
    base.update(overrides)
    return CachedStep(**base)

def test_normal_path_builds_valid_input_text_node():
    node = build_node(make_step())
    assert node["interaction_action"]["input_text"]["command"] == 'get_by_label("Full Name")'
    assert node["interaction_action"]["input_text"]["input_text"] == "myname"

def test_dedup_case_keeps_only_last_value_for_same_field():
    from filter import filter_redundant
    steps = [
        make_step(step_index=0, value="wrong"),
        make_step(step_index=1, value="myname"),
    ]
    kept = filter_redundant(steps)
    assert len(kept) == 1
    assert kept[0].value == "myname"

def test_xpath_fallback_case():
    step = make_step(resolved_selector_strategy="xpath",
                     resolved_selector="//input[@id='city']")
    node = build_node(step)
    assert node["interaction_action"]["input_text"]["xpath"] == "//input[@id='city']"
    assert node["interaction_action"]["input_text"]["command"] is None

def test_build_automation_validates_against_real_schema():
    automation = build_automation("[https://example.com](https://example.com)", [make_step()])
    assert automation.url == "[https://example.com](https://example.com)"
    assert len(automation.nodes) == 1

```

**Done-check:** all three fixtures pass, and `build_automation` raises (via `Automation.model_validate`) if a required field like `prompt_instructions` is missing - proving the schema-validation safety net actually works, not just that happy-path JSON is produced.

## 5. Second-site validation

Repeat sections 1-3 against the Phase 6 multi-step site. Confirm navigation-changing steps (`go_to_url`/`click_element` that change page) convert correctly, not just form fills - this is the part a single-page-form test can't exercise.

## 6. Submission-mechanics checklist (from `Engcon Hackathon goal.md`)

* [ ] Both `optexity` and `browser-use` are forked to **your own** GitHub (not working directly on Optexity's repos)
* [ ] A new branch created in your own fork of each repo, all code committed there
* [ ] PR opened from your branch to **your own fork's `main**` - explicitly **not** to the upstream Optexity repos
* [ ] Both PR links ready to submit
* [ ] Demo-ready answers for each evaluation criterion: code quality, latency/performance numbers (Section 2 above), extra features (bonus items from `02_implementation_plan.md` Phase 7, if attempted), and the "why" behind each decision (`03_design_decisions_and_tradeoffs.md`)

## 7. Deslop checklist (final pass before calling it done)

* [ ] No stray `print()`/debug logging left in the hook or converter beyond what's intentionally part of the cache
* [ ] No leftover `TODO`/`FIXME` markers in committed code
* [ ] Naming is consistent between the cache schema (`CachedStep` fields), the filter, and the converter - no renamed-but-not-everywhere fields
* [ ] Every cross-reference between the five markdown docs in this folder actually points to a section that exists (checked manually, not just written on faith)
* [ ] Every JSON/code snippet across all docs is syntactically valid (spot-checked, not executed, since there is no live environment in this planning session)

```

```