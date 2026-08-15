"""Report latency and LLM token usage for completed runs, and diff two of them.

Automations run through the inference server, not in-process, so this reads what a run already
leaves behind rather than trying to drive one: every step writes
`<save_directory>/<task_id>/logs/step_<n>/state.json` containing `started_at`, `completed_at` and
the accumulated `token_usage` (see optexity/inference/core/logging.py).

Usage:
    python -m optexity.tools.run_and_compare                      # summarise the two latest runs
    python -m optexity.tools.run_and_compare <task_dir> [<task_dir>]
"""

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from optexity.schema.task import Task

# Where the inference server writes task output; mirrors Task.save_directory's default.
DEFAULT_SAVE_DIRECTORY = Task.model_fields["save_directory"].default


@dataclass
class RunSummary:
    task_directory: Path
    nodes: int
    elapsed_seconds: float | None
    agent_llm_calls: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    total_cost: float


def _count_agent_llm_calls(task_directory: Path) -> int:
    """Count the browser-use agent's LLM calls.

    The agent saves one `conversation_<id>_<n>.txt` per call (Agent is constructed with
    save_conversation_path=<step dir> in handle_agentic_task.py). This is the only place that usage
    is visible from outside: the agent's own token counts live on the AgentHistoryList returned by
    agent.run() and are never merged into memory.token_usage, so the token columns below report
    Optexity's LLM calls only and read 0 for an agentic run.
    """
    return len(list(task_directory.glob("logs/step_*/conversation_*.txt")))


def _latest_state(task_directory: Path) -> tuple[dict, int]:
    """The highest-numbered step's state.json holds the cumulative totals for the run."""
    states = sorted(
        task_directory.glob("logs/step_*/state.json"),
        key=lambda p: int(p.parent.name.removeprefix("step_")),
    )
    if not states:
        raise FileNotFoundError(f"No step state files under {task_directory}")
    return json.loads(states[-1].read_text()), len(states)


def summarise(task_directory: Path) -> RunSummary:
    state, node_count = _latest_state(task_directory)

    elapsed = None
    if state.get("started_at") and state.get("completed_at"):
        started = datetime.fromisoformat(state["started_at"])
        completed = datetime.fromisoformat(state["completed_at"])
        elapsed = (completed - started).total_seconds()

    usage = state.get("token_usage") or {}
    return RunSummary(
        task_directory=task_directory,
        nodes=node_count,
        elapsed_seconds=elapsed,
        agent_llm_calls=_count_agent_llm_calls(task_directory),
        input_tokens=int(usage.get("input_tokens", 0)),
        output_tokens=int(usage.get("output_tokens", 0)),
        total_tokens=int(usage.get("total_tokens", 0)),
        total_cost=float(usage.get("total_cost", 0.0)),
    )


def _format(summary: RunSummary) -> str:
    elapsed = f"{summary.elapsed_seconds:.1f}s" if summary.elapsed_seconds is not None else "unknown"
    return (
        f"  {'nodes':<22} {summary.nodes}\n"
        f"  {'elapsed':<22} {elapsed}\n"
        f"  {'agent LLM calls':<22} {summary.agent_llm_calls}\n"
        f"  {'optexity LLM tokens':<22} {summary.total_tokens} "
        f"(in {summary.input_tokens} / out {summary.output_tokens}), ${summary.total_cost:.4f}"
    )


def _recent_task_directories(save_directory: Path, count: int) -> list[Path]:
    candidates = [p for p in save_directory.iterdir() if (p / "logs").is_dir()]
    return sorted(candidates, key=lambda p: p.stat().st_mtime)[-count:]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_directories", nargs="*", type=Path)
    parser.add_argument("--save-directory", type=Path, default=DEFAULT_SAVE_DIRECTORY)
    args = parser.parse_args()

    directories = args.task_directories or _recent_task_directories(args.save_directory, 2)
    if not directories:
        parser.error(f"No task directories found under {args.save_directory}")

    summaries = [summarise(d) for d in directories]
    labels = ["AGENTIC BASELINE", "CACHED REPLAY"] if len(summaries) == 2 else [""] * len(summaries)

    for label, summary in zip(labels, summaries):
        print(f"{label} ({summary.task_directory.name})" if label else summary.task_directory.name)
        print(_format(summary))
        print()

    if len(summaries) == 2:
        baseline, cached = summaries
        print("-" * 60)
        if baseline.elapsed_seconds and cached.elapsed_seconds:
            change = (cached.elapsed_seconds - baseline.elapsed_seconds) / baseline.elapsed_seconds
            print(f"  elapsed         {baseline.elapsed_seconds:.1f}s -> {cached.elapsed_seconds:.1f}s "
                  f"({change:+.0%})")
        print(f"  agent LLM calls {baseline.agent_llm_calls} -> {cached.agent_llm_calls}")
        print()
        print(f"  {_verdict(cached)}")


def _verdict(cached: RunSummary) -> str:
    """Say plainly what the cached replay actually did.

    The three outcomes are meaningfully different, and two of them look like success if you only
    read the elapsed time: falling back to the agent is slower than the baseline, and falling back
    to Optexity's own index-prediction LLM is nearly invisible.
    """
    if cached.agent_llm_calls:
        return (
            "The cached replay still invoked the browser-use agent - a locator went stale and the "
            "agentic fallback recovered it. This is not a cached run."
        )
    if cached.total_tokens:
        return (
            f"The cached replay avoided the agent, but spent {cached.total_tokens} tokens on "
            f"Optexity's index prediction - at least one `command` failed to match and was "
            f"recovered by the LLM. Check which node in the task log."
        )
    return "The cached replay used no LLM at all."


if __name__ == "__main__":
    main()
