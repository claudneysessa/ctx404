# Calculator laboratories

These laboratories test both CTX404 installation modes with real, independent Claude Code chats.

## Lab A — calculator born under CTX404

1. Create a new directory and invoke `/ctx404`.
2. CTX404 initializes Git and installs governance directly; it does not invoke `/init` or generate a recap.
3. Start a fresh chat and request a scalable terminal calculator using only the Python standard library.

### Observed result — 2026-08-02

- Public installation completed in `new` mode without native `/init`.
- A fresh Opus chat built a registry-driven menu calculator with 11 operations and 60 passing standard-library tests.
- The real CLI opened correctly and exited cleanly.
- Durable context completed at revision 1 and the context doctor reported no issues or warnings.

## Lab B — CTX404 adopts a finished calculator

1. Start with the finished 60-test calculator, an existing Git history, README, `CLAUDE.md`, and custom Claude settings.
2. Invoke `/ctx404` without explaining the project.
3. Verify preservation, then start a fresh chat and request an `average` operation without restating the architecture.

### Observed result — 2026-08-02

- CTX404 detected `adopt`, performed no retrospective analysis, and explicitly reported that `/init` and recap were not run.
- Calculator source, tests and README were unchanged by installation; all 60 tests still passed.
- Existing `CLAUDE.md` guidance and unrelated settings survived the governance merge.
- A fresh Opus chat found the registry extension point, added `average` without changing the CLI or dispatcher, and added two focused tests.
- All 62 tests passed; context completed at revision 1 with a clean doctor.

## What this proves

They demonstrate bootstrap and non-destructive adoption in two controlled Windows laboratories. They do not prove universal compatibility, automatic delegation, guaranteed token reduction or equivalent behavior across every Claude Code release. CTX404 does not manage unrelated global Claude integrations. Automated tests cover deterministic bootstrap and context mechanics separately.

## Reproduce

Use disposable repositories while evaluating a public beta. Commit or back up valuable existing work first.

```text
/ctx404
```

For the birth lab, ask a fresh chat to build a terminal calculator with an extensible operation registry and standard-library tests. For adoption, invoke `/ctx404` in a completed disposable project, verify its diff, then request one small feature in a fresh chat. Compare `.claude/context/current.json`, `.claude/context/history.jsonl`, the project diff and tests after each step.
