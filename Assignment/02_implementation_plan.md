```markdown
# Implementation Plan: Agentic -> Cached -> Deterministic Memory Layer

**Audience:** a junior developer picking this up cold, after reading `01_optexity_end_to_end_understanding.md` and `browser-use_codebase_understanding.md`. Each phase names the files touched, which fork they live in, a runnable-shaped snippet, and a done-check. Code is illustrative and will need names/imports adjusted per the "Confirm before you build" checklist in `browser-use_codebase_understanding.md` §5 - it is written so that adjustment is a small, localized edit, not a rewrite.

Repo split (per goal doc + `optexity_codebase_understand.md`'s `../browser-use` sibling-path convention):
- **`browser-use` fork** - owns the caching *hook* (Phase 2), because that's where actions are actually executed.
- **`optexity` fork** - owns the *filter* and *converter* (Phases 3-4), because neither needs browser-use internals (both are pure transforms over `cache.jsonl`) and the converter needs the `Automation` Pydantic schema to self-validate output, which only exists in this fork.

## Phase 0 - Environment (already covered by the goal doc, not repeated here)

Both forks cloned as siblings, both `pip install -e .`'d into the same conda env, in that order (browser-use before/with optexity per the goal doc's warning about install order). Not re-executed as part of this planning work - see `Engcon Hackathon goal.md` Setup sections.

## Phase 1 - Baseline agentic run

Use the exact starting automation from the goal doc, saved as `test_automation.json`:

```json
{
  "url": "[https://www.roboform.com/filling-test-all-fields](https://www.roboform.com/filling-test-all-fields)",
  "parameters": { "input_parameters": {}, "generated_parameters": {} },
  "nodes": [
    {
      "type": "action_node",
      "interaction_action": {
        "agentic_task": {
          "task": "fill the full name as myname, address line one as xyz and line 2 as abc, city as SF",
          "max_steps": 15,
          "backend": "browser_use"
        }
      }
    }
  ]
}

```

Run it once via the local child-process override (goal doc's `optexity/inference/child_process.py` patch). Confirm the form actually gets filled. This run is the reference for correctness comparison in Phase 5 - no caching yet, just proving the baseline works.

**Done-check:** roboform form shows Full Name / Address Line 1 / Address Line 2 / City filled with the values from the task string.

## Phase 2 - Caching hook (in the `browser-use` fork)

### 2a. The cache record shape

New file: `browser_use_fork/browser_use/memory_cache/models.py` (path illustrative - put it wherever the fork's convention for internal utilities is; do not touch the schema/`Automation` model, that lives in optexity).

```python
from pydantic import BaseModel
from typing import Literal

class CachedStep(BaseModel):
    step_index: int
    action_name: str                  # e.g. "click_element_by_index", "input_text"
    dom_index: int | None = None      # the transient [n] index, kept for debugging only
    resolved_selector: str | None = None
    resolved_selector_strategy: Literal[
        "role", "label", "test_id", "text", "css", "xpath", "unknown"
    ] = "unknown"
    accessible_name: str | None = None  # e.g. role's `name=` value, needed to rebuild get_by_role(...)
    value: str | None = None            # text typed / url navigated / option selected
    page_url_before: str
    success: bool
    timestamp: float

```

`resolved_selector_strategy` exists specifically so the Phase 4 converter can follow Optexity's own locator preference order (`01_...md` §5) instead of guessing from a bare string.

### 2b. The choke-point wrapper

This is the one piece that depends on the "Confirm before you build" checklist - the snippet below wraps a placeholder `execute_action`; rename per what you actually found.

```python
import time
from pathlib import Path
from .models import CachedStep

CACHE_PATH = Path("cache.jsonl")
_step_counter = 0

def _classify_selector(resolved_info: dict) -> tuple[str, str | None, str | None]:
    """Best-effort mapping from whatever the choke point exposes to
    (strategy, resolved_selector, accessible_name), following the
    role > label > test_id > text > css > xpath preference order."""
    if role := resolved_info.get("role"):
        return "role", role, resolved_info.get("accessible_name")
    if label := resolved_info.get("label"):
        return "label", label, None
    if test_id := resolved_info.get("test_id"):
        return "test_id", test_id, None
    if text := resolved_info.get("text"):
        return "text", text, None
    if css := resolved_info.get("css_selector"):
        return "css", css, None
    if xpath := resolved_info.get("xpath"):
        return "xpath", xpath, None
    return "unknown", None, None

def cached_execute_action(original_execute_action):
    """Decorator: wraps the real dispatch choke point (Section 4 of
    browser-use_codebase_understanding.md). Adjust the signature to
    match what you actually find there."""
    
    def wrapper(action_name, params, browser_context, *args, **kwargs):
        global _step_counter
        page_url_before = browser_context.current_page.url  # adjust accessor as needed
        result = original_execute_action(action_name, params, browser_context, *args, **kwargs)

        resolved_info = getattr(result, "resolved_element_info", {}) or {}
        strategy, selector, accessible_name = _classify_selector(resolved_info)

        step = CachedStep(
            step_index=_step_counter,
            action_name=action_name,
            dom_index=params.get("index"),
            resolved_selector=selector,
            resolved_selector_strategy=strategy,
            accessible_name=accessible_name,
            value=params.get("text") or params.get("url") or params.get("value"),
            page_url_before=page_url_before,
            success=getattr(result, "success", True),
            timestamp=time.time(),
        )
        
        _step_counter += 1
        with CACHE_PATH.open("a") as f:
            f.write(step.model_dump_json() + "\n")

        return result

    return wrapper

```

Apply it at import/init time around the real dispatch method (e.g. `registry.execute_action = cached_execute_action(registry.execute_action)`), rather than editing every action function individually - this is the design decision explained in `03_design_decisions_and_tradeoffs.md`.

**Done-check:** rerun Phase 1's task; `cache.jsonl` now has one line per action the agent took, in order, with real resolved selector info (not just the raw index).

## Phase 3 - Redundant-step filtering (in the `optexity` fork)

New file: `optexity/tools/filter.py`. This is a pure transform over `cache.jsonl` - it needs no browser-use internals, so it lives alongside the converter (Phase 4) rather than inside the browser-use fork.

```python
from models import CachedStep # copy of the CachedStep model from Phase 2a, or a shared package

def load_steps(path: str) -> list[CachedStep]:
    with open(path) as f:
        return [CachedStep.model_validate_json(line) for line in f if line.strip()]

def filter_redundant(steps: list[CachedStep]) -> list[CachedStep]:
    kept: list[CachedStep] = []
    last_index_by_selector: dict[str, int] = {}

    for step in steps:
        if not step.success:
            continue # drop failed attempts; only the eventual success matters

        key = step.resolved_selector or f"idx:{step.dom_index}"

        # last-write-wins: if the same field/element was acted on again
        # before this run ends, the later value is the real one - drop
        # the earlier attempt rather than keeping both.
        if key in last_index_by_selector and step.action_name in ("input_text", "select_option"):
            kept[last_index_by_selector[key]] = step
            continue
            
        last_index_by_selector[key] = len(kept)
        kept.append(step)

    return kept

```

This is deliberately simple (see `03_design_decisions_and_tradeoffs.md` for why rule-based, not ML-based). Two rules only: drop failed attempts, and collapse repeated writes to the same field into the last one.

Note: `CachedStep` (Phase 2a) is defined inside the browser-use fork but read here in the optexity fork. For a POC, the simplest fix is a small duplicate of the model in `optexity/tools/models.py` (both sides only need it to read/write the same JSON shape, not share a Python object) - don't reach across fork boundaries at runtime just to avoid a five-line duplicate.

**Done-check:** for the roboform task (4 fields), `filter_redundant` output has exactly 4 `input_text` steps (or a `click_element` at the end if the agent also clicked submit) - no duplicates, no failed-attempt noise.

## Phase 4 - Cache -> automation converter (in the `optexity` fork)

New file: `optexity/tools/cache_to_automation.py`.

```python
from optexity.schema.automation import Automation

def _build_command(step) -> tuple[str | None, str | None]:
    """Returns (command, xpath) per Optexity's locator preference order."""
    if step.resolved_selector_strategy == "role":
        name = step.accessible_name or ""
        return f'get_by_role("{step.resolved_selector}", name="{name}")', None
    if step.resolved_selector_strategy == "label":
        return f'get_by_label("{step.resolved_selector}")', None
    if step.resolved_selector_strategy == "test_id":
        return f'get_by_test_id("{step.resolved_selector}")', None
    if step.resolved_selector_strategy == "text":
        return f'get_by_text("{step.resolved_selector}")', None
    if step.resolved_selector_strategy == "css":
        return f'locator("{step.resolved_selector}")', None
    if step.resolved_selector_strategy == "xpath":
        return None, step.resolved_selector
    return None, None # unknown - will rely on prompt_instructions only

_ACTION_MAP = {
    "click_element_by_index": "click_element",
    "input_text": "input_text",
    "go_to_url": "go_to_url",
}

def build_node(step) -> dict:
    optexity_action = _ACTION_MAP.get(step.action_name)
    if optexity_action is None:
        raise ValueError(f"No mapping for browser-use action '{step.action_name}' - "
                         f"extend _ACTION_MAP or handle it explicitly")

    command, xpath = _build_command(step)
    body = {
        "command": command,
        "xpath": xpath,
        "prompt_instructions": f"Perform {optexity_action} for step {step.step_index} "
                               f"(derived from a cached agentic run)",
    }
    if optexity_action == "input_text":
        body["input_text"] = step.value

    return {
        "type": "action_node",
        "interaction_action": {optexity_action: body},
    }

def build_automation(url: str, steps: list) -> Automation:
    automation_dict = {
        "url": url,
        "parameters": {"input_parameters": {}, "generated_parameters": {}},
        "nodes": [build_node(s) for s in steps],
    }
    # Validate against the real schema before anything is written to disk - 
    # catches drift immediately instead of shipping a malformed automation.
    return Automation.model_validate(automation_dict)

if __name__ == "__main__":
    from filter import load_steps, filter_redundant # Phase 3, same fork

    steps = filter_redundant(load_steps("cache.jsonl"))
    automation = build_automation("[https://www.roboform.com/filling-test-all-fields](https://www.roboform.com/filling-test-all-fields)", steps)

    with open("test_automation_cached.json", "w") as f:
        f.write(automation.model_dump_json(indent=2))

```

**Done-check:** `test_automation_cached.json` exists, is valid per `Automation.model_validate`, and visually matches the shape of the goal doc's expected-output example (one `input_text` node per field, `command` populated, not fabricated).

## Phase 5 - Replay & compare

Minimal harness - wrap two runs and diff time + LLM-call count:

```python
import time

def run_and_measure(automation_path: str, llm_call_counter) -> dict:
    start = time.time()
    llm_call_counter.reset()
    run_automation_locally(automation_path) # existing local-run entrypoint from Phase 0/1
    return {
        "elapsed_seconds": time.time() - start,
        "llm_calls": llm_call_counter.count,
    }

agentic_result = run_and_measure("test_automation.json", llm_call_counter)
cached_result = run_and_measure("test_automation_cached.json", llm_call_counter)

print(f"Agentic: {agentic_result}")
print(f"Cached: {cached_result}")

```

`llm_call_counter` can be as simple as another wrapper around whatever function makes the actual LLM completion call inside browser-use - increment a counter, reset between runs. Expect `cached_result['llm_calls'] == 0` and a large drop in `elapsed_seconds`; these numbers directly feed the "latency/performance" evaluation criterion and `04_test_and_validation_plan.md`.

**Done-check:** cached run fills the form correctly with `llm_calls == 0`, and completes measurably faster than the agentic run.

## Phase 6 - Apply to a second, multi-step site

Requirement from the goal doc: pick a site with real multi-page/multi-click navigation (not another single-page form), and avoid CAPTCHA-gated sites. Repeat Phases 1-5 unchanged - the hook, filter, and converter are all site-agnostic. The only new code is the initial `agentic_task` automation JSON pointed at the new site and task description.

**Done-check:** same as Phase 5, on the second site.

## Phase 7 - Bonus (stretch, not required for the core deliverable)

Both bonus items below are self-contained additions on top of Phases 1-6 - a junior dev can adopt either independently, or skip both without weakening the core deliverable. Each has its own done-check so it can be verified in isolation.

### 7a. LLM-assisted auto-build (in the `optexity` fork)

Goal: replace Phase 4's hand-written `_ACTION_MAP` / `_build_command` logic with an LLM call, while keeping Phase 4's converter as a trustworthy baseline to catch regressions - per the reasoning in `03_design_decisions_and_tradeoffs.md` §5.

New file: `optexity/tools/llm_cache_to_automation.py`.

```python
import json
from litellm import completion # optexity already depends on litellm (see optexity_codebase_understand.md)
from optexity.schema.automation import Automation

SYSTEM_PROMPT = """You convert a list of recorded browser actions into a single
Optexity Automation JSON object. Return ONLY valid JSON matching the provided
JSON schema - no prose, no markdown fences.

When choosing a `command` locator for each step, follow this preference order
(from Optexity's own locator docs): role > label > test_id > text > css > xpath.
Use the step's `resolved_selector_strategy` field to pick the right form:
  role   -> get_by_role("<resolved_selector>", name="<accessible_name>")
  label  -> get_by_label("<resolved_selector>")
  test_id -> get_by_test_id("<resolved_selector>")
  text   -> get_by_text("<resolved_selector>")
  css    -> locator("<resolved_selector>")
  xpath  -> put the value in the node's `xpath` field instead of `command`

Every interaction action MUST include a non-empty `prompt_instructions`."""

def build_messages(url: str, steps: list[dict]) -> list[dict]:
    schema = Automation.model_json_schema()
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps({
            "url": url,
            "target_json_schema": schema,
            "cached_steps": steps, # list of CachedStep.model_dump(), post-filter_redundant
        })},
    ]

def llm_build_automation(url: str, steps: list[dict], max_repair_attempts: int = 3) -> Automation:
    messages = build_messages(url, steps)

    for attempt in range(max_repair_attempts):
        response = completion(
            model="gpt-4o",
            messages=messages,
            response_format={"type": "json_object"},
        )
        raw_json = response["choices"][0]["message"]["content"]
        
        try:
            return Automation.model_validate_json(raw_json)
        except Exception as validation_error:
            # Self-correction loop: feed the exact validation error back
            # rather than retrying blind - cheaper and more reliable than
            # a fresh attempt with no feedback.
            messages.append({"role": "assistant", "content": raw_json})
            messages.append({
                "role": "user",
                "content": f"That failed schema validation: {validation_error}.\n"
                           f"Return corrected JSON only, same rules as before.",
            })
            
    raise RuntimeError(f"LLM failed to produce a schema-valid Automation after {max_repair_attempts} attempts")

def build_and_diff(url: str, filtered_steps: list) -> dict:
    """Runs both the deterministic Phase 4 converter and the LLM-assisted
    converter on the same input, and reports where they disagree - the
    baseline is the source of truth until the LLM path has proven itself."""
    from cache_to_automation import build_automation # Phase 4

    baseline = build_automation(url, filtered_steps)
    llm_generated = llm_build_automation(url, [s.model_dump() for s in filtered_steps])

    return {
        "baseline_node_count": len(baseline.nodes),
        "llm_node_count": len(llm_generated.nodes),
        "node_count_matches": len(baseline.nodes) == len(llm_generated.nodes),
        "baseline": baseline,
        "llm_generated": llm_generated,
    }

```

**Done-check:** on the roboform cache, `build_and_diff(...)["node_count_matches"]` is `True`, and a manual skim of `llm_generated` vs `baseline` shows the same fields (same `command`s, same `input_text` values) - any drift here is a signal to fix the prompt, not to trust the LLM output as-is.

### 7b. Iterative recache / self-healing loop (in the `optexity` fork)

Goal: when a deterministic node in the cached automation fails (e.g. a locator that no longer matches because the page changed slightly), don't just fail the whole automation - fall back to a scoped `agentic_task` for that one node, recapture what the agent does to recover, and patch only that node.

New file: `optexity/tools/self_healing_runner.py`.

```python
from optexity.schema.automation import Automation
from filter import load_steps, filter_redundant
from cache_to_automation import build_node

MAX_HEALING_ITERATIONS = 3

def run_single_node(automation: Automation, node_index: int) -> bool:
    """Executes exactly one node of an automation and returns whether it
    succeeded. Placeholder - wire this to whatever the local dev harness
    (Phase 0/1) exposes for running a subset of nodes; the goal doc's
    child_process.py override is the natural place to add single-node
    execution if it isn't already exposed."""
    raise NotImplementedError

def run_with_self_healing(
    automation: Automation,
    remaining_goal_by_node: dict[int, str],
) -> Automation:
    """`remaining_goal_by_node` maps a node index to a natural-language
    description of what that node was meant to accomplish - used to build
    the scoped agentic_task fallback when that node fails."""
    
    for iteration in range(MAX_HEALING_ITERATIONS):
        failure_index = next(
            (i for i, _ in enumerate(automation.nodes) if not run_single_node(automation, i)),
            None,
        )

        if failure_index is None:
            return automation # every node succeeded

        goal = remaining_goal_by_node.get(
            failure_index, "Recover and complete the remaining workflow"
        )
        recovery_automation = Automation.model_validate({
            "url": automation.url,
            "parameters": {"input_parameters": {}, "generated_parameters": {}},
            "nodes": [{
                "type": "action_node",
                "interaction_action": {
                    "agentic_task": {"task": goal, "max_steps": 10, "backend": "browser_use"},
                },
            }],
        })
        run_single_node(recovery_automation, 0) # Phase 2's hook is already
                                                # active for any agentic_task,
                                                # no extra wiring needed here

        new_steps = filter_redundant(load_steps("cache.jsonl"))
        automation.nodes[failure_index] = build_node(new_steps[-1])

    raise RuntimeError(
        f"Automation still failing at a node after {MAX_HEALING_ITERATIONS} healing attempts - "
        f"needs a human look, not another automated retry."
    )

```

**Done-check:** deliberately break one field's locator in `test_automation_cached.json` (e.g. rename a `get_by_label(...)` string so it no longer matches), run `run_with_self_healing`, and confirm it detects the failing node, recovers via the scoped agentic fallback, patches only that node, and the automation succeeds on the next pass - while the other, unaffected nodes are never re-run agentically.

This loop is also the seed of the standing production mechanism described in `05_production_grade_architecture.md` §5 - there it runs continuously as a background service instead of a one-shot local script.

```

```