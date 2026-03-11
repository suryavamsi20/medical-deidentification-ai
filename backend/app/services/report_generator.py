from __future__ import annotations

from collections import Counter

from ..models.entities import Detection


def build_report(strategy: str, detections: list[Detection]) -> dict[str, object]:
    counts = Counter(detection.entity_type for detection in detections)
    summary = [{"entity_type": entity_type, "count": count} for entity_type, count in sorted(counts.items())]
    entries = [
        {
            "entity_type": detection.entity_type,
            "placeholder": detection.placeholder,
            "original": detection.original,
            "replacement": detection.replacement,
            "source": detection.source,
            "score": round(detection.score, 4),
        }
        for detection in detections
    ]
    return {
        "strategy": strategy,
        "total_redactions": len(detections),
        "entity_types_detected": [item["entity_type"] for item in summary],
        "summary": summary,
        "entries": entries,
    }
