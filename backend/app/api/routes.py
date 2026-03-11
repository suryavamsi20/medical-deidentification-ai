from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..core.config import settings
from ..models.schemas import UploadResponse
from ..services.redactor import deidentify_text
from ..utils.file_parser import detect_input_kind, parse_document


router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "medical-deidentification-backend",
    }


@router.post("/upload-document", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    strategy: str = Form("placeholder"),
) -> dict[str, object]:
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty or unreadable.")
    if len(file_bytes) > settings.max_upload_size:
        raise HTTPException(status_code=413, detail="File is too large. Maximum upload size is 5 MB.")

    filename = file.filename or "uploaded-document.txt"

    try:
        document_text, extraction_method = parse_document(filename, file_bytes)
        result = deidentify_text(document_text, strategy=strategy)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="The server could not process this document.") from error

    return {
        "filename": filename,
        "input_kind": detect_input_kind(filename),
        "extraction_method": extraction_method,
        "strategy": strategy,
        **result,
    }
