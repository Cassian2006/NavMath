from __future__ import annotations

from typing import Any

from app.services.knowledge import get_import_status, save_import_csv


def handle_csv_import(kind: str, content: bytes) -> dict[str, Any]:
    return save_import_csv(kind, content)


def load_import_dashboard() -> dict[str, Any]:
    return get_import_status()
