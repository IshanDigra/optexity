"""Print a recorded agentic run as a readable table.

This is the step that shows the generated automation's locators were *derived* from what the agent
actually did, rather than written by hand. It also flags the two things that make a cache unusable:
steps whose element could not be resolved to a locator, and duplicate locators that cannot be told
apart on replay.

    python -m optexity.tools.inspect_cache
    python -m optexity.tools.inspect_cache --cache cache.roboform.jsonl
"""

import argparse
from collections import Counter

from optexity.tools.filter import NON_REPLAYABLE_ACTIONS, load_steps


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", default="cache.jsonl")
    args = parser.parse_args()

    steps = load_steps(args.cache)
    if not steps:
        print(f"{args.cache} is empty - the agent recorded nothing.")
        return

    print(f"{'#':>3}  {'action':<16} {'strategy':<9} {'selector':<42} {'value':<20} ok")
    print("-" * 100)
    for step in steps:
        selector = step.resolved_selector or ""
        name = f" ({step.accessible_name})" if step.accessible_name else ""
        print(
            f"{step.step_index:>3}  {step.action_name:<16} {step.resolved_selector_strategy:<9} "
            f"{(selector + name)[:42]:<42} {str(step.value or '')[:20]:<20} "
            f"{'y' if step.success else 'n'}"
        )

    replayable = [s for s in steps if s.success and s.action_name not in NON_REPLAYABLE_ACTIONS]
    unresolved = [s for s in replayable if s.resolved_selector_strategy == "unknown"]
    locators = Counter(
        (s.resolved_selector_strategy, s.resolved_selector, s.accessible_name) for s in replayable
    )
    ambiguous = [key for key, count in locators.items() if count > 1]

    print()
    print(f"{len(steps)} recorded, {len(replayable)} replayable "
          f"({len(steps) - len(replayable)} dropped as failed or non-replayable)")

    if unresolved:
        print(f"\n{len(unresolved)} replayable step(s) have NO resolved locator "
              f"(strategy 'unknown'): {[s.step_index for s in unresolved]}")
        print("These convert to a node with no command, so replay falls back to the LLM.")

    if ambiguous:
        print(f"\n{len(ambiguous)} locator(s) appear on more than one step: {ambiguous}")
        print("If those were meant to be different elements, they will collapse into one node.")

    if not unresolved and not ambiguous:
        print("\nEvery replayable step resolved to a distinct locator - ready to convert.")


if __name__ == "__main__":
    main()
