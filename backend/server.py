from __future__ import annotations

try:
    from backend.app.api.http_server import DeidentificationHandler, run
except ModuleNotFoundError:
    from app.api.http_server import DeidentificationHandler, run

__all__ = ["DeidentificationHandler", "run"]


if __name__ == "__main__":
    run()
