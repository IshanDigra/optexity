"""Reduce a raw agentic trace to the minimal set of steps worth replaying.

Two rules only, both deliberately explainable:
  1. drop steps that are not replayable as a deterministic Optexity action
  2. last-write-wins for repeated writes to the same element

The rules are intentionally not learned or clustered - this stage sits inside a pipeline whose
whole purpose is removing non-determinism, so it should not introduce any of its own.
"""

from optexity.tools.models import CachedStep

# browser-use actions that exist purely to let the agent think: bookkeeping, observation and
# scrolling. They have no Optexity interaction-action equivalent and replaying them adds latency
# without changing the outcome.
NON_REPLAYABLE_ACTIONS = frozenset(
    {
        "done",
        "wait",
        "scroll",
        "screenshot",
        "extract",
        "find_text",
        "dropdown_options",
        "evaluate",
        "read_file",
        "write_file",
        "replace_file",
    }
)

# Actions that overwrite a value rather than accumulate it, so only the final one matters.
OVERWRITING_ACTIONS = frozenset({"input", "select_dropdown"})


def load_steps(path: str) -> list[CachedStep]:
    with open(path) as f:
        return [CachedStep.model_validate_json(line) for line in f if line.strip()]


def _dedup_key(step: CachedStep) -> str:
    """Identify the element a step acted on.

    The resolved selector alone is not enough: with the role strategy it is just the ARIA role,
    so every text input on a form shares the selector "textbox" and last-write-wins would collapse
    an entire form into a single node. The accessible name is what distinguishes them.
    """
    if step.resolved_selector is None:
        return f"idx:{step.dom_index}"
    return f"{step.resolved_selector_strategy}|{step.resolved_selector}|{step.accessible_name or ''}"


def filter_redundant(steps: list[CachedStep]) -> list[CachedStep]:
    kept: list[CachedStep] = []
    position_by_element: dict[str, int] = {}

    for step in steps:
        # Only the eventual success matters; the agent's failed attempts are exploration noise.
        if not step.success:
            continue

        if step.action_name in NON_REPLAYABLE_ACTIONS:
            continue

        key = _dedup_key(step)

        if step.action_name in OVERWRITING_ACTIONS and key in position_by_element:
            kept[position_by_element[key]] = step
            continue

        position_by_element[key] = len(kept)
        kept.append(step)

    return kept
