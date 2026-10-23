# Licensing and third-party sources

This repository contains components with different licenses. The root Apache-2.0
license was present in the repository's initial commit and is retained for new
repository documentation and build/CI scaffolding. It does not override the
component-specific licenses below.

## Original packaging code — MIT

The original 0.1.0 packaging delivery retains its MIT license in
`LICENSES/MIT.txt` and `shared/LICENSE.packaging`. This scope covers:

- `shared/peach-qnap.sh`, `shared/image.txt`
- `config/peach-qnap.conf`, `qpkg.cfg`, `package_routines`
- `tests/test_launcher.py`

The QPKG `QPKG_LICENSE=MIT` field describes this launcher, not all contents of the
installer framework or the downloaded application. No change to the previously
released runtime payload is made by this repository organization.

## QNAP QDK — GPL

- Source: https://github.com/qnap-dev/QDK
- Version: 2.5.3
- Commit: `b7b5f4c86ebe95b10a62d64725515e7cdcf4bb35`
- Original source: `vendor/QDK-source.tar.gz` (Git administrative data omitted)
- License text: `LICENSES/GPL-2.0.txt`, also `shared/LICENSE.QDK`

QDK's `qbuild` and `qinstall.sh` carry GPL-2.0-or-later notices. Retain the
upstream notices and file-specific terms throughout the supplied QDK source;
the GPL license text alone does not change those notices.

The QPKG contains QDK's installer framework. Source is included alongside the
packaging source so recipients can inspect and rebuild it. The macOS build-host
changes are recorded in `qbuild-macos.patch`; that derivative patch is covered
by the QDK license, not the root Apache license. The patch is historical build
provenance, not a general-purpose macOS port of QDK.

## Peach — AGPL-3.0-or-later

- Project: https://github.com/peach-mitao/peach
- Version: 0.46.1
- Version source: https://github.com/peach-mitao/peach/tree/v0.46.1
- License: https://github.com/peach-mitao/peach/blob/master/LICENSE
- Image: `longmeidao/peach:0.46.1`
- Manifest digest: `sha256:8b949a03460a41952a3c7e5c8394145dd04a063d2759de4243c0487337fbfe16`

The QPKG does not bundle Peach's executable code or container layers; the NAS
pulls the upstream image on first start. This packaging does not modify Peach.
If distributing modified Peach code or redistributing its image, preserve its
license and corresponding-source provisions as well as third-party notices.

QNAP and Peach names identify compatibility and upstream sources. No official
endorsement or affiliation is implied.
