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
