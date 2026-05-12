#!/usr/bin/env -S /tmp/gd-venv/bin/python
"""Tiny CLI for Google Docs tab operations using the service account at
/Users/shayanys/.config/google-docs-mcp/sa.json. Bypasses the buggy
@a-bonus/google-docs-mcp field-mask handling by calling the Docs API directly.

Usage:
  gdocs.py tabs <docId>                                # list tab tree (title + tabId)
  gdocs.py find-tab <docId> <title>                    # print tabId of tab with that title
  gdocs.py add-tab <docId> <title> [parentTabId]       # create tab; titles must be globally unique
  gdocs.py write <docId> <tabId> <text>                # insert plain text at start of tab
  gdocs.py append <docId> <tabId> <text>               # append plain text to end of tab
  gdocs.py read <docId> <tabId>                        # print tab body as plain text

docId is the long string between /d/ and /edit in a Google Docs URL.

Env: SA_PATH overrides the service-account path.
"""
import json, os, sys

SA = os.environ.get('SA_PATH', '/Users/shayanys/.config/google-docs-mcp/sa.json')

from google.oauth2 import service_account
from googleapiclient.discovery import build

def docs_client():
    creds = service_account.Credentials.from_service_account_file(
        SA, scopes=['https://www.googleapis.com/auth/documents'])
    return build('docs', 'v1', credentials=creds)

def get_doc_with_tabs(docId):
    # Critical: do NOT pass `fields=` when includeTabsContent=True.
    # Any field mask selecting from `tabs` triggers
    # "Field mask cannot retrieve comment-specific fields when include_comments is false."
    return docs_client().documents().get(
        documentId=docId, includeTabsContent=True).execute()

def walk_tabs(tabs, depth=0):
    for t in tabs:
        p = t.get('tabProperties', {})
        yield depth, p.get('title'), p.get('tabId'), p.get('parentTabId')
        yield from walk_tabs(t.get('childTabs', []), depth + 1)

def find_tab_obj(tabs, title):
    for t in tabs:
        if t.get('tabProperties', {}).get('title') == title:
            return t
        sub = find_tab_obj(t.get('childTabs', []), title)
        if sub:
            return sub
    return None

def tab_text(tab):
    out = []
    for el in tab.get('documentTab', {}).get('body', {}).get('content', []):
        para = el.get('paragraph')
        if para:
            for run in para.get('elements', []):
                tr = run.get('textRun')
                if tr:
                    out.append(tr.get('content', ''))
    return ''.join(out)

def cmd_tabs(docId):
    doc = get_doc_with_tabs(docId)
    for depth, title, tid, parent in walk_tabs(doc.get('tabs', [])):
        print(f"{'  '*depth}{title}\t{tid}\tparent={parent or '-'}")

def cmd_find_tab(docId, title):
    doc = get_doc_with_tabs(docId)
    tab = find_tab_obj(doc.get('tabs', []), title)
    if not tab:
        print(f"NOT FOUND: {title}", file=sys.stderr); sys.exit(1)
    print(tab['tabProperties']['tabId'])

def cmd_add_tab(docId, title, parent=None):
    props = {'title': title}
    if parent:
        props['parentTabId'] = parent
    res = docs_client().documents().batchUpdate(
        documentId=docId,
        body={'requests': [{'addDocumentTab': {'tabProperties': props}}]}).execute()
    new = res['replies'][0]['addDocumentTab']['tabProperties']
    print(json.dumps(new, indent=2))

def cmd_write(docId, tabId, text):
    docs_client().documents().batchUpdate(
        documentId=docId,
        body={'requests': [{'insertText': {
            'location': {'index': 1, 'tabId': tabId}, 'text': text}}]}).execute()
    print(f"wrote {len(text)} chars to {tabId}")

def cmd_append(docId, tabId, text):
    doc = get_doc_with_tabs(docId)
    # Find the tab and locate end index
    tab = None
    for t in walk_all(doc.get('tabs', [])):
        if t.get('tabProperties', {}).get('tabId') == tabId:
            tab = t; break
    if not tab:
        print(f"tab not found: {tabId}", file=sys.stderr); sys.exit(1)
    body = tab['documentTab']['body']['content']
    end = body[-1]['endIndex'] - 1  # last index minus newline
    docs_client().documents().batchUpdate(
        documentId=docId,
        body={'requests': [{'insertText': {
            'location': {'index': end, 'tabId': tabId}, 'text': text}}]}).execute()
    print(f"appended {len(text)} chars to {tabId}")

def walk_all(tabs):
    for t in tabs:
        yield t
        yield from walk_all(t.get('childTabs', []))

def cmd_read(docId, tabId):
    doc = get_doc_with_tabs(docId)
    for t in walk_all(doc.get('tabs', [])):
        if t.get('tabProperties', {}).get('tabId') == tabId:
            sys.stdout.write(tab_text(t))
            return
    print(f"tab not found: {tabId}", file=sys.stderr); sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    cmd, *args = sys.argv[1:]
    table = {
        'tabs': cmd_tabs, 'find-tab': cmd_find_tab,
        'add-tab': cmd_add_tab, 'write': cmd_write, 'append': cmd_append,
        'read': cmd_read,
    }
    if cmd not in table:
        print(__doc__); sys.exit(1)
    table[cmd](*args)

if __name__ == '__main__':
    main()
