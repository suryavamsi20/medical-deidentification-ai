from __future__ import annotations

import re

from ..models.entities import Detection
from . import synthetic_data
from .entity_merger import resolve_overlaps
from .llm_phi_detector import extract_names, looks_like_name, normalize_name_candidate
from .phi_detector import detect_phi
from .report_generator import build_report


NAME_TOKEN = r"[A-Za-z][A-Za-z'.-]*"
HONORIFIC = r"(?:(?:Mr|Mrs|Ms|Miss|Dr)\.?\s+)?"
CAPTURED_NAME = rf"({HONORIFIC}{NAME_TOKEN}(?:\s+{NAME_TOKEN}){{0,3}})"

PATIENT_NAME_PATTERNS = (
    re.compile(rf"(?im)^(?:patient\s*name|patient)\s*[:\-]\s*{CAPTURED_NAME}\s*$"),
    re.compile(rf"(?im)\bpatient\s*name\s*[:\-]\s*{CAPTURED_NAME}\b"),
)

CLINICIAN_NAME_PATTERNS = (
    re.compile(rf"(?im)^(?:doctor|dr|referred\s*by|consultant)\s*[:\-]\s*{CAPTURED_NAME}\s*$"),
    re.compile(rf"(?im)\b(?:doctor|dr|referred\s*by|consultant)\s*[:\-]\s*{CAPTURED_NAME}\b"),
)

ENTITY_CONFIG = {
    "patient_name": {"placeholder": "[PATIENT_NAME]", "synthetic_factory": synthetic_data.patient_name},
    "clinician_name": {"placeholder": "[CLINICIAN_NAME]", "synthetic_factory": synthetic_data.clinician_name},
    "person_name": {"placeholder": "[PERSON_NAME]", "synthetic_factory": synthetic_data.person_name},
    "email": {"placeholder": "[EMAIL_ADDRESS]", "synthetic_factory": synthetic_data.email},
    "phone": {"placeholder": "[PHONE_NUMBER]", "synthetic_factory": synthetic_data.phone},
    "ssn": {"placeholder": "[SOCIAL_SECURITY_NUMBER]", "synthetic_factory": synthetic_data.ssn},
    "mrn": {"placeholder": "[MEDICAL_RECORD_NUMBER]", "synthetic_factory": synthetic_data.mrn},
    "account_number": {"placeholder": "[ACCOUNT_NUMBER]", "synthetic_factory": synthetic_data.account_number},
    "policy_number": {"placeholder": "[POLICY_NUMBER]", "synthetic_factory": synthetic_data.policy_number},
    "license_number": {"placeholder": "[LICENSE_NUMBER]", "synthetic_factory": synthetic_data.license_number},
    "date": {"placeholder": "[DATE]", "synthetic_factory": synthetic_data.date},
    "address": {"placeholder": "[ADDRESS]", "synthetic_factory": synthetic_data.address},
    "ip_address": {"placeholder": "[IP_ADDRESS]", "synthetic_factory": synthetic_data.ip_address},
    "url": {"placeholder": "[URL]", "synthetic_factory": synthetic_data.url},
    "age_over_89": {"placeholder": "[AGE_OVER_89]", "synthetic_factory": synthetic_data.age_over_89},
}


def resolve_replacement(entity_type: str, original: str, strategy: str) -> tuple[str, str]:
    config = ENTITY_CONFIG[entity_type]
    placeholder = config["placeholder"]
    replacement = config["synthetic_factory"](original) if strategy == "synthetic" else placeholder
    return placeholder, replacement


def find_all_occurrences(text: str, value: str) -> list[tuple[int, int]]:
    if not value:
        return []
    pattern = re.compile(rf"\b{re.escape(value)}\b", re.IGNORECASE)
    return [(match.start(), match.end()) for match in pattern.finditer(text)]


def build_name_detections(text: str, strategy: str) -> list[Detection]:
    candidates: dict[tuple[str, str], str] = {}

    def capture_patterns(patterns: tuple[re.Pattern[str], ...], entity_type: str) -> None:
        for pattern in patterns:
            for match in pattern.finditer(text):
                candidate = normalize_name_candidate(match.group(1))
                if looks_like_name(candidate):
                    candidates[(entity_type, candidate.lower())] = candidate

    capture_patterns(PATIENT_NAME_PATTERNS, "patient_name")
    capture_patterns(CLINICIAN_NAME_PATTERNS, "clinician_name")

    llm_names = extract_names(text)
    for candidate in llm_names["patient_names"]:
        if looks_like_name(candidate):
            candidates[("patient_name", candidate.lower())] = candidate
    for candidate in llm_names["clinician_names"]:
        if looks_like_name(candidate):
            candidates[("clinician_name", candidate.lower())] = candidate

    detections: list[Detection] = []
    for (entity_type, _), candidate in candidates.items():
        placeholder, replacement = resolve_replacement(entity_type, candidate, strategy)
        for start, end in find_all_occurrences(text, candidate):
            detections.append(
                Detection(
                    entity_type=entity_type,
                    start=start,
                    end=end,
                    original=text[start:end],
                    placeholder=placeholder,
                    replacement=replacement,
                    source="ollama_label_hybrid",
                    score=0.98,
                )
            )
    return detections


def apply_detections(text: str, detections: list[Detection]) -> str:
    if not detections:
        return text

    pieces: list[str] = []
    cursor = 0
    for detection in detections:
        pieces.append(text[cursor : detection.start])
        pieces.append(detection.replacement)
        cursor = detection.end
    pieces.append(text[cursor:])
    return "".join(pieces)


def deidentify_text(text: str, strategy: str = "placeholder") -> dict[str, object]:
    normalized_strategy = strategy.strip().lower() if strategy else "placeholder"
    if normalized_strategy not in {"placeholder", "synthetic"}:
        raise ValueError("Strategy must be either 'placeholder' or 'synthetic'.")

    def replacement_resolver(entity_type: str, original: str) -> tuple[str, str]:
        return resolve_replacement(entity_type, original, normalized_strategy)

    detections = build_name_detections(text, normalized_strategy) + detect_phi(text, replacement_resolver)
    merged = resolve_overlaps(detections)
    redacted_text = apply_detections(text, merged)
    report = build_report(normalized_strategy, merged)

    return {
        "original_text": text,
        "redacted_text": redacted_text,
        "redaction_count": report["total_redactions"],
        "detected_types": report["entity_types_detected"],
        "redaction_report": report,
    }
