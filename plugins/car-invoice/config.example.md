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

## vehicles.json format

Copy `vehicles.example.json` to your config location and fill in your vehicles:

```json
{
  "vehicles": [
    {
      "key": "sedan",
      "name": "2020 Toyota Camry SE",
      "vin": "4T1B11HK0LU000001",
      "paperless_storage_path": "car/sedan/{created_year}/",
      "paperless_tag": "sedan"
    }
  ]
}
```

| Field | Required | Description |
|---|---|---|
| `key` | ✓ | Machine identifier used in `vehicle_match` field of extracted JSON. Lowercase, hyphen-joined. |
| `name` | ✓ | Human-readable name (year, make, model, trim). |
| `vin` | — | Full 17-character VIN. Used by the linter to cross-check extracted VINs. |
| `paperless_storage_path` | — | Storage path template for Paperless. Created by `setup_paperless.py`. |
| `paperless_tag` | — | Tag created in Paperless for this vehicle. Defaults to the key if omitted. |

After filling in `vehicles.json`, run `setup_paperless.py` once to create the
corresponding storage paths, tags, and custom fields in your Paperless instance:

```bash
source "${CLAUDE_PLUGIN_ROOT}/scripts/init-env.sh"
cd "${CLAUDE_PLUGIN_ROOT}/scripts" && uv run setup_paperless.py
```

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
