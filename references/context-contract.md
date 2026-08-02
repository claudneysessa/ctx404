# CTX404 context contract

The installed repository separates five responsibilities:

- `CLAUDE.md`: permanent operating protocol.
- `.claude/context/index.json`: compact map of available context.
- `.claude/context/current.json`: current state and next step.
- `.claude/context/topics/`: details loaded only when relevant.
- `.claude/context/history.jsonl`: append-only history, queried only when history is needed.
- `.claude/context/index.json` → `governance`: authority mode and pointers to pre-existing owner sources.

Maintain these invariants:

- JSON files remain valid UTF-8.
- Topic identifiers are unique and stable.
- Indexed paths are relative to the repository root and exist.
- Current state contains no historical narrative.
- The index contains summaries and pointers, not full documents.
- Important durable information does not exist only in chat history.
- In `index` mode, update facts in their owning authority and keep CTX404 as a compact pointer; do not duplicate full living documents.
- In `exclusive` mode, migration or retirement of a previous system remains separate explicit work.
- Secrets may be referenced by path but their values never enter context summaries.

Global skill updates never overlay planted project files. Use the explicit reviewed upgrade workflow for supported version-to-version migrations.

Topic Markdown files use the flat frontmatter contract stored at `.claude/context/templates/topic.md`. Run `context_tool.py sync` after topic changes and `context_tool.py doctor` before considering relevant context maintenance complete.
