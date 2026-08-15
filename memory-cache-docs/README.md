# Memory / Caching Layer for `agentic_task`

Run an `agentic_task` once, record what the agent actually did, discard the exploration, and emit a
deterministic Optexity automation that replays the same work with no LLM in the loop.

**Measured on roboform:** 27.7s → 16.2s, **2 agent LLM calls → 0**.

This work spans two repos:

- **optexity** (this repo) — the filter, converter, inspection and comparison tooling, plus the
  local-development override.
- **browser-use** — the caching hook on `Registry.execute_action`, on the
  `feature/memory-cache-layer` branch, which is based on the **`optexity` branch** (not `main`).

| Doc | What it answers |
|---|---|
| [01_what_i_implemented.md](01_what_i_implemented.md) | What was built, how the pieces fit, and what changed once it was actually run |
| [02_design_decisions_and_tradeoffs.md](02_design_decisions_and_tradeoffs.md) | Every non-obvious choice, the alternative rejected, and why |
| [03_trial_run_results.md](03_trial_run_results.md) | The evidence — real caches, generated automations, measured numbers, honest caveats |
| [04_future_production_considerations.md](04_future_production_considerations.md) | What this is not yet: there is no cache *lookup* step. What production needs |
| [05_setup_guide_feedback.md](05_setup_guide_feedback.md) | Setup notes: two things that fail silently, worth adding to the brief |

## Try it

```bash
export PYTHONPATH=<path>/browser-use:<path>/optexity     # see 05 for why

# 1. agentic baseline - the hook writes cache.jsonl
OPTEXITY_LOCAL_AUTOMATION=test_automation.json optexity inference --port 9000 --child_process_id 0

# 2. see what was captured
python -m optexity.tools.inspect_cache

# 3. convert to a deterministic automation
python -m optexity.tools.cache_to_automation

# 4. replay it
OPTEXITY_LOCAL_AUTOMATION=test_automation_cached.json optexity inference --port 9000 --child_process_id 0

# 5. compare
python -m optexity.tools.run_and_compare
```

Tests: `pytest optexity/tools/test_cache_to_automation.py` (18 cases, each one a bug that actually
occurred).
