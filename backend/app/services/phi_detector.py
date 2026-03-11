from __future__ import annotations

import re
from functools import lru_cache

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider

from ..models.entities import Detection
from .llm_phi_detector import looks_like_freeform_person


PRESIDIO_ENTITY_MAP = {
    "PERSON": "person_name",
    "EMAIL_ADDRESS": "email",
    "PHONE_NUMBER": "phone",
    "US_SSN": "ssn",
    "DATE_TIME": "date",
    "URL": "url",
    "IP_ADDRESS": "ip_address",
    "MEDICAL_RECORD_NUMBER": "mrn",
    "ACCOUNT_NUMBER": "account_number",
    "POLICY_NUMBER": "policy_number",
    "LICENSE_NUMBER": "license_number",
    "ADDRESS": "address",
    "AGE_OVER_89": "age_over_89",
}


@lru_cache(maxsize=1)
def get_analyzer() -> AnalyzerEngine:
    configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
    }
    provider = NlpEngineProvider(nlp_configuration=configuration)
    nlp_engine = provider.create_engine()
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])

    recognizers = [
        PatternRecognizer(
            supported_entity="MEDICAL_RECORD_NUMBER",
            patterns=[Pattern("mrn_pattern", r"\b(?:MRN|Medical Record Number|Patient ID)[:#\s-]*[A-Z0-9]{5,}\b", 0.9)],
        ),
        PatternRecognizer(
            supported_entity="ACCOUNT_NUMBER",
            patterns=[Pattern("account_pattern", r"\b(?:Account Number|Acct(?:ount)?(?: No\.?| Number)?)[:#\s-]*[A-Z0-9-]{5,}\b", 0.85)],
        ),
        PatternRecognizer(
            supported_entity="POLICY_NUMBER",
            patterns=[Pattern("policy_pattern", r"\b(?:Policy Number|Policy No\.?|Member ID|Subscriber ID|Insurance ID)[:#\s-]*[A-Z0-9-]{5,}\b", 0.85)],
        ),
        PatternRecognizer(
            supported_entity="LICENSE_NUMBER",
            patterns=[Pattern("license_pattern", r"\b(?:Driver(?:'s)? License|License Number|License No\.?)[:#\s-]*[A-Z0-9-]{5,}\b", 0.85)],
        ),
        PatternRecognizer(
            supported_entity="ADDRESS",
            patterns=[Pattern("address_pattern", r"\b\d{1,5}[ ]+[A-Z][A-Za-z0-9., ]{3,40}[ ](?:Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Drive|Dr|Boulevard|Blvd)\b", 0.7)],
        ),
        PatternRecognizer(
            supported_entity="URL",
            patterns=[Pattern("url_pattern", r"\bhttps?://[^\s]+", 0.85)],
        ),
        PatternRecognizer(
            supported_entity="IP_ADDRESS",
            patterns=[Pattern("ip_pattern", r"\b(?:\d{1,3}\.){3}\d{1,3}\b", 0.85)],
        ),
        PatternRecognizer(
            supported_entity="AGE_OVER_89",
            patterns=[Pattern("age_pattern", r"\b(?:9\d|1[01]\d|12\d)\s*(?:years?\s*old|yo|y/o)\b", 0.85)],
        ),
    ]

    for recognizer in recognizers:
        analyzer.registry.add_recognizer(recognizer)

    return analyzer


def detect_phi(text: str, replacement_resolver) -> list[Detection]:
    analyzer = get_analyzer()
    results = analyzer.analyze(
        text=text,
        language="en",
        entities=[
            "PERSON",
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "US_SSN",
            "DATE_TIME",
            "URL",
            "IP_ADDRESS",
            "MEDICAL_RECORD_NUMBER",
            "ACCOUNT_NUMBER",
            "POLICY_NUMBER",
            "LICENSE_NUMBER",
            "ADDRESS",
            "AGE_OVER_89",
        ],
    )

    detections: list[Detection] = []
    for result in results:
        entity_type = PRESIDIO_ENTITY_MAP.get(result.entity_type)
        if not entity_type:
            continue

        original = text[result.start : result.end]
        if entity_type == "date" and re.search(r"\b(?:9\d|1[01]\d|12\d)\s*(?:years?\s*old|yo|y/o)\b", original, re.IGNORECASE):
            continue
        if entity_type == "person_name" and not looks_like_freeform_person(original):
            continue

        placeholder, replacement = replacement_resolver(entity_type, original)
        detections.append(
            Detection(
                entity_type=entity_type,
                start=result.start,
                end=result.end,
                original=original,
                placeholder=placeholder,
                replacement=replacement,
                source=f"presidio:{result.entity_type}",
                score=float(result.score),
            )
        )

    return detections
