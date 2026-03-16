from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_hex(*parts: Any, length: int = 12) -> str:
    payload = "::".join(canonical_json(part) if isinstance(part, (dict, list, tuple)) else str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]


def stable_seed(*parts: Any) -> int:
    return int(stable_hex(*parts, length=8), 16)


def assign_split(key: str, ratios: dict[str, float]) -> str:
    normalized = dict(ratios)
    total = sum(float(v) for v in normalized.values())
    if total <= 0:
        raise ValueError("Split ratios must sum to a positive number.")
    cumulative = 0.0
    ordered = []
    for name, value in normalized.items():
        frac = float(value) / total
        cumulative += frac
        ordered.append((name, cumulative))
    ticket = int(stable_hex(key, "split", length=8), 16) / 16**8
    for name, cutoff in ordered:
        if ticket <= cutoff:
            return name
    return ordered[-1][0]
