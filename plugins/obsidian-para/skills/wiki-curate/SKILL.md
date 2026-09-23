---
name: wiki-curate
description: "Author content in an Obsidian PARA vault: research a topic into the wiki, brainstorm an idea into a seed note, beautify or clean up an existing note, or open a finished note in Obsidian. Use when the user says research X for the wiki, write up, brainstorm, capture this idea, clean up this note, tidy, beautify, or improve a note."
argument-hint: "[research <topic> | brainstorm <idea> | beautify <note>]"
---

# Wiki Curate — Research, Brainstorm, Beautify

Create and improve notes in the vault. `wiki-process` handles inbox intake and `wiki-lint` handles vault health; this skill handles deliberate authoring.

Before writing, read `${user_config.wikiRoot}/AGENTS.md` (or `CLAUDE.md` if the vault uses that name). Its frontmatter schema, heading contracts, link rules, and approval boundaries override anything below.

---

## Research

Research produces two different kinds of output, and they go in different places:

- **Neutral survey** — what exists, how it works, the trade-offs, and real source links. It goes in `${user_config.resourcesBase}/` so any future project can reuse it.
- **Opinionated synthesis** — a recommendation for one project or life area. It goes in the relevant folder under `${user_config.projectsBase}/` or `${user_config.areasBase}/` and links to the survey.

Steps:

1. Read the relevant `_index.md` files, starting with `${user_config.resourcesBase}/_index.md`, and check whether a survey already exists. Prefer extending an existing note to creating a duplicate.
2. Research the question. Record a real URL for every claim you took from a source; mark claims you could not verify.
3. Write the neutral survey as `type: research` with the heading contract from the vault schema.
4. For a project-scoped request, write the synthesis note too. A purely exploratory request needs only the survey.
5. Update the `_index.md` of every folder you wrote to. If the topic spans several areas and has 5+ notes, propose a Map of Content in `${user_config.mocBase}/`.

If you delegate research to subagents, a subagent writes only the neutral survey. The lead writes any project synthesis, because synthesis needs the full project context the subagent does not have.

## Brainstorm

1. Check existing notes on the topic so the idea links into what is already there.
2. Create a note with `type: idea` and `status: seed` in the relevant project or area folder.
3. Link it to related notes and update the folder's `_index.md`.

## Beautify a note

When asked to clean up or improve a note:

1. Preserve the author's voice and ideas. Restructure; do not rewrite opinions.
2. Apply the heading contract for the note's `type`.
3. Add missing frontmatter fields and fill `summary` when it is empty.
4. Add a short lead paragraph after the title if it lacks one.
5. Link related notes where they fit naturally in the text.
6. Replace ASCII diagrams with Mermaid when a diagram helps.
7. Keep existing content. Move outdated or off-topic sections under `## Archive` instead of deleting them.

## Opening a note in Obsidian

Usually leave notes closed; the user can read them later. Open one only when the result should be visible now, such as a finished write-up the user asked for or a note that needs review before the conversation moves on. Only the main session opens notes; subagents never do.

```bash
open "obsidian://open?vault=${user_config.obsidianVaultName}&file=<URL-encoded path relative to vault root>"
```

On Linux use `xdg-open` instead of `open`.
