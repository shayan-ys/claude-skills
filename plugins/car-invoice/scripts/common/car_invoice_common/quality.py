"""Post-OCR page quality gate for PaddleOCR-VL output.

Detects hallucination patterns, near-empty pages, and repetition loops.
Call check_pages_raise() to block the pipeline on bad pages.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


class OcrQualityError(Exception):
    """Raised when the quality gate flags one or more pages."""

    def __init__(self, faults: list[PageFault]) -> None:
        self.faults = faults
        lines = [f"  page {f.page_num}: {', '.join(f.reasons)}" for f in faults]
        super().__init__("OCR quality gate failed:\n" + "\n".join(lines))


@dataclass
class PageFault:
    page_num: int
    reasons: list[str] = field(default_factory=list)


HALLUCINATION_STRINGS = [
    "download your product",
    "service part 04",
    "download free",
    "update to the latest version",
]

# 50+ char substring repeated 4+ times — only catches egregious loops the sanitizer missed
_REPETITION_RE = re.compile(r"(.{50,}?)\1{3,}", re.IGNORECASE | re.DOTALL)

# "Page N/M" or "Page N of M" — captures the total M
_PAGE_MARKER_RE = re.compile(r"\bpage\s+\d+\s*(?:[/]|of)\s*(\d+)", re.IGNORECASE)


def _non_empty_lines(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if ln.strip()]


def _check_page_text(text: str, page_num: int, total_pages: int) -> list[str]:
    reasons: list[str] = []
    stripped = text.strip()
    lines = _non_empty_lines(text)

    # Known hallucination strings
    lower = stripped.lower()
    for s in HALLUCINATION_STRINGS:
        if s in lower:
            reasons.append(f"hallucination string: {s!r}")
            break

    # Post-OCR repetition detector (50+ char substring repeated 4+ times)
    if _REPETITION_RE.search(stripped):
        reasons.append("repeated text pattern detected")

    # >30% duplicate lines (requires >4 lines to avoid short-page false positives)
    if len(lines) > 4:
        counts: dict[str, int] = {}
        for ln in lines:
            counts[ln.strip().lower()] = counts.get(ln.strip().lower(), 0) + 1
        dup_lines = sum(1 for cnt in counts.values() if cnt > 1)
        if dup_lines / len(lines) > 0.30:
            reasons.append(f"duplicate lines: {dup_lines}/{len(lines)}")

    # PAGE N OF M mismatch: only flag when claimed_total > actual (OCR hallucinated more pages).
    for m in _PAGE_MARKER_RE.finditer(stripped):
        claimed_total = int(m.group(1))
        if claimed_total > total_pages:
            reasons.append(
                f"page marker claims {claimed_total} total pages but doc has {total_pages}"
            )
            break

    return reasons


def check_pages(page_texts: list[str]) -> list[PageFault]:
    """Check a list of OCR page texts. Returns PageFault list (empty = all clean)."""
    total = len(page_texts)
    faults: list[PageFault] = []

    # Pipeline-level catastrophic failure: OCR produced almost nothing across the whole doc.
    total_chars = sum(len(t.strip()) for t in page_texts)
    sparse_pages = sum(1 for t in page_texts if len(t.strip()) < 50)
    if total_chars < 500 or (total > 0 and sparse_pages / total > 0.5):
        faults.append(PageFault(
            page_num=0,
            reasons=[f"catastrophic OCR failure: {total_chars} chars across {total} pages"],
        ))
        return faults

    for idx, text in enumerate(page_texts):
        reasons = _check_page_text(text, page_num=idx + 1, total_pages=total)
        if reasons:
            faults.append(PageFault(page_num=idx + 1, reasons=reasons))
    return faults


def check_pages_raise(page_texts: list[str]) -> None:
    """Run check_pages and raise OcrQualityError if any faults found."""
    faults = check_pages(page_texts)
    if faults:
        raise OcrQualityError(faults)


def check_pages_from_dir(page_dir: Path) -> list[PageFault]:
    """Load page_N.md files from a directory and run quality checks."""
    page_dir = Path(page_dir)
    pages = sorted(
        page_dir.glob("page_*.md"),
        key=lambda p: int(p.stem.split("_")[1]),
    )
    if not pages:
        raise FileNotFoundError(f"No page_*.md files found in {page_dir}")
    texts = [p.read_text(encoding="utf-8") for p in pages]
    return check_pages(texts)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quality.py <page-dir>", file=sys.stderr)
        sys.exit(1)
    faults = check_pages_from_dir(Path(sys.argv[1]))
    if not faults:
        print("All pages passed quality checks.")
    else:
        print(f"Quality gate flagged {len(faults)} page(s):")
        for f in faults:
            print(f"  page {f.page_num}: {', '.join(f.reasons)}")
        sys.exit(1)
