# Tested environments

CTX404 makes compatibility claims only where there is evidence.

## Real Claude Code laboratory

| Date | Environment | Coverage | Result |
|---|---|---|---|
| 2026-08-02 | Windows, PowerShell, Python 3.14.6, Git, Claude Code with Opus 5 / Haiku 4.5 | Install, `/ctx404`, calculator implementation, second-chat extension, third-chat resume | Passed; 39 tests and context revision 2 |

The detailed, sanitized evidence is in [`examples/calculator-lab/README.md`](examples/calculator-lab/README.md).

## Automated CI

GitHub Actions runs the deterministic Python test suite on current `windows-latest`, `ubuntu-latest` and `macos-latest` hosted runners with Python 3.11 and 3.14 where available in the matrix.

CI validates deterministic components; it does not claim that a hosted runner executed paid Claude model calls. Community reports are welcome for additional Claude Code versions, shells and operating systems.
