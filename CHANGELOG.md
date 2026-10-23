# Changelog

## 1.1.1 — 2026-10-23 (prerelease)

- Do not abort installation if the optional QTS admin page cannot register.
- Preserve a direct Peach App Center entry when registration fails and record
  the detailed error in an owner-only admin-page.log.
- Read the QTS HTTPS management port from Stunnel/Port.
- Resolve the delivered script directory directly and tolerate QTS getcfg
  returning nonzero for defaulted/missing port settings.
- Exact cause of the reported NAS registration failure still requires its log.

## 1.1.0 — 2026-10-23 (prerelease)

- Add a QTS administrator-authenticated page to set/reset Peach passwords without SSH.
- Point App Center at that page; preserve direct Peach access on port 8900.
- Add upstream Peach icons in QDK standard sizes, including disabled-state artwork.
- Check session authorization, CSRF, container ownership, and password handling.
- Add a real upstream-container password setup/reset check to release builds.
- NAS integration of this new CGI entry point still needs on-device confirmation.

## 1.0.2 — 2026-10-23 (prerelease)

- Download the pinned Peach image through docker.1ms.run for mainland China
  connectivity; preserve the upstream SHA256 digest and application version.
- Include the requested image reference in registry download errors.

## Earlier packaging changes

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
