# QTS password management and icons

User-approved scope: remove SSH from the normal password setup/reset flow and add missing App Center icons, preserving the working container deployment.

Use a static Go CGI on the QTS HTTP service. Authenticate existing QTS cookies using a fixed loopback authLogin.cgi endpoint and require administrator privileges. Protect password POSTs with Origin checking and a session-bound CSRF token. Pass new passwords over stdin to the owned container and reuse Peach access.save with its existing file lock. Do not disable authentication or replace the application image. Alternatives (public first-run wizard or fixed default password) do not establish administrator ownership.

Register only the package-owned CGI symlink on install/start, remove only that symlink on uninstall, and retain the existing data volume. Keep direct port 8900 access. Use upstream Peach artwork with its license and original source included.

Validation: Go authorization/form tests, existing launcher and packaging tests, CGI link ownership tests, real pinned-image password integration, static Linux build and QPKG payload/icon verification. QTS cookies/CGI execution and desktop caching require final NAS verification.
