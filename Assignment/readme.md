# Assignment: Browser-Use Memory/Caching Layer

## The goal, in three sentences

Optexity replays declarative automations deterministically, but falls back to an LLM-driven `browser_use` agent (`agentic_task`) for steps too unpredictable to hard-code — and every agentic run re-derives its plan from scratch at full LLM cost. This plan builds a memory layer: run an agentic task once, cache the steps `browser_use` actually took, filter out redundant/failed exploration, and convert the rest into a deterministic Optexity automation that replays with zero LLM calls. It's scoped first to `https://www.roboform.com/filling-test-all-fields`, then to one additional multi-step site, per the assignment.

## Documents in this plan

| Doc | What it answers |
|---|---|
| [`../browser-use_codebase_understanding.md`](../browser-use_codebase_understanding.md) | How `browser_use` is architected (agent loop, DOM indexing, action dispatch), and exactly what to confirm in your own clone before hooking it |
| [`01_optexity_end_to_end_understanding.md`](01_optexity_end_to_end_understanding.md) | How Optexity itself works end to end - automation schema, action vocabulary, locator strategy, codebase module map |
| [`02_implementation_plan.md`](02_implementation_plan.md) | The actual build, phase by phase, with runnable-shaped code for the hook, filter, converter, and replay harness |
| [`03_design_decisions_and_tradeoffs.md`](03_design_decisions_and_tradeoffs.md) | Every non-obvious choice made above, what else was considered, and why it was rejected |
| [`04_test_and_validation_plan.md`](04_test_and_validation_plan.md) | How to prove it works: functional, performance, regression, unit tests, and submission mechanics |
-- 05 & 06 also there. update their reference here. 

## Evaluation criteria -> where it's addressed

The goal doc states you'll be evaluated on: code quality, latency/performance, extra features, time taken to build, and (during the demo) questions about code decisions.

| Criterion | Where |
|---|---|
| **Code quality** | `02_implementation_plan.md` phases 2-4 (small, single-responsibility pieces: hook / filter / converter, each independently testable per `04_test_and_validation_plan.md` §4) |
| **Latency / performance** | `02_implementation_plan.md` Phase 5 (replay harness); numbers recorded per `04_test_and_validation_plan.md` §2 |
| **Extra features** | `02_implementation_plan.md` Phase 7 (LLM-assisted auto-build; iterative recache loop) — explicitly marked bonus/stretch, not required for the core deliverable |
| **Time taken to build** | Phases are ordered so Phases 1-5 alone satisfy the core assignment on the roboform site; Phase 6 repeats the same pipeline on a second site with no new design, keeping the marginal cost of the second site low |
| **Questions about code decisions** | `03_design_decisions_and_tradeoffs.md` - read this immediately before the demo |

## What's explicitly out of scope for this planning work

Per `instructions.md`, this is a research/planning-only work item: no code was executed, no repo was cloned or forked, and no `optexity`/`browser-use` local setup was performed in this session. `optexity_codebase_understand.md` is treated as ground truth (a real prior digest of the optexity fork); the browser-use architecture doc is explicitly general-knowledge-based and caveated - see its own scope note before trusting any specific name in it.