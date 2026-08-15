
# browser-use Codebase Understanding (Architecture-Level)

## Scope and honesty note

Unlike `optexity_codebase_understand.md` (a real file-by-file digest of an actual Optexity checkout), **this document is not derived from reading the Optexity fork of browser-use.** No repo and no internet access were available while writing it. It describes the architecture of the **public, open-source `browser-use` project** from general knowledge, at the level that is genuinely stable across versions and forks (the overall loop and pattern, not exact line numbers).

Treat everything below as "the shape of the thing to go find," not "verified code." Section 5 is a mandatory checklist - do not start wiring a caching hook until it's filled in against your own local clone of `Optexity/browser-use`.

The Optexity dashboard docs corroborate the parts of this shape that matter for the hackathon: `Engcon Hackathon goal.md` shows the exact indexed-DOM string format the agent reasons over (`[67]<a id=dlbtn />`) and confirms the LLM's job is just to pick an index and an action - everything below explains what happens on either side of that choice.

## 1. The agent step loop

browser-use runs a loop, roughly:



loop until done or max_steps reached:
1. Extract current page state -> build an indexed DOM string
(interactive elements numbered [0], [1], [2], ... - this is
the exact string format shown in Engcon Hackathon goal.md)
2. Send { task, DOM string, action history } to the LLM
3. Parse the LLM's response into one or more structured actions,
e.g. "click index 67" or "type "myname" into index 12"
4. Execute each action against the real browser (Playwright)
5. Record the result (success/failure, new page state) into
agent history



`max_steps` (an `agentic_task` field per `Optexity/Actions Types/agentic tasks.md`) simply bounds how many times this loop can run.

## 2. DOM indexing / the selector map

Step 1 above requires mapping a bracket index like `[67]` to a real, clickable element. This is the part of browser-use that inspects the live DOM (accessibility tree + visibility/interactability checks) and builds a **selector map**: `{ index -> element_handle_or_locator_info }`. The LLM only ever sees the index; browser-use is what resolves it back to something Playwright can act on.

This matters directly for the caching design in `hackathon-plan/02_implementation_plan.md`: **the index itself is not a stable cache key** - it can shift between runs if the DOM re-renders differently (an extra popup, a slow-loading element, A/B-tested markup). What must be cached is whatever *real* locator information browser-use resolved the index to (an accessible role+name, a label, an id, or at minimum an XPath) - not the transient index number.

## 3. Controller + action registry pattern

Step 4 (executing an action) is not one giant if/else. The public project uses a registry of small, named action functions - things like `click_element_by_index`, `input_text`, `scroll_down`, `go_to_url`, `done` - each responsible for one action type and each ultimately calling a real Playwright method (`locator.click()`, `locator.fill()`, `page.goto()`, ...). A controller object owns this registry and is what the agent loop calls into once the LLM's chosen action has been parsed.

This is a deliberate design choice on their part (not just an implementation detail): it means new actions can be registered without touching the agent loop, and - usefully for this hackathon - it means there is a small, finite set of action *names* to map onto Optexity's own interaction actions (`click_element`, `input_text`, `select_option`, `go_to_url`, ... - see `Optexity/Actions Types/interaction actions.md`). The two vocabularies are close enough that the mapping in the converter script (Phase 4 of the implementation plan) is mostly 1:1.

## 4. The dispatch choke point (where to hook)

Whatever the exact function/method name turns out to be in your clone, there is one place every chosen action passes through on its way from "LLM decided this" to "Playwright did this" - call it the **dispatch choke point**. In the public project this is the controller/registry's central "run this named action with these params" method.

This is the single best place to add caching, for one reason: everything you need for the cache record is already normalized and available there -
- the action name (`click_element_by_index`, `input_text`, ...)
- the resolved element / index for that step
- the parameter(s) the LLM chose (text to type, index to click)
- whether execution succeeded

Instrumenting here means you do **not** need to touch every individual action function, and you do **not** need to parse free-text LLM output (which changes wording between model versions/prompts) - see `hackathon-plan/03_design_decisions_and_tradeoffs.md` for the fuller comparison of alternatives.

## 5. Confirm before you build (junior-dev checklist)

Before writing any hook code, open your local clone of the Optexity fork of `browser-use` (`Optexity/browser-use`, installed per the goal doc's "Setup for Development" section) and fill this in:

- [ ] **Agent loop location**: which file/class runs the step loop described in Section 1? (Public project: an `Agent` class, roughly `browser_use/agent/service.py`.)
- [ ] **Controller/registry location**: which file/class owns the action registry described in Section 3? (Public project: roughly `browser_use/controller/service.py` + `browser_use/controller/registry/service.py`.)
- [ ] **Exact dispatch method name and signature**: what is the choke-point method from Section 4 actually called, and what arguments does it take/return? This is the one thing the caching hook in `hackathon-plan/02_implementation_plan.md` (Phase 2) directly wraps - the snippet there is written to be adaptable to whatever this turns out to be, but you must know the real name and signature first.
- [ ] **Shape of the resolved element/selector info** available at that choke point: does it expose a CSS selector, an XPath, an accessible role+name, or only the raw index? This determines how much of the "prefer role/label over raw index" strategy (Section 2, and `Optexity/advance/locators.md`) you can actually implement without extra DOM inspection.
- [ ] **Naming drift**: since this is specifically the `optexity-browser-use` fork (per the `optexity` package's dependency on `optexity-browser-use>=0.9.5`, noted in `optexity_codebase_understand.md`), check whether Optexity has renamed or wrapped any of the above - forks commonly add their own thin wrapper around the upstream controller.

Once these five are answered from the real source, the Phase 2 snippet in the implementation plan needs only its wrapped function name and import path changed - the caching logic itself does not depend on which exact names you found.

