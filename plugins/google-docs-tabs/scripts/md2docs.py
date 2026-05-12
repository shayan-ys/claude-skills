#!/usr/bin/env python3
"""Render a markdown file into a Google Docs tab with real formatting.

Usage:
  md2docs.py <docId> <tabId> <mdPath>

Replaces the entire tab body with rendered markdown. Supports:
  # / ## / ### headings, **bold**, *italic*, `code`, - bullets, 1. numbered,
  > blockquote, --- hr, | tables |, blank lines.
"""
import json, os, re, sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

SA = os.environ.get('SA_PATH')
if not SA:
    sys.exit("error: SA_PATH env var is required (path to Google service-account JSON)")

def docs_client():
    creds = service_account.Credentials.from_service_account_file(
        SA, scopes=['https://www.googleapis.com/auth/documents'])
    return build('docs', 'v1', credentials=creds)

def get_doc(docId):
    return docs_client().documents().get(documentId=docId, includeTabsContent=True).execute()

def walk_all(tabs):
    for t in tabs:
        yield t
        yield from walk_all(t.get('childTabs', []))

# ---------- markdown parsing ----------

INLINE_RE = re.compile(r'(\*\*[^*\n]+?\*\*|\*[^*\n]+?\*|`[^`\n]+?`)')

def parse_inline(text):
    """Return list of (text, style_dict). style_dict applies to that span."""
    spans = []
    pos = 0
    for m in INLINE_RE.finditer(text):
        if m.start() > pos:
            spans.append((text[pos:m.start()], {}))
        tok = m.group(0)
        if tok.startswith('**'):
            spans.append((tok[2:-2], {'bold': True}))
        elif tok.startswith('`'):
            spans.append((tok[1:-1], {'code': True}))
        else:
            spans.append((tok[1:-1], {'italic': True}))
        pos = m.end()
    if pos < len(text):
        spans.append((text[pos:], {}))
    return spans

def parse_blocks(md):
    """Return list of block dicts: {type, level?, spans, items?}"""
    lines = md.split('\n')
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip()

        if not stripped:
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^-{3,}\s*$', stripped):
            blocks.append({'type': 'hr'})
            i += 1
            continue

        # Headings
        m = re.match(r'^(#{1,6})\s+(.*)$', stripped)
        if m:
            level = len(m.group(1))
            blocks.append({'type': 'heading', 'level': level,
                           'spans': parse_inline(m.group(2))})
            i += 1
            continue

        # Tables
        if '|' in stripped and i + 1 < len(lines) and re.match(r'^\s*\|?[\s\-:|]+\|?\s*$', lines[i+1]):
            rows = []
            while i < len(lines) and '|' in lines[i]:
                row = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                rows.append(row)
                i += 1
            # rows[1] is the separator
            header = rows[0]
            body = rows[2:]
            blocks.append({'type': 'table', 'header': header, 'body': body})
            continue

        # Blockquote
        if stripped.startswith('>'):
            qlines = []
            while i < len(lines) and lines[i].lstrip().startswith('>'):
                qlines.append(re.sub(r'^\s*>\s?', '', lines[i]))
                i += 1
            blocks.append({'type': 'quote',
                           'spans': parse_inline('\n'.join(qlines).strip())})
            continue

        # Bullet list
        if re.match(r'^[-*]\s+', stripped):
            items = []
            while i < len(lines) and re.match(r'^[-*]\s+', lines[i].strip()):
                txt = re.sub(r'^[-*]\s+', '', lines[i].strip())
                items.append(parse_inline(txt))
                i += 1
            blocks.append({'type': 'bullets', 'items': items})
            continue

        # Numbered list
        if re.match(r'^\d+\.\s+', stripped):
            items = []
            while i < len(lines) and re.match(r'^\d+\.\s+', lines[i].strip()):
                txt = re.sub(r'^\d+\.\s+', '', lines[i].strip())
                items.append(parse_inline(txt))
                i += 1
            blocks.append({'type': 'numbered', 'items': items})
            continue

        # Paragraph (collect until blank line)
        plines = [stripped]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#{1,6}\s|>|[-*]\s|\d+\.\s|-{3,}\s*$)', lines[i].strip()):
            plines.append(lines[i].rstrip())
            i += 1
        blocks.append({'type': 'para', 'spans': parse_inline(' '.join(plines))})
    return blocks

# ---------- request building ----------

HEADING_NAMED_STYLE = {1: 'HEADING_1', 2: 'HEADING_2', 3: 'HEADING_3',
                      4: 'HEADING_4', 5: 'HEADING_5', 6: 'HEADING_6'}

def build_requests(blocks, tabId, start_index=1):
    """Return (requests, total_inserted_chars). Inserts in reverse-friendly order:
    we insert sequentially at increasing indices, then apply styles in a second pass.
    Approach: build the full text first, then a single insertText, then style updates."""
    # Build text and collect style ranges (relative to start_index)
    text_parts = []
    style_reqs = []  # (range_start, range_end, style_kind, payload)
    para_styles = []  # (range_start, range_end, named_style)
    bullet_ranges = []  # (range_start, range_end, preset)

    cursor = start_index

    def emit_text(s):
        nonlocal cursor
        text_parts.append(s)
        cursor += len(s)

    def emit_spans(spans):
        for txt, style in spans:
            seg_start = cursor
            emit_text(txt)
            seg_end = cursor
            if style.get('bold'):
                style_reqs.append((seg_start, seg_end, {'bold': True}, 'bold'))
            if style.get('italic'):
                style_reqs.append((seg_start, seg_end, {'italic': True}, 'italic'))
            if style.get('code'):
                style_reqs.append((seg_start, seg_end,
                    {'weightedFontFamily': {'fontFamily': 'Roboto Mono'},
                     'backgroundColor': {'color': {'rgbColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}}}},
                    'code'))

    for b in blocks:
        if b['type'] == 'heading':
            p_start = cursor
            emit_spans(b['spans'])
            emit_text('\n')
            para_styles.append((p_start, cursor, HEADING_NAMED_STYLE.get(b['level'], 'HEADING_3')))
        elif b['type'] == 'para':
            p_start = cursor
            emit_spans(b['spans'])
            emit_text('\n')
            para_styles.append((p_start, cursor, 'NORMAL_TEXT'))
        elif b['type'] == 'quote':
            p_start = cursor
            emit_spans(b['spans'])
            emit_text('\n')
            # use NORMAL_TEXT but italicize entire range and indent
            style_reqs.append((p_start, cursor - 1, {'italic': True}, 'italic'))
            para_styles.append((p_start, cursor, 'NORMAL_TEXT'))
        elif b['type'] == 'hr':
            p_start = cursor
            emit_text('───\n')
            para_styles.append((p_start, cursor, 'NORMAL_TEXT'))
        elif b['type'] == 'bullets':
            list_start = cursor
            for spans in b['items']:
                emit_spans(spans)
                emit_text('\n')
            list_end = cursor
            bullet_ranges.append((list_start, list_end, 'BULLET_DISC_CIRCLE_SQUARE'))
        elif b['type'] == 'numbered':
            list_start = cursor
            for spans in b['items']:
                emit_spans(spans)
                emit_text('\n')
            list_end = cursor
            bullet_ranges.append((list_start, list_end, 'NUMBERED_DECIMAL_ALPHA_ROMAN'))
        elif b['type'] == 'table':
            # Render as plain bolded header line + tab-separated rows
            p_start = cursor
            emit_spans([(' | '.join(b['header']), {'bold': True})])
            emit_text('\n')
            para_styles.append((p_start, cursor, 'NORMAL_TEXT'))
            for row in b['body']:
                p_start = cursor
                emit_spans(parse_inline(' | '.join(row)))
                emit_text('\n')
                para_styles.append((p_start, cursor, 'NORMAL_TEXT'))

    full_text = ''.join(text_parts)

    requests = []
    # 1. insert text
    requests.append({'insertText': {
        'location': {'index': start_index, 'tabId': tabId},
        'text': full_text}})

    # 2. paragraph styles (apply named style)
    for s, e, named in para_styles:
        if e <= s:
            continue
        requests.append({'updateParagraphStyle': {
            'range': {'startIndex': s, 'endIndex': e, 'tabId': tabId},
            'paragraphStyle': {'namedStyleType': named},
            'fields': 'namedStyleType'}})

    # 3. bullets
    for s, e, preset in bullet_ranges:
        if e <= s:
            continue
        requests.append({'createParagraphBullets': {
            'range': {'startIndex': s, 'endIndex': e, 'tabId': tabId},
            'bulletPreset': preset}})

    # 4. text styles
    for s, e, payload, kind in style_reqs:
        if e <= s:
            continue
        if kind == 'bold':
            fields = 'bold'
        elif kind == 'italic':
            fields = 'italic'
        elif kind == 'code':
            fields = 'weightedFontFamily,backgroundColor'
        requests.append({'updateTextStyle': {
            'range': {'startIndex': s, 'endIndex': e, 'tabId': tabId},
            'textStyle': payload,
            'fields': fields}})

    return requests, len(full_text)

def clear_tab(client, docId, tabId):
    """Delete all body content in the tab, leaving an empty paragraph."""
    doc = get_doc(docId)
    tab = next((t for t in walk_all(doc.get('tabs', []))
                if t.get('tabProperties', {}).get('tabId') == tabId), None)
    if not tab:
        raise SystemExit(f"tab not found: {tabId}")
    body = tab['documentTab']['body']['content']
    end = body[-1]['endIndex'] - 1
    if end <= 1:
        return
    client.documents().batchUpdate(
        documentId=docId,
        body={'requests': [{'deleteContentRange': {
            'range': {'startIndex': 1, 'endIndex': end, 'tabId': tabId}}}]}).execute()

def main():
    if len(sys.argv) != 4:
        print(__doc__); sys.exit(1)
    docId, tabId, mdPath = sys.argv[1:]
    md = open(mdPath).read()
    blocks = parse_blocks(md)
    client = docs_client()
    clear_tab(client, docId, tabId)
    reqs, n = build_requests(blocks, tabId)
    # Batch in chunks of 1000 requests to stay under API limits
    for i in range(0, len(reqs), 500):
        client.documents().batchUpdate(
            documentId=docId, body={'requests': reqs[i:i+500]}).execute()
    print(f"rendered {n} chars in {len(reqs)} requests to {tabId}")

if __name__ == '__main__':
    main()
