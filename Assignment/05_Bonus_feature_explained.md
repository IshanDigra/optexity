# Bonus Features, Explained Simply

The code-level version of these two features lives in `02_implementation_plan.md` Phase 7 (7a and 7b). This doc is the plain-language version - no code, just what each one does and why it exists.

## Quick recap of the core (non-bonus) idea

1. Run the AI agent once on a task (e.g. "fill this form"). It works, but slowly and expensively - the LLM has to reason at every single click.
2. Log every action it took.
3. **A human** looks at that log and hand-writes a fast, deterministic script that replays the same actions without any AI involved - no more LLM cost, no more waiting.

That hand-writing step in #3 is manual work. The two bonus features each attack a different weakness in that setup.

## Bonus 1 (Phase 7a): LLM-assisted auto-build - "let the AI write the conversion, not just a human"

**The problem it solves:** step 3 above requires a person to sit down and translate the raw log into the final script by hand. That's tedious, and doesn't scale if there are hundreds of tasks to convert.

**The idea:** instead of a human writing that translation, ask an LLM to do it: *"Here's the raw log of what the agent did, and here's the exact format the final script needs to be in - please write the deterministic version for me."*

**The safety net:** LLMs can produce broken or subtly wrong output, so two guardrails are built in:
- Whatever the LLM produces is checked against Optexity's official rulebook (its schema validator). If it's malformed, the exact error is fed straight back to the LLM - *"this failed, here's why, fix it"* - and it gets a couple of retries.
- The human-written version from step 3 is kept around as an answer key, and the AI's version is compared against it. If they disagree, that's a signal to double-check before trusting the AI's version.

**Analogy:** step 3 alone is "you translate this document yourself." Bonus 1 is "have a translator do it, but keep your own translation as an answer key, and have someone proofread the translator's spelling before publishing."

## Bonus 2 (Phase 7b): Self-healing loop - "when the fast script breaks, only fix the broken part"

**The problem it solves:** the deterministic script from step 3 is fast, but brittle. If the website changes even slightly (a button moves, a label gets renamed), the script can break - it's just replaying fixed clicks, with no ability to reason about what changed.

**The idea:** instead of the whole automation failing outright when one step breaks, the system notices *which single step* failed, temporarily calls the AI agent back in - but only to solve that one broken step, not the whole task from scratch - records what the AI did to fix it, and patches just that one step in the script. Every other step that still works is left untouched.

**Analogy:** imagine a recipe card with 10 steps written out so anyone can follow it without thinking. One day step 6 stops working because the store changed how an ingredient is packaged. Instead of throwing out the whole recipe and improvising from scratch, you call an expert cook just for step 6, watch how they solve it, write *that one step* back onto the card, and keep using the same recipe for the other 9 steps.

## Why these are "bonus" and not required

The core assignment already proves the main point - agentic once, then cached and deterministic forever after, faster and cheaper - using a human to do the conversion one time. Both bonus items are about removing the human from a different moment: Bonus 1 removes the human from writing the conversion the first time; Bonus 2 removes the human from fixing it when it later breaks. Neither is needed to demonstrate the core idea works - they show the design was thought through past a one-shot demo, toward something that could run unattended.