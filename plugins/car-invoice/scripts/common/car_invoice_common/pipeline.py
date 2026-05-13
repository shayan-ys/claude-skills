"""Conventions shared by document pipelines (.pipeline/<doc_id>/ layout, pipeline_status)."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from . import paperless as pl

PIPELINE_STATUS_FIELD = "pipeline_status"

_FIELD_ID_CACHE: dict[str, int] = {}


def doc_dir(pipeline_root: Path, doc_id: int) -> Path:
    """Return <pipeline_root>/<doc_id>/, creating it if needed."""
    d = pipeline_root / str(doc_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def extraction_path(pipeline_root: Path, doc_id: int) -> Path:
    return doc_dir(pipeline_root, doc_id) / "extraction.json"


def write_extraction(pipeline_root: Path, doc_id: int, data: dict) -> Path:
    """Atomically write extraction.json via tmp-file + rename."""
    dest = extraction_path(pipeline_root, doc_id)
    fd, tmp_name = tempfile.mkstemp(
        prefix=".extraction-", suffix=".json", dir=dest.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_name, dest)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise
    return dest


def load_history(pipeline_root: Path, *, skip: Path | None = None) -> list[dict]:
    """Load every <pipeline_root>/*/extraction.json. Optionally skip one path."""
    out: list[dict] = []
    skip_resolved = skip.resolve() if skip else None
    for p in pipeline_root.glob("*/extraction.json"):
        if skip_resolved and p.resolve() == skip_resolved:
            continue
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return out


def get_custom_field_id(field_name: str) -> int:
    """Cached lookup of a Paperless custom-field id by name."""
    if field_name not in _FIELD_ID_CACHE:
        for f in pl.list_all("/api/custom_fields/"):
            _FIELD_ID_CACHE[f["name"]] = f["id"]
    return _FIELD_ID_CACHE[field_name]


def get_pipeline_status(doc: dict, field_name: str = PIPELINE_STATUS_FIELD) -> str | None:
    """Read a Paperless custom-field value from a document dict."""
    field_id = get_custom_field_id(field_name)
    for cf in doc.get("custom_fields") or []:
        if cf.get("field") == field_id:
            return cf.get("value")
    return None


def set_pipeline_status(
    doc_id: int, status: str, field_name: str = PIPELINE_STATUS_FIELD
) -> None:
    """PATCH a single custom-field value on a Paperless document."""
    pl.patch_document(doc_id, {"custom_fields": [
        {"field": get_custom_field_id(field_name), "value": status},
    ]})
