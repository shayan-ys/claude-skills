# car-invoice — placeholder reference

This plugin requires runtime configuration for your Paperless-ngx instance and
your vehicle list. Install the plugin, then fill in each userConfig key via
the plugin settings UI (or your secret manager of choice).

## userConfig keys

| Key | Required | What it is | Example value |
|---|---|---|---|
| `paperlessUrl` | ✓ | Base URL of your Paperless-ngx instance. Exposed as `PAPERLESS_URL`. | `http://192.168.1.100:8000` |
| `paperlessToken` | ✓ | API token from Paperless Settings › Administration › Auth Token. Exposed as `PAPERLESS_TOKEN`. See below for secret-manager injection. | `abc123def456...` |
| `vehiclesConfigPath` | ✓ | Absolute path to your `vehicles.json` (copy `vehicles.example.json` and fill in your vehicles). Exposed as `CAR_INVOICE_VEHICLES_PATH`. | `/Users/you/.config/car-invoice/vehicles.json` |
| `pipelineStateDir` | — | Where to store OCR cache and staged extractions. Defaults to `~/.local/state/car-invoice` if unset. Exposed as `CAR_INVOICE_STATE_DIR`. | `/data/car-invoice-state` |

## Paperless API token

Get your token from:  
**Paperless-ngx → Settings → Administration → Auth Token**

You can also create one via the API:
```bash
curl -X POST http://<your-paperless-url>/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "yourpassword"}'
```

### Injecting the token without plaintext storage

Rather than storing the token in plain text, inject it at runtime:

**1Password / op run:**
```bash
# In your shell profile:
export PAPERLESS_TOKEN="op://YourVault/Paperless/token"
# Then run Claude Code with:
op run -- claude
```

**pass (Unix password store):**
```bash
export PAPERLESS_TOKEN="$(pass show paperless/api-token)"
```

**chamber (AWS Parameter Store):**
```bash
chamber exec car-invoice -- claude
```

When `PAPERLESS_TOKEN` is already set in the environment, the plugin uses it
directly and ignores the userConfig value.

## vehicles.json schema

`vehicles.json` is the single source of truth for your fleet. Copy `vehicles.example.json`,
fill in your vehicles, and save it somewhere permanent (e.g. `~/.config/car-invoice/vehicles.json`).

### Full annotated example

```json
{
  "vehicles": [
    {
      "key": "sedan",
      "name": "2020 Toyota Camry SE",
      "vin": "4T1B11HK0LU000001",
      "paperless_storage_path": "car/sedan/{created_year}/",
      "paperless_tag": "sedan",
      "paperless_storage_path_id": null,
      "paperless_tag_id": null
    }
  ]
}
```

### Field reference

| Field | Required | Set by | Description |
|---|---|---|---|
| `key` | ✓ | you | Machine identifier. Used as `vehicle_match` in extracted JSON and as the vehicle identifier throughout the pipeline. Lowercase, hyphen-joined (e.g. `sedan`, `family-suv`). |
| `name` | ✓ | you | Human-readable label shown in lint errors and summaries. Include year, make, model, trim (e.g. `2020 Toyota Camry SE`). |
| `vin` | — | you | Full 17-character VIN. The linter cross-checks extracted VINs against this value. Leave blank if unknown. |
| `paperless_storage_path` | — | you | Paperless storage path template. `{created_year}` is expanded by Paperless. Defaults to `car/<key>/{created_year}/` if omitted. |
| `paperless_tag` | — | you | Tag name created in Paperless for this vehicle. Defaults to `key` if omitted. |
| `paperless_storage_path_id` | — | `setup_paperless.py` | Numeric ID of the Paperless storage path object. Leave `null` before first run; `setup_paperless.py` fills it in automatically. Used by Phase 2 (push.py). |
| `paperless_tag_id` | — | `setup_paperless.py` | Numeric ID of the Paperless tag object for this vehicle. Leave `null` before first run; `setup_paperless.py` fills it in automatically. Used by Phase 2 (push.py). |

### First-time setup workflow

1. Copy `vehicles.example.json`, fill in `key`, `name`, `vin`, and the two `paperless_*` name fields.  
   Leave `paperless_storage_path_id` and `paperless_tag_id` as `null`.

2. Run `setup_paperless.py` (idempotent — safe to re-run):
   ```bash
   source "${CLAUDE_PLUGIN_ROOT}/scripts/init-env.sh"
   cd "${CLAUDE_PLUGIN_ROOT}/scripts" && uv run setup_paperless.py
   ```
   It creates (or finds) the storage paths, tags, and custom fields in Paperless, then
   **writes the assigned numeric IDs back into your `vehicles.json`**.

3. Your `vehicles.json` now contains the filled-in IDs:
   ```json
   { "vehicles": [{ ..., "paperless_storage_path_id": 5, "paperless_tag_id": 12 }] }
   ```

4. These IDs are used by Phase 2 (`push.py`) when it PATCHes documents with the correct
   storage path and tags. Phase 1 (extraction + staging) works without them.

## Pipeline state directory

Staged extractions and OCR cache live at `~/.local/state/car-invoice/<doc_id>/`:

```
~/.local/state/car-invoice/
└── <doc_id>/
    ├── original.pdf             ← downloaded from Paperless
    ├── page_1.md, page_2.md     ← per-page OCR output
    ├── ocr_combined.md          ← full OCR (all pages joined)
    ├── extraction.candidate.json ← in-progress extraction (deleted on commit)
    └── extraction.json          ← committed extraction
```

This directory is NOT inside the plugin directory, so it survives plugin updates.
Back it up if you want to preserve the OCR cache across reinstalls.
