"""Canonical enums for car-pipeline extractions.

Car-specific vocabulary lives here because these tags and severities are
domain-specific to car-maintenance invoices.

Used by:
  - lint.py            : warn on non-canonical values, offer alias suggestions
  - extraction_prompt  : linked as the source-of-truth for tags/severity

When adding a new canonical tag or severity, update BOTH this file and the
"CANONICAL TAGS" section of extraction_prompt.md.
"""
from __future__ import annotations

# --- record_type ----------------------------------------------------------

RECORD_TYPES: frozenset[str] = frozenset({"service", "repair", "upgrade"})

# --- deferred severity ----------------------------------------------------
# yellow = attention-soon (inspection middle column, or "recommended not done")
# red    = immediate attention (inspection right column)
# info   = shop suggestion without an inspection flag (declined services list)

DEFERRED_SEVERITIES: frozenset[str] = frozenset({"yellow", "red", "info"})

# --- jobs[].tags ----------------------------------------------------------
# Canonical vocabulary. Keep lowercase, hyphen-joined. Expand deliberately.

CANONICAL_TAGS: frozenset[str] = frozenset({
    # routine maintenance
    "oil-change",
    "maintenance",
    "inspection",
    "cabin-air-filter",
    "engine-air-filter",
    "brake-service",
    "brake-fluid-flush",
    "transmission-fluid",
    "coolant-flush",
    "spark-plugs",
    "ignition",
    "serpentine-belt",
    "belt",
    "battery",
    "alignment",
    "wiper-blades",
    "fuel-induction",
    # tires — note: swap and storage are distinct operations
    "tires",
    "tire-swap",        # seasonal changeover (on/off vehicle)
    "tire-storage",     # holding tires off-vehicle between seasons
    "seasonal",
    # warranty / recall / goodwill
    "warranty",
    "recall",
    "goodwill",
    # body / rust / accessories
    "rust-protection",
    "detailing",
    # diagnostics
    "diagnostic",
})

# Aliases → canonical. When lint sees an alias it warns and suggests the target.
# Keep this list explicit; do not fuzzy-match.
TAG_ALIASES: dict[str, str] = {
    # tire vocabulary collapse (storage kept distinct)
    "tire-change": "tire-swap",
    "seasonal-changeover": "tire-swap",
    "tire-rotation": "tire-swap",
    # abbreviation expansion
    "lof": "oil-change",           # lube, oil & filter
    "dvi": "inspection",           # dealer vehicle inspection
    "pdel": "inspection",          # pre-delivery / dealer inspection
    "bcm": "recall",               # BCM-related items are recall work
    # casing/style normalizations
    "oilchange": "oil-change",
    "sparkplugs": "spark-plugs",
    "brake": "brake-service",
    "brakes": "brake-service",
}


def canonicalize_tag(tag: str) -> tuple[str, bool]:
    """Return (canonical_tag, was_aliased).

    If tag is already canonical, returns (tag, False).
    If tag is a known alias, returns (canonical, True).
    If tag is unknown, returns (tag, False) — caller decides warn/error.
    """
    if tag in CANONICAL_TAGS:
        return tag, False
    if tag in TAG_ALIASES:
        return TAG_ALIASES[tag], True
    return tag, False


def is_known_tag(tag: str) -> bool:
    """True if tag is canonical OR a known alias."""
    return tag in CANONICAL_TAGS or tag in TAG_ALIASES


# --- customer name normalization -----------------------------------------

def normalize_customer(name: str) -> str:
    """Normalize a customer name to title case, first-last order.

    Rules:
      - ALL CAPS → title case ("JOHN SMITH" → "John Smith")
      - "Last, First" → "First Last"
      - collapse whitespace

    Leaves already-normalized names ("John Smith") untouched.
    """
    s = " ".join(name.split())
    if "," in s:
        parts = [p.strip() for p in s.split(",", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            s = f"{parts[1]} {parts[0]}"
    # If the string has no lowercase letters, title-case it. Otherwise leave
    # it alone (don't clobber names like "McDonald" or "de la Cruz").
    if s and not any(c.islower() for c in s if c.isalpha()):
        s = s.title()
    return s


# --- money precision ------------------------------------------------------

def round_money(value: float | int | None) -> float | None:
    """Round a money value to 2 decimal places, preserving None."""
    if value is None:
        return None
    return round(float(value), 2)
