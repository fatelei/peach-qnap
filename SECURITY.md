# Security policy

This project is an experimental NAS package. No release currently has completed
NAS validation. The latest published prerelease is the maintenance target; no
response-time guarantee is offered.

Do not disclose login tokens, database contents, NAS credentials or private media
in public issues. Use GitHub's private vulnerability reporting option if it is
available on this repository. If it is unavailable, open an issue requesting a
private contact channel without publishing vulnerability details or secrets.

The launcher should keep the container unprivileged, mount media read-only and
retain the data volume on uninstall. It must not mount the Docker socket or the
NAS root filesystem inside Peach. Changes to these boundaries need explicit
review and documentation.

For vulnerabilities in Peach itself, follow the upstream policy:
https://github.com/peach-mitao/peach/blob/master/SECURITY.md

## QTS password management

The CGI verifies QTS `qtoken`/`NAS_SID` against fixed loopback QTS authentication endpoints and requires both `authPassed=1` and `isAdmin=1`. It never accepts a user-provided authentication destination, follows redirects, or uses environment proxies. Local HTTPS certificate validation is disabled only for this loopback QTS endpoint, whose certificate commonly does not cover 127.0.0.1.

Password POSTs require a matching Origin and a session-bound HMAC CSRF token. Passwords are sent to the owned Peach container on stdin; command output and credentials are not logged or echoed. A QTS administrator can reset an existing Peach password without knowing it; that is an explicit administrator capability. Existing passwords remain unchanged until the form is submitted. The application is intended for a trusted LAN; use the QTS HTTPS management URL for password changes.
