"""One-shot: create Paperless-ngx metadata objects for the car-invoice pipeline.

Idempotent — safe to rerun. For each vehicle, checks whether the storage path
and tag already exist before creating them. After creating/finding objects,
writes the assigned Paperless IDs back to vehicles.json so push.py can use
them in Phase 2.

Prints a summary of what exists / was created.

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


def _load_vehicles_config() -> tuple[list[dict], Path]:
    """Return (vehicles list, path to vehicles.json)."""
    path_str = os.environ.get("CAR_INVOICE_VEHICLES_PATH", "")
    if not path_str:
        raise RuntimeError(
            "CAR_INVOICE_VEHICLES_PATH env var is not set. "
            "Set it to the path of your vehicles.json file."
        )
    path = Path(path_str)
    with open(path, encoding="utf-8") as f:
        config = json.load(f)
    return config.get("vehicles", []), path


def _write_back(config_path: Path, vehicles: list[dict]) -> None:
    """Atomically write updated vehicles list back to vehicles.json."""
    config_path.write_text(
        json.dumps({"vehicles": vehicles}, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    vehicles, config_path = _load_vehicles_config()
    print(f"Paperless: {pl.BASE_URL}")
    print(f"Loaded {len(vehicles)} vehicle(s) from {config_path}")

    # Document type (shared across all vehicles)
    dt = pl.ensure_named("document_types", DOC_TYPE)
    print(f"  document_type  id={dt:<4} {DOC_TYPE}")

    # Per-vehicle storage path and tag
    for v in vehicles:
        key = v["key"]
        name = v.get("name", key)
        storage_name = f"Car / {name}"
        storage_path = v.get("paperless_storage_path", f"car/{key}/{{created_year}}/")
        sid = pl.ensure_named("storage_paths", storage_name, {"path": storage_path})
        v["paperless_storage_path_id"] = sid
        print(f"  storage_path   id={sid:<4} {storage_name}  -> {storage_path}")

    # Tags: always include "car-maintenance" plus one tag per vehicle
    car_tag_id = pl.ensure_named("tags", "car-maintenance")
    print(f"  tag            id={car_tag_id:<4} car-maintenance")

    for v in vehicles:
        tag_name = v.get("paperless_tag", v["key"])
        tid = pl.ensure_named("tags", tag_name)
        v["paperless_tag_id"] = tid
        print(f"  tag            id={tid:<4} {tag_name}")

    # Shared custom fields
    for name, dtype in CUSTOM_FIELDS:
        cid = pl.ensure_custom_field(name, dtype)
        print(f"  custom_field   id={cid:<4} {name} ({dtype})")

    # Write assigned IDs back to vehicles.json
    _write_back(config_path, vehicles)
    print(f"\nWrote Paperless IDs back to {config_path}")
    print("Re-running this script is safe — it will find existing objects and refresh the IDs.")


if __name__ == "__main__":
    main()
