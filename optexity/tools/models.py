"""Read-side mirror of `browser_use.memory_cache.models.CachedStep`.

Deliberately duplicated rather than imported: the two sides only need to agree on the JSON shape
of `cache.jsonl`, not share a Python object, and importing across the fork boundary at runtime
would couple this package to browser-use internals for the sake of a dozen lines.
"""

from typing import Literal

from pydantic import BaseModel


class CachedStep(BaseModel):
    step_index: int
    action_name: str  # the registered browser-use action, e.g. 'click', 'input', 'navigate'
    dom_index: int | None = None
    resolved_selector: str | None = None
    resolved_selector_strategy: Literal[
        "role", "label", "test_id", "text", "css", "xpath", "unknown"
    ] = "unknown"
    accessible_name: str | None = None
    value: str | None = None
    page_url_before: str
    success: bool
    timestamp: float
