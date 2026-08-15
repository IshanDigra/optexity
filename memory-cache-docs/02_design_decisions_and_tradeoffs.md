# Design Decisions and Tradeoffs

The four decisions that shaped the design, then a table of the rest. Where a choice was corrected by
evidence, that is recorded rather than hidden — the corrections were the most informative part.

---

## 1. Hook the dispatch choke point

`Registry.execute_action` is the single method every action passes through between "the LLM chose
this" and "Playwright did it". One wrapper covers every action.

- **Not per-action patching** — N places to keep in sync, and any action added later escapes caching
  silently.
- **Not parsing the LLM's output** — recovering *"I will click index 67 because…"* couples the cache
  to prompt wording and model version. That is the exact fragility this layer exists to remove.

An earlier revision moved the decorator to `Tools.act`, which is called by keyword with an
`ActionModel`, so `params.get('index')` could never work. `execute_action` receives
`(action_name: str, params: dict)` — a plain dict, exactly what the hook needs.

## 2. Record resolved locators, never the DOM index

The `[n]` index is an artifact of one DOM snapshot. An ad, a popup or lazily-loaded content
renumbers it, so "click index 67" becomes silently wrong — a different element, no error. Caching by
index would trade LLM non-determinism for DOM-ordering non-determinism, which is worse because it
fails quietly.

**The role branch needs a guard.** Optexity's preference order puts `get_by_role` first, and the
obvious implementation is "use role if a role exists". But roles exist on essentially every
interactive element, so that makes every lower strategy dead code and emits
`get_by_role("textbox", name="")` — which matches every input on the page. Optexity evaluates
commands literally (`eval(f"page.{command}")`) then calls `.wait_for(state="visible")`; a multi-match
raises Playwright strict mode and the run falls back to the index-prediction LLM, destroying the
zero-token result.

"Prefer role" means *prefer a role that identifies something*. The branch is taken only when the
element has a non-empty accessible name.

## 3. XPath goes in `command`, not the `xpath` field

`BaseAction.xpath` exists in the schema, and putting an xpath there is the obvious reading. **Nothing
under `optexity/inference` reads that field** — a node carrying only an xpath has no locator at
replay and falls straight through to the LLM. Reading the schema was not enough; this only surfaced
by tracing what the execution engine actually consumes.

So xpath is emitted as `locator("xpath=/html/…").first`, normalised to absolute — browser-use reports
paths without a leading slash, which Playwright treats as relative.

## 4. Exclude `evaluate` from the agent's toolset

On the multi-step site the agent did the entire job through JavaScript. `evaluate` changes page state
without touching an element, so it leaves **no locator to record**: the cache showed four blank rows
and two clicks for a task that visibly succeeded.

- **Not mapped to `python_script_action`** — it would work (that action receives the Playwright
  `page`) and needs no re-run, but the automation becomes opaque JS blobs rather than inspectable
  locator nodes, and JS that assigns field values commonly bypasses framework event handlers, so it
  can silently no-op.
- **`screenshot` is deliberately *not* excluded** — `agentic_task` defaults to `use_vision=False`, so
  screenshots are often how the agent orients itself. They are observation, not action; the filter
  drops them and they cost nothing downstream.

An action the memory layer structurally cannot learn from is worse than one that is merely slow.

---

## The rest

| Decision | Why | Rejected |
|---|---|---|
| **Dedup key is `(strategy, selector, accessible_name)`** | With the role strategy the selector is the ARIA role, so four form fields all key as `"textbox"` | Keying on the selector alone — silently collapses a whole form into one node |
| **Two filter rules only**: drop failures, last-write-wins | Explainable in a sentence; a reviewer can audit it by reading | Embedding/similarity dedup — a non-deterministic component inside a pipeline built to remove non-determinism, and unexplainable in review |
| **`.first` on every locator** | The cached selector describes the element the agent chose; degrading to "same element as last time" beats raising strict mode and handing the step to the LLM | Strict matching. Tradeoff accepted: it can mask ambiguity, so `inspect_cache` surfaces duplicate locators at build time |
| **Navigation settle time derived from `page_url_before`** | The agentic run re-read the DOM before every action, absorbing page loads. Deterministic replay races them. The signal was already in the cache | A fixed delay everywhere — pays the cost on every node. The 5s schema default would make a 4-node replay 20s of `sleep` |
| **JSONL, truncated per run** | Diffable in review, readable in a demo, crash-safe per line without transactions | SQLite (a dependency and migrations for a few dozen rows); in-memory + pickle (loses exactly the crashed runs worth studying); appending across runs (converter reads two workflows mixed) |
| **`send_keys` / `upload_file` unmapped** | A cached step carries neither a `KEY_NAMES`-valid key nor a file source | Emitting them anyway — a node that fails at replay is worse than a clear error at build time |
| **Hook in browser-use, converter in optexity** | The hook needs browser-use internals; the converter needs `Automation` to validate against | Both in one repo. The first attempt vendored an 18-line stub `Automation` into browser-use, which made `model_validate` meaningless while looking like validation |
| **Always `Automation.model_validate` before writing** | Optexity ships this for free; skipping it means failing late during replay instead of at build time | Trusting hand-written or LLM-written JSON |
| **Deterministic converter first, LLM second** | Both emit schema-valid JSON by construction, so validation alone cannot detect a dropped node or invented selector. The deterministic output is the answer key | LLM-only. On the roboform cache the two agree exactly — which is only meaningful *because* there was something to compare against |
