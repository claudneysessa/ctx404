# Security policy

## Supported versions

CTX404 is currently a public beta. Security fixes target the latest release and the `main` branch.

## Reporting a vulnerability

Do not open a public issue when a report could expose credentials, private context, unsafe command execution or a path traversal/destructive-file risk. Use GitHub's private vulnerability reporting feature under the repository Security tab.

Include the affected version, platform, reproduction steps, impact and a sanitized proof of concept. Do not include real secrets or private repository contents.

## Context safety

CTX404 context is designed to be versionable. Generated governance instructs agents never to copy passwords, private keys, API tokens or secret values into summaries, topic files or history. Users remain responsible for reviewing repository contents before adding a remote or publishing.
