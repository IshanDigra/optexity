from optexity.tools.models import CachedStep

def load_steps(path: str) -> list[CachedStep]:
    with open(path) as f:
        return [CachedStep.model_validate_json(line) for line in f if line.strip()]

def filter_redundant(steps: list[CachedStep]) -> list[CachedStep]:
    kept: list[CachedStep] = []
    last_index_by_selector: dict[str, int] = {}

    for step in steps:
        if not step.success:
            continue

        key = step.resolved_selector or f"idx:{step.dom_index}"

        if key in last_index_by_selector and step.action_name in ("input_text", "select_option"):
            kept[last_index_by_selector[key]] = step
            continue

        last_index_by_selector[key] = len(kept)
        kept.append(step)

    return kept
