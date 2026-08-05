---
paths:
  - ".claude/context/**"
---

# CTX404 context-writing procedure

<!--
Managed by CTX404. A reviewed upgrade replaces this file entirely; do not edit it.
Claude Code loads this rule on its own when .claude/context/ is touched, so it stays out of
the always-loaded core in .claude/ctx404-instructions.md.
-->

## Complete relevant work

1. Opus decides the durable summary, next step, status, affected topics, and references.
2. Write each affected topic through the helper, never with a file-editing tool. Claude decides the body; the helper builds the frontmatter, owns revision and timestamps, and syncs the index:

   ```text
   python .claude/scripts/context_tool.py topic-write --id "<topic-id>" --summary "<one line>" --keyword "<keyword>" --keyword "<keyword>" --body-file -
   ```

   The body is read from stdin. Pass an existing `--id` to update that topic; provenance is preserved.
3. Run the deterministic completion command once. It synchronizes topics, assigns the real timestamp, appends history, increments current revision, updates current last, and runs doctor:

   ```text
   python .claude/scripts/context_tool.py complete --summary "<completed result>" --next-step "<next action or no pending work>" --status active --topic "<topic-id>" --ref "<relative-path>"
   ```

4. Include repeated `--topic` and `--ref` arguments only when relevant. Use `--event-type` for a more specific history type when useful.
5. Do not manually write timestamps, increment revisions, append history, or edit `current.json` for ordinary completion.
6. Do not consider relevant work complete unless `complete` returns `ok: true` and doctor has no issues.

## Topic format

`topic-write` builds the frontmatter, so do not hand-write it. Supply a body in Markdown, a summary under 200 characters, and up to 10 keywords. Topic ids use lowercase letters, digits and hyphens. `.claude/context/templates/topic.md` documents the resulting shape for reading, not for copying by hand.

## Context boundaries

- `.claude/context/index.json` is a compact map, not an encyclopedia.
- `.claude/context/current.json` represents the present, not history.
- `.claude/context/history.jsonl` is append-only operational history and is not loaded by default.
- `.claude/context/topics/` contains details loaded on demand.
- `.claude/context/project-definition.md` is project-owned identity and scope. CTX404 never rewrites it.
- `README.md` contains consolidated project documentation.
- Use relative paths, stable topic IDs, short summaries, and explicit keywords.
- Never copy secret values into context, summaries, history entries, or chat. Reference only their safe relative location when needed.
- Never invent missing context. If repair is needed, preserve evidence and correct only what can be verified.
