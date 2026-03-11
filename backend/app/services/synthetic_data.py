from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta


def stable_index(value: str, size: int) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % size


def stable_digits(value: str, length: int) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    digits = "".join(str(int(char, 16) % 10) for char in digest)
    while len(digits) < length:
        digits += digits
    return digits[:length]


def patient_name(value: str) -> str:
    first_names = ["Aarav", "Maya", "Noah", "Elena", "Luca", "Nina", "Owen", "Sara"]
    last_names = ["Carter", "Iyer", "Mitchell", "Patel", "Reed", "Shaw", "Turner", "Brooks"]
    return f"{first_names[stable_index(value, len(first_names))]} {last_names[stable_index(value[::-1], len(last_names))]}"


def clinician_name(value: str) -> str:
    first_names = ["Amelia", "Daniel", "Grace", "Henry", "Leah", "Marcus", "Priya", "Victor"]
    last_names = ["Adams", "Bennett", "Clark", "Dawson", "Evans", "Foster", "Hayes", "Morgan"]
    return f"Dr. {first_names[stable_index(value, len(first_names))]} {last_names[stable_index(value[::-1], len(last_names))]}"


def person_name(value: str) -> str:
    return patient_name(value)


def phone(value: str) -> str:
    digits = stable_digits(value, 7)
    return f"202-555-{digits[-4:]}"


def ssn(value: str) -> str:
    digits = stable_digits(value, 9)
    return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"


def mrn(value: str) -> str:
    return f"MRN-{stable_digits(value, 8)}"


def account_number(value: str) -> str:
    return f"ACCT-{stable_digits(value, 8)}"


def policy_number(value: str) -> str:
    return f"POL-{stable_digits(value, 6)}"


def license_number(value: str) -> str:
    return f"DL-{stable_digits(value, 7)}"


def ip_address(value: str) -> str:
    digits = stable_digits(value, 4)
    octets = [
        str(10 + int(digits[0]) % 20),
        str(20 + int(digits[1]) % 50),
        str(30 + int(digits[2]) % 50),
        str(40 + int(digits[3]) % 50),
    ]
    return ".".join(octets)


def url(value: str) -> str:
    paths = ["patient-summary", "clinical-note", "imaging-report", "follow-up"]
    return f"https://demohealth.org/{paths[stable_index(value, len(paths))]}/{stable_digits(value, 5)}"


def age_over_89(value: str) -> str:
    return "90 years old"


def email(value: str) -> str:
    locals_ = ["care.team", "patient.alias", "clinical.record", "health.user"]
    domains = ["demohealth.org", "syntheticclinic.net", "trialhospital.com"]
    return f"{locals_[stable_index(value, len(locals_))]}@{domains[stable_index(value[::-1], len(domains))]}"


def address(value: str) -> str:
    streets = ["Maple Avenue", "Oak Street", "River Drive", "Cedar Lane", "Park Boulevard"]
    number = int(stable_digits(value, 4))
    return f"{100 + (number % 8900)} {streets[stable_index(value, len(streets))]}"


def date(value: str) -> str:
    formats = ("%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y", "%d-%m-%Y", "%m-%d-%Y", "%b %d, %Y", "%B %d, %Y")
    normalized = re.sub(r"\s+", " ", value.strip())
    for fmt in formats:
        try:
            parsed = datetime.strptime(normalized, fmt)
            shifted = parsed + timedelta(days=(stable_index(value, 27) + 3))
            return shifted.strftime(fmt)
        except ValueError:
            continue
    return "01/15/2030"
