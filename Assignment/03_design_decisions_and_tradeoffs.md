```markdown
# Design Decisions and Tradeoffs

The goal doc explicitly warns: *"During the demo of this assignment, you will be asked questions around your code decisions."* This document exists to answer those questions before they're asked - each decision below states what was chosen, what else was considered, and why the alternative was rejected.

## 1. Where to intercept: dispatch choke point vs. per-action patching vs. parsing LLM text

**Chosen:** wrap the single controller/registry dispatch method that every action funnels through (`browser_use_codebase_understanding.md` §4), rather than editing each action function individually.

**Alternatives considered:**
- *Patch every action function* (`click_element_by_index`, `input_text`, etc. individually). Rejected: N places to keep in sync instead of 1; any new action type added to the fork silently escapes caching until someone remembers to patch it too.
- *Parse the raw LLM completion text* ("I will click index 67 because...") to recover the action. Rejected: this couples the cache to prompt wording and model version - the exact failure mode the memory layer is trying to eliminate for the *automation*, we'd be reintroducing for the *cache itself*. The choke point gives already-parsed, structured data for free.

## 2. Selector-capture strategy: role/label preference vs. raw DOM index vs. raw CSS/XPath-only

**Chosen:** capture whatever real locator information (role+name, label, test-id, text, CSS, XPath - in that preference order) browser-use resolved the chosen index to, mirroring Optexity's own documented hierarchy (`01_...md` §5).

**Alternatives considered:**
- *Cache the raw `[n]` index and replay by index.* Rejected outright: the index is a transient artifact of one DOM snapshot. A slightly different render (ad loaded, popup present, lazy content) reassigns indices, so "click index 67" becomes silently wrong on replay - this defeats the entire "deterministic and reliable" goal, it would just be trading LLM non-determinism for DOM-ordering non-determinism.
- *Always fall back to XPath.* Rejected as the default (though kept as the lowest-priority fallback): Optexity's own docs flag XPath as more fragile than role/label-based Playwright locators, and using it universally would produce automations that are technically deterministic but still brittle to markup changes - the same failure mode, one layer down.

## 3. Cache storage format: JSONL vs. SQLite vs. in-memory

**Chosen:** append-only JSONL file (`cache.jsonl`), one `CachedStep` per line.

**Alternatives considered:**
- *SQLite.* Rejected for this POC: adds a dependency and schema-migration surface for no benefit at this scale (a handful to a few dozen steps per run); JSONL is trivially diffable in a PR review and in the demo, and is crash-safe per line (a mid-run failure still leaves earlier steps readable) without needing transactions.
- *In-memory list, pickled at the end.* Rejected: loses everything if the agent run crashes or hits `max_steps` mid-way, which is exactly the scenario most worth capturing (it's where the interesting "redundant exploration" steps live).

The goal doc itself says "you can just log the cache" for the core assignment - JSONL is the simplest thing that satisfies that literally. This is explicitly a POC-scoped choice, not a production design - see `05_production_grade_architecture.md` for what a durable, shared, lookup-before-run cache actually needs (a cache key beyond `url`, a promotion gate, staleness handling).

## 4. Redundant-step filtering: rule-based vs. ML/clustering-based dedup

**Chosen:** two explicit rules - drop failed attempts, and last-write-wins for repeated writes to the same resolved selector (`02_implementation_plan.md` Phase 3).

**Alternatives considered:**
- *Similarity-clustering or embedding-based dedup* of action sequences. Rejected: it would be its own non-deterministic component inside a pipeline whose entire point is removing non-determinism - and it's unexplainable in a demo Q&A ("why did it drop that step?" -> "the model said so" is a worse answer than a two-line rule you can read aloud).
- *No filtering at all* (convert every logged step 1:1). Rejected: browser-use is known to take exploratory/backtracking steps while reasoning (per the goal doc's own framing - "browser-use can take redundant steps while exploring"); converting all of them would produce an automation that repeats work (e.g. typing into the same field twice) instead of the clean, minimal one the assignment asks for.

## 5. Manual-first converter vs. LLM-auto-build from the start

**Chosen:** hand-written mapping script first (Phase 4), LLM-assisted auto-build as a bonus (Phase 7) layered on top of it, not a replacement for it.

**Why:** the goal doc itself scopes it this way ("for the assignment, you can just log the cache and manually build the new automation to verify if the actual code based cache is working or not" - auto-build is explicitly listed as bonus). Beyond just following the brief, the manual path also produces a trustworthy baseline: once the LLM-assisted bonus path exists, its output can be diffed against the manual converter's output on the same cache to sanity-check the LLM didn't hallucinate a node or drop a field - without a baseline, there'd be no way to tell if the auto-built automation was actually correct.

## 6. Which fork owns which piece of code

**Chosen:** the caching hook lives in the `browser-use` fork (Phase 2); the filter and converter live in the `optexity` fork (Phases 3-4).

**Why:** this isn't arbitrary - it follows what each schema/dependency actually needs. The hook needs access to browser-use's internal action-execution objects, which only exist inside that fork. The converter needs to import and validate against `optexity.schema.automation.Automation`, which only exists inside the optexity fork. Putting the converter inside browser-use would mean vendoring or duplicating Optexity's schema; putting the hook inside optexity would mean reaching into browser-use's internals from outside its package boundary. Splitting them where the goal doc's own submission instructions expect two separate PRs (one per fork) also keeps that mapping 1:1 with the actual repo split.

## 7. Validating generated output against the real schema, always

**Chosen:** every automation this pipeline produces - hand-converted or LLM-auto-built - is passed through `Automation.model_validate(...)` before being written to disk or replayed.

**Why:** Optexity already ships this validation for free as a Pydantic model; not using it and instead trusting hand-written or LLM-written JSON directly would be reinventing schema validation worse, and would let a malformed automation fail late (during replay) instead of immediately (at build time) - the earlier failure is strictly more useful during a time-boxed hackathon build.

```