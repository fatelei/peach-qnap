#!/usr/bin/env bash
set -euo pipefail
root=$(git rev-parse --show-toplevel)
cd "$root"
tag=${1:?Usage: scripts/build-release.sh vX.Y.Z}
version=$(python3 scripts/release.py validate "$tag")
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo 'Commit tracked changes before building a release.' >&2
    exit 1
fi
out="$root/dist/$tag"
if [ -e "$out" ]; then
    echo "Output directory already exists: $out. Choose an empty output location by removing only this generated directory first." >&2
    exit 1
fi
temp=$(mktemp -d)
trap 'rm -rf "$temp"' EXIT
mkdir -p "$temp/source" "$out"
# Build only the committed tree, so the attached source matches the package.
git archive HEAD | tar -xf - -C "$temp/source"
source_root="$temp/source"
printf '%s  %s\n' \
    730a594eacff637039947465217a7438498eddf23984898d0b998698b2a91532 \
    "$source_root/vendor/QDK-source.tar.gz" | sha256sum --check
tar -xzf "$source_root/vendor/QDK-source.tar.gz" -C "$temp"
runtime="$temp/QDK/shared"
cc "$temp/QDK/src/qpkg_encrypt.c" -o "$runtime/bin/qpkg_encrypt"
printf 'QDK_VERSION=2.5.3\nQDK_PATH="%s"\n' "$runtime" > "$runtime/qdk.conf"
export QDK_PATH="$runtime"
export PATH="$runtime/bin:$PATH"
bash "$runtime/bin/qbuild" --root "$source_root" --build-arch x86_64 --build-dir "$out" --gzip
package="$out/PeachQNAP_${version}_x86_64.qpkg"
python3 scripts/release.py verify "$package" --root "$source_root"
git archive --format=tar.gz --prefix="peach-qnap-${version}/" \
    --output="$out/PeachQNAP-${version}-source.tar.gz" HEAD
python3 scripts/release.py checksums "$out"
# QDK's MD5 file embeds temporary paths; publish the portable SHA-256 file instead.
rm -f "$out"/*.md5
cat > "$out/RELEASE_NOTES.md" <<EOF
Peach QNAP ${version}：非官方测试版 QPKG，适用于 x86-64 QNAP、QTS >= 5.2.0 和 Container Station >= 3.1.2。

源码提交：$(git rev-parse HEAD)
固定容器镜像：$(cat shared/image.txt)

在 App Center 手动安装。包未签名，首次启动需要访问 Docker Hub；默认不挂载媒体目录。安装说明见仓库 docs/installation.zh-CN.md。

本次自动运行了测试、ShellCheck、Linux QDK 构建以及 QPKG 包尾和源码一致性校验。
尚未完成 NAS 实机安装、开机启动、真实媒体播放或硬件转码验证。请勿将本版本视为稳定版或 QNAP 官方认证应用。

附件包括 QPKG、匹配的源码归档（含 QDK 对应源码及许可证）和 SHA256SUMS.txt。
EOF
echo "Release files: $out"
