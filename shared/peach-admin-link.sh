#!/bin/sh
# MIT. QTS recreates its CGI directory at boot; restore only our own link.
set -eu
PATH=/bin:/usr/bin:/sbin:/usr/sbin
export PATH
GETCFG=/sbin/getcfg
SETCFG=/sbin/setcfg
ROOT=$($GETCFG PeachQNAP Install_Path -f /etc/config/qpkg.conf)
LINK=/home/httpd/cgi-bin/peach-qnap.cgi
TARGET="$ROOT/peach-admin.cgi"
[ -d "$ROOT" ] || exit 1
case "${1:-}" in
    install)
        [ -x "$TARGET" ] || { echo 'Peach admin CGI is missing.' >&2; exit 1; }
        if [ -e "$LINK" ] || [ -L "$LINK" ]; then
            if [ ! -L "$LINK" ] || [ "$(readlink "$LINK")" != "$TARGET" ]; then
                echo 'Peach admin CGI path is occupied; not overwriting it.' >&2
                exit 1
            fi
        else
            ln -s "$TARGET" "$LINK"
        fi
        port=$($GETCFG System 'Web Access Port' -d 8080 -f /etc/config/uLinux.conf)
        ssl=$($GETCFG System 'SSL Port' -d 443 -f /etc/config/uLinux.conf)
        "$SETCFG" PeachQNAP WebUI /cgi-bin/peach-qnap.cgi -f /etc/config/qpkg.conf
        "$SETCFG" PeachQNAP Web_Port "$port" -f /etc/config/qpkg.conf
        "$SETCFG" PeachQNAP Web_SSL_Port "$ssl" -f /etc/config/qpkg.conf
        ;;
    remove)
        if [ -L "$LINK" ] && [ "$(readlink "$LINK")" = "$TARGET" ]; then rm "$LINK"; fi
        ;;
    *) exit 2;;
esac
