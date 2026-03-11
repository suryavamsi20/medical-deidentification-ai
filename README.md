# Medical De-Identification AI

Medical De-Identification AI is a containerized full-stack application for removing protected health information (PHI) from clinical notes, PDFs, and medical images. The stack includes:

- `frontend`: React + Vite UI served from Nginx
- `backend`: FastAPI API for parsing, OCR, PHI detection, redaction, and reporting
- `ollama`: local model service used for document-aware name extraction

## Features

- Upload plain text, PDF, and image files
- Extract embedded PDF text when available
- Fall back to OCR for scanned PDFs and images
- Detect PHI with a hybrid pipeline using Presidio, spaCy, regex recognizers, and Ollama
- Redact with placeholders or replace with deterministic synthetic values
- Return an audit-friendly redaction report

## Implementation Design

### Model Choice

The backend uses a hybrid approach instead of relying on a single model:

- `Presidio + spaCy` handle broad PHI categories such as dates, emails, phone numbers, URLs, addresses, and identifiers
- `Custom regex recognizers` cover healthcare-specific structured values such as MRNs, policy numbers, and account numbers
- `Ollama` is used narrowly for patient and clinician name extraction, where document context matters more than pure pattern matching

This split keeps the pipeline practical: deterministic detectors handle structured PHI, while the local LLM helps with ambiguous human-name extraction in clinical text.

### OCR Handling

OCR lives in [`backend/app/utils/file_parser.py`](/c:/Users/eluri surya vamsi/medical-deidentification-ai/backend/app/utils/file_parser.py):

- Text files are decoded directly
- PDFs are first read with `pypdf`
- If a PDF page has no extractable text, the backend renders pages with `PyMuPDF`
- Rendered pages and uploaded images are passed through `RapidOCR`

That means the same upload route can handle both digitally generated documents and scanned medical paperwork.

### Context Preservation Strategy

The redaction strategy is designed to preserve medical meaning while removing identifiers:

- Replacements are entity-specific, not generic blanket masking
- Placeholder mode uses semantic labels like `[PATIENT_NAME]` and `[DATE]` so the clinical role of each value remains readable
- Synthetic mode generates realistic stand-ins of the same type, which preserves note structure for demos and downstream review
- Name detection is merged with structured detections through overlap resolution so the final redacted text stays coherent and avoids duplicate substitutions

The result is that the note remains clinically interpretable even after PHI removal.

## Project Structure

```text
medical-deidentification-ai/
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- core/
|   |   |-- models/
|   |   |-- services/
|   |   `-- utils/
|   |-- Dockerfile
|   `-- requirements.txt
|-- frontend/
|   |-- src/
|   |-- Dockerfile
|   `-- nginx.conf
|-- docs/
|-- .dockerignore
|-- .env.example
`-- docker-compose.yml
```

## Environment Variables

Copy the example file if you want to override defaults:

```powershell
Copy-Item .env.example .env
```

Available variables:

| Variable | Default | Purpose |
|---|---|---|
| `BACKEND_PORT` | `8000` | Host port mapped to the FastAPI container |
| `FRONTEND_PORT` | `5173` | Host port mapped to the frontend container |
| `OLLAMA_PORT` | `11434` | Host port mapped to the Ollama container |
| `MAX_UPLOAD_SIZE_MB` | `5` | Maximum allowed upload size |
| `OLLAMA_MODEL` | `llama3:latest` | Model pulled by the Ollama init service |
| `VITE_API_BASE_URL` | `http://localhost:8000` | API URL baked into the frontend image at build time |

## Docker Setup

### Prerequisites

- Docker Desktop with Docker Compose enabled
- Enough disk space for the Ollama model pull on first startup

### Start the Full Stack

From the repository root:

```powershell
docker compose up --build
```

On the first run, Compose will:

1. Build the backend image
2. Build the frontend image
3. Start `ollama`
4. Pull the configured Ollama model through `ollama-init`
5. Start the FastAPI backend
6. Start the frontend

### Access the Application

- Frontend: `http://localhost:5173`
- Backend health check: `http://localhost:8000/health`
- Ollama API: `http://localhost:11434`

### Stop the Stack

```powershell
docker compose down
```

To remove the persisted Ollama model volume as well:

```powershell
docker compose down -v
```

## Step-by-Step Run Guide

1. Open a terminal in the repository root.
2. Optionally create a `.env` file from `.env.example` and adjust ports or the Ollama model.
3. Run `docker compose up --build`.
4. Wait for the `ollama-init` container to finish pulling the configured model.
5. Open `http://localhost:5173`.
6. Upload a `.txt`, `.pdf`, `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tif`, `.tiff`, or `.webp` document.
7. Choose either `Neutral placeholders` or `Synthetic replacements`.
8. Review the original text, redacted text, and redaction report in the UI.

## API Summary

### `GET /health`

Returns:

```json
{
  "status": "ok",
  "service": "medical-deidentification-backend"
}
```

### `POST /upload-document`

Multipart form fields:

- `file`: uploaded medical document
- `strategy`: `placeholder` or `synthetic`

Response fields include:

- `filename`
- `input_kind`
- `extraction_method`
- `strategy`
- `original_text`
- `redacted_text`
- `redaction_count`
- `detected_types`
- `redaction_report`

## Container Notes

- The backend image installs system libraries needed by OCR and ONNX runtime workloads.
- The frontend image is built once and served by Nginx on port `5173`.
- Ollama model data is stored in a named Docker volume so the model is not re-downloaded on every restart.

## Troubleshooting

- If the frontend cannot reach the backend, rebuild after changing `VITE_API_BASE_URL` because it is injected at frontend build time.
- If startup is slow on the first run, that is usually the Ollama model pull.
- If OCR seems empty for a document, verify the upload contains legible scanned text and is within the configured size limit.
