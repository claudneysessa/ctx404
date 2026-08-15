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

## Record a deliberation

A session that only discussed still produces context. Write it as a topic body with these headings, omitting any that has no content:

```markdown
## Decided
What holds now, in the user's own terms.

## Rejected
Each option considered and turned down, with the reason it was turned down.
This section is the point of the record. A rejected option that is not written
down returns next session as a fresh suggestion, and the user pays for it twice.

## Revoked
A decision that was made and later reversed, what replaced it, and when.
Keep the original decision visible; do not silently overwrite it.

## Constraints
Requirements, preferences, and limits the user revealed while deciding.

## Open
What is still undecided, phrased as the question that needs an answer.
```

Use `--event-type decision` on `complete` so the history distinguishes deliberation from a code change. When a later session reverses one of these, update the same topic instead of opening a new one: append to `Revoked`, then correct `Decided`.

## Review deliberation

Topic bodies are not reachable through `find`, which only reads summaries and keywords. Read them back with `review`:

```text
python .claude/scripts/context_tool.py review --section rejected
python .claude/scripts/context_tool.py review --query "<term>"
python .claude/scripts/context_tool.py review --topic "<topic-id>"
```

Run it before proposing anything that resembles previous work. If the idea is already under `Rejected`, say so and give the recorded reason instead of proposing it again as if it were new. The user is entitled to reconsider a rejected option deliberately; they are not required to remember it unaided, and neither are you.

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
