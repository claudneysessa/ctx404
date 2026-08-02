# Calculator continuity laboratory

This laboratory tested whether CTX404 could preserve useful context across independent Claude Code chats without turning Opus into a file-search worker.

## Scenario

1. Create an empty directory and invoke `/ctx404`.
2. In the same chat, request a scalable terminal calculator using only the Python standard library.
3. End the chat.
4. Start a fresh chat and implement the calculator from repository context.
5. End the chat.
6. Start another fresh chat and request exponentiation without re-explaining the architecture.

## Observed result — 2026-08-02

- The `/ctx404` chat initialized Git, delegated native `/init` and installed the complete context protocol.
- That first process remained open while unrelated globally configured integrations started; the generated repository was already valid.
- A fresh, isolated chat recovered the generated governance, implemented an operation registry, menu-driven CLI and 31 passing tests, then completed context revision 1.
- Another independent chat loaded the indexed context, added exponentiation through one decorated registry function without changing the dispatcher and completed context revision 2.
- Extended validation: 38 tests passed, the context doctor reported no issues or warnings, and a real CLI smoke test produced `8 ^ 2 = 64`.
- The exponentiation work also caught two tests that had used `pow` as an intentionally unknown key; the chat changed that sentinel to `sqrt` instead of allowing misleading tests.

## What this proves

It demonstrates continuity in one controlled Windows laboratory. It does not prove universal compatibility, automatic delegation, guaranteed token reduction or equivalent behavior across every Claude Code release. CTX404 does not manage unrelated global Claude integrations. Automated tests cover deterministic bootstrap and context mechanics separately.

## Reproduce

Use an empty disposable directory. Never run a beta bootstrap against valuable or non-empty work.

```text
/ctx404
```

Then ask Claude to build a terminal calculator with an extensible operation registry and standard-library tests. In a fresh chat, request exponentiation without restating the architecture. Compare `.claude/context/current.json`, `.claude/context/history.jsonl` and the test count after each step.
