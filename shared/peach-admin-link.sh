#!/bin/sh
# MIT. QTS recreates its CGI directory at boot; restore only our own link.
set -eu
PATH=/bin:/usr/bin:/sbin:/usr/sbin
export PATH
GETCFG=/sbin/getcfg
SETCFG=/sbin/setcfg
# During installation, use the delivered script location rather than a possibly
# stale package registration. All callers invoke this script by its full path.
ROOT=$(CDPATH='' cd "${0%/*}" && pwd)
LINK=/home/httpd/cgi-bin/peach-qnap.cgi
TARGET="$ROOT/peach-admin.cgi"
read_port(){
    # Some QTS getcfg versions print -d but still return nonzero for absent keys.
    value=$("$GETCFG" "$1" "$2" -d "$3" -f "$4" 2>/dev/null || :)
    case "$value" in ''|*[!0-9]*) value=$3;; esac
    if [ "$value" -lt 1 ] || [ "$value" -gt 65535 ]; then value=$3; fi
    printf '%s\n' "$value"
}
case "${1:-}" in
    register)
        # Do not expose credentials; these operations handle paths and ports only.
        if (umask 077; "$0" install > "$ROOT/admin-page.log" 2>&1); then
            exit 0
        fi
        "$0" fallback >> "$ROOT/admin-page.log" 2>&1 || :
        echo "Peach admin registration failed; see $ROOT/admin-page.log. Direct Peach access remains available." >&2
        exit 1
        ;;
    fallback)
        port=$(read_port PeachQNAP Port 8900 "$ROOT/peach-qnap.conf")
        "$SETCFG" PeachQNAP WebUI / -f /etc/config/qpkg.conf
        "$SETCFG" PeachQNAP Web_Port "$port" -f /etc/config/qpkg.conf
        "$SETCFG" PeachQNAP Web_SSL_Port '' -f /etc/config/qpkg.conf
        ;;
    install)
        [ -x "$TARGET" ] || { echo "Peach admin CGI is missing or not executable: $TARGET" >&2; exit 1; }
        [ -d "${LINK%/*}" ] || { echo "QTS CGI directory does not exist: ${LINK%/*}" >&2; exit 1; }
        if [ -e "$LINK" ] || [ -L "$LINK" ]; then
            if [ ! -L "$LINK" ] || [ "$(readlink "$LINK")" != "$TARGET" ]; then
                echo "Peach admin CGI path is occupied: $LINK; not overwriting it." >&2
                exit 1
            fi
        else
            ln -s "$TARGET" "$LINK"
        fi
        port=$(read_port System 'Web Access Port' 8080 /etc/config/uLinux.conf)
        ssl=$(read_port Stunnel Port 443 /etc/config/uLinux.conf)
        "$SETCFG" PeachQNAP WebUI /cgi-bin/peach-qnap.cgi -f /etc/config/qpkg.conf
        "$SETCFG" PeachQNAP Web_Port "$port" -f /etc/config/qpkg.conf
        "$SETCFG" PeachQNAP Web_SSL_Port "$ssl" -f /etc/config/qpkg.conf
        ;;
    remove)
        if [ -L "$LINK" ] && [ "$(readlink "$LINK")" = "$TARGET" ]; then rm "$LINK"; fi
        ;;
    *) exit 2;;
esac
