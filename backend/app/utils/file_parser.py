from __future__ import annotations

from io import BytesIO
from pathlib import Path

import fitz
from PIL import Image
from pypdf import PdfReader
from rapidocr_onnxruntime import RapidOCR

from ..core.config import settings


OCR_ENGINE = RapidOCR()


def run_ocr_on_image(image: Image.Image) -> str:
    result, _ = OCR_ENGINE(image)
    if not result:
        return ""
    return "\n".join(item[1] for item in result if len(item) > 1 and item[1]).strip()


def extract_text_from_pdf(file_bytes: bytes) -> str:
    extracted_pages: list[str] = []
    reader = PdfReader(BytesIO(file_bytes))

    for page in reader.pages:
        page_text = (page.extract_text() or "").strip()
        if page_text:
            extracted_pages.append(page_text)

    if extracted_pages:
        return "\n\n".join(extracted_pages).strip()

    pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
    try:
        ocr_pages: list[str] = []
        for page in pdf_document:
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.open(BytesIO(pixmap.tobytes("png")))
            page_text = run_ocr_on_image(image)
            if page_text:
                ocr_pages.append(page_text)
        return "\n\n".join(ocr_pages).strip()
    finally:
        pdf_document.close()


def extract_text_from_image(file_bytes: bytes) -> str:
    image = Image.open(BytesIO(file_bytes))
    return run_ocr_on_image(image)


def parse_document(filename: str, file_bytes: bytes) -> tuple[str, str]:
    suffix = Path(filename).suffix.lower()

    if suffix in settings.pdf_extensions:
        extracted = extract_text_from_pdf(file_bytes)
        if not extracted:
            raise ValueError("The PDF did not contain readable text and OCR could not extract any text.")
        return extracted, "pdf_text_or_ocr"

    if suffix in settings.image_extensions:
        extracted = extract_text_from_image(file_bytes)
        if not extracted:
            raise ValueError("OCR could not detect readable text in the uploaded image.")
        return extracted, "image_ocr"

    if suffix not in settings.text_extensions:
        decoded = file_bytes.decode("utf-8", errors="ignore").strip()
        if not decoded:
            raise ValueError(
                "Unsupported file type. Upload text, PDF, or image files such as .txt, .pdf, .png, or .jpg."
            )
        return decoded, "plain_text_fallback"

    return file_bytes.decode("utf-8", errors="ignore").strip(), "plain_text"


def detect_input_kind(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in settings.pdf_extensions:
        return "pdf"
    if suffix in settings.image_extensions:
        return "image"
    return "text"
