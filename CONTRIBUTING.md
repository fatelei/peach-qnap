# Contributing

Please open an issue describing the problem or intended behavior before a large
change. Small documentation fixes and narrowly scoped bug fixes may go directly
to a pull request.

## Local checks

Use Python 3 and ShellCheck, then run `make test` and `make lint`. Build with
QNAP QDK 2.5.3 on Linux/QNAP as described in `BUILD.md`. The launcher must remain
compatible with QNAP's `/bin/sh`; do not introduce Bash-only runtime syntax.

Keep data preservation, ownership labels and failure paths covered by tests.
Never delete the user's data volume as part of routine upgrades or uninstall.
Do not commit NAS databases, login tokens, private media or unredacted logs.

## Pull requests

Describe the concrete behavior change, tests performed and any untested NAS
behavior. For real-device reports include model, CPU architecture, QTS version,
Container Station version and sanitized error messages. Clearly distinguish
mock tests, container tests and NAS tests.

## Licensing

Contributions use the license applicable to the file/component being changed.
New repository scaffolding uses Apache-2.0; original launcher files retain MIT;
QDK-derived changes retain QDK's GPL terms. See `THIRD_PARTY_NOTICES.md`.
Preserve copyright notices and document the origin of copied third-party code.
