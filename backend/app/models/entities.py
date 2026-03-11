from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Detection:
    entity_type: str
    start: int
    end: int
    original: str
    placeholder: str
    replacement: str
    source: str
    score: float
