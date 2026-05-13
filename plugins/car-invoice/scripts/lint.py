"""
Deterministic linter for car-pipeline extraction.json files.
No LLM calls. Reads staged extraction.json files for history context.
Vehicles are loaded from CAR_INVOICE_VEHICLES_PATH (your vehicles.json).

Usage:
    python lint.py <extraction.json>

Python API:
    from lint import lint, LintResult
    result = lint(extraction: dict, history: list[dict], ocr_path=None) -> LintResult
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

from car_invoice_common.pipeline import load_history
from vocab import (
    CANONICAL_TAGS,
    DEFERRED_SEVERITIES,
    RECORD_TYPES,
    TAG_ALIASES,
    normalize_customer,
)


def _load_vehicles() -> dict[str, dict]:
    """Load vehicle definitions from CAR_INVOICE_VEHICLES_PATH env var."""
    path = os.environ.get("CAR_INVOICE_VEHICLES_PATH", "")
    if not path:
        raise RuntimeError(
            "CAR_INVOICE_VEHICLES_PATH env var is not set. "
            "Set it to the path of your vehicles.json file."
        )
    with open(path, encoding="utf-8") as f:
        config = json.load(f)
    result: dict[str, dict] = {}
    for v in config.get("vehicles", []):
        key = v["key"]
        result[key] = {
            "name": v["name"],
            "vin": v.get("vin"),
        }
    return result


KNOWN_VEHICLES: dict[str, dict] = _load_vehicles()
KNOWN_VINS: dict[str, str] = {
    v["vin"]: k for k, v in KNOWN_VEHICLES.items() if v.get("vin")
}

VALID_RECORD_TYPES = RECORD_TYPES
ODOMETER_JUMP_LIMIT = 50_000
COST_TOLERANCE = 1.00  # dollars

# Phrases that signal Claude inferred/calculated a cost rather than reading it verbatim.
FORBIDDEN_NOTES_PHRASES = [
    "inferred",
    "cumulative",
    "minus Job",
    "minus job",
    "subtracted",
    "derived from",
    "calculated from",
    "difference between",
    "remainder",
    "calculated",
    "derived",
    "approx",
    "assumed",
]

# Regex patterns for total_cost verification in OCR text.
# Accepts TOTAL INVOICE / INVOICE TOTAL and shops that use "Grand Total".
_TOTAL_INVOICE_RE = re.compile(
    r"(?:TOTAL\s+INVOICE|INVOICE\s+TOTAL|GRAND\s+TOTAL)\s*\$?\s*([\d,]+\.?\d*)",
    re.IGNORECASE,
)


@dataclass
class LintResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def error(self, msg: str) -> None:
        self.errors.append(f"ERROR: {msg}")

    def warn(self, msg: str) -> None:
        self.warnings.append(f"WARN: {msg}")


def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _vehicle_label(vehicle_key: str) -> str:
    v = KNOWN_VEHICLES.get(vehicle_key)
    return v["name"] if v else vehicle_key


def _odometer_history_for_vehicle(
    vehicle_key: str, history: list[dict]
) -> list[tuple[date, int]]:
    """Return sorted (date, odometer) pairs for a vehicle from history records."""
    points: list[tuple[date, int]] = []
    for rec in history:
        inv = rec.get("invoice", {})
        if inv.get("vehicle_match") != vehicle_key:
            continue
        odo = inv.get("odometer")
        d = _parse_date(inv.get("date"))
        if odo is not None and d is not None:
            points.append((d, int(odo)))
    points.sort()
    return points


def _check_job_contiguity(ocr_path: Optional[Path], result: LintResult) -> None:
    """Verify JOB# CHARGES lines in the OCR form a contiguous sequence 1..N."""
    if ocr_path is None:
        return
    if not ocr_path.exists():
        result.warn(f"ocr_combined.md not found at {ocr_path} — job contiguity check skipped")
        return

    text = ocr_path.read_text(errors="replace")
    matches = re.findall(r"JOB#\s*(\d+)\s+CHARGES", text, re.IGNORECASE)
    if not matches:
        result.warn("Job contiguity — no 'JOB# N CHARGES' patterns found in OCR; check skipped")
        return

    seen = sorted({int(m) for m in matches})
    expected = list(range(1, max(seen) + 1))
    missing = sorted(set(expected) - set(seen))
    if missing:
        result.error(
            f"Job contiguity — saw JOB# {','.join(str(s) for s in seen)} "
            f"but job(s) {','.join(str(m) for m in missing)} "
            f"missing from OCR CHARGES lines (check OCR for dropped JOB# header)"
        )


def _check_cost_checksum(inv: dict, jobs: list, result: LintResult) -> None:
    """Verify sum(jobs.cost) + tax + misc_chg - misc_disc ≈ invoice.total_cost."""
    total_cost = inv.get("total_cost")
    if total_cost is None:
        return

    job_sum = 0.0
    unreadable_count = 0
    for i, job in enumerate(jobs):
        cost = job.get("cost")
        if cost is None:
            if job.get("cost_unreadable"):
                result.warn(
                    f"jobs[{i}].cost is null and cost_unreadable=true — "
                    f"excluded from checksum. Description: {str(job.get('description', ''))[:60]}"
                )
                unreadable_count += 1
            continue
        job_sum += cost

    tax = inv.get("subtotal_tax") or 0.0
    misc_chg = inv.get("subtotal_misc_chg") or 0.0
    misc_disc = inv.get("subtotal_misc_disc") or 0.0
    expected = job_sum + tax + misc_chg - misc_disc

    diff = abs(expected - total_cost)
    if diff > COST_TOLERANCE:
        breakdown = (
            f"jobs={job_sum:.2f}"
            + (f" + tax={tax:.2f}" if tax else "")
            + (f" + misc_chg={misc_chg:.2f}" if misc_chg else "")
            + (f" - misc_disc={misc_disc:.2f}" if misc_disc else "")
            + f" = expected={expected:.2f}"
        )
        suffix = (
            f"; {unreadable_count} job(s) with cost_unreadable=true excluded — downgrading to warning"
            if unreadable_count
            else ""
        )
        msg = (
            f"Cost checksum — {breakdown}, actual total_cost={total_cost:.2f}, "
            f"delta=${diff:.2f} (tolerance ${COST_TOLERANCE:.2f}){suffix}"
        )
        if unreadable_count:
            result.warn(msg)
        else:
            result.error(msg)


def _check_forbidden_phrases(jobs: list, result: LintResult) -> None:
    """Fail if any job notes contain arithmetic-inference markers."""
    for i, job in enumerate(jobs):
        notes = job.get("notes") or ""
        for phrase in FORBIDDEN_NOTES_PHRASES:
            if phrase.lower() in notes.lower():
                snippet = notes[:120].replace("\n", " ")
                result.error(
                    f"jobs[{i}].notes contains forbidden phrase '{phrase}' — "
                    f"cost must be read verbatim, not inferred. "
                    f"If cost is unreadable set cost_unreadable=true and cost=null. "
                    f"Snippet: «{snippet}»"
                )
                break  # one error per job


def _normalise_for_match(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def _check_total_invoice_in_ocr(inv: dict, ocr_path: Optional[Path], result: LintResult) -> None:
    """Verify invoice.total_cost appears as TOTAL INVOICE $X in the OCR."""
    total_cost = inv.get("total_cost")
    if total_cost is None or ocr_path is None or not ocr_path.exists():
        return

    text = ocr_path.read_text(errors="replace")
    matches = _TOTAL_INVOICE_RE.findall(text)
    if not matches:
        return  # pattern not present — skip rather than false-positive

    ocr_totals = {float(m.replace(",", "")) for m in matches}
    if not any(abs(total_cost - t) <= COST_TOLERANCE for t in ocr_totals):
        result.error(
            f"invoice.total_cost={total_cost:.2f} not found as TOTAL INVOICE / INVOICE TOTAL / "
            f"GRAND TOTAL in OCR (found: {sorted(ocr_totals)})"
        )


def _normalize_ws(s: str) -> str:
    return " ".join(s.split()).lower()


def _contains_quote(haystack: str, needle: str) -> bool:
    return _normalize_ws(needle) in _normalize_ws(haystack)


def _check_deferred_provenance(
    extraction: dict, ocr_path: Optional[Path], result: LintResult
) -> None:
    """Each deferred item must have source_quote that appears (whitespace-normalized) in ocr_combined.md."""
    deferred = extraction.get("deferred", [])
    if not deferred:
        return

    if ocr_path is None or not ocr_path.exists():
        result.warn("ocr_combined.md not available — deferred provenance check skipped")
        return

    ocr_text = ocr_path.read_text(errors="replace")

    for i, item in enumerate(deferred):
        quote = item.get("source_quote")
        desc_snippet = str(item.get("description", ""))[:80]

        severity = item.get("severity")
        if severity not in DEFERRED_SEVERITIES:
            result.error(
                f"deferred[{i}].severity '{severity}' not in {sorted(DEFERRED_SEVERITIES)}"
            )

        if not quote:
            result.error(
                f"deferred[{i}].source_quote is missing — "
                f"every deferred item must cite the verbatim OCR line that supports it. "
                f"Description: «{desc_snippet}»"
            )
            continue

        norm_quote = _normalize_ws(quote)
        if len(norm_quote) < 15:
            if not _contains_quote(ocr_text, quote):
                result.warn(
                    f"deferred[{i}].source_quote is very short ({len(norm_quote)} chars) and "
                    f"not found in ocr_combined.md — quote: «{quote[:80]}»"
                )
        elif not _contains_quote(ocr_text, quote):
            result.error(
                f"deferred[{i}].source_quote not found in ocr_combined.md — "
                f"quote: «{quote[:80]}» "
                f"(check spelling/OCR artefacts; use the exact OCR text)"
            )


def lint(
    extraction: dict,
    history: list[dict],
    ocr_path: Optional[Path] = None,
) -> LintResult:
    result = LintResult()
    inv = extraction.get("invoice", {})

    # --- Required fields ---
    invoice_date = _parse_date(inv.get("date"))
    if invoice_date is None:
        result.error("invoice.date is missing or invalid")

    vehicle_key = inv.get("vehicle_match")
    if not vehicle_key or vehicle_key not in KNOWN_VEHICLES:
        known = ", ".join(KNOWN_VEHICLES.keys())
        result.error(
            f"invoice.vehicle_match '{vehicle_key}' not in known vehicles ({known})"
        )

    odometer = inv.get("odometer")
    if odometer is None:
        result.warn("invoice.odometer is None — odometer check skipped")

    total_cost = inv.get("total_cost")
    if total_cost is not None and total_cost == 0:
        result.warn("invoice.total_cost is 0 — verify this is correct")

    # customer — flag non-normalized names (all caps, Last,First order)
    customer = inv.get("customer")
    if isinstance(customer, str) and customer.strip():
        normalized = normalize_customer(customer)
        if normalized != customer:
            result.warn(
                f"invoice.customer '{customer}' is not normalized — "
                f"expected '{normalized}' (title case, first-last order)"
            )

    # subtotal_misc_disc — prefer null over 0.0 for "no discount"
    misc_disc = inv.get("subtotal_misc_disc")
    if misc_disc == 0 or misc_disc == 0.0:
        result.warn(
            "invoice.subtotal_misc_disc is 0.0 — use null when no discount "
            "line is present on the invoice"
        )

    # --- VIN check ---
    vin = inv.get("vin")
    if vin is not None:
        matched_key = KNOWN_VINS.get(vin)
        if matched_key is None:
            known_vins = ", ".join(KNOWN_VINS.keys())
            result.error(
                f"VIN {vin} not found in known vehicles. Known VINs: {known_vins}"
            )
        elif vehicle_key and matched_key != vehicle_key:
            result.error(
                f"VIN {vin} belongs to {_vehicle_label(matched_key)} "
                f"but vehicle_match is '{vehicle_key}' ({_vehicle_label(vehicle_key)})"
            )

    # --- Per-job checks ---
    jobs = extraction.get("jobs", [])
    if not isinstance(jobs, list):
        result.error("jobs must be a list")
    else:
        seen_job_numbers: set[int] = set()
        for i, job in enumerate(jobs):
            prefix = f"jobs[{i}]"
            desc = job.get("description")
            if not desc or not str(desc).strip():
                result.error(f"{prefix}.description is empty")
            rec_type = job.get("record_type")
            if rec_type not in VALID_RECORD_TYPES:
                result.error(
                    f"{prefix}.record_type '{rec_type}' not in {VALID_RECORD_TYPES}"
                )

            # cost / cost_unreadable — must be exactly one of: cost=number OR cost=null+cost_unreadable=true
            cost = job.get("cost")
            cost_unreadable = job.get("cost_unreadable")
            if cost is None:
                if cost_unreadable is not True:
                    result.error(
                        f"{prefix}.cost is null but cost_unreadable is not true — "
                        f"set cost_unreadable=true when cost cannot be read"
                    )
            else:
                if cost_unreadable is not None:
                    result.error(
                        f"{prefix}.cost_unreadable must be omitted when cost is a number "
                        f"(cost={cost}, cost_unreadable={cost_unreadable})"
                    )
                if cost < 0:
                    result.error(f"{prefix}.cost {cost} is negative")

            # source_line — required; empty only when cost == 0.00
            source_line = job.get("source_line")
            if source_line is None:
                result.error(
                    f"{prefix}.source_line is missing — "
                    f"must be the verbatim OCR line the cost was read from"
                )
            elif source_line == "" and cost != 0.0:
                result.error(
                    f"{prefix}.source_line is empty but cost={cost} — "
                    f"empty source_line is only allowed for zero-cost (warranty/recall) jobs"
                )

            # tags — warn on unknown or aliased vocabulary
            tags = job.get("tags") or []
            if not isinstance(tags, list):
                result.error(f"{prefix}.tags must be a list")
            else:
                for tag in tags:
                    if not isinstance(tag, str):
                        result.error(f"{prefix}.tags contains non-string value {tag!r}")
                    elif tag in TAG_ALIASES:
                        result.warn(
                            f"{prefix}.tags — '{tag}' is an alias for "
                            f"'{TAG_ALIASES[tag]}' (use the canonical form)"
                        )
                    elif tag not in CANONICAL_TAGS:
                        result.warn(
                            f"{prefix}.tags — '{tag}' is not in the canonical "
                            f"tag vocabulary (see vocab.py in your car-invoice plugin scripts)"
                        )

            # job_number — required, unique
            job_num = job.get("job_number")
            if job_num is None:
                result.error(f"{prefix}.job_number is missing")
            elif not isinstance(job_num, int):
                result.error(f"{prefix}.job_number must be an integer, got {job_num!r}")
            elif job_num in seen_job_numbers:
                result.error(f"{prefix}.job_number {job_num} is duplicated")
            else:
                seen_job_numbers.add(job_num)

    # --- missing_jobs invariant ---
    missing_jobs = extraction.get("missing_jobs", [])
    if not isinstance(missing_jobs, list):
        result.error("missing_jobs must be a list")
    else:
        if isinstance(jobs, list):
            job_numbers = {
                j.get("job_number")
                for j in jobs
                if isinstance(j.get("job_number"), int)
            }
            missing_set = set()
            for m in missing_jobs:
                if not isinstance(m, int):
                    result.error(f"missing_jobs contains non-integer value {m!r}")
                else:
                    missing_set.add(m)

            overlap = job_numbers & missing_set
            if overlap:
                result.error(
                    f"missing_jobs overlap with job_numbers — "
                    f"job(s) {sorted(overlap)} appear in both jobs[] and missing_jobs"
                )

            all_nums = job_numbers | missing_set
            if all_nums:
                expected = set(range(1, max(all_nums) + 1))
                gaps = sorted(expected - all_nums)
                if gaps:
                    result.error(
                        f"Job contiguity (field-level) — job_numbers ∪ missing_jobs has gaps: "
                        f"{gaps}. All jobs 1..{max(all_nums)} must be accounted for"
                    )

    # --- Date-aware odometer bracketing ---
    if odometer is not None and invoice_date is not None and vehicle_key in KNOWN_VEHICLES:
        odo_int = int(odometer)
        vehicle_label = _vehicle_label(vehicle_key)
        history_points = _odometer_history_for_vehicle(vehicle_key, history)

        prev_entries = [(d, o) for d, o in history_points if d < invoice_date]
        next_entries = [(d, o) for d, o in history_points if d > invoice_date]

        surrounding_str = ""
        if history_points:
            nearby = prev_entries[-3:] + next_entries[:3]
            surrounding_str = " Surrounding entries: " + ", ".join(
                f"{o} ({d})" for d, o in sorted(nearby)
            )

        if prev_entries:
            prev_date, prev_odo = prev_entries[-1]
            if odo_int < prev_odo:
                result.error(
                    f"odometer {odo_int} < prior entry {prev_odo} ({prev_date}) "
                    f"for {vehicle_label}. Possible dropped digit?{surrounding_str}"
                )
            elif odo_int - prev_odo >= ODOMETER_JUMP_LIMIT:
                result.error(
                    f"odometer jump of {odo_int - prev_odo} km since {prev_date} "
                    f"({prev_odo}) for {vehicle_label} seems impossible (limit {ODOMETER_JUMP_LIMIT}).{surrounding_str}"
                )

        if next_entries:
            next_date, next_odo = next_entries[0]
            if odo_int > next_odo:
                result.error(
                    f"odometer {odo_int} > later entry {next_odo} ({next_date}) "
                    f"for {vehicle_label}. Possible extra digit?{surrounding_str}"
                )

    if isinstance(jobs, list):
        _check_cost_checksum(inv, jobs, result)
        _check_forbidden_phrases(jobs, result)
    _check_job_contiguity(ocr_path, result)
    _check_total_invoice_in_ocr(inv, ocr_path, result)
    _check_deferred_provenance(extraction, ocr_path, result)

    return result


_PIPELINE_DIR = Path(
    os.environ.get(
        "CAR_INVOICE_STATE_DIR",
        Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "car-invoice",
    )
)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(f"Usage: {argv[0]} <extraction.json>", file=sys.stderr)
        return 2

    extraction_file = Path(argv[1])
    try:
        with open(extraction_file) as f:
            extraction = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: Cannot read {extraction_file}: {e}", file=sys.stderr)
        return 2

    history = load_history(_PIPELINE_DIR, skip=extraction_file)
    ocr_path = extraction_file.parent / "ocr_combined.md"
    result = lint(extraction, history, ocr_path=ocr_path)

    for msg in result.errors:
        print(msg)
    for msg in result.warnings:
        print(msg)

    if result.ok:
        print(f"PASS — {len(result.warnings)} warning(s)")
        return 0
    else:
        print(f"FAIL — {len(result.errors)} error(s), {len(result.warnings)} warning(s)")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
