"""One-shot: create Paperless-ngx metadata objects for the car-invoice pipeline.

Idempotent — safe to rerun. Prints a summary of what exists / was created.

Reads your vehicles from CAR_INVOICE_VEHICLES_PATH (vehicles.json).
Each vehicle gets:
  - a storage path  (car/<key>/{created_year}/)
  - a tag           (the vehicle's paperless_tag, defaults to the key)

Also creates shared metadata:
  - document type   "Car Maintenance"
  - custom fields   lubelogger_ids (string), pipeline_status (string)

Run once after initial setup:
    source init-env.sh && uv run setup_paperless.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from car_invoice_common import paperless as pl


DOC_TYPE = "Car Maintenance"

CUSTOM_FIELDS = [
    ("lubelogger_ids", "string"),
    ("pipeline_status", "string"),
]


def _load_vehicles() -> list[dict]:
    path = os.environ.get("CAR_INVOICE_VEHICLES_PATH", "")
    if not path:
        raise RuntimeError(
            "CAR_INVOICE_VEHICLES_PATH env var is not set. "
            "Set it to the path of your vehicles.json file."
        )
    with open(path, encoding="utf-8") as f:
        config = json.load(f)
    return config.get("vehicles", [])


def main() -> None:
    vehicles = _load_vehicles()
    print(f"Paperless: {pl.BASE_URL}")
    print(f"Loaded {len(vehicles)} vehicle(s) from vehicles config")

    dt = pl.ensure_named("document_types", DOC_TYPE)
    print(f"  document_type  id={dt:<4} {DOC_TYPE}")

    for v in vehicles:
        key = v["key"]
        name = v.get("name", key)
        storage_name = f"Car / {name}"
        storage_path = v.get("paperless_storage_path", f"car/{key}/{{created_year}}/")
        sid = pl.ensure_named("storage_paths", storage_name, {"path": storage_path})
        print(f"  storage_path   id={sid:<4} {storage_name}  -> {storage_path}")

    # Tags: always include "car-maintenance" plus one tag per vehicle
    tags = ["car-maintenance"] + [v.get("paperless_tag", v["key"]) for v in vehicles]
    for tag in tags:
        tid = pl.ensure_named("tags", tag)
        print(f"  tag            id={tid:<4} {tag}")

    for name, dtype in CUSTOM_FIELDS:
        cid = pl.ensure_custom_field(name, dtype)
        print(f"  custom_field   id={cid:<4} {name} ({dtype})")


if __name__ == "__main__":
    main()
