# car-invoice

> Process scanned car-maintenance invoices end-to-end — OCR, structured extraction, lint, and stage to Paperless-ngx.

**Requirements: macOS on Apple Silicon (M1/M2/M3/M4).** This plugin uses [mlx_vlm](https://github.com/Blaizzy/mlx-vlm) for OCR, which is Apple-only. Linux/x86 users can fork and swap the OCR backend — see `scripts/ocr/ocr.py` for the contract (it takes a PDF path, writes `page_N.md` files, and prints their paths to stdout).

## What it does

`/car-invoice` processes one invoice per invocation through a five-stage pipeline:

1. **Resolve** — find the next unprocessed Paperless document (or accept a specific doc ID/URL)
2. **Fetch + OCR** — download the PDF from Paperless, run PaddleOCR-VL, produce per-page markdown combining VLM output and the PDF text layer
3. **Extract** — Claude reads the OCR markdown and produces a structured JSON following strict rules (no arithmetic, verbatim source quotes, vehicle matching)
4. **Lint** — a deterministic Python linter validates the JSON (cost checksums, VIN cross-checks, odometer bracketing against history, deferred-item provenance)
5. **Approve + Stage** — you review a compact summary, optionally edit, then approve; the extraction is committed and `pipeline_status=staged` is set in Paperless

Phase 2 (push to LubeLogger + full Paperless metadata update) is stubbed in `scripts/push.py` — not yet implemented.

## Prerequisites

- Mac with Apple Silicon (M1 or later)
- [uv](https://docs.astral.sh/uv/) (`brew install uv`)
- [Paperless-ngx](https://docs.paperless-ngx.com/) instance running and reachable
- Your invoices already imported into Paperless (scanned PDFs)

## Installation

### 1. Install the plugin

Install via your Claude Code plugin manager (or clone directly into your plugins directory).

### 2. Bootstrap the scripts venv

```bash
cd "${CLAUDE_PLUGIN_ROOT}/scripts"
uv venv
uv sync
```

### 3. Bootstrap the OCR venv

The OCR engine uses a separate venv because its dependencies (mlx-vlm) are large and ML-specific.

```bash
cd "${CLAUDE_PLUGIN_ROOT}/scripts/ocr"
uv venv
uv sync
```

This will download the PaddleOCR-VL 1.5 4-bit model (~2 GB) on first run.

### 4. Configure the plugin

Copy `vehicles.example.json` to your preferred location (e.g. `~/.config/car-invoice/vehicles.json`) and fill in your vehicles. Leave `paperless_storage_path_id` and `paperless_tag_id` as `null` for now — they are filled in by `setup_paperless.py` in the next step:

```json
{
  "vehicles": [
    {
      "key": "my-car",
      "name": "2020 Toyota Camry SE",
      "vin": "4T1B11HK0LU000001",
      "paperless_storage_path": "car/my-car/{created_year}/",
      "paperless_tag": "my-car",
      "paperless_storage_path_id": null,
      "paperless_tag_id": null
    }
  ]
}
```

Then configure the plugin userConfig:
- **Paperless URL** — e.g. `http://192.168.1.100:8000`
- **Paperless API token** — from Paperless Settings › Administration › Auth Token
- **Vehicles config path** — absolute path to your `vehicles.json`
- **Pipeline state dir** — optional; defaults to `~/.local/state/car-invoice`

See `config.example.md` for the full vehicles.json schema and secret-manager injection patterns.

### 5. Create Paperless metadata objects (idempotent)

Run `setup_paperless.py` once to create the storage paths, tags, and custom fields in Paperless. It is **idempotent** — re-running is safe, it checks for existing objects before creating new ones.

```bash
source "${CLAUDE_PLUGIN_ROOT}/scripts/init-env.sh"
cd "${CLAUDE_PLUGIN_ROOT}/scripts" && uv run setup_paperless.py
```

After it runs, it **writes the assigned Paperless IDs back to your `vehicles.json`**, filling in `paperless_storage_path_id` and `paperless_tag_id`. These IDs are used by Phase 2 (push.py) to PATCH documents with the correct metadata.

Example post-run `vehicles.json` (IDs assigned by Paperless):

```json
{
  "vehicles": [
    {
      "key": "my-car",
      "name": "2020 Toyota Camry SE",
      "paperless_storage_path_id": 5,
      "paperless_tag_id": 12
    }
  ]
}
```

## Usage

```
/car-invoice                    # process the next unprocessed invoice in queue
/car-invoice 42                 # process doc ID 42
/car-invoice http://...         # process doc by Paperless URL
/car-invoice 42 --force         # reprocess an already-staged doc
/car-invoice 42 --force-ocr     # discard cached OCR and re-run
```

## How it works in detail

### OCR strategy

Each PDF page is processed two ways:
1. **VLM OCR** (PaddleOCR-VL 1.5 4-bit via mlx_vlm) — image-based, good at tables and checkboxes but can garble digits
2. **PDF text layer** — exact characters from the embedded text stream (when present)

Both outputs are merged into a labeled markdown block per page. Claude uses both as complementary evidence, preferring the text layer when they disagree on numerals.

### Extraction rules

The extraction prompt (`scripts/extraction_prompt.md`) defines strict rules:
- **No arithmetic** — every cost must be read verbatim from a specific OCR line
- **Source provenance** — every job cost and deferred item must cite the exact OCR substring it came from
- **Total invoice only** — `total_cost` can only come from an explicit `TOTAL INVOICE` / `INVOICE TOTAL` / `Grand Total` line

### Linter checks

`lint.py` validates the extraction against these rules deterministically:
- Cost checksum: `sum(jobs.cost) + tax + misc_chg - misc_disc ≈ total_cost` (±$1.00)
- VIN cross-check: extracted VIN must match one of your configured vehicles
- Odometer bracketing: new reading must be consistent with historical readings
- Deferred provenance: `source_quote` must appear verbatim in the OCR text
- Job contiguity: every `JOB# N` marker must be accounted for (either as a job or in `missing_jobs`)

### Pipeline state

Extractions are staged at `~/.local/state/car-invoice/<doc_id>/extraction.json` and `pipeline_status=staged` is set as a custom field in Paperless. This lets you:
- Resume a partial run (the candidate JSON is preserved between invocations)
- Run push.py later to complete Phase 2

## File layout

```
plugins/car-invoice/
├── .claude-plugin/
│   └── plugin.json              # userConfig schema
├── commands/
│   └── car-invoice.md           # the /car-invoice slash command
├── scripts/
│   ├── enrich.py                # pipeline orchestrator (resolve/fetch/lint/commit)
│   ├── lint.py                  # deterministic JSON linter
│   ├── vocab.py                 # canonical tag/severity vocabulary
│   ├── extraction_prompt.md     # Claude's extraction rulebook
│   ├── setup_paperless.py       # one-shot Paperless metadata setup
│   ├── push.py                  # Phase 2 stub (not yet implemented)
│   ├── init-env.sh              # env var injector (source before uv run)
│   ├── pyproject.toml
│   ├── common/                  # shared utilities (Paperless client, pipeline state, quality gate)
│   │   ├── car_invoice_common/
│   │   │   ├── paperless.py     # Token-auth Paperless REST client
│   │   │   ├── pipeline.py      # pipeline state helpers
│   │   │   └── quality.py       # OCR quality gate
│   │   └── pyproject.toml
│   └── ocr/                     # OCR sidecar (separate venv — heavy ML deps)
│       ├── ocr.py               # PaddleOCR-VL wrapper
│       └── pyproject.toml
├── vehicles.example.json        # vehicle config template
├── config.example.md            # userConfig and vehicles.json reference
└── README.md                    # this file
```

## Troubleshooting

**`PAPERLESS_TOKEN env var is not set`**  
Run `source "${CLAUDE_PLUGIN_ROOT}/scripts/init-env.sh"` first, or verify your plugin userConfig has `paperlessToken` set.

**`CAR_INVOICE_VEHICLES_PATH env var is not set`**  
Set `vehiclesConfigPath` in plugin userConfig to the absolute path of your `vehicles.json`.

**OCR venv not found at scripts/ocr/.venv**  
Run: `cd "${CLAUDE_PLUGIN_ROOT}/scripts/ocr" && uv venv && uv sync`

**OCR is slow on first run**  
The model (~2 GB) is downloaded on first use. Subsequent runs use the cached model.

**`HALLUCINATION_STRINGS` / quality gate keeps failing**  
The quality gate (`common/car_invoice_common/quality.py`) detected repetition or known hallucination patterns. Pass `--force-ocr` to re-run OCR if you believe the cached output is stale, or pass `--force` to override the quality gate check (at your own risk).

**`invoice.vehicle_match ... not in known vehicles`**  
The VIN or make/model in the invoice doesn't match any vehicle in your `vehicles.json`. Either update `vehicles.json` to add the vehicle, or manually set `vehicle_match` during the edit step.

## Known limitations

- **Mac/Apple Silicon only** — the OCR engine requires MLX. No Linux/Windows fallback for the OCR step. If you already have cached OCR output (page_*.md files), the extraction/lint/commit steps work on any platform.
- **Phase 2 not implemented** — LubeLogger push and full Paperless metadata update are stubbed. See `scripts/push.py`.
- **`pipeline_status` field name** — if you run multiple Claude Code pipelines on the same Paperless instance, they will share the `pipeline_status` custom field. Future pipelines should use a namespaced field name (e.g. `car_invoice_pipeline_status`).

## License

MIT
