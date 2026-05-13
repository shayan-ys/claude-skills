"""Paperless-ngx REST client. Auth via PAPERLESS_TOKEN env var (Token auth).

Set these environment variables before importing:
  PAPERLESS_URL    — base URL of your Paperless-ngx instance, e.g. http://192.168.1.100:8000
  PAPERLESS_TOKEN  — API token from Paperless Settings › Administration › Auth Token

Tip: inject secrets with `op run`, `pass`, `chamber`, or any secret manager rather
than storing them in plaintext shell profiles.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

_base = os.environ.get("PAPERLESS_URL", "").rstrip("/")
if not _base:
    raise RuntimeError(
        "PAPERLESS_URL env var is not set. "
        "Set it to your Paperless-ngx base URL (e.g. http://192.168.1.100:8000)."
    )
BASE_URL: str = _base

_TOKEN_CACHE: dict[str, str] = {}


def _auth_header() -> str:
    if "v" in _TOKEN_CACHE:
        return _TOKEN_CACHE["v"]
    token = os.environ.get("PAPERLESS_TOKEN", "")
    if not token:
        raise RuntimeError(
            "PAPERLESS_TOKEN env var is not set. "
            "Get your token from Paperless Settings › Administration › Auth Token."
        )
    _TOKEN_CACHE["v"] = f"Token {token}"
    return _TOKEN_CACHE["v"]


def request(
    method: str,
    path: str,
    *,
    params: dict | None = None,
    json_body: Any = None,
    stream_to: Path | None = None,
) -> Any:
    url = f"{BASE_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = None
    headers = {"Authorization": _auth_header(), "Accept": "application/json"}
    if json_body is not None:
        data = json.dumps(json_body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            if stream_to is not None:
                stream_to.parent.mkdir(parents=True, exist_ok=True)
                with stream_to.open("wb") as f:
                    while chunk := r.read(65536):
                        f.write(chunk)
                return stream_to
            raw = r.read()
            if not raw:
                return None
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"{method} {path} → {e.code}: {body}") from None


def list_all(path: str, params: dict | None = None) -> list[dict]:
    params = dict(params or {})
    params.setdefault("page_size", 100)
    out: list[dict] = []
    url: str | None = path
    while url:
        rel = url[len(BASE_URL):] if url.startswith("http") else url
        data = request("GET", rel, params=params if rel == path else None)
        out.extend(data.get("results", []))
        url = data.get("next")
        params = None
    return out


def download_original(doc_id: int, dest: Path) -> Path:
    return request("GET", f"/api/documents/{doc_id}/download/", stream_to=dest)


def ensure_named(endpoint: str, name: str, extra: dict | None = None) -> int:
    """Idempotent: find-or-create by name. Returns the object's id."""
    for obj in list_all(f"/api/{endpoint}/"):
        if obj.get("name") == name:
            return obj["id"]
    body = {"name": name, **(extra or {})}
    created = request("POST", f"/api/{endpoint}/", json_body=body)
    return created["id"]


def ensure_custom_field(name: str, data_type: str = "string") -> int:
    for obj in list_all("/api/custom_fields/"):
        if obj.get("name") == name:
            return obj["id"]
    created = request(
        "POST",
        "/api/custom_fields/",
        json_body={"name": name, "data_type": data_type},
    )
    return created["id"]


def patch_document(doc_id: int, body: dict) -> dict:
    return request("PATCH", f"/api/documents/{doc_id}/", json_body=body)
