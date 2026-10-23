#!/bin/sh
# MIT. Unofficial QNAP launcher; upstream Peach is AGPL-3.0-or-later.
set -eu
PATH=/bin:/usr/bin:/sbin:/usr/sbin
export PATH
export QNAP_QPKG=PeachQNAP
NAME=peach-qnap
VOLUME=peach-qnap-data
LABEL=io.peach.qnap.owner
QCONF=/etc/config/qpkg.conf
GETCFG=/sbin/getcfg
SETCFG=/sbin/setcfg
ROOT=$($GETCFG PeachQNAP Install_Path -f "$QCONF")
[ -d "$ROOT" ] || { echo 'PeachQNAP install directory not found.' >&2; exit 1; }
CS=$($GETCFG container-station Install_Path -f "$QCONF")
DOCKER="$CS/bin/docker"
[ -x "$DOCKER" ] || { echo 'Container Station Docker CLI not found.' >&2; exit 1; }
CONF="$ROOT/peach-qnap.conf"
IMAGE=$(cat "$ROOT/image.txt")
fail(){ echo "PeachQNAP: $*" >&2; exit 1; }
cfg(){ "$GETCFG" PeachQNAP "$1" -d "$2" -f "$CONF"; }
exists(){ "$DOCKER" container inspect "$NAME" >/dev/null 2>&1; }
owned(){
    [ "$("$DOCKER" container inspect --format '{{index .Config.Labels "io.peach.qnap.owner"}}' "$NAME")" = PeachQNAP ] ||
        fail "Container name $NAME is already used by another application; nothing was changed."
}
lock(){
    # flock releases its lock automatically if the service command is killed.
    command -v flock >/dev/null 2>&1 || fail 'flock is required.'
    exec 9>"$ROOT/.service.lock"
    flock -n 9 || fail 'Another PeachQNAP operation is in progress.'
}
check_daemon(){ "$DOCKER" info >/dev/null 2>&1 || fail 'Container Station is not running.'; }
stop_container(){
    if exists; then
        owned
        "$DOCKER" stop --time 75 "$NAME" >/dev/null || fail 'Failed to stop container.'
    fi
}
start_container(){
    [ "$("$GETCFG" PeachQNAP Enable -d FALSE -f "$QCONF")" = TRUE ] || fail 'Enable PeachQNAP in App Center first.'
    [ "$(uname -m)" = x86_64 ] || fail 'This package requires x86_64.'
    media=$(cfg MediaPath '')
    bind=$(cfg BindAddress 0.0.0.0)
    port=$(cfg Port 8900)
    case "$port" in ''|*[!0-9]*) fail 'Port must be an integer.';; esac
    [ "$port" -ge 1024 ] && [ "$port" -le 65535 ] || fail 'Port must be 1024..65535.'
    case "$bind" in ''|*[!0-9.]*) fail 'BindAddress must be an IPv4 address.';; esac
    if [ -n "$media" ]; then
        case "$media" in /share/?*) ;; *) fail 'MediaPath must be an existing directory beneath /share/.';; esac
        case "$media" in *,*|*'
'*) fail 'MediaPath cannot contain commas or newlines.';; esac
        [ -d "$media" ] || fail "Media directory is unavailable: $media"
    fi
    if exists; then owned; fi
    # Never pull updates on every start. image.txt pins the package image.
    "$DOCKER" image inspect "$IMAGE" >/dev/null 2>&1 || "$DOCKER" pull "$IMAGE" || fail 'Image download failed. Check Docker Hub connectivity.'
    if "$DOCKER" volume inspect "$VOLUME" >/dev/null 2>&1; then
        [ "$("$DOCKER" volume inspect --format '{{index .Labels "io.peach.qnap.owner"}}' "$VOLUME")" = PeachQNAP ] || fail 'Data volume name is used by another application.'
    else
        "$DOCKER" volume create --label "$LABEL=PeachQNAP" "$VOLUME" >/dev/null
    fi
    if exists; then
        stop_container
        "$DOCKER" container rm "$NAME" >/dev/null
    fi
    set -- run -d --name "$NAME" --label "$LABEL=PeachQNAP" --init \
        --restart unless-stopped --stop-timeout 75 \
        --log-driver json-file --log-opt max-size=10m --log-opt max-file=3 \
        -p "$bind:$port:8900" --mount "type=volume,source=$VOLUME,target=/data"
    if [ -n "$media" ]; then
        set -- "$@" --mount "type=bind,source=$media,target=/media,readonly"
    fi
    "$DOCKER" "$@" "$IMAGE" >/dev/null || fail 'Container creation failed; data volume was retained. Check port conflicts and Docker logs.'
    "$SETCFG" PeachQNAP Web_Port "$port" -f "$QCONF"
    # Wait for the upstream readiness check; do not report success for a crash loop.
    count=0
    while [ "$count" -lt 60 ]; do
        state=$("$DOCKER" container inspect --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' "$NAME")
        case "$state" in
            'running healthy') echo "PeachQNAP ready on port $port"; return 0;;
            *unhealthy*|exited*|dead*) fail 'Peach failed its health check. Use Container Station logs for peach-qnap.';;
        esac
        count=$((count + 1))
        sleep 3
    done
    fail 'Peach readiness timed out. Data was retained; inspect container logs.'
}

case "${1:-}" in
    start) lock; check_daemon; start_container;;
    stop) lock; check_daemon; stop_container;;
    restart) lock; check_daemon; start_container;;
    remove)
        lock; check_daemon
        if exists; then owned; stop_container; "$DOCKER" container rm "$NAME" >/dev/null; fi
        echo "Kept Docker data volume $VOLUME."
        ;;
    status) check_daemon; exists && owned && "$DOCKER" container inspect --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' "$NAME";;
    token) check_daemon; owned; "$DOCKER" exec "$NAME" peach token;;
    *) echo "Usage: $0 {start|stop|restart|remove|status|token}" >&2; exit 2;;
esac
