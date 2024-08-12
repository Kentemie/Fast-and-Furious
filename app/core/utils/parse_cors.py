from typing import Any


def parse_cors(value: Any) -> list[str] | str:
    if isinstance(value, str) and not value.startswith("["):
        return [i.strip() for i in value.split(",")]
    elif isinstance(value, list | str):
        return value
    raise ValueError(value)
