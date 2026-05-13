---
name: notes-publish
description: Publish a Claude-authored writeup as a private, beautifully designed page on notes.shayanys.com — gets back a 22-char unguessable URL, search-engine-blocked, with a disclaimer footer. Always renders as a mobile-first designed page (works on iPhone 8's 320px viewport up). Use whenever Shayan wants to give a piece of content a shareable link without it being public/indexed: "publish this as a note", "share this privately", "make a private link for X", "put this on notes.shayanys.com", "unlist that note", "what's published on notes", "share by private URL", or any time the conversation produces a writeup (trip plan, research summary, recipe, longform reply) that he wants to send to one person via DM. Also use for unpublish/list operations on existing notes. The pipeline is at `Tools/notes-publisher/` in the Digital Brain repo.
---

# Publishing private notes to notes.shayanys.com

## What this is

A Mac-side pipeline (`Tools/notes-publisher/`) that publishes a static HTML page to `https://notes.shayanys.com/<22-char-slug>/`, pushes it through the private repo `shayan-ys/notes-site`, lets a Cloudflare Worker serve it, and then asks the Pi-side `notes-dash` mirror at `pi-jeff.nord:8181` to rebuild immediately so the new note shows up there too.

Three CLI surfaces:
- **`publish-and-refresh.sh`** — canonical publish path. Wraps `publish.py` + a Pi rebuild kick.
- **`list.py`** — read the ledger.
- **`unpublish.py`** — remove a slug.

## Privacy model — phrase it honestly

The privacy is **URL-obscurity**, not access control. Be straight with Shayan if the topic comes up:

- 22 chars of base64url ≈ 128 bits of entropy. Not crawlable, not guessable.
- Server headers: `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store` on HTML.
- `<meta name="robots" content="noindex,nofollow">` + `robots.txt: Disallow: /` keeps it out of search.
- Page footer warns the reader that any messenger the link passes through can see the URL.

**What it does NOT defend against:** anyone with the link can read the page. No auth. Forwarded link = forwarded access. Messengers that log URLs (Slack, iMessage previews, email scanners) hold the keys. Don't oversell.

---

## The publish workflow

Two steps: **design the body** (using the `frontend-design` skill), then **run the publish script**.

### Step 1: Design the body with the `frontend-design` skill

The published page is wrapped by `templates.py:wrap_body()`, which contributes:
- All required `<meta>` tags (charset, viewport with `viewport-fit=cover`, robots noindex, no-referrer, color-scheme light/dark).
- A favicon link to `/favicon.svg` (the notes-dash mark — a small italic `N` on cream with a vermilion dot).
- A tiny **fallback** baseline: `box-sizing: border-box`, fluid padding via `clamp()`, serif type matching the favicon palette (cream `#f3ece0` / ink `#1a1410`), `max-width: 70ch`, dark-mode fallback. Any `<style>` block in your body **overrides** all of this — that's by design.
- The disclaimer footer.

So the body file you produce should be a **self-contained designed page**: inline `<style>`, inline SVG decoration if you want it, custom typography, the whole thing. The wrapper will not fight you.

**Invoke the `frontend-design` skill** to design the body. Brief it with:

1. **Purpose**: What is this note? (trip plan, recipe, research summary, condolence note, gift-idea list, longform reply…) The aesthetic should reflect the content's tone.
2. **Recipient context if known**: one person via DM, technical vs. non-technical, mood (warm, businesslike, playful).
3. **Hard mobile constraints** (these are non-negotiable for this pipeline):
   - Must look polished at **320px viewport width** (iPhone 8 / SE portrait minus chrome). Pull this up in DevTools mentally: 320 px is *tight*. No horizontal scroll. No content cut off.
   - Fluid type: prefer `clamp(min, fluid, max)` over fixed `px`. Body text ~`clamp(1rem, 0.95rem + 0.3vw, 1.125rem)`. Headings scale down hard on small screens.
   - No fixed-pixel widths on containers (`max-width` is fine; `width: 700px` is not).
   - Touch targets (links, buttons) at least **44×44px** of hit area.
   - Generous line-height (≥1.5 for body) and `overflow-wrap: break-word` so long URLs don't blow out the layout.
   - Honor `@media (prefers-color-scheme: dark)` if you commit to a dark theme — or stay light/dark-neutral. Don't ship a light-only design that's unreadable in dark mode.
4. **Output shape**: a single HTML fragment that is *body content only* — what goes inside `<body>`. May include `<style>` blocks, may include inline `<svg>`, may include `<script>` (no external requests though — CSP-wise the Worker is permissive but external network calls from a notes page are weird). No `<!doctype>`, no `<html>`, no `<head>`, no top-level `<body>` tag.

Write the resulting fragment to a temp file (e.g. `/tmp/notes-<short-id>.html`).

**Example brief to frontend-design** (do not paraphrase as instructions to the user — this is how the body should be authored):

> Build a body fragment for a note titled "Trip to Elora". Editorial/travel-magazine aesthetic: serif display headings, generous whitespace, a small inline SVG ribbon as a section separator, warm palette anchored on cream `#f3ece0` and vermilion `#b73e1f` (matching the site favicon). Mobile-first; must read well at 320px. Body content: a one-paragraph intro, a "Stops" list with 4 items each having a name and a one-line note, and a closing line. Output: just the inner-body HTML with its own `<style>` tag.

### Step 2: Run the publish script

```bash
cd "/Users/shayanys/Documents/personal/home-lab/Digital Brain/Tools/notes-publisher"
source ~/.config/op/homeserver.env
./publish-and-refresh.sh /tmp/notes-<short-id>.html --title "Trip to Elora"
```

The script:
1. Calls `publish.py` inside `op run --env-file .env.tpl --` so `GITHUB_TOKEN` is injected and the git push works.
2. Captures the URL printed by `publish.py`.
3. SSHes to `pi-jeff.nord` and runs `docker exec notes-dash python3 /app/build_manifest.py` so the dashboard's manifest and `stats.json` rebuild *immediately* — the */10 cron is the fallback, this is the fast path. Touch ID prompt for the 1P SSH agent is expected once per session.
4. If the Pi rebuild fails (Pi offline, Touch ID timeout, container not running), publish still succeeds — the rebuild step is best-effort. It prints `dashboard rebuild: skipped/failed` to stderr and continues.
5. Prints the URL verbatim on the **last line of stdout**.

**Print the URL exactly as the script returned it** when reporting back to Shayan. Don't paraphrase, don't add tracking params.

### Pi dashboard widget caveat

The Homepage tile at `pi-jeff.nord:3000` polls `notes-dash`'s `stats.json` every 60s (`refreshInterval: 60000` in `Tools/homepage/config/services.yaml`). Even after the immediate Pi rebuild, that tile can lag up to a minute. There's no "refresh now" API on the Homepage widget; this is just how it works.

### Cloudflare propagation

The Worker redeploys on git push. ~15–30s after the script returns, the URL goes live. First curl might 404 in that window — that's expected, not a bug.

### Optional: pass `--skip-pi`

If you're publishing while the Pi is being worked on (sshd restart in progress, etc.) and don't want the SSH attempt, append `--skip-pi`:

```bash
./publish-and-refresh.sh /tmp/body.html --title "x" --skip-pi
```

---

## The list workflow

```bash
cd "/Users/shayanys/Documents/personal/home-lab/Digital Brain/Tools/notes-publisher"
.venv/bin/python list.py
```

Prints a table sorted by `updated` descending. No `op run` needed — pure local read of `.pipeline/repo/.ledger.json`.

---

## The unpublish workflow

```bash
cd "/Users/shayanys/Documents/personal/home-lab/Digital Brain/Tools/notes-publisher"
source ~/.config/op/homeserver.env
op run --env-file .env.tpl -- .venv/bin/python unpublish.py --slug=<slug>
```

Use `--slug=<slug>` (named option, with `=`), not positional — older slugs starting with `-` collided with flag parsing. Current `slug.py` regenerates until the first char is alphanumeric, so new slugs are safe; old ones still work via `--slug=...`.

Unpublish: removes `<slug>/` from the repo, removes the ledger entry, commits, pushes. The edge cache may still serve the old page for up to 1 hour (`Cache-Control: public, max-age=3600` in `_headers`); there is no explicit cache-purge call.

If you also want the Pi dashboard to drop the entry immediately, follow up with:

```bash
ssh pi-jeff.nord 'docker exec notes-dash python3 /app/build_manifest.py'
```

(There's no `unpublish-and-refresh.sh` yet — add one if this becomes a frequent flow.)

---

## Verifying a publish/unpublish (smoke test)

macOS's local DNS resolver caches negative lookups for `notes.shayanys.com` aggressively. Bypass it with `--resolve`:

```bash
IP=$(dig +short notes.shayanys.com @1.1.1.1 | head -1)

# Page is live
curl -s --resolve "notes.shayanys.com:443:$IP" -o /dev/null -w "%{http_code}\n" "https://notes.shayanys.com/<slug>/"
# Expect: 200 (after ~30s of CF redeploy)

# Favicon shipped
curl -s --resolve "notes.shayanys.com:443:$IP" -o /dev/null -w "%{http_code}\n" "https://notes.shayanys.com/favicon.svg"
# Expect: 200

# Spot-check the design markers
curl -s --resolve "notes.shayanys.com:443:$IP" "https://notes.shayanys.com/<slug>/" \
  | grep -E '<title>|<link rel="icon"|viewport|color-scheme'

# Pi dashboard picked it up. manifest.json is a bare top-level array of page objects.
curl -s "http://pi-jeff.nord:8181/manifest.json" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d))'
```

If you must verify without `--resolve`, `sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder` clears the local cache. `--resolve` is faster and no sudo.

---

## Common pitfalls

- **Forgetting `source ~/.config/op/homeserver.env`**: `publish-and-refresh.sh` checks for `OP_SERVICE_ACCOUNT_TOKEN` and exits 2 with a clear error if missing. Just source the env and rerun.
- **Body file is a full HTML document**: the wrapper wraps just the inner-body HTML. If you ship `<!doctype html><html>...`, you'll get nested `<html>` and broken rendering. The frontend-design output should be body-content only.
- **Body styles conflict with the wrapper**: shouldn't happen — the wrapper's `<style>` is generic and the body's `<style>` comes later in the document, so it wins by source order. If a wrapper rule survives unexpectedly (most often `body { max-width: 70ch }`), override it explicitly in the body's style, e.g. `body { max-width: none; }`.
- **Title with shell metacharacters**: pass `--title` as a single quoted argument. `wrap_body()` HTML-escapes the title (covered by `test_wrap_escapes_title`), so `&`, `<`, `>` are safe content-wise — quoting is just shell hygiene.
- **Editing in `.pipeline/repo/` directly**: don't. That's the pipeline's working clone. The exception is `.pipeline/repo/favicon.svg`, which is a tracked site asset (one-time write); modifying anything else there can conflict with the next `git pull` inside `publish.py`.
- **iPhone 8 viewport (320 CSS px) regressions**: if the user complains a published page "looks plain" or "doesn't fit on my phone", load it in DevTools at 320px width *before* re-publishing a fix. Almost every reported "ugly" issue is one of: missing custom `<style>` block in the body, fixed `px` widths, or skipped `frontend-design` invocation.

---

## When NOT to use this skill

- Shayan wants something on his actual blog or Wiki — that's the Obsidian vault under `Wiki/`, not this. This skill is for ephemeral private one-off shares.
- Content is sensitive (passwords, internal client info, PII, financial). URL-obscurity is not enough — DM the content as text instead.
- Recipient needs editable / collaborative access. This serves static HTML only.
- The content is throwaway and a paragraph in chat would do. Not every reply needs a URL.
