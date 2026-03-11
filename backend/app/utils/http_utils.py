from __future__ import annotations

import json
import re
from pathlib import Path


def json_bytes(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def parse_multipart_form(headers: dict[str, str], body: bytes) -> tuple[dict[str, str], tuple[str, bytes]]:
    content_type = headers.get("content-type", "")
    boundary_match = re.search(r"boundary=(.+)", content_type)
    if "multipart/form-data" not in content_type or not boundary_match:
        raise ValueError("Expected multipart/form-data upload.")

    boundary = boundary_match.group(1).strip().strip('"')
    boundary_bytes = f"--{boundary}".encode("utf-8")
    parts = [part for part in body.split(boundary_bytes) if b"Content-Disposition" in part]
    fields: dict[str, str] = {}
    uploaded_file: tuple[str, bytes] | None = None

    for part in parts:
        header_blob, _, content = part.partition(b"\r\n\r\n")
        header_text = header_blob.decode("utf-8", errors="ignore")
        name_match = re.search(r'name="(?P<name>[^"]+)"', header_text, re.IGNORECASE)
        if not name_match:
            continue

        filename_match = re.search(r'filename="(?P<filename>[^"]*)"', header_text, re.IGNORECASE)
        field_name = name_match.group("name")
        filename = filename_match.group("filename") if filename_match else None
        content_bytes = content.rstrip(b"\r\n-")

        if field_name == "file" and filename:
            safe_filename = Path(filename).name or "uploaded-document.txt"
            uploaded_file = (safe_filename, content_bytes)
            continue

        fields[field_name] = content_bytes.decode("utf-8", errors="ignore").strip()

    if not uploaded_file:
        raise ValueError("No file field named 'file' was found in the request.")

    return fields, uploaded_file
