# Setup Notes

A couple of things that tripped me up during setup. Both fail quietly rather than erroring, so they
cost me a while before I worked out what was going on. Passing them on in case they're worth folding
into the brief for the next person.

---

## `pip install -e .` can quietly do nothing on macOS

This one cost me the most time by far. I'd made my changes in the browser-use fork, installed it with
`pip install -e .`, and nothing happened. No error. `pip list` showed the editable install sitting
there. But my code was never actually running.

What's going on: pip writes a `.pth` file into site-packages pointing at your clone. On macOS that
file can end up with the `UF_HIDDEN` flag set, and Python 3.13's `site.addpackage` skips hidden
`.pth` files — silently, no warning. So the path never makes it onto `sys.path`, and imports fall
back to whatever packaged copy happens to be installed instead.

`chflags nohidden <venv>/lib/python3.13/site-packages/*.pth` clears it, though in my case it came
back later, so I stopped relying on it.

A one-line check after the install steps would catch this:

```bash
python -c "import browser_use, optexity; print(browser_use.__file__); print(optexity.__file__)"
```

Both paths should be inside your clones. If either one points into site-packages, the editable
install didn't take, and the easiest fix is just setting `PYTHONPATH` to the two clone directories
instead of trying to reinstall.

Worth calling out because the main deliverable is a hook inside the browser-use fork. If the
editable install silently didn't work, that hook is dead code and there's nothing obviously wrong to
go looking for.

## The child_process.py patch has drifted

The brief says to add the snippet after line 575. In the current tree line 575 is inside
`get_app_with_endpoints`, which isn't where it belongs. The automation fetch it's meant to follow is
in `task_processor()`, around line 436. Anchoring to the function rather than a line number would
save some hunting, and wouldn't drift again:

> Add the following inside `task_processor()`, right after the automation-fetch `try/except` and
> before the `if not fetch_success:` block.

Two small changes to the snippet itself I'd suggest:

**Read the filename from an environment variable.** The assignment is fundamentally a comparison
between the agentic run and the cached one, and with a hardcoded filename you end up editing source
in between every run. Something like:

```python
local_automation_path = os.environ.get("OPTEXITY_LOCAL_AUTOMATION", "test_automation.json")
if os.path.exists(local_automation_path):
    with open(local_automation_path) as f:
        task.automation = Automation.model_validate(json.load(f))
    fetch_success = True
```

**Mention the parameter filtering.** The endpoint you curl sends `input_parameters` that your local
automation may not declare, and `worker.py` then fails on the unexpected keys. Filtering
`task.input_parameters` down to what the local automation declares avoids a fairly confusing crash.
It also makes the rule visible — if your local automation needs a parameter, it has to declare it.

## One small thing

`.env` can't have a space after the `=`. `export KEY= value` sets the variable to empty and then
tries to export a variable named after the value. The shell error is easy to scroll past, and after
that every LLM call fails on auth, which sends you looking in completely the wrong place.

---

## What ended up working

For reference, this is what I sourced in every terminal:

```bash
OPTEXITY_ROOT="${HOME}/Desktop/Optexity"

cd "${OPTEXITY_ROOT}/optexity"
source .env
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

`PYTHONPATH` sidesteps the `.pth` problem entirely, and the check at the end tells you straight away
whether the hook is actually loaded before you spend a run finding out it isn't.
