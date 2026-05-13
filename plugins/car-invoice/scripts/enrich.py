"""Atomic verbs for the /car-invoice slash command.

Each subcommand prints one JSON object to stdout. Errors go to stderr and
exit nonzero. Shared state between verbs is the on-disk layout in
<PIPELINE_DIR>/<doc_id>/.

Subcommands:
    resolve [id-or-url]   resolve target doc (queue or ad-hoc)
    fetch   <id> [--force-ocr]
    lint    <id>          reads candidate JSON from stdin
    commit  <id>

Environment variables (set via init-env.sh or directly):
    PAPERLESS_URL             — base URL of your Paperless-ngx instance
    PAPERLESS_TOKEN           — API token from Paperless Settings
    CAR_INVOICE_VEHICLES_PATH — path to your vehicles.json
    CAR_INVOICE_STATE_DIR     — optional; defaults to ~/.local/state/car-invoice
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from car_invoice_common import paperless as pl
from car_invoice_common.pipeline import (
    doc_dir,
    extraction_path,
    get_pipeline_status,
    load_history,
    set_pipeline_status,
    write_extraction,
)
from car_invoice_common.quality import OcrQualityError, check_pages_raise
from lint import lint as _lint  # type: ignore

# --- paths ----------------------------------------------------------------

SCRIPTS_DIR = Path(__file__).resolve().parent
OCR_SCRIPT = SCRIPTS_DIR / "ocr" / "ocr.py"
OCR_PYTHON = SCRIPTS_DIR / "ocr" / ".venv" / "bin" / "python"

_xdg_state = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
PIPELINE_DIR = Path(os.environ.get("CAR_INVOICE_STATE_DIR", _xdg_state / "car-invoice"))

TERMINAL_STATUSES = frozenset({"staged", "done"})


def _emit(obj: Any) -> None:
    json.dump(obj, sys.stdout)
    sys.stdout.write("\n")


def _die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)


def _parse_id_or_url(arg: str | None) -> int | None:
    if not arg:
        return None
    arg = arg.strip()
    if arg.isdigit():
        return int(arg)
    m = re.search(r"/documents/(\d+)/?", arg)
    if m:
        return int(m.group(1))
    _die(f"cannot parse doc id from argument: {arg!r}")


def _first_unprocessed() -> dict | None:
    docs = pl.list_all("/api/documents/", {"storage_path__isnull": "true"})
    docs = [d for d in docs if get_pipeline_status(d) not in TERMINAL_STATUSES]
    if not docs:
        return None
    docs.sort(key=lambda d: d["id"])
    return docs[0]


def cmd_resolve(args: argparse.Namespace) -> None:
    doc_id = _parse_id_or_url(args.target)
    if doc_id is None:
        doc = _first_unprocessed()
        if doc is None:
            _emit({"id": None, "message": "nothing to do"})
            return
    else:
        doc = pl.request("GET", f"/api/documents/{doc_id}/")
    status = get_pipeline_status(doc)
    _emit({
        "id": doc["id"],
        "title": doc.get("title"),
        "date": doc.get("created_date") or doc.get("created"),
        "paperless_url": f"{pl.BASE_URL}/documents/{doc['id']}/",
        "pipeline_status": status,
        "already_staged": status in TERMINAL_STATUSES,
    })


def _run_ocr(pdf: Path, out_dir: Path) -> list[Path]:
    if not OCR_PYTHON.exists():
        _die(
            f"OCR venv not found at {OCR_PYTHON}. "
            f"Run: cd {SCRIPTS_DIR}/ocr && uv venv && uv sync"
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(
        [str(OCR_PYTHON), str(OCR_SCRIPT), str(pdf), str(out_dir)],
        capture_output=True, text=True, check=True,
    )
    pages = [Path(line) for line in p.stdout.strip().splitlines() if line]
    if not pages:
        raise RuntimeError(f"OCR produced no pages for {pdf}\nstderr: {p.stderr[-500:]}")
    return pages


def cmd_fetch(args: argparse.Namespace) -> None:
    doc_id = args.doc_id
    work = doc_dir(PIPELINE_DIR, doc_id)
    pdf = work / "original.pdf"
    combined = work / "ocr_combined.md"

    if not pdf.exists():
        pl.download_original(doc_id, pdf)

    if args.force_ocr:
        for p in work.glob("page_*.md"):
            p.unlink()
        combined.unlink(missing_ok=True)

    pages = sorted(work.glob("page_*.md"))
    if not pages:
        pages = _run_ocr(pdf, work)
    page_texts = [p.read_text(encoding="utf-8") for p in pages]

    try:
        check_pages_raise(page_texts)
    except OcrQualityError as e:
        _die(f"OCR quality gate failed: {e}", code=2)

    markdown = "\n\n".join(
        f"--- page {i + 1} ---\n{text}" for i, text in enumerate(page_texts)
    )
    combined.write_text(markdown, encoding="utf-8")

    _emit({
        "pdf": str(pdf),
        "ocr_combined_md": str(combined),
        "pages": [str(p) for p in pages],
    })


def _candidate_path(doc_id: int) -> Path:
    return doc_dir(PIPELINE_DIR, doc_id) / "extraction.candidate.json"


def cmd_lint(args: argparse.Namespace) -> None:
    raw = sys.stdin.read()
    try:
        extraction = json.loads(raw)
    except json.JSONDecodeError as e:
        _die(f"invalid JSON on stdin: {e}", code=3)

    extraction["source"] = {
        "paperless_id": args.doc_id,
        "paperless_url": f"{pl.BASE_URL}/documents/{args.doc_id}/",
    }

    cand = _candidate_path(args.doc_id)
    cand.parent.mkdir(parents=True, exist_ok=True)
    cand.write_text(json.dumps(extraction, indent=2), encoding="utf-8")

    # History excludes the committed extraction for this doc (if any) so a
    # --force re-lint doesn't compare against its own predecessor.
    skip = extraction_path(PIPELINE_DIR, args.doc_id)
    history = load_history(PIPELINE_DIR, skip=skip)

    result = _lint(extraction, history)
    _emit({
        "ok": result.ok,
        "errors": list(result.errors),
        "warnings": list(result.warnings),
        "candidate_path": str(cand),
    })


def _make_job_key(pid: int, date: str, description: str, cost: float, idx: int) -> str:
    norm = re.sub(r"\s+", " ", description.lower()).strip()[:200]
    h = hashlib.sha1(f"{pid}|{date}|{norm}|{cost}|{idx}".encode()).hexdigest()[:8]
    return f"pl-{pid}-{date}-{idx:02d}-{h}"


def _attach_job_keys(extraction: dict) -> None:
    pid = extraction["source"]["paperless_id"]
    date = extraction["invoice"]["date"]
    for i, job in enumerate(extraction.get("jobs", [])):
        job["pipeline_job_key"] = _make_job_key(
            pid, date, job.get("description", ""), float(job.get("cost") or 0), i
        )


def cmd_commit(args: argparse.Namespace) -> None:
    cand = _candidate_path(args.doc_id)
    if not cand.exists():
        _die(
            f"no candidate at {cand}. Run 'lint' first to produce a candidate.",
            code=4,
        )

    extraction = json.loads(cand.read_text(encoding="utf-8"))
    _attach_job_keys(extraction)

    skip = extraction_path(PIPELINE_DIR, args.doc_id)
    history = load_history(PIPELINE_DIR, skip=skip)
    result = _lint(extraction, history)
    if not result.ok:
        _die(
            "candidate no longer passes lint — refusing to commit. "
            "Re-run lint with updated JSON. errors: " + "; ".join(result.errors),
            code=5,
        )

    dest = write_extraction(PIPELINE_DIR, args.doc_id, extraction)
    cand.unlink()
    set_pipeline_status(args.doc_id, "staged")
    _emit({"path": str(dest)})


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_resolve = sub.add_parser("resolve")
    p_resolve.add_argument("target", nargs="?")
    p_resolve.set_defaults(func=cmd_resolve)

    p_fetch = sub.add_parser("fetch")
    p_fetch.add_argument("doc_id", type=int)
    p_fetch.add_argument("--force-ocr", action="store_true")
    p_fetch.set_defaults(func=cmd_fetch)

    p_lint = sub.add_parser("lint")
    p_lint.add_argument("doc_id", type=int)
    p_lint.set_defaults(func=cmd_lint)

    p_commit = sub.add_parser("commit")
    p_commit.add_argument("doc_id", type=int)
    p_commit.set_defaults(func=cmd_commit)

    args = ap.parse_args()
    PIPELINE_DIR.mkdir(parents=True, exist_ok=True)
    args.func(args)


if __name__ == "__main__":
    main()
