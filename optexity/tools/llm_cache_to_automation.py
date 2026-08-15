import json

from litellm import completion

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
    url: str, steps: list[dict], max_repair_attempts: int = 3
) -> Automation:
    messages = build_messages(url, steps)

    for attempt in range(max_repair_attempts):
        response = completion(
            model="gpt-4o",
            messages=messages,
            response_format={"type": "json_object"},
        )
        raw_json = response.choices[0].message.content

        try:
            return Automation.model_validate_json(raw_json)
        except Exception as validation_error:
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


def build_and_diff(url: str, filtered_steps: list) -> dict:
    """Runs both the deterministic Phase 4 converter and the LLM-assisted
    converter on the same input, and reports where they disagree - the
    baseline is the source of truth until the LLM path has proven itself."""
    from optexity.tools.cache_to_automation import build_automation

    baseline = build_automation(url, filtered_steps)
    llm_generated = llm_build_automation(
        url, [s.model_dump() for s in filtered_steps]
    )

    return {
        "baseline_node_count": len(baseline.nodes),
        "llm_node_count": len(llm_generated.nodes),
        "node_count_matches": len(baseline.nodes) == len(llm_generated.nodes),
        "baseline": baseline,
        "llm_generated": llm_generated,
    }
