import asyncio
import time
import uuid
from datetime import datetime, timezone

from optexity.schema.automation import Automation
from optexity.schema.task import Task
from optexity.inference.core.run_automation import run_automation


class LLMCallCounter:
    def __init__(self):
        self.count = 0

    def reset(self):
        self.count = 0

    def increment(self):
        self.count += 1


async def run_automation_locally(automation_path: str):
    import json
    with open(automation_path) as f:
        data = json.load(f)

    automation = Automation.model_validate(data)
    task = Task(
        task_id=str(uuid.uuid4()),
        user_id="local_user",
        recording_id="local_recording",
        automation=automation,
        input_parameters={},
        unique_parameter_names=[],
        created_at=datetime.now(timezone.utc),
        status="queued",
    )
    await run_automation(task, 0)


async def run_and_measure(automation_path: str, llm_call_counter: LLMCallCounter) -> dict:
    start = time.time()
    llm_call_counter.reset()
    try:
        await run_automation_locally(automation_path)
    except Exception as e:
        print(f"Error running automation: {e}")
    return {
        "elapsed_seconds": time.time() - start,
        "llm_calls": llm_call_counter.count,
    }


if __name__ == "__main__":
    import os
    llm_call_counter = LLMCallCounter()

    agentic_result = None
    if os.path.exists("test_automation.json"):
        agentic_result = asyncio.run(run_and_measure("test_automation.json", llm_call_counter))

    cached_result = None
    if os.path.exists("test_automation_cached.json"):
        cached_result = asyncio.run(run_and_measure("test_automation_cached.json", llm_call_counter))

    print(f"Agentic: {agentic_result}")
    print(f"Cached: {cached_result}")
