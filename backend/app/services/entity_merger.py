from __future__ import annotations

from ..models.entities import Detection


def resolve_overlaps(detections: list[Detection]) -> list[Detection]:
    ordered = sorted(detections, key=lambda item: (item.start, -(item.end - item.start), -item.score))
    chosen: list[Detection] = []

    for detection in ordered:
        overlaps = False
        for existing in chosen:
            if not (detection.end <= existing.start or detection.start >= existing.end):
                overlaps = True
                break
        if not overlaps:
            chosen.append(detection)

    return sorted(chosen, key=lambda item: item.start)
