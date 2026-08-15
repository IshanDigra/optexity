# Trial Run Results

Everything below is copied from real runs. The caches are the evidence that the generated locators
were *derived* rather than written by hand — each `command` traces to a row in the cache, and each
cache row was recorded by the hook during the agentic run.

---

## Site 1 — roboform.com/filling-test-all-fields

**Seed** (`test_automation.json`) — one agentic node:

> fill the full name as Ishan, address line one as xyz and line 2 as abc, city as SF

### What the hook recorded

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

The agent solved this cleanly, so there is little exploration to discard — only `done`. The
`input[name='…']` selectors come from roboform's markup, not from the task string.

### Generated automation

`5 steps → 4 kept`, one node per field:

```
locator("input[name='04fullname']").first   <- 'Ishan'
locator("input[name='10address1']").first   <- 'xyz'
locator("input[name='11address2']").first   <- 'abc'
locator("input[name='13adr_city']").first   <- 'SF'
```

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

### Bonus — LLM-assisted converter, same cache

Run live against `gemini/gemini-3.5-flash-lite`:

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

**Seed** (`test_automation_site2.json`, `expected_downloads: 1`):

> Wait for the page to finish loading. Open the Settings section clicking in the top left corner.
> Change the cloud sync key to 'ishan', then click Connect and save it. Finally, download the backup
> file.

### First attempt — failed, and worth reading

```
  5  evaluate     (blank)
  6  click        xpath  html/body/header/div/div[1]/div[1]
  7  evaluate     (blank)
  8  evaluate     (blank)
  9  evaluate     (blank)
 10  click        role   button ( Backup)
```

The agent completed the task — its own summary read *"Successfully opened the settings, updated the
cloud sync key to 'ishan', connected/saved, and downloaded the…"* — but did the substantive work in
**JavaScript** via `evaluate`, which touches no element and leaves no locator. The converted
automation contained 2 of ~6 real steps.

The replay therefore failed on the first node and the agentic fallback took over:

```
  elapsed         88.4s -> 96.4s (+9%)
  agent LLM calls 12 -> 12
  The cached replay still invoked the browser-use agent - a locator went stale
  and the agentic fallback recovered it. This is not a cached run.
```

**That +9% is not a measurement of caching.** It is the cost of failing deterministically and then
doing the full agentic run anyway. Three distinct bugs sat behind it:

1. `evaluate`'s payload is in a `code` parameter the hook never read, so those rows logged blank.
2. The one usable click resolved to xpath, which the converter put in the node's `xpath` field —
   a field nothing reads, so that node had no locator at all.
3. No settle time after navigation.

All three are fixed (see `02_design_decisions_and_tradeoffs.md` §4, §6, §8). `evaluate` is now
excluded from the agent's toolset, so the work must go through real clicks and typing, which the
hook can record.

---

## Reading the numbers honestly

**`optexity LLM tokens` shows 0 for the agentic baseline, and that is correct, not a bug.** It counts
Optexity's own index-prediction and input-prediction calls, which fire only when a node's `command`
fails to match. An agentic run has no such nodes. browser-use's usage lives on the
`AgentHistoryList` returned by `agent.run()` and is never merged into `memory.token_usage`, so it is
invisible to that counter — which is why `agent LLM calls` is counted separately, from the
`conversation_*.txt` files the agent writes.

**The headline number is `2 LLM calls → 0`, not the −41%.** Both runs pay browser startup, and the
cached run adds 0.5s settle time per node — 2s of its 16.2s. The latency gain is real but dragged
down by fixed costs the caching layer cannot remove.

**Roboform understates the ceiling.** The baseline needed only 2 LLM calls because the agent solved
a single-page form in one shot. The MagicPouch baseline needed 12 for a multi-page flow. The saving
scales with how much reasoning the task required, so the more complex the workflow, the larger the
gap.

## Reproducing

```bash
source Assignment/env.sh
.venv/bin/python -m optexity.tools.inspect_cache --cache cache.roboform.jsonl
.venv/bin/python -m optexity.tools.cache_to_automation \
    --cache cache.roboform.jsonl --seed test_automation.json --out /tmp/check.json
.venv/bin/python -m optexity.tools.run_and_compare
```

The caches and generated automations are gitignored as run artifacts. `Assignment/07_live_testing_runbook.md`
is the step-by-step procedure, including how each PASS condition was checked.
