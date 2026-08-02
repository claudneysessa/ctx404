# Calculator continuity laboratory

This laboratory tested whether CTX404 could preserve useful context across independent Claude Code chats without turning Opus into a file-search worker.

## Scenario

1. Create an empty directory and invoke `/ctx404`.
2. In the same chat, request a scalable terminal calculator using only the Python standard library.
3. End the chat.
4. Start a fresh chat and request exponentiation without re-explaining the architecture.
5. End the chat.
6. Start another fresh chat and ask for a read-only project status and safe next extension.

## Observed result — 2026-08-02

- Initial chat created an operation registry, menu-driven CLI and tests.
- Opus found and corrected two real edge cases: zero being mistaken for quit at operand prompts and non-finite multiplication output.
- Initial validation: 31 tests passed.
- The second chat recovered the architecture, added exponentiation through the registry without editing the dispatcher and recorded context revision 2.
- Extended validation: 39 tests passed.
- The third chat correctly reported purpose, architecture, last change, 39-test count, revision 2 and a safe modulo extension without changing files.

## What this proves

It demonstrates continuity in one controlled Windows laboratory. It does not prove universal compatibility, a guaranteed token reduction or equivalent behavior across every Claude Code release. Automated tests cover deterministic bootstrap and context mechanics separately.

## Reproduce

Use an empty disposable directory. Never run a beta bootstrap against valuable or non-empty work.

```text
/ctx404
```

Then ask Claude to build a terminal calculator with an extensible operation registry and standard-library tests. In fresh chats, request exponentiation and finally a read-only resume. Compare `.claude/context/current.json`, `.claude/context/history.jsonl` and the test count after each step.
