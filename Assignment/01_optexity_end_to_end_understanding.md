# Optexity: End-to-End Understanding

This is a narrative walkthrough, not a raw dump. It's built from the doc files in `Work_Items/EngHub Hackathon/Optexity/` plus the existing codebase digest at `Work_Items/EngHub Hackathon/optexity_codebase_understand.md` (treated as ground truth per a real prior repo read - file sizes, license text, and headers in that file are genuine, not fabricated). Where a claim comes from the codebase digest rather than the public docs, it's called out explicitly.

## 1. What Optexity is, in one paragraph

Optexity is a browser-automation platform: you record or hand-author a **declarative automation** (a JSON document), Optexity's inference layer replays it against a real Chromium/Chrome browser via Playwright, and - for the parts of a workflow that are too unpredictable to describe declaratively (unstable layouts, popups, CAPTCHAs) - it can delegate a single step to an AI agent (`agentic_task`, backed by `browser_use`) that reasons its way through instead of following a fixed locator.

## 2. The end-to-end flow

```
Record (Chrome extension) or hand-write JSON
    |
    v
Automation JSON stored on the dashboard (dashboard.optexity.com)
    |
    v
Inference request (local child-process server, or
inference-api.optexity.com in the cloud)
    |
    v
Automation is replayed node-by-node against a real browser
    |-- deterministic nodes -> direct Playwright calls (fast, no LLM cost)
    `-- agentic_task nodes -> browser_use agent loop (LLM reasoning, costs tokens/time)
    |
    v
Tasks tab + Task Analytics populated; callbacks fire if configured
```

The Setup section of `Engcon Hackathon goal.md` walks this exact path manually once (sign in, record, run, verify Tasks/Analytics populate) before any development starts.

## 3. The automation schema

Verified against `Optexity/Building Automations/automation structre.md`:

```
Automation
|-- url                          # starting point
|-- browser_channel              # "chromium" (default) | "chrome"
|-- os_emulation                 # "windows" | "linux" | null
|-- max_retries                  # total run attempts (default 1)
|-- expected_downloads           # files to wait for
|-- reuse_page_if_already_on_url # skip nav if a dedicated browser is already there
|-- parameters
|   |-- input_parameters         # provided before execution
|   |-- secure_parameters        # e.g. 1Password-backed secrets
|   `-- generated_parameters     # extracted during execution
|-- nodes[]                      # ordered list of:
    |-- action_node              # single atomic action
    |-- for_loop_node            # iterate over values or locator matches
    `-- if_else_node             # conditional branch
```

An `action_node` holds **exactly one** of: `interaction_action`, `extraction_action`, `assertion_action`, `python_script_action`, or `sleep_action` (per `Optexity/Building Automations/action node.md`), plus optional timing knobs (`before_sleep_time`, `end_sleep_time`, `expect_new_tab`).

This schema is a **Pydantic model** on the Optexity side (`Automation` - referenced directly in the goal doc's local-dev override snippet as `Automation.model_validate(automation)`), which is exactly what the converter script in `02_implementation_plan.md` reuses to self-validate the automation it generates from a cache.

## 4. Interaction actions (the deterministic vocabulary)

Verified against `Optexity/Actions Types/interaction actions.md`. These are the action types the caching layer's output needs to target:

| Action | Purpose |
|---|---|
| `click_element` | click buttons/links/elements |
| `input_text` | type into text fields |
| `select_option` | choose from a dropdown |
| `check` | check/uncheck a checkbox |
| `upload_file` | upload a local file or one fetched from a URL |
| `go_to_url` / `go_back` | navigation |
| `close_tabs_until` | tab management |
| `download_url_as_pdf` | save current/other page as PDF |
| `key_press` | keyboard input |
| `agentic_task` | the AI-agent fallback this whole hackathon is about reducing reliance on |
| `close_overlay_popup` | specialized agentic helper for dismissing overlays |

All element-targeting actions share a common contract:

```json
{
  "command": "get_by_role(\"button\", name=\"Submit\")",
  "xpath": null,
  "prompt_instructions": "Click the submit button",
  "skip_prompt": false,
  "assert_locator_presence": false,
  "max_tries": 10,
  "max_timeout_seconds_per_try": 1.0
}
```

`command` (a Playwright locator expression) or `xpath` is used for deterministic, zero-LLM-token element finding; `prompt_instructions` is a required natural-language fallback used only if the locator fails. This dual design - deterministic-first, LLM-fallback-second - is exactly the pattern the hackathon asks us to reproduce for whole **sequences** of steps, not just single elements.

## 5. Locator strategy (directly reused later)

Verified against `Optexity/advance/locators.md`. Optexity's own recommended preference order:

```
1. get_by_role(...)       - role + accessible name (most resilient)
2. get_by_label(...)      - form fields
3. get_by_test_id(...)    - data-testid
4. get_by_text(...)       - unique visible text
5. locator("css...")      - unique id/class
6. xpath                  - complex traversal, more fragile
7. prompt_instructions    - dynamic/variable elements, LLM fallback
```

`02_implementation_plan.md`'s cache-to-automation converter walks this exact preference order when deciding what `command` string to emit for a cached step, rather than inventing its own scheme.

## 6. Agentic tasks (what we're building a memory layer for)

Verified against `Optexity/Actions Types/agentic tasks.md`:

```json
{
  "interaction_action": {
    "agentic_task": {
      "task": "Navigate to settings and enable two-factor authentication",
      "max_steps": 15,
      "backend": "browser_use",
      "use_vision": false,
      "keep_alive": true
    }
  }
}
```

`backend` can be `"browser_use"` or `"browserbase"`; the hackathon is scoped to `browser_use`. `max_steps` bounds how many actions the agent may take - the docs' own guidance (3-5 for simple, 10-15 for medium, 20-30 for complex) is a useful sanity check when picking `max_steps` for the roboform baseline task, which the goal doc sets at `15`.

Optexity's own best-practice list already states the philosophy this hackathon operationalizes: **"Start with static [actions], use agentic only where needed"** and **"Review execution logs, refine task descriptions based on results."** The memory/caching layer is essentially automating that manual "review logs and convert to static" step.

## 7. Local development loop

Because automations normally live in Optexity's database (no local access for a hackathon participant), the goal doc provides an override: add a few lines to `optexity/inference/child_process.py` (after line 575) that load `test_automation.json` from disk and force-assign it onto the task before execution, bypassing the DB lookup entirely. This is the mechanism used to iterate on `test_automation.json` -> `test_automation_cached.json` locally against `https://www.roboform.com/filling-test-all-fields` without needing server-side automation edits per iteration.

## 8. Codebase architecture (from `optexity_codebase_understand.md`)

The full file-by-file digest lives in `optexity_codebase_understand.md` (2420 lines) - this is a summary of its shape, not a replacement for it:

- **License/packaging**: MIT, package `optexity` at version `0.1.5.134`, depends on `optexity-browser-use>=0.9.5` - confirming the browser-use dependency is a **named, versioned fork**, not just "based on browser-use."
- **`pyrightconfig.json`** references a sibling path `../browser-use` - confirming the intended local dev layout is two sibling clones (`optexity/` and `browser-use/`), exactly matching the goal doc's fork-both-repos instructions.
- **Core modules** (per the digest): `schema/` (the `Automation` Pydantic model and node/action types described in Sections 3-4 above), `inference/` (the child-process server and execution engine, including `optexity/inference/child_process.py`), and an agentic-fallback code path that's how `agentic_task` gets from schema to an actual `browser_use` agent invocation.
- For exact class/function signatures, treat `optexity_codebase_understand.md` as the primary source - this document only orients you to which section of it to open.

## 9. What this means for the hackathon

Everything the memory layer needs to produce is already a first-class, documented target: a list of `action_node`s using `input_text`/`click_element` with a `command` built per the locator preference order above, plus a required `prompt_instructions`. Nothing about the **output format** is ambiguous - the hard part (covered in `02_implementation_plan.md`) is entirely on the **input** side: getting a clean, deduplicated log of what `browser_use` actually did during one agentic run.