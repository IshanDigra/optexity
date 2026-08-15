"""Turn a filtered cache of agentic steps into a deterministic Optexity automation.

The `command` on every generated node is derived from the locator information the agent actually
resolved during its run - nothing here invents a selector.

    python -m optexity.tools.cache_to_automation
    python -m optexity.tools.cache_to_automation --cache cache.site2.jsonl --seed test_automation_site2.json
"""

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from optexity.schema.automation import Automation
from optexity.tools.filter import filter_redundant, load_steps
from optexity.tools.models import CachedStep

# browser-use's registered action names -> Optexity interaction actions.
# Deliberately narrow: an action is only listed here if a cached step carries everything the
# corresponding Optexity action needs. `send_keys` (needs a key validated against KEY_NAMES) and
# `upload_file` (needs a file path or URL) do not, so they are reported as unsupported rather than
# converted into a node that fails at replay time.
ACTION_MAP = {
    "click": "click_element",
    "input": "input_text",
    "navigate": "go_to_url",
    "select_dropdown": "select_option",
    "go_back": "go_back",
}

# Actions whose Optexity model derives from BaseAction, i.e. it is located via a `command`.
LOCATOR_BASED_ACTIONS = frozenset({"click_element", "input_text", "select_option"})

# Replay does not need the agent's thinking time. The schema default is 5s per node, which would
# otherwise dominate - and distort - the latency comparison against the agentic run.
DEFAULT_END_SLEEP_TIME = 0.5
NAVIGATION_END_SLEEP_TIME = 3.0


@dataclass(frozen=True)
class PlannedNode:
    """One cached step and the decisions made about it, so the summary and the written file
    cannot disagree."""

    step: CachedStep
    optexity_action: str
    command: str | None
    caused_navigation: bool


def _quote(value: str) -> str:
    """Escape a value for embedding in a double-quoted Python string inside a locator expression."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_command(step: CachedStep) -> str | None:
    """Build a Playwright locator expression, following Optexity's locator preference order.

    Returns None when the agent's element could not be resolved to anything reusable, in which case
    the node falls back to `prompt_instructions` at replay.

    `.first` is appended throughout: a cached selector describes the element the agent chose, and if
    it happens to match more than one node at replay time Playwright's strict mode raises instead of
    acting. Taking the first match degrades to "same element as last time" rather than failing the
    whole automation.
    """
    selector = step.resolved_selector
    if selector is None:
        return None

    strategy = step.resolved_selector_strategy

    if strategy == "role":
        return f'get_by_role("{_quote(selector)}", name="{_quote(step.accessible_name or "")}").first'
    if strategy == "label":
        return f'get_by_label("{_quote(selector)}").first'
    if strategy == "test_id":
        return f'get_by_test_id("{_quote(selector)}").first'
    if strategy == "text":
        return f'get_by_text("{_quote(selector)}").first'
    if strategy == "css":
        return f'locator("{_quote(selector)}").first'
    if strategy == "xpath":
        # Emitted as a command rather than into the node's `xpath` field. That field exists on
        # BaseAction but nothing under optexity/inference ever reads it, so a node carrying only an
        # xpath has no locator at replay and falls straight through to the LLM. browser-use reports
        # paths without a leading slash ("html/body/..."), which Playwright treats as relative.
        absolute = selector if selector.startswith("/") else f"/{selector}"
        return f'locator("xpath={_quote(absolute)}").first'

    return None


def describe(step: CachedStep, optexity_action: str) -> str:
    """Natural-language fallback, used only if the locator stops matching."""
    target = step.accessible_name or step.resolved_selector or f"element {step.dom_index}"

    if optexity_action == "input_text":
        return f'Enter "{step.value}" into the "{target}" field'
    if optexity_action == "click_element":
        return f'Click "{target}"'
    if optexity_action == "select_option":
        return f'Select "{step.value}" in "{target}"'
    return f"Perform {optexity_action} on {target}"


def plan_nodes(url: str, steps: list[CachedStep]) -> list[PlannedNode]:
    """Decide what each surviving step becomes. Single source of truth for both the generated
    automation and the summary printed alongside it."""
    steps = _drop_redundant_opening_navigation(url, steps)

    planned = []
    for index, step in enumerate(steps):
        optexity_action = ACTION_MAP.get(step.action_name)
        if optexity_action is None:
            raise ValueError(
                f"No mapping for browser-use action '{step.action_name}' - either add it to "
                f"ACTION_MAP here, or to NON_REPLAYABLE_ACTIONS in filter.py if it has no "
                f"deterministic equivalent"
            )

        # `page_url_before` is recorded per step, so a difference against the next step means this
        # one navigated. The final step has no successor to compare against.
        following = steps[index + 1] if index + 1 < len(steps) else None
        caused_navigation = (
            following is not None and step.page_url_before != following.page_url_before
        )

        planned.append(
            PlannedNode(
                step=step,
                optexity_action=optexity_action,
                command=build_command(step),
                caused_navigation=caused_navigation,
            )
        )
    return planned


def build_node(planned: PlannedNode) -> dict:
    action, step = planned.optexity_action, planned.step

    if action == "go_to_url":
        body: dict = {"url": step.value}
    elif action == "go_back":
        body = {}
    else:
        body = {
            "command": planned.command,
            "prompt_instructions": describe(step, action),
        }
        if action == "input_text":
            body["input_text"] = step.value
        elif action == "select_option":
            body["select_values"] = [step.value] if step.value else None

    return {
        "type": "action_node",
        # A step that changed the page needs time for the next one's locator to exist. The agentic
        # run absorbed this implicitly - it re-read the DOM before every action - so without it a
        # deterministic replay races the page and drops back to the LLM.
        "end_sleep_time": (
            NAVIGATION_END_SLEEP_TIME if planned.caused_navigation else DEFAULT_END_SLEEP_TIME
        ),
        "interaction_action": {action: body},
    }


def _drop_redundant_opening_navigation(url: str, steps: list[CachedStep]) -> list[CachedStep]:
    """The automation's own `url` already opens the page, so the agent's first navigation to it
    would just reload it."""
    if steps and steps[0].action_name == "navigate" and steps[0].value == url:
        return steps[1:]
    return steps


def build_automation(seed: Automation, steps: list[CachedStep], url: str | None = None) -> Automation:
    """Build the deterministic equivalent of `seed` from the steps its agentic run produced.

    `url`, `parameters` and `expected_downloads` are inherited from the seed: the cached automation
    is triggered exactly like the agentic one, so it has to declare the same parameters or the local
    override in child_process.py strips them.
    """
    url = url or seed.url
    automation_dict = {
        "url": url,
        "expected_downloads": seed.expected_downloads,
        "parameters": seed.parameters.model_dump(mode="json"),
        "nodes": [build_node(p) for p in plan_nodes(url, steps)],
    }
    # Validate against the real schema before anything reaches disk, so a malformed automation
    # fails here rather than halfway through a replay.
    return Automation.model_validate(automation_dict)


def _report(planned: list[PlannedNode], seed: Automation) -> None:
    for node in planned:
        if node.optexity_action in LOCATOR_BASED_ACTIONS:
            detail = node.command or "(no locator - will fall back to the LLM)"
        else:
            detail = node.step.value or ""
        print(f"  {node.optexity_action}: {detail}{'   [navigates]' if node.caused_navigation else ''}")

    if not seed.expected_downloads:
        return

    if any(n.optexity_action == "click_element" for n in planned):
        print(
            f"\nNOTE: the seed expects {seed.expected_downloads} download(s). The cache cannot tell "
            f"which click produced the file, so no node sets `expect_download`. If the replay "
            f"downloads nothing, set it by hand on the relevant click_element node."
        )
    else:
        print(
            f"\nWARNING: the seed expects {seed.expected_downloads} download(s) but no click was "
            f"cached - the download step was not captured."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", default="cache.jsonl")
    parser.add_argument("--out", default="test_automation_cached.json")
    parser.add_argument(
        "--seed",
        default="test_automation.json",
        help="the agentic automation this cache came from; its url, parameters and "
        "expected_downloads are inherited so the cached automation is triggered identically",
    )
    parser.add_argument("--url", help="override the seed's url")
    args = parser.parse_args()

    seed = Automation.model_validate(json.loads(Path(args.seed).read_text()))
    url = args.url or seed.url

    raw = load_steps(args.cache)
    steps = filter_redundant(raw)
    automation = build_automation(seed, steps, url=url)
    planned = plan_nodes(url, steps)

    Path(args.out).write_text(
        json.dumps(automation.model_dump(mode="json", exclude_none=True), indent=2)
    )

    print(f"{args.cache}: {len(raw)} steps -> {len(planned)} kept -> {args.out}")
    _report(planned, seed)


if __name__ == "__main__":
    main()
