from optexity.schema.automation import Automation
from optexity.tools.cache_to_automation import build_node
from optexity.tools.filter import filter_redundant, load_steps

MAX_HEALING_ITERATIONS = 3


def run_single_node(automation: Automation, node_index: int) -> bool:
    """Executes exactly one node of an automation and returns whether it
    succeeded. Placeholder - wire this to whatever the local dev harness
    exposes for running a subset of nodes."""
    raise NotImplementedError


def run_with_self_healing(
    automation: Automation,
    remaining_goal_by_node: dict[int, str],
) -> Automation:
    for iteration in range(MAX_HEALING_ITERATIONS):
        failure_index = next(
            (
                i
                for i, _ in enumerate(automation.nodes)
                if not run_single_node(automation, i)
            ),
            None,
        )

        if failure_index is None:
            return automation

        goal = remaining_goal_by_node.get(
            failure_index, "Recover and complete the remaining workflow"
        )
        recovery_automation = Automation.model_validate(
            {
                "url": automation.url,
                "parameters": {"input_parameters": {}, "generated_parameters": {}},
                "nodes": [
                    {
                        "type": "action_node",
                        "interaction_action": {
                            "agentic_task": {
                                "task": goal,
                                "max_steps": 10,
                                "backend": "browser_use",
                            },
                        },
                    }
                ],
            }
        )
        run_single_node(recovery_automation, 0)

        new_steps = filter_redundant(load_steps("cache.jsonl"))
        automation.nodes[failure_index] = build_node(new_steps[-1])

    raise RuntimeError(
        f"Automation still failing at a node after {MAX_HEALING_ITERATIONS} healing attempts - "
        f"needs a human look, not another automated retry."
    )
