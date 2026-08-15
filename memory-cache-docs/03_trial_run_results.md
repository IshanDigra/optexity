# Trial Run Results

Everything below is copied from real runs. The cache is the evidence that the generated locators were
*derived* rather than written by hand — every `command` in the automation traces back to a
`resolved_selector` recorded by the hook during the agentic run.

---

## Site 1 — roboform.com/filling-test-all-fields

**Seed** (`test_automation.json`) — one agentic node:

> fill the full name as Ishan, address line one as xyz and line 2 as abc, city as SF

### The cache the hook produced

`cache.jsonl`, one JSON line per action the agent dispatched:

```jsonl
{"step_index":0,"action_name":"input","dom_index":107,"resolved_selector":"input[name='04fullname']","resolved_selector_strategy":"css","accessible_name":null,"value":"Ishan","page_url_before":"https://www.roboform.com/filling-test-all-fields","success":true,"timestamp":1786821542.6375659}
{"step_index":1,"action_name":"input","dom_index":110,"resolved_selector":"input[name='10address1']","resolved_selector_strategy":"css","accessible_name":null,"value":"xyz","page_url_before":"https://www.roboform.com/filling-test-all-fields","success":true,"timestamp":1786821542.787314}
{"step_index":2,"action_name":"input","dom_index":111,"resolved_selector":"input[name='11address2']","resolved_selector_strategy":"css","accessible_name":null,"value":"abc","page_url_before":"https://www.roboform.com/filling-test-all-fields","success":true,"timestamp":1786821542.9415581}
{"step_index":3,"action_name":"input","dom_index":112,"resolved_selector":"input[name='13adr_city']","resolved_selector_strategy":"css","accessible_name":null,"value":"SF","page_url_before":"https://www.roboform.com/filling-test-all-fields","success":true,"timestamp":1786821543.090858}
{"step_index":4,"action_name":"done","dom_index":null,"resolved_selector":null,"resolved_selector_strategy":"unknown","accessible_name":null,"value":"Successfully filled the full name as Ishan, address line one as xyz, address line 2 as abc, and city as SF on the RoboForm test form.","page_url_before":"https://www.roboform.com/filling-test-all-fields","success":true,"timestamp":1786821546.5883641}
```

Note `dom_index` 107/110/111/112 is recorded for debugging but **never replayed** — those numbers are
an artifact of one DOM snapshot. `resolved_selector` is what survives.

As a table (`python -m optexity.tools.inspect_cache`):

```
  #  action           strategy  selector                                   value                ok
----------------------------------------------------------------------------------------------------
  0  input            css       input[name='04fullname']                   Ishan                y
  1  input            css       input[name='10address1']                   xyz                  y
  2  input            css       input[name='11address2']                   abc                  y
  3  input            css       input[name='13adr_city']                   SF                   y
  4  done             unknown                                              Successfully filled  y

5 recorded, 4 replayable (1 dropped as failed or non-replayable)
Every replayable step resolved to a distinct locator - ready to convert.
```

The agent solved this in one pass, so there is little exploration to discard — only `done`. The
`input[name='…']` selectors come from roboform's markup; nothing in the task string mentions them.

### The automation generated from it

`test_automation_cached.json` — 4 nodes, one per field. Each `command` is the `resolved_selector`
from the corresponding cache line, and each `input_text` is that line's `value`:

```json
{
  "url": "https://www.roboform.com/filling-test-all-fields",
  "expected_downloads": 0,
  "parameters": { "input_parameters": {}, "secure_parameters": {}, "generated_parameters": {} },
  "nodes": [
    {
      "type": "action_node",
      "end_sleep_time": 0.5,
      "interaction_action": {
        "max_tries": 10,
        "max_timeout_seconds_per_try": 1.0,
        "verify_before_step": true,
        "input_text": {
          "command": "locator(\"input[name='04fullname']\").first",
          "prompt_instructions": "Enter \"Ishan\" into the \"input[name='04fullname']\" field",
          "input_text": "Ishan",
          "fill_or_type": "fill",
          "click_before_input": true,
          "skip_command": false,
          "skip_prompt": false,
          "assert_locator_presence": false,
          "is_slider": false,
          "press_enter": false
        }
      },
      "before_sleep_time": 0.0,
      "expect_new_tab": false,
      "max_new_tab_wait_time": 0.0
    }
  ]
}
```

The remaining three nodes are identical in shape:

| # | `command` | `input_text` |
|---|---|---|
| 1 | `locator("input[name='04fullname']").first` | `Ishan` |
| 2 | `locator("input[name='10address1']").first` | `xyz` |
| 3 | `locator("input[name='11address2']").first` | `abc` |
| 4 | `locator("input[name='13adr_city']").first` | `SF` |

`end_sleep_time` is 0.5 rather than the schema default of 5.0 — otherwise a four-node replay would
spend 20s asleep and the latency comparison would be measuring `time.sleep`. No step changed the
page URL, so none qualified for the longer navigation settle time.

### Measured

```
AGENTIC BASELINE                    CACHED REPLAY
  nodes                  2            nodes                  5
  elapsed                27.7s        elapsed                16.2s
  agent LLM calls        2            agent LLM calls        0
  optexity LLM tokens    0            optexity LLM tokens    0

  elapsed         27.7s -> 16.2s (-41%)
  agent LLM calls 2 -> 0
  The cached replay used no LLM at all.
```

Form filled identically both times.

### Bonus — LLM-assisted converter on the same cache

Live against `gemini/gemini-3.5-flash-lite`:

```
node counts   : 4 vs 4 -> True
commands match: True
  SAME  locator("input[name='04fullname']").first
  SAME  locator("input[name='10address1']").first
  SAME  locator("input[name='11address2']").first
  SAME  locator("input[name='13adr_city']").first
```

---

## Site 2 — ishandigra.github.io/MagicPouch

Multi-step by requirement: open settings, edit a field, click Connect, download a backup.
`expected_downloads: 1`.

> Wait for the page to finish loading. Open the Settings section clicking in the top left corner.
> Change the cloud sync key to 'ishan', then click Connect and save it. Finally, download the backup
> file.

### The cache — and why it was unusable

```
  #  action           strategy  selector                                   value                ok
  0-4  screenshot     unknown                                                                   y
  5  evaluate         unknown                                              (blank)              y
  6  click            xpath     html/body/header/div/div[1]/div[1]                              y
  7  evaluate         unknown                                              (blank)              y
  8  evaluate         unknown                                              (blank)              y
  9  evaluate         unknown                                              (blank)              y
 10  click            role      button ( Backup)                                                y
 11  done             unknown                                              Successfully opened  y

12 recorded, 2 replayable (10 dropped as failed or non-replayable)
```

The agent completed the task — its own summary read *"Successfully opened the settings, updated the
cloud sync key to 'ishan', connected/saved, and downloaded the…"* — but did the substantive work in
**JavaScript** via `evaluate`, which touches no element and so leaves no locator behind. The
converted automation contained 2 of roughly 6 real steps:

```
click_element: locator("xpath=/html/body/header/div/div[1]/div[1]").first
click_element: get_by_role("button", name=" Backup").first
```

The replay failed on the first node and the agentic fallback took over:

```
  elapsed         88.4s -> 96.4s (+9%)
  agent LLM calls 12 -> 12
  The cached replay still invoked the browser-use agent - a locator went stale
  and the agentic fallback recovered it. This is not a cached run.
```

**That +9% is not a measurement of caching.** It is the cost of failing deterministically and then
doing the full agentic run anyway. Three distinct bugs sat behind it:

1. `evaluate`'s payload lives in a `code` parameter the hook never read, so those rows logged blank.
2. The one usable click resolved to xpath, which the converter put in the node's `xpath` field — a
   field nothing under `optexity/inference` reads, so that node had **no locator at all**.
3. No settle time after a step that changes the page.

All three are fixed (see [02_design_decisions_and_tradeoffs.md](02_design_decisions_and_tradeoffs.md)
§3 for the xpath field, §4 for `evaluate`, and "The rest" for navigation settle time). `evaluate` is now
excluded from the agent's toolset, so the work has to go through real clicks and typing, which the
hook can record.

**This site has not been re-run since those fixes**, so it is documented here as a diagnosed failure
rather than a second success. The fixes are covered by tests, but the end-to-end confirmation is
outstanding.

---

## Reading the numbers honestly

**`optexity LLM tokens` shows 0 for the agentic baseline, and that is correct, not a bug.** It counts
Optexity's own index-prediction and input-prediction calls, which fire only when a node's `command`
fails to match — an agentic run has no such nodes. browser-use's usage lives on the
`AgentHistoryList` returned by `agent.run()` and is never merged into `memory.token_usage`, so it is
invisible to that counter. That is why `agent LLM calls` is counted separately, from the
`conversation_*.txt` files the agent writes.

**The headline number is `2 LLM calls → 0`, not the −41%.** Both runs pay browser startup, and the
cached run adds 0.5s settle time per node — 2s of its 16.2s. The latency gain is real but dragged
down by fixed costs the caching layer cannot remove.

**Roboform understates the ceiling.** Its baseline needed only 2 LLM calls because the agent solved a
single-page form in one shot; the MagicPouch baseline needed 12 for a multi-page flow. The saving
scales with how much reasoning the task required.

## Reproducing

```bash
source Assignment/env.sh
python -m optexity.tools.inspect_cache --cache cache.roboform.jsonl
python -m optexity.tools.cache_to_automation \
    --cache cache.roboform.jsonl --seed test_automation.json --out /tmp/check.json
python -m optexity.tools.run_and_compare
```

Caches and generated automations are gitignored as run artifacts.
`Assignment/07_live_testing_runbook.md` is the step-by-step procedure with the PASS condition for
each phase.
