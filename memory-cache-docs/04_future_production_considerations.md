# Future Production Considerations

## The honest starting point: there is no cache step

What ships here is **capture-and-convert, not a cache.**

Which automation runs is chosen by a human typing a filename:

```bash
OPTEXITY_LOCAL_AUTOMATION=test_automation_cached.json optexity inference --port 9000 ...
```

Nothing ever asks *"has this task been solved before?"* The layer records an agentic run and can
produce a deterministic replacement, but a person decides when to use it. Every gap below follows
from closing that one.

```
  TODAY                                    PRODUCTION

  agentic_task                             agentic_task
       |                                        |
       v                                        v
  [ run agentically ]                    [ Cache Lookup ]
       |                                    /        \
       v                                 hit          miss
  [ hook -> cache.jsonl ]                 |             |
       |                                  v             v
       v                          [ replay cached ]  [ run agentically ]
  [ human runs converter ]                |             |
       |                                  |             v
       v                                  |        [ convert -> candidate ]
  [ human edits run command ]             |             |
                                          |             v
                                          |        [ promotion gate ]
                                          v             |
                                   [ record outcome ] <-+
```

---

## 1. Lookup before run

The step that turns this into a cache. On reaching an `agentic_task`, compute a key and check for a
promoted automation before paying for LLM reasoning.

```python
def build_cache_key(url: str, task_text: str, dom_fingerprint: str) -> str:
    normalized = "-".join(task_text.lower().split())
    return "automation_cache:" + hashlib.sha256(
        f"{url}::{normalized}::{dom_fingerprint}".encode()
    ).hexdigest()
```

**Why the DOM fingerprint, and not just the URL.** The same URL renders differently for different
account states, feature flags and A/B branches. A cached locator set built for one variant applied to
another fails in the worst way — it may match *something*. A hash of the sorted `(role,
accessible_name)` pairs of visible interactive elements makes a mismatched variant miss the cache
and correctly fall back to agentic. This is the same information `_classify_selector` already reads,
so the hook is most of the way there.

## 2. Parameterize, don't literal-bake

The converter writes the value it observed:

```json
{"input_text": {"command": "locator(\"input[name='04fullname']\").first", "input_text": "Ishan"}}
```

That automation only ever fills in `Ishan`. A production entry has to reconstruct the template:

```json
{"input_text": {"command": "...", "input_text": "{name[0]}"}}
```

Optexity's schema already supports substitution, so the mechanism exists. What is missing is
correlating each cached `value` back against the `input_parameters` that produced the seed task
string, and re-templating on the way out. Without this a cache entry serves exactly one input — it
caches a *transcript* rather than a *workflow*, which is the difference between a demo and a feature.

## 3. LLM-generated deterministic steps as the primary path

`llm_cache_to_automation.py` is the seed of this and it works today — verified live, producing
commands identical to the deterministic converter on the roboform cache. Promoting it from bonus to
default is what makes the layer general: the hand-written `ACTION_MAP` covers five actions, and
extending it is manual work per action type, whereas a model given the cache and
`Automation.model_json_schema()` generalises to actions nobody mapped.

Three things it needs before it can be trusted unattended:

- **Schema validation with error feedback** — already implemented; failures are fed back verbatim for
  up to three repair attempts rather than retrying blind.
- **Diff against the deterministic converter** — already implemented, and load-bearing. Both outputs
  are schema-valid by construction, so validation alone cannot detect a dropped node or an invented
  selector. Keep the deterministic path as the answer key wherever it has an opinion.
- **Disagreement policy.** Currently `build_and_diff` reports; production has to decide. Reasonable
  default: on disagreement, ship the deterministic output and log the divergence for review, since a
  wrong-but-valid automation submits wrong data silently.

## 4. Promotion gate

Never hard-cut from agentic to cached on the strength of one conversion.

1. **Shadow** — run the candidate alongside live agentic traffic without letting it affect the
   outcome; compare results.
2. **Promote on threshold** — after N consecutive successes across genuinely different sessions, try
   it first, with agentic as fallback.
3. **Fallback-first permanently**, not just during bootstrap. A trusted automation should still fall
   back and re-cache rather than fail a production workflow because a selector moved.

This mirrors the asymmetry already in Optexity's schema — `command` first, `prompt_instructions` as
the AI fallback. Production caching is that same pattern one level up.

## 5. Staleness

Sites change, and a stale automation can fail *quietly*: `.first` will happily act on the wrong
element. Task Analytics already tracks per-task failure rates, so the signal exists — a rising
failure rate on a cached node invalidates the entry, the next run misses cache, and the workflow is
re-learned agentically. That closes the loop without new monitoring infrastructure.

Worth pairing with an assertion: `assert_locator_presence` on generated nodes would turn silent
wrong-element actions into loud failures.

## 6. Storage

Cache-aside over two tiers:

| Tier | Holds | Why |
|---|---|---|
| Redis | `{automation_db_id, status, version}` + success/failure counters, TTL | Looked up on every `agentic_task` execution; needs to be low-latency and shared across service instances |
| Postgres | the full `automation_json`, `status` (`candidate`/`promoted`/`deprecated`), version history | The automation represents real, expensive work and must not be silently evicted |

Redis is fast because it is memory-based, which is exactly why it is the wrong home for the only
copy of something you cannot afford to lose. Losing the pointer costs one redundant agentic run.
Postgres is durable and already in the platform — this is a new table, not a new database. Redis is
the one genuinely new piece of infrastructure and worth naming as such.

## 7. Multi-tenancy

If several customers run "the same" site, one global entry per `(url, task)` will not generalise —
different account states produce different DOM. The fingerprint is the first defence; if
fingerprints diverge per tenant in practice, namespace the key per tenant rather than assuming a
global cache applies everywhere.

---

## Known gaps in what ships today

Stated plainly, because they are the first things a reviewer should ask about:

- **Downloads.** `CachedStep` has no field recording that a click produced a file, so the converter
  never sets `ClickElementAction.expect_download`. The converter warns when the seed expects
  downloads but no node claims one. Fixing it properly means recording download side-effects in the
  hook.
- **`send_keys` and `upload_file` are unmapped.** A cached step carries neither a `KEY_NAMES`-valid
  key nor a file source. They raise a clear error rather than emitting a node that fails at replay.
- **No iterative re-caching loop.** The second bonus — cache, rebuild, re-run, re-cache — is not
  built. §4's promotion gate plus §5's staleness invalidation is that loop as a standing service
  rather than a one-shot script, and is the right shape for it.
- **`.first` can mask ambiguity.** Accepted deliberately (see design decisions §5);
  `inspect_cache` surfaces duplicate locators at build time so it is visible before replay.
