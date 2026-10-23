# Build and verification

This is an unofficial QNAP container launcher, not a fork of Peach itself.
It downloads the upstream 0.46.1 image by immutable digest on first start.

## Linux / QNAP build

Install QNAP QDK 2.5.3 and its dependencies using the upstream instructions.
The original QDK source for commit b7b5f4c86ebe95b10a62d64725515e7cdcf4bb35
is included in `vendor/QDK-source.tar.gz`, including the GPL license and
the source of the installer framework contained in the QPKG.

From this source directory:

```sh
chmod 755 shared/peach-qnap.sh
qbuild --root "$PWD" --build-arch x86_64 --build-dir "$PWD/build" --gzip
python3 tests/test_launcher.py
shellcheck -s sh shared/peach-qnap.sh
```

## Build used for this delivery

Docker Desktop stalled when starting isolated build containers, so the
delivered package was produced by QDK on macOS. `qbuild-macos.patch` contains
the exact build-host portability changes: available host executable paths
and BSD sed's explicit empty backup suffix. QDK's generated installer header
and `qinstall.sh` were not modified. `qpkg_encrypt` was compiled from QDK's
original `src/qpkg_encrypt.c` with the host C compiler.

To reproduce that host setup, extract the vendor archive, copy its `shared/`
directory as the QDK runtime, apply the patch to `bin/qbuild`, and write the
following runtime `qdk.conf` using its absolute location:

```sh
QDK_VERSION=2.5.3
QDK_PATH="/absolute/path/to/runtime"
```

Compile `src/qpkg_encrypt.c` into the runtime's `bin/qpkg_encrypt`, add that
`bin/` directory to PATH, export QDK_PATH, and use the qbuild command above
with `COPYFILE_DISABLE=1`. A Linux build does not need the portability patch.

The package was independently parsed with Python's tarfile module to verify
control/payload archives, exact shipped-source equality, executable file
mode and the QNAP footer checksum. This is not NAS installation validation.

## Runtime design

- Container Station >= 3.1.2, QTS >= 5.2.0, x86_64 only.
- INI configuration read by QNAP getcfg, never sourced as shell code.
- No privileged container, Docker socket mount or NAS root mount.
- Empty MediaPath means no media bind mount; configured media is read-only.
- Owned container and volume labels are checked before changes.
- Cached pinned image reused; download failure leaves an existing container alone.
- App data remains in peach-qnap-data on uninstall. No volume deletion code.
- Initial credential is available through `peach token`; not copied to logs.
- Native service locking requires `flock`; actual availability on the target
  firmware must be verified. Failure is explicit rather than running unlocked.

The 12 tests use fake QNAP and Docker commands. They validate launcher control
flow, not QTS integration, Docker runtime behavior, hardware transcoding or
media playback. See the accompanying Chinese installation and validation notes.

The management CGI requires Go >= 1.23. `make admin` cross-compiles a static Linux amd64 binary (CGO disabled). Release archives include its complete source, embedded Python adapter, and the compiled binary.
