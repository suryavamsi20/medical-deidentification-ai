from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from ..core.config import settings


NAME_TOKEN = r"[A-Za-z][A-Za-z'.-]*"
NON_NAME_VALUES = {
    "self",
    "male",
    "female",
    "cbc",
    "complete blood count",
    "test name",
    "reference range",
    "result",
    "unit",
}


def normalize_name_candidate(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip(" :;-")).strip()


def looks_like_name(value: str) -> bool:
    normalized = normalize_name_candidate(value)
    if not normalized:
        return False

    lowered = normalized.lower()
    if lowered in NON_NAME_VALUES:
        return False

    tokens = [token for token in re.split(r"\s+", normalized) if token]
    if not tokens or len(tokens) > 5:
        return False

    if any(any(char.isdigit() for char in token) for token in tokens):
        return False

    meaningful_tokens = [
        token for token in tokens if token.rstrip(".").lower() not in {"mr", "mrs", "ms", "miss", "dr"}
    ]
    if not meaningful_tokens:
        return False

    return all(re.fullmatch(NAME_TOKEN, token) for token in meaningful_tokens)


def looks_like_freeform_person(value: str) -> bool:
    if not looks_like_name(value):
        return False
    tokens = [token for token in re.split(r"\s+", normalize_name_candidate(value)) if token]
    meaningful_tokens = [
        token for token in tokens if token.rstrip(".").lower() not in {"mr", "mrs", "ms", "miss", "dr"}
    ]
    return len(meaningful_tokens) >= 2


def extract_names(text: str) -> dict[str, list[str]]:
    prompt = (
        "Extract explicit human names from this medical document.\n"
        "Return strict JSON with keys patient_names and clinician_names.\n"
        "Rules:\n"
        "- Include only names of people.\n"
        "- Do not include SELF, Male, Female, CBC, test names, organizations, IDs, or headers.\n"
        "- Preserve the exact surface form from the text when possible.\n"
        "- If none exist, return empty arrays.\n\n"
        f"Document:\n{text[:6000]}"
    )
    payload = json.dumps(
        {
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        settings.ollama_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
            parsed = json.loads(data.get("response", "{}"))
            return {
                "patient_names": [normalize_name_candidate(name) for name in parsed.get("patient_names", [])],
                "clinician_names": [normalize_name_candidate(name) for name in parsed.get("clinician_names", [])],
            }
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return {"patient_names": [], "clinician_names": []}
