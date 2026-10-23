# Release procedure

1. Run `make test` and `make lint` and inspect the complete diff.
2. Verify the upstream image/tag and pin its manifest digest in `shared/image.txt`.
3. Update `qpkg.cfg`, `CHANGELOG.md` and the compatibility/validation notes.
4. Build using QDK 2.5.3. Keep artifacts out of the Git tree (`dist/` is ignored).
5. Verify the QPKG payload and footer, then record SHA-256 checksums. Test install,
   stop/start, reboot, upgrade, media permissions and uninstall on the target NAS.
6. For any uncompleted device checks, publish only as a prerelease and state the
   exact limitations. Do not imply QNAP certification or a digital signature.
7. Publish a tag, QPKG, checksum file and matching source archive together. The
   source archive must include `vendor/QDK-source.tar.gz`, the host-build patch,
   packaging files and applicable licenses. `git archive` includes tracked vendor
   source, while excluding private local data and ignored build outputs.

Version 0.1.0 retains the already-built test QPKG and its matching original source
archive. The reorganized repository changes documentation and layout, not the
installer payload. See `BUILD.md` for the historical build-host adaptations.
