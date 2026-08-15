# From POC Cache to Production-Grade Architecture

This doc answers a question the hackathon assignment doesn't ask directly but the demo almost certainly will: *what you built is a local file and a one-shot script - what would this actually look like as a product feature?*

## 1. What the POC uses today (recap)

Per `03_design_decisions_and_tradeoffs.md` §3: a single append-only `cache.jsonl` file on local disk, written once during one agentic run, read once by a manual conversion script (`02_implementation_plan.md` Phase 4), producing one static `test_automation_cached.json`. There is no lookup step - nothing checks "have we cached this before?" before running agentically - and nothing persists past the local filesystem. That scope was correct for a 1-3 hour build; it is not a caching *system*, just a capture-and-convert pipeline. Everything below is the gap between the two.

## 2. What's missing for production

| Gap | Why it matters |
|---|---|
| No lookup-before-run | The POC only caches *after* an agentic run. Production needs to check for an existing cached automation *before* paying for an LLM-driven run at all. |
| No durable, shared store | `cache.jsonl` is local and per-run. Production needs the derived automation available to every future run of the same task, across machines/users. |
| No trust gate | The POC's converter output is used immediately. Blindly replacing an agentic step with a derived automation in live traffic risks silently submitting wrong data if the conversion was subtly wrong - this needs a promotion step before it's trusted unattended. |
| No staleness handling | Sites change. A cached automation that was correct last month can silently start failing (or worse, silently submit wrong data without raising) as the page evolves. |
| No parameterization | The POC's converter bakes the *literal* value from one run (e.g. "myname") into `input_text`. A real cache entry needs to serve the same task with different `input_parameters` values on every run, not just replay the one it was seeded with. |

## 3. Cache key design

The naive key is `hash(url + task_text)`. Two refinements matter:

- **Parameterize, don't literal-bake.** Optexity's schema already supports variable substitution (`{email[0]}` - see `01_optexity_end_to_end_understanding.md` §3-4). The POC converter (`02_implementation_plan.md` Phase 4) doesn't do this - it writes `step.value` directly. A production converter needs to correlate each cached step's `value` against the *originating* `agentic_task`'s task string (which itself was built from `input_parameters`, e.g. `"fill full name as {name[0]}"`) and reconstruct the templated form. This turns one seed run into an automation that serves every future value of that parameter, not just the one it happened to see first - the actual point of caching a *workflow*, not a *transcript*.
- **Fingerprint the DOM shape, not just the URL.** The same URL can render meaningfully different DOM for different account states, feature flags, or A/B tests. A mismatched DOM shape correctly misses the cache and falls back to agentic rather than replaying a locator set built for a different page variant.

## 4. Proposed architecture

```
agentic_task node    | Cache Lookup Service  |
execution request -> | key = hash(url,       |
                     | task_text, dom_fingerprint) |
                     
                       hit |       | miss
                           v       v
               | Replay cached,  | | Run agentic (existing     |
               | parameterized   | | Optexity path) + Phase    |
               | automation      | | 2 caching hook            |
               
                       | node fails            |
                       v                       v
               | Self-healing loop | | Filter + Converter      |
               | (Phase 7b, as a   | | (Phases 3-4) produce    |
               | standing service, | | a *candidate* automation|
               | not a one-shot)   | 
               
                                               |
                                               v
                                 | Promotion Gate:           |
                                 | shadow-run candidate N    |
                                 | times before it can       |
                                 | replace the agentic path  |
                                 
                                               | passes threshold
                                               v
               | Two-tier Production Cache Store (Section 7) |
               | - Redis: fast key->pointer lookup, TTL, counters|
               | - Postgres: the actual automation_json + status |
               |   (same DB family as Optexity's existing    |
               |    `Task.automation` store, per             |
               |    `optexity_codebase_understand.md`)       |
               
                                       | feeds
                                       v
               | Task Analytics (already exists on the dashboard)|
               | - reused as the staleness signal: rising failure|
               | rate on a cached node -> auto-invalidate -> next|
               | run misses cache -> re-learns via agentic + recache|
```

The deliberate design choice here: **reuse what Optexity already has** (the automation store behind `Task.automation`, and the existing Task Analytics dashboard) rather
than standing up a parallel cache database and a parallel monitoring system. The new pieces are only the lookup step, the promotion gate, and the parameterization logic in
the converter - everything else already exists in the platform.

## 5. Promotion gate and the safer default

Rather than a hard cutover ("replace this agentic node with the cached automation the moment one candidate exists"), the safer production default is:

1. **Shadow mode**: run the candidate automation alongside (or instead of a small percentage of) live agentic traffic for the same task, without letting its result affect the real outcome yet, and compare success/output against the agentic run.
2. **Threshold-based promotion**: once the candidate succeeds N consecutive times (or above some success rate over M attempts) across genuinely different sessions, promote it to be tried first, with agentic as the fallback on failure - not the other way around.
3. **Fallback-first as the permanent steady state, not just a bootstrap phase**: even a "trusted" cached automation should still fall back to agentic on failure and recache the result (this is exactly Phase 7b's self-healing loop, running continuously) rather than ever hard-failing a production workflow because a selector went stale.

This mirrors the same asymmetry already designed into Optexity's own schema - `command` first (deterministic, fast), `prompt_instructions` as an AI fallback when the locator fails (`01_optexity_end_to_end_understanding.md` §4-5). Production caching is that same pattern applied one level up: cached automation first, agentic as the fallback when the cache is wrong.

## 6. Multi-tenancy note

If this platform serves multiple customers/environments against nominally "the same" site, a single global cache entry per `(url, task)` will not generalize - different tenants can have different account states or feature flags producing different DOM shapes. The DOM-fingerprint component of the cache key (Section 3) is the first line of defense; if fingerprints diverge often enough per tenant, the key should be namespaced per tenant rather than assuming a global cache automatically applies everywhere.

## 7. Which cache, concretely - and a reference implementation

The direct answer: **two tiers, not one.**

| Tier | Technology | Holds | Why |
|---|---|---|---|
| Fast lookup | **Redis** (`redis-py`) | A small pointer: `{automation_db_id, status, version}`, plus a success/failure counter per key, with a TTL | Lookup happens on every single `agentic_task` node execution - it needs to be low-latency and shared across every service instance, not a per-process in-memory dict. TTL gives cheap default staleness expiry for free. |
| Source of truth | **Postgres** (same database family already backing Optexity's automation store, per `optexity_codebase_understand.md`) | The full `automation_json`, its `status` (`candidate` / `promoted` / `deprecated`), and version history | The actual JSON is too large and too important to lose to keep only in a cache; Postgres is durable and already exists in the platform - this is not a new database, it's a new *table*. |

This is a standard **cache-aside** pattern: check Redis first; on a pointer hit, fetch the real automation from Postgres by id; on a total miss, run agentic and populate both.

**Why two tiers instead of just one:** Redis is fast because it's memory-based, which is exactly why it's the wrong place to keep the only copy of something you can't afford to lose - it can evict entries under memory pressure and isn't durable across a restart unless configured as a database in its own right (not what it's for here). Postgres is durable and structured (query by status, keep version history) but isn't what you want taking the hit of a lookup on *every single* `agentic_task` node execution. So: Redis holds a cheap, disposable pointer (`{automation_db_id, status, version}`) - if it's lost, the worst case is one redundant agentic run to relearn it. Postgres holds the actual `automation_json`, which represents real, possibly expensive work, and is never at risk of being silently evicted.

**This does introduce one genuinely new piece of infrastructure** - Redis - which the "reuse everything" framing in Section 4 slightly understates. It's called out explicitly here rather than glossed over: everything *except* the fast-lookup layer reuses existing Optexity infrastructure (the automation database, Task Analytics), but a low-latency shared lookup cache is new.

### 7a. Postgres table

```sql
CREATE TABLE cached_automations (
    id                  BIGSERIAL PRIMARY KEY,
    cache_key           TEXT UNIQUE NOT NULL,
    url                 TEXT NOT NULL,
    task_signature      TEXT NOT NULL,
    dom_fingerprint     TEXT NOT NULL,
    automation_json     JSONB NOT NULL,
    status              TEXT NOT NULL DEFAULT 'candidate',  -- candidate | promoted | deprecated
    version             INT NOT NULL DEFAULT 1,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_validated_at   TIMESTAMPTZ
);
```

### 7b. Cache key (parameterized per Section 3, not literal-baked)

```python
import hashlib

def build_cache_key(url: str, task_text: str, dom_fingerprint: str) -> str:
    normalized_task = "-".join(task_text.lower().split())
    raw = f"{url}::{normalized_task}::{dom_fingerprint}"
    return "automation_cache:" + hashlib.sha256(raw.encode()).hexdigest()
```

`dom_fingerprint` is computed from whatever browser-use's selector map exposes at the start of the run (see `browser_use_codebase_understanding.md` §2) - e.g. a hash of the sorted set of `(role, accessible_name)` pairs for visible interactive elements. Its exact source needs the same "confirm in your local clone" treatment as the rest of the browser-use integration.

### 7c. Redis client wrapper

```python
import json
import redis

class AutomationCacheClient:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self._r = redis.Redis.from_url(redis_url, decode_responses=True)

    def get_pointer(self, cache_key: str) -> dict | None:
        raw = self._r.get(cache_key)
        return json.loads(raw) if raw else None

    def set_pointer(self, cache_key: str, pointer: dict, ttl_seconds: int = 7 * 24 * 3600):
        self._r.set(cache_key, json.dumps(pointer), ex=ttl_seconds)

    def record_result(self, cache_key: str, success: bool) -> tuple[int, int]:
        stats_key = f"{cache_key}:stats"
        field = "success_count" if success else "failure_count"
        pipe = self._r.pipeline()
        pipe.hincrby(stats_key, field, 1)
        pipe.hgetall(stats_key)
        _, stats = pipe.execute()
        return int(stats.get("success_count", 0)), int(stats.get("failure_count", 0))

    def invalidate(self, cache_key: str):
        self._r.delete(cache_key)
        self._r.delete(f"{cache_key}:stats")
```

### 7d. Lookup-before-run flow

```python
PROMOTION_SUCCESS_THRESHOLD = 5
MAX_FAILURES_DURING_TRIAL = 1

def get_or_learn_automation(url: str, task_text: str, dom_fingerprint: str,
                            cache: AutomationCacheClient, db, run_agentic_and_convert):
    """'run_agentic_and_convert' is Phases 1-4 (or 7a) end to end: run the 
    agentic task, cache the steps, filter, convert to a candidate Automation."""
    cache_key = build_cache_key(url, task_text, dom_fingerprint)
    pointer = cache.get_pointer(cache_key)

    if pointer is not None:
        # hit - whether "candidate" (still on trial) or "promoted" (trusted),
        # replay it; the caller reports the outcome via record_outcome below
        automation = db.fetch_automation(pointer["automation_db_id"])
        return automation, cache_key, pointer["automation_db_id"]

    # total miss - learn it once, store as a candidate, not yet trusted
    automation = run_agentic_and_convert(url, task_text)
    db_id = db.insert_candidate(cache_key, url, task_text, dom_fingerprint, automation)
    cache.set_pointer(cache_key, {"automation_db_id": db_id, "status": "candidate", "version": 1})
    return automation, cache_key, db_id

def record_outcome(cache_key: str, db_id: int, success: bool, 
                   cache: AutomationCacheClient, db):
    """Call this after every replay of a cached automation - during the 
    trial period AND after promotion, so a promoted automation that starts 
    failing in production gets demoted automatically (feeds Phase 7b's 
    self-healing loop, which re-learns via a scoped agentic fallback)."""
    successes, failures = cache.record_result(cache_key, success)

    if failures > MAX_FAILURES_DURING_TRIAL:
        cache.invalidate(cache_key)
        db.mark_deprecated(db_id)
        return "deprecated"

    if successes >= PROMOTION_SUCCESS_THRESHOLD:
        db.mark_promoted(db_id)
        cache.set_pointer(cache_key, {"automation_db_id": db_id, "status": "promoted", "version": 1})
        return "promoted"

    return "candidate"
```

**Done-check (if this were actually built):** seed one candidate, replay it 5 times successfully - confirm `record_outcome` returns `"promoted"` on the 5th call and the Postgres row's `status` flips; then force one failure on a promoted entry and confirm it flips to `"deprecated"` and the Redis pointer is gone, so the very next lookup misses and re-learns via `run_agentic_and_convert`.

### 7e. Optional, at higher scale: a Bloom filter to skip the Redis round-trip

Not needed for the hackathon or a first production rollout - a Redis `GET` is already sub-millisecond. This only earns its keep once request volume is high enough that avoiding the network hop to Redis itself matters. Included here because it's a legitimate next optimization, not because the design above requires it.

**The idea:** keep a small, local, in-process Bloom filter on each service instance, refreshed periodically from Postgres. Before even calling Redis, ask the Bloom filter "have we ever cached this key?" - if it says "definitely not," skip straight to the agentic path and never make the Redis call at all.

```python
import math
from bitarray import bitarray
import mmh3 # murmurhash3 - fast, non-cryptographic, standard choice for Bloom filters

class LocalBloomFilter:
    def __init__(self, capacity: int = 1_000_000, error_rate: float = 0.01):
        self.size = int(-(capacity * math.log(error_rate)) / (math.log(2) ** 2))
        self.hash_count = max(1, int((self.size / capacity) * math.log(2)))
        self.bits = bitarray(self.size)
        self.bits.setall(False)

    def add(self, key: str):
        for seed in range(self.hash_count):
            self.bits[mmh3.hash(key, seed) % self.size] = True

    def might_contain(self, key: str) -> bool:
        return all(self.bits[mmh3.hash(key, seed) % self.size] for seed in range(self.hash_count))

def refresh_from_db(db, capacity_hint: int) -> LocalBloomFilter:
    """Rebuild from Postgres - cheap, since it only reads cache_key strings,
    not the full automation_json. Run this on a background timer (e.g. every 
    5 minutes), not on the request path."""
    fresh = LocalBloomFilter(capacity=max(capacity_hint, 1000))
    for key in db.iter_all_cache_keys(): # SELECT cache_key FROM cached_automations
        fresh.add(key)
    return fresh
```

Wired into the lookup path, checked before `cache.get_pointer(...)`:

```python
def get_or_learn_automation_with_bloom(url, task_text, dom_fingerprint, 
                                       bloom: LocalBloomFilter, cache, db, 
                                       run_agentic_and_convert):
    cache_key = build_cache_key(url, task_text, dom_fingerprint)

    if not bloom.might_contain(cache_key):
        # Definitely never cached anywhere -- skip the Redis network call entirely
        automation = run_agentic_and_convert(url, task_text)
        db_id = db.insert_candidate(cache_key, url, task_text, dom_fingerprint, automation)
        cache.set_pointer(cache_key, {"automation_db_id": db_id, "status": "candidate", "version": 1})
        bloom.add(cache_key)  # update this instance's copy immediately; 
                              # other instances catch up on their next refresh
        return automation, cache_key, db_id

    # Bloom filter says "maybe" -- fall through to the real Redis/Postgres flow
    return get_or_learn_automation(url, task_text, dom_fingerprint, cache, db, run_agentic_and_convert)
```

**Honest tradeoff, not a correctness risk:** a Bloom filter never produces a false *negative* for a key it has actually indexed - but because each instance's copy is only refreshed periodically, there's a window where instance A caches something and instance B's Bloom filter doesn't know yet. In that window, B will treat a real cache hit as "definitely not cached" and redundantly re-run the agentic path once. That's wasted work, not a wrong answer - it still produces a correct result, it just misses the speed benefit that one time. Worth using only once that redundant-work cost is smaller than the network-hop cost it's saving.

**Done-check (if this were actually built):** seed one candidate, replay it 5 times successfully - confirm `record_outcome` returns `"promoted"` on the 5th call and the Postgres row's `status` flips; then force one failure on a promoted entry and confirm it flips to `"deprecated"` and the Redis pointer is gone, so the very next lookup misses and re-learns via `run_agentic_and_convert`.

## 8. What ships in this hackathon vs. what's described here

Everything in `02_implementation_plan.md` Phases 1-7 is meant to be buildable in the 1-3 hour window, including the bonus phases. This document - including Section 7's Redis/Postgres implementation - is intentionally *not* part of that build. It's the answer to "what's next," so the demo has a credible answer for "is this just a script, or does it point somewhere real."