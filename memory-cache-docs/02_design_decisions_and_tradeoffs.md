# Design Decisions and Tradeoffs

Each decision below states what was chosen, what else was considered, and why the alternative was
rejected. Where a choice was corrected by evidence, that is recorded rather than hidden — the
corrections were the most informative part of the build.

---

## 1. Where to intercept: the dispatch choke point

**Chosen:** wrap `Registry.execute_action`, the single method every action funnels through.

**Rejected — patch each action function.** N places to keep in sync instead of one, and any action
added to the fork later escapes caching silently until someone remembers.

**Rejected — parse the LLM's completion text.** Recovering "I will click index 67 because…" couples
the cache to prompt wording and model version. That is precisely the fragility the memory layer
exists to remove; reintroducing it one layer down would be self-defeating. The choke point hands
over already-parsed data for free.

**Confirmed by evidence.** An earlier revision moved the decorator to `Tools.act`. That method is
called entirely by keyword with an `ActionModel`, so `params.get('index')` could never work.
`execute_action` receives `(action_name: str, params: dict)` — a plain dict, exactly what the hook
needs.

## 2. What to record: resolved locators, never the DOM index

**Chosen:** capture whatever real locator information the index resolved to.

**Rejected — cache the `[n]` index and replay by index.** The index is an artifact of one DOM
snapshot. An ad, a popup or lazily-loaded content renumbers it, so "click index 67" becomes silently
wrong — a different element, no error. That trades LLM non-determinism for DOM-ordering
non-determinism, which is worse because it fails quietly.

**Rejected — XPath for everything.** Optexity's own docs flag XPath as the most brittle option.
Universal XPath produces automations that are technically deterministic but break on any markup
change — the same failure mode one level down. It is kept as the last resort only.

## 3. Role only when it has a distinguishing name

**Chosen:** take the `role` branch only when the element has a non-empty accessible name; otherwise
fall through to aria-label → test-id → text → id → name attribute → xpath.

**Why:** Optexity's preference order puts `get_by_role` first, and the obvious implementation is
"use role if a role exists". But roles exist on essentially every interactive element, which makes
every lower branch dead code and produces `get_by_role("textbox", name="")`. Optexity evaluates the
command literally (`eval(f"page.{command}")`) then calls `.wait_for(state="visible")`; a multi-match
raises Playwright strict mode, the deterministic path fails, and the run silently falls back to the
index-prediction LLM — destroying the zero-token result the layer exists to produce.

The preference order is right. "Prefer role" means *prefer a role that identifies something*.

## 4. XPath as a `command`, not in the `xpath` field

**Chosen:** emit `locator("xpath=/html/…").first` as a `command`.

**Why:** `BaseAction.xpath` exists in the schema, and putting an xpath there is the obvious reading.
Nothing under `optexity/inference` reads that field — I grepped the whole package. A node carrying
only an xpath has no locator at replay and falls straight through to the LLM. Reading the schema was
not enough; this only surfaced by tracing what the execution engine consumes.

browser-use also reports paths without a leading slash (`html/body/…`), which Playwright treats as
relative, so the converter normalises to absolute.

## 5. Appending `.first` to every locator

**Chosen:** always append `.first`.

**Tradeoff, accepted knowingly:** it can mask genuine ambiguity — if a cached selector matches three
elements, we silently take the first rather than failing loudly.

**Why anyway:** the cached selector describes *the element the agent chose*. Without `.first`, a
selector that becomes ambiguous raises strict mode and hands the step to the LLM. With it, the
degradation is "the same element as last time", which is almost always right and never costs tokens.
`inspect_cache` surfaces duplicate locators before conversion, so the ambiguity is visible at build
time rather than hidden at replay time.

## 6. Excluding `evaluate` from the agent's toolset

**Chosen:** `Tools(exclude_actions=["evaluate"])` for agentic tasks.

**Why:** on the multi-step site the agent did the entire job — opening settings, setting a key,
clicking Connect — through JavaScript. `evaluate` changes page state without touching an element, so
it leaves **no locator to record**. The cache showed four blank `evaluate` rows and two clicks; the
converted automation was missing the actual work. An action the memory layer structurally cannot
learn from is worse than one that is merely slow.

**Rejected — map `evaluate` to `python_script_action`.** It would work (that action receives the
Playwright `page`), and it needs no re-run. But the automation becomes opaque JavaScript blobs
rather than inspectable locator nodes, and JS that assigns field values commonly bypasses framework
event handlers, so it can silently no-op on replay.

**Deliberately *not* excluded: `screenshot`.** `agentic_task` defaults to `use_vision=False`, so
screenshots are often how the agent orients itself. They are observation, not action — the filter
drops them and they cost nothing downstream. Removing the tool would risk task failure for no gain.

## 7. Rule-based filtering, not clustering

**Chosen:** two rules — drop failures, last-write-wins per element.

**Rejected — embedding or similarity-based dedup.** It would put a non-deterministic component
inside a pipeline whose entire purpose is removing non-determinism. It is also unexplainable in
review: "why was that step dropped?" → "the model decided" is a worse answer than a two-line rule you
can read aloud.

**Rejected — no filtering.** Converting every logged step 1:1 reproduces the agent's exploration,
including typing into the same field twice.

## 8. Deriving navigation settle time from the cache

**Chosen:** a step whose `page_url_before` differs from the next step's gets 3.0s instead of 0.5s.

**Why:** the agentic run re-read the DOM before every action, absorbing page loads implicitly. A
deterministic replay has no such pause and races the page — the next locator does not exist yet, and
the run falls back to the LLM. The signal was already in the cache; it needed reading, not new
capture.

The schema default of 5s per node was overridden to 0.5s. Left alone, a four-node replay would spend
20s asleep and the latency comparison would measure `time.sleep`.

## 9. Cache format: append-only JSONL

**Chosen:** one `CachedStep` per line in `cache.jsonl`.

**Rejected — SQLite.** A dependency and a migration surface for a few dozen rows per run. JSONL is
diffable in review, readable in a demo, and crash-safe per line without transactions.

**Rejected — in-memory, pickled at the end.** Loses everything if the agent crashes or hits
`max_steps` — exactly the runs where the redundant-exploration steps are most interesting.

Truncate-on-first-write rather than append across runs: otherwise a second run concatenates onto the
first and the converter reads a mixture of two workflows.

## 10. Which fork owns which piece

**Chosen:** the hook in browser-use; the filter, converter and tooling in optexity.

**Why:** it follows what each side needs. The hook needs browser-use's internal execution objects.
The converter needs `optexity.schema.automation.Automation` to validate against. Putting the
converter in browser-use would mean vendoring Optexity's schema — the first attempt did exactly
that, with an 18-line stub `Automation`, which made `model_validate` meaningless while looking like
validation. That stub was deleted.

## 11. Validating against the real schema, always

**Chosen:** every generated automation passes `Automation.model_validate` before reaching disk.

**Why:** Optexity ships this validation for free. Not using it means a malformed automation fails
late, during replay, instead of immediately at build time.

## 12. Hand-written converter first, LLM second

**Chosen:** deterministic converter as the primary path; LLM-assisted as a bonus layered on top,
diffed against it.

**Why:** the brief scopes it this way, but there is a stronger reason. Both converters emit
schema-valid JSON by construction, so validation alone cannot tell you the model dropped a node or
invented a selector. The deterministic output is the answer key. On the roboform cache the two agree
exactly — which is only a meaningful statement *because* there was something to compare against.
