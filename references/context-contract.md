# CTX404 context contract

The installed repository separates five responsibilities:

- `CLAUDE.md`: permanent operating protocol.
- `.claude/context/index.json`: compact map of available context.
- `.claude/context/current.json`: current state and next step.
- `.claude/context/topics/`: details loaded only when relevant.
- `.claude/context/history.jsonl`: append-only history, queried only when history is needed.

Maintain these invariants:

- JSON files remain valid UTF-8.
- Topic identifiers are unique and stable.
- Indexed paths are relative to the repository root and exist.
- Current state contains no historical narrative.
- The index contains summaries and pointers, not full documents.
- Important durable information does not exist only in chat history.
- Secrets may be referenced by path but their values never enter context summaries.

Topic Markdown files use the flat frontmatter contract stored at `.claude/context/templates/topic.md`. Run `context_tool.py sync` after topic changes and `context_tool.py doctor` before considering relevant context maintenance complete.
