# Changelog

## Overview
This change implements a deterministic caching layer for AI agent workflows. The goal is to record an initial LLM-driven run (which is slow and expensive) and convert its actions into a deterministic automation script (fast and cheap) for subsequent executions.

## Features Implemented

### 1. Model Definition (`optexity/tools/models.py`)
- Created `CachedStep` Pydantic model to define the schema for steps cached during an agentic run.
- Captures details such as action name, DOM index, resolved selector, value, and page URL.

### 2. Cache Filtering (`optexity/tools/filter.py`)
- Implemented `filter_redundant` to remove failed attempts (e.g., when the LLM makes an error) and collapse repeated writes (last-write-wins) to the same field, optimizing the generated automation.
- Reduces noise in the cached steps to yield a clean final script.

### 3. Automation Converter (`optexity/tools/cache_to_automation.py`)
- Implemented `build_automation` and `build_node` functions to parse cached steps and map them to Optexity interaction actions.
- Respects Optexity's locator preference order (`role` > `label` > `test_id` > `text` > `css` > `xpath`).
- Automatically validates the resulting dictionary against the `Automation` Pydantic schema to catch errors early.

### 4. Converter Unit Tests (`optexity/tools/test_cache_to_automation.py`)
- Created a robust test suite for the conversion process.
- Validates that normal paths build valid nodes, filtering correctly deduplicates elements, xpath logic behaves properly, and the full built structure matches the expected Pydantic definitions.

### 5. Local Dev Overrides (`optexity/inference/child_process.py`)
- Added logic in the child process's task allocation sequence to optionally pull the `Automation` definition straight from disk (`test_automation_cached.json` or `test_automation.json`) rather than failing out waiting for the server.

### 6. LLM Auto-build Bonus (`optexity/tools/llm_cache_to_automation.py`)
- Added an experimental LLM-assisted building path that generates an `Automation` schema using LiteLLM.
- Includes a self-correcting retry loop based on schema validation errors.

### 7. Self-Healing Runner Bonus (`optexity/tools/self_healing_runner.py`)
- Implemented logic that iterates over a generated automation, intercepts node failures, and selectively falls back to scoped `agentic_task`s to patch those nodes without rewriting the entire cache file.

### 8. Performance Comparison (`optexity/tools/run_and_compare.py`)
- Added a simple harness to measure the `elapsed_seconds` and `llm_calls` differences between the original agentic file and its cached equivalent.
