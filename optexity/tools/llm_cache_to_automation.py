"""LLM-assisted alternative to the hand-written converter.

Kept alongside `cache_to_automation.py` rather than replacing it: that module stays the baseline
this output is diffed against, so a hallucinated or dropped node is visible instead of silently
shipped. See `build_and_diff`.
"""

import json
import os

from litellm import completion

from optexity.schema.automation import Automation
from optexity.tools.models import CachedStep

DEFAULT_MODEL = os.environ.get("LLM_MODEL", "gemini/gemini-3.5-flash-lite")

SYSTEM_PROMPT = """You convert a list of recorded browser actions into a single
Optexity Automation JSON object. Return ONLY valid JSON matching the provided
JSON schema - no prose, no markdown fences.

Map each step's `action_name` (a browser-use action) to an Optexity interaction action:
  click           -> click_element
  input           -> input_text        (put the step's `value` in the `input_text` field)
  navigate        -> go_to_url         (put the step's `value` in the `url` field)
  select_dropdown -> select_option     (put the step's `value` in `select_values` as a list)
  go_back         -> go_back
Skip any other action - it is agent bookkeeping with no deterministic equivalent.

When choosing a `command` locator, follow this preference order (from Optexity's own
locator docs): role > label > test_id > text > css > xpath. Use the step's
`resolved_selector_strategy` field to pick the right form, and append `.first` so a
selector matching several elements does not trip Playwright's strict mode:
  role    -> get_by_role("<resolved_selector>", name="<accessible_name>").first
  label   -> get_by_label("<resolved_selector>").first
  test_id -> get_by_test_id("<resolved_selector>").first
  text    -> get_by_text("<resolved_selector>").first
  css     -> locator("<resolved_selector>").first
  xpath   -> locator("xpath=<resolved_selector>").first, ensuring the path starts with "/"

NEVER put anything in a node's `xpath` field. That field exists on the schema but nothing in
the execution engine reads it, so a node carrying only an xpath has no locator at replay and
falls straight through to the LLM - the opposite of the point of this conversion.

Give every located action a `prompt_instructions` describing what it does. The schema does
not require it, but it is the fallback used when the locator stops matching, so a node
without one has no way to recover.

Set `end_sleep_time` to 0.5 on every node, except a node whose `page_url_before` differs from
the next step's, which navigated and should get 3.0 so the next locator has time to exist.
The schema default of 5 seconds is agent thinking time a deterministic replay does not need."""


def build_messages(url: str, steps: list[dict]) -> list[dict]:
    schema = Automation.model_json_schema()
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": json.dumps(
                {
                    "url": url,
                    "target_json_schema": schema,
                    "cached_steps": steps,
                }
            ),
        },
    ]


def llm_build_automation(
    url: str, steps: list[dict], max_repair_attempts: int = 3, model: str = DEFAULT_MODEL
) -> Automation:
    messages = build_messages(url, steps)

    for _ in range(max_repair_attempts):
        response = completion(
            model=model,
            messages=messages,
            api_key=os.environ.get("LLM_MODEL_API_KEY"),
            response_format={"type": "json_object"},
        )
        raw_json = response.choices[0].message.content

        try:
            return Automation.model_validate_json(raw_json)
        except Exception as validation_error:
            # Feed the exact validation error back rather than retrying blind.
            messages.append({"role": "assistant", "content": raw_json})
            messages.append(
                {
                    "role": "user",
                    "content": f"That failed schema validation: {validation_error}.\n"
                    f"Return corrected JSON only, same rules as before.",
                }
            )

    raise RuntimeError(
        f"LLM failed to produce a schema-valid Automation after {max_repair_attempts} attempts"
    )


def _commands(automation: Automation) -> list[str | None]:
    """The `command` of every locator-based node, in order."""
    commands = []
    for node in automation.nodes:
        action = getattr(node, "interaction_action", None)
        if action is None:
            continue
        for name in ("click_element", "input_text", "select_option"):
            if (body := getattr(action, name, None)) is not None:
                commands.append(body.command)
    return commands


def build_and_diff(seed: Automation, filtered_steps: list[CachedStep]) -> dict:
    """Run the deterministic converter and the LLM-assisted one on the same cache and report where
    they disagree.

    The deterministic converter is the source of truth until the LLM path has earned trust: without
    a baseline to diff against there is no way to notice that the model dropped a node or invented
    a selector, since both outputs are schema-valid by construction.
    """
    from optexity.tools.cache_to_automation import build_automation

    baseline = build_automation(seed, filtered_steps)
    llm_generated = llm_build_automation(seed.url, [s.model_dump() for s in filtered_steps])

    baseline_commands = _commands(baseline)
    llm_commands = _commands(llm_generated)

    return {
        "baseline_node_count": len(baseline.nodes),
        "llm_node_count": len(llm_generated.nodes),
        "node_count_matches": len(baseline.nodes) == len(llm_generated.nodes),
        "commands_match": baseline_commands == llm_commands,
        "baseline_commands": baseline_commands,
        "llm_commands": llm_commands,
        "baseline": baseline,
        "llm_generated": llm_generated,
    }
