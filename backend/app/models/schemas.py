from __future__ import annotations

from pydantic import BaseModel


class RedactionReportEntry(BaseModel):
    entity_type: str
    placeholder: str
    original: str
    replacement: str
    source: str
    score: float


class RedactionSummaryItem(BaseModel):
    entity_type: str
    count: int


class RedactionReport(BaseModel):
    strategy: str
    total_redactions: int
    entity_types_detected: list[str]
    summary: list[RedactionSummaryItem]
    entries: list[RedactionReportEntry]


class UploadResponse(BaseModel):
    filename: str
    input_kind: str
    extraction_method: str
    strategy: str
    original_text: str
    redacted_text: str
    redaction_count: int
    detected_types: list[str]
    redaction_report: RedactionReport
