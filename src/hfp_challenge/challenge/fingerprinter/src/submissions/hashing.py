import hashlib
import json
from typing import Any


def hash_payload(payload: dict[str, Any]) -> str:
    normalized: dict[str, str] = {}
    for key, value in payload.items():
        if value is None:
            normalized[key] = ""
        elif isinstance(value, bool):
            normalized[key] = "1" if value else "0"
        elif isinstance(value, (int, float)):
            normalized[key] = str(value)
        else:
            normalized[key] = str(value).lower().strip()

    sorted_json = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(sorted_json.encode()).hexdigest()


def hash_keys(payload: dict[str, Any], keys: list[str], digest_len: int = 24) -> str:
    parts = []
    for key in keys:
        value = payload.get(key)
        parts.append("" if value is None else str(value))
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:digest_len]


__all__ = ["hash_payload", "hash_keys"]
