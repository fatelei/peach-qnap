# Changelog

## 0.1.0 — 2026-10-23 (prerelease)

- Initial x86-64 QPKG launcher for Container Station.
- Pin Peach 0.46.1 by image digest; preserve application data in a named volume.
- Optional read-only media mount, App Center service commands and health checks.
- Protect containers and volumes not owned by this package.
- Include packaging source, QDK corresponding source and component licenses.
- Add 12 mock tests, ShellCheck checks and repository CI.

Not yet validated: NAS installation, boot integration, real media playback and
hardware transcoding. Docker startup validation was not completed on the build
host. See `docs/validation.zh-CN.md`.
