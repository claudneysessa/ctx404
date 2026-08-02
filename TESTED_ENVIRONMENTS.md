# Tested environments

CTX404 makes compatibility claims only where there is evidence.

## Real Claude Code laboratory

| Date | Environment | Coverage | Result |
|---|---|---|---|
| 2026-08-02 | Windows, PowerShell, Python 3.14.6, Git, Claude Code 2.1.220 with Opus | Public install, `/ctx404` bootstrap, independent-chat implementation and independent-chat extension | Passed; 38 tests, clean context doctor and revision 2 |

The detailed, sanitized evidence is in [`examples/calculator-lab/README.md`](examples/calculator-lab/README.md).

## Automated CI

GitHub Actions runs the deterministic Python test suite on current `windows-latest`, `ubuntu-latest` and `macos-latest` hosted runners with Python 3.11 and 3.14 where available in the matrix.

CI validates deterministic components; it does not claim that a hosted runner executed paid Claude model calls. Community reports are welcome for additional Claude Code versions, shells and operating systems.

The first laboratory session initialized the repository successfully but remained open while unrelated globally configured integrations started. Repeating the implementation and continuation chats with an empty MCP configuration isolated CTX404 and completed normally. This is an environment caveat, not evidence that CTX404 controls or disables a user's global integrations.
