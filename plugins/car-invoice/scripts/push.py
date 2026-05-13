"""Phase 2 push — STUB.

This script replays every staged extraction.json into LubeLogger and then
PATCHes Paperless (title, doc type, correspondent, tags, storage path,
lubelogger_ids, pipeline_status=done).

Not implemented yet — finish the extraction backfill first, review the staged
JSON in your pipeline state directory, then flesh this out.

Phase 1 is extraction-only: OCR → extract → lint → stage to Paperless.
Phase 2 adds the LubeLogger push and Paperless metadata update.
"""
from __future__ import annotations

import sys


def main() -> None:
    print(
        "push.py is not implemented yet. Stage all docs with enrich.py first, "
        "review them in your pipeline state directory, then implement push.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
