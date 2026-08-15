import logging

from browser_use import Agent, BrowserSession, Tools

from optexity.inference.infra.browser import Browser
from optexity.inference.models import normalize_model
from optexity.inference.models.chat_litellm import build_agent_llm
from optexity.schema.actions.interaction_action import (
    AgenticTask,
    CloseOverlayPopupAction,
)
from optexity.schema.memory import Memory
from optexity.schema.task import Task

logger = logging.getLogger(__name__)

# Actions whose effect cannot be expressed as a deterministic Optexity interaction action.
#
# `evaluate` runs arbitrary JavaScript. An agent that reaches for it can change page state without
# ever touching an element, so the run leaves no locator behind to replay - the work becomes
# invisible to anything reconstructing the workflow from what the agent did. Excluding it forces the
# agent to use real clicks and typing, which do convert.
#
# Note `screenshot` is deliberately NOT excluded: agentic_task defaults to use_vision=False, so
# taking a screenshot is often how the agent orients itself. It is observation rather than action,
# so it costs a little latency but nothing downstream.
NON_REPLAYABLE_TOOLS = ["evaluate"]


async def handle_agentic_task(
    agentic_task_action: AgenticTask | CloseOverlayPopupAction,
    task: Task,
    memory: Memory,
    browser: Browser,
):

    if agentic_task_action.backend == "browser_use":

        if isinstance(agentic_task_action, CloseOverlayPopupAction):
            tools = Tools(
                exclude_actions=[
                    "search",
                    "navigate",
                    "go_back",
                    "upload_file",
                    "scroll",
                    "find_text",
                    "send_keys",
                    "evaluate",
                    "switch",
                    "close",
                    "extract",
                    "dropdown_options",
                    "select_dropdown",
                    "write_file",
                    "read_file",
                    "replace_file",
                ]
            )
        else:
            tools = Tools(exclude_actions=NON_REPLAYABLE_TOOLS)
        llm = build_agent_llm(normalize_model(task.llm_provider, task.llm_model_name))
        browser_session = BrowserSession(
            cdp_url=browser.cdp_url, keep_alive=agentic_task_action.keep_alive
        )

        step_directory = (
            task.logs_directory / f"step_{str(memory.automation_state.step_index)}"
        )
        step_directory.mkdir(parents=True, exist_ok=True)

        agent = Agent(
            task=agentic_task_action.task,
            llm=llm,
            browser_session=browser_session,
            use_vision=agentic_task_action.use_vision,
            tools=tools,
            calculate_cost=True,
            save_conversation_path=step_directory,
        )
        logger.debug(f"Starting browser session for agentic task {browser.cdp_url} ")
        await agent.browser_session.start()
        logger.debug(f"Finally running agentic task on browser_use {browser.cdp_url} ")
        history = await agent.run(max_steps=agentic_task_action.max_steps)
        logger.debug(f"Agentic task completed on browser_use {browser.cdp_url} ")

        agent.stop()
        if agent.browser_session:
            await agent.browser_session.stop()
            await agent.browser_session.reset()

        return history

    elif agentic_task_action.backend == "browserbase":
        raise NotImplementedError("Browserbase is not supported yet")

    return None
