# Changelog

## Unreleased

- Replace the unavailable QTS `flock` dependency with an atomic directory lock.
- Release service locks on normal exits and handled signals; retain existing locks
  conservatively until the owner is checked after an unclean shutdown.

- Derive QPKG versions from tags without requiring manual template edits.
- Recover existing tags using current build tools and record exact source provenance.
- Attach missing assets to existing releases without replacing published files.
- Show actionable GitHub error annotations for invalid release inputs.

- Automatically build and publish prerelease packages for matching `vX.Y.Z` tags.
- Add a manual build-only workflow, pinned QDK source verification, matching
  source archives and portable SHA-256 checksums.
- Add release-version and artifact validation tests.

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
