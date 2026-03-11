from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from ..core.config import settings
from ..services.redactor import deidentify_text
from ..utils.file_parser import detect_input_kind, parse_document
from ..utils.http_utils import json_bytes, parse_multipart_form


class DeidentificationHandler(BaseHTTPRequestHandler):
    server_version = "MedicalDeidHTTP/1.0"

    def _write_json(self, status: int, payload: dict[str, object]) -> None:
        data = json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:
        self._write_json(HTTPStatus.OK, {"ok": True})

    def do_GET(self) -> None:
        if self.path == "/health":
            self._write_json(HTTPStatus.OK, {"status": "ok", "service": "medical-deidentification-backend"})
            return
        self._write_json(HTTPStatus.NOT_FOUND, {"detail": "Not found."})

    def do_POST(self) -> None:
        if self.path != "/upload-document":
            self._write_json(HTTPStatus.NOT_FOUND, {"detail": "Not found."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._write_json(HTTPStatus.BAD_REQUEST, {"detail": "Invalid content length."})
            return

        if content_length <= 0:
            self._write_json(HTTPStatus.BAD_REQUEST, {"detail": "Request body is empty."})
            return

        if content_length > settings.max_upload_size:
            self._write_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"detail": "File is too large. Maximum upload size is 5 MB."})
            return

        try:
            body = self.rfile.read(content_length)
            fields, (filename, file_bytes) = parse_multipart_form(
                {key.lower(): value for key, value in self.headers.items()},
                body,
            )
            strategy = fields.get("strategy", "placeholder")
            document_text, extraction_method = parse_document(filename, file_bytes)
            if not document_text:
                raise ValueError("Uploaded file is empty or unreadable.")

            result = deidentify_text(document_text, strategy=strategy)
            self._write_json(
                HTTPStatus.OK,
                {
                    "filename": filename,
                    "input_kind": detect_input_kind(filename),
                    "extraction_method": extraction_method,
                    "strategy": strategy,
                    **result,
                },
            )
        except ValueError as error:
            self._write_json(HTTPStatus.BAD_REQUEST, {"detail": str(error)})
        except Exception:
            self._write_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"detail": "The server could not process this document."})

    def log_message(self, format: str, *args: object) -> None:
        return


def run() -> None:
    server = ThreadingHTTPServer((settings.host, settings.port), DeidentificationHandler)
    print(f"Backend running on http://{settings.host}:{settings.port}")
    server.serve_forever()
