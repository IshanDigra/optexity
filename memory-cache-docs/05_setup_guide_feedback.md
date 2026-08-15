# Setup Guide — Suggested Corrections

Feedback on the assignment brief's setup section, from actually following it. Four things cost real
time, and all four fail *silently* — no error, just behaviour that looks like your own bug. Each is
listed with the symptom first, since that is how a candidate meets it.

---

## 1. Forking gives you a branch that cannot run

**Symptom:** `ImportError: cannot import name 'Agent' from 'browser_use'`, or the agentic task
returns instantly having done nothing, or
`get_browser_state_summary() got an unexpected keyword argument 'include_full_page'`.

**Cause:** `Optexity/browser-use`'s default branch is `main`, which is a plain copy of public
browser-use `0.11.4`. Forking and cloning gives you that. But `optexity` depends on
`optexity-browser-use>=0.9.5`, and the code that satisfies it lives on a **different branch of the
same repo**, called `optexity` — published as `optexity-browser-use 0.9.5.4`, and carrying API the
public project does not have (`include_full_page` among it).

Following the brief exactly produces a setup where `optexity` cannot drive `browser_use`, and the
failure surfaces far from the cause.

**Suggested wording:**

> 4. Fork https://github.com/Optexity/browser-use
> 5. Clone your fork, then check out the **`optexity` branch** — `main` is upstream browser-use and
>    is not the version optexity runs against:
>    ```bash
>    git clone https://github.com/<you>/browser-use && cd browser-use
>    git remote add upstream https://github.com/Optexity/browser-use
>    git fetch upstream optexity && git checkout -b optexity upstream/optexity
>    ```
>    Confirm before continuing — this must print `optexity-browser-use`:
>    ```bash
>    grep '^name' pyproject.toml
>    ```

Alternatively, making `optexity` the default branch of that repo would remove the trap entirely.

## 2. `pip install -e .` can silently do nothing on macOS

**Symptom:** edits to your clone have no effect. `pip list` shows the editable install. No error
anywhere.

**Cause:** the `.pth` file pip writes into `site-packages` picks up macOS's `UF_HIDDEN` flag, and
Python 3.13's `site.addpackage` **skips hidden `.pth` files without logging**. The editable path is
never added to `sys.path`, so imports quietly resolve to a packaged copy instead. `chflags nohidden`
clears it, but it can come back.

This one is expensive: it makes the assignment's core deliverable — a hook inside your browser-use
fork — dead code, while everything appears installed correctly.

**Suggested addition:** a verification step after each install, which catches this and §3 at once:

> ```bash
> python -c "import browser_use, optexity; print(browser_use.__file__); print(optexity.__file__)"
> ```
> Both paths must point inside your clones. If either points into `site-packages`, the editable
> install did not take effect — set `PYTHONPATH` to the two clone directories rather than
> reinstalling.

## 3. Install order: the warning understates it

The brief says *"otherwise optexity install might override browser use install locally"*. In practice
both distributions provide the same top-level `browser_use` package, so whichever is installed second
wins and **there is no warning at all** — not a conflict message, not a version mismatch.

Worth stating the consequence explicitly, and noting that `pip install -e ./browser-use --no-deps` is
usually what you want: the fork's dependency pins can otherwise pull `openai` past the ceiling
`optexity`'s `litellm` pin requires.

## 4. The `child_process.py` patch has drifted

**Symptom:** the snippet lands in the middle of an unrelated function.

Line 575 is now inside `get_app_with_endpoints`. The automation fetch it is meant to follow is in
`task_processor()`, around line 436 in the current tree. Anchoring to a function name rather than a
line number would survive future edits:

> Add the following inside `task_processor()`, immediately after the automation-fetch `try/except`
> and before the `if not fetch_success:` block.

Two improvements worth folding into the snippet itself:

**Read the filename from an environment variable.** The A/B the assignment is graded on requires
alternating between the agentic and cached automations. Hardcoding one filename means editing source
between every run:

```python
local_automation_path = os.environ.get("OPTEXITY_LOCAL_AUTOMATION", "test_automation.json")
if os.path.exists(local_automation_path):
    with open(local_automation_path) as f:
        task.automation = Automation.model_validate(json.load(f))
    fetch_success = True
```

**Mention the parameter filtering.** The endpoint you curl supplies `input_parameters` the local
automation may not declare, and `worker.py` fails on the unexpected keys. Filtering
`task.input_parameters` to what the local automation declares avoids a confusing crash — and tells
candidates that a local automation needing a parameter must declare it.

---

## Things the brief gets right and should keep

- Providing the exact starting `test_automation.json`. Removes all ambiguity about the target.
- *"the values in the commands should be sourced from what you derive from the caching and not made
  up."* This is the sentence that defines the task. It rules out hand-writing the answer while
  leaving the approach open.
- Requiring a **multi-step** second site. A single-page form only ever produces `input_text` nodes,
  so it never exercises clicks or navigation — where cached locators are most fragile. Site 2 is
  where the interesting failures live.
- Not opening PRs against the upstream repos.

## One addition worth considering

A note that the agent may solve a task via **JavaScript** (browser-use's `evaluate` action) rather
than clicks. When it does, it changes page state without touching an element, so there is no locator
to cache and the memory layer has nothing to learn — the cache looks nearly empty for a task that
visibly succeeded. It is a genuinely instructive obstacle, so it may be worth leaving in place rather
than warning about; but it is the kind of thing that reads as a broken hook when it is not.

---

## Working environment setup

For reference, this reliably produced a working environment. Sourced in every terminal:

```bash
OPTEXITY_ROOT="${HOME}/Desktop/Optexity"

cd "${OPTEXITY_ROOT}/optexity"
source .env                                   # note: no spaces around `=` in .env
export ENV_PATH="${OPTEXITY_ROOT}/optexity/.env"
export PYTHONPATH="${OPTEXITY_ROOT}/browser-use:${OPTEXITY_ROOT}/optexity"
export PATH="${OPTEXITY_ROOT}/optexity/.venv/bin:${PATH}"

python -c "
import browser_use
from browser_use.tools.registry.service import Registry
print(browser_use.__file__)
print('hook active:', Registry.execute_action.__qualname__.startswith('cached'))
"
```

`PYTHONPATH` sidesteps §2 entirely, and the final check catches §1, §2 and §3 in one command.

One more small trap: `.env` must have no space after `=`. `export KEY= value` sets the variable to
empty and then tries to export a variable named after the value — the shell error is easy to miss,
and every LLM call then fails authentication.
