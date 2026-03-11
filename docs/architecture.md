# Architecture

## Backend

The backend is organized as a small service-oriented package:

- `backend/app/main.py`
  FastAPI application bootstrap.
- `backend/app/api/routes.py`
  HTTP routes for health and document upload.
- `backend/app/api/http_server.py`
  Optional standard-library HTTP entry point.
- `backend/app/services/phi_detector.py`
  Presidio + SpaCy structured PHI detection.
- `backend/app/services/llm_phi_detector.py`
  Ollama-assisted patient and clinician name extraction.
- `backend/app/services/entity_merger.py`
  Overlap resolution for competing detections.
- `backend/app/services/redactor.py`
  Main orchestration of detection, replacement, and final response payloads.
- `backend/app/services/synthetic_data.py`
  Deterministic fake-value generation for anonymization mode.
- `backend/app/services/report_generator.py`
  Redaction report construction.
- `backend/app/utils/file_parser.py`
  OCR and PDF/text extraction.
- `backend/app/utils/http_utils.py`
  Multipart parsing and JSON helpers for the lightweight HTTP server.
- `backend/app/models/entities.py`
  Internal detection dataclass.
- `backend/app/models/schemas.py`
  API response schemas.
- `backend/app/core/config.py`
  Central settings and environment-driven configuration.

## Frontend

The frontend remains a simple React upload interface:

- `frontend/src/components/UploadBox.jsx`
  File selection and de-identification strategy selection.
- `frontend/src/pages/Dashboard.jsx`
  Before/after display and audit report rendering.
- `frontend/src/services/api.js`
  API client for multipart upload requests.

## Request Flow

1. A user uploads a text, PDF, or image document from the frontend.
2. The backend parses the file and extracts text directly or through OCR.
3. Ollama extracts patient and clinician names from the medical context.
4. Presidio + SpaCy detect structured PHI entities.
5. Detections are merged, redacted or replaced with synthetic values, and summarized into a report.
6. The frontend renders original text, redacted text, metadata, and the audit trail.
