from __future__ import annotations

import os


class Settings:
    host: str = os.getenv("BACKEND_HOST", "127.0.0.1")
    port: int = int(os.getenv("BACKEND_PORT", "8000"))
    max_upload_size: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5")) * 1024 * 1024

    text_extensions = {".txt", ".md", ".csv", ".json", ".log", ".text"}
    image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
    pdf_extensions = {".pdf"}

    ollama_url: str = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3:latest")


settings = Settings()
