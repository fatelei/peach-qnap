# Vendored source

`QDK-source.tar.gz` is the original source snapshot from:

- Repository: https://github.com/qnap-dev/QDK
- Commit: `b7b5f4c86ebe95b10a62d64725515e7cdcf4bb35`
- QDK version: 2.5.3
- Archive SHA-256: `730a594eacff637039947465217a7438498eddf23984898d0b998698b2a91532`

Only Git administrative data (`.git/`) was omitted. This snapshot preserves the
upstream source, copyright notices and GPL license. Extract it to inspect the
installer and build-tool sources. The separate `qbuild-macos.patch` at repository
root records the build-host modifications used for the original test package.

Keep this corresponding source with release source archives containing the QDK
installer framework; do not replace it with a link-only placeholder.
