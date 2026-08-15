from typing import Literal

from pydantic import BaseModel


class CachedStep(BaseModel):
    step_index: int
    action_name: str
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
