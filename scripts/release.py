#!/usr/bin/env python3
"""Validate release versions and the contents of a QDK-built package."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import tarfile
import sys


def validate_tag(tag):
    if not re.fullmatch(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", tag):
        raise ValueError("Use a version tag such as v0.1.1 (numeric major.minor.patch).")
    version = tag[1:]
    if len(version) > 10:
        raise ValueError("QPKG version must fit the 10-character QNAP version field.")
    return version


def prepare_source(tag, root, source_commit, tooling_commit):
    """Set the version only in the disposable source tree that will be shipped."""
    version = validate_tag(tag)
    config = root / "qpkg.cfg"
    updated, count = re.subn(r'^QPKG_VER="[^"]+"$', f'QPKG_VER="{version}"', config.read_text(), flags=re.M)
    if count != 1:
        raise ValueError("qpkg.cfg must contain exactly one quoted QPKG_VER field.")
    for commit in (source_commit, tooling_commit):
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise ValueError("Source and build-tool commits must be full Git SHA-1 values.")
    config.write_text(updated)
    (root / "RELEASE_BUILD.json").write_text(json.dumps({
        "tag": tag, "version": version, "source_commit": source_commit,
        "tooling_commit": tooling_commit,
        "generated_change": "qpkg.cfg QPKG_VER is set from the release tag",
    }, indent=2) + "\n")
    return version


def verify_package(package, root):
    data = package.read_bytes()
    if data[-10:] != b"QNAPQPKG  ":
        raise ValueError("Missing QNAP package footer.")
    checksum = str(len(data) * 3589 + 1000000000)[:10].encode()
    if data[-60:-50] != checksum:
        raise ValueError("Invalid QNAP package footer checksum.")
    header = data[:8192].decode(errors="replace")
    script = re.search(r"script_len=(\d+)", header)
    control = re.search(r"\$script_len \+ (\d+)", header)
    if not script or not control:
        raise ValueError("Unrecognized QDK archive offsets.")
    start, length = int(script[1]), int(control[1])
    with tarfile.open(fileobj=io.BytesIO(data[start:start + length]), mode="r:") as outer:
        with tarfile.open(fileobj=io.BytesIO(outer.extractfile(outer.getmembers()[0]).read()), mode="r:gz") as archive:
            for name in ("qpkg.cfg", "package_routines"):
                if archive.extractfile("./" + name).read() != (root / name).read_bytes():
                    raise ValueError(f"Control archive does not match source: {name}")
    with tarfile.open(fileobj=io.BytesIO(data[start + length:]), mode="r:gz") as archive:
        expected = {"peach-qnap.conf": root / "config/peach-qnap.conf"}
        expected.update({p.name: p for p in (root / "shared").iterdir() if p.is_file()})
        for name, icon in ((".qpkg_icon.gif", "PeachQNAP.png"), (".qpkg_icon_80.gif", "PeachQNAP_80.png"), (".qpkg_icon_gray.gif", "PeachQNAP_gray.png")):
            source = root / "icons" / icon
            if source.is_file():
                expected[name] = source
        for name, source in expected.items():
            if archive.extractfile("./" + name).read() != source.read_bytes():
                raise ValueError(f"Payload does not match source: {name}")
        for name in ("peach-qnap.sh", "peach-admin.cgi", "peach-admin-link.sh"):
            if (root / "shared" / name).is_file() and not archive.getmember("./" + name).mode & 0o111:
                raise ValueError(f"Program is not executable: {name}")


def write_checksums(directory):
    files = sorted([*directory.glob("*.qpkg"), *directory.glob("*-source.tar.gz")])
    if len(files) != 2:
        raise ValueError("Expected exactly one QPKG and one source archive.")
    (directory / "SHA256SUMS.txt").write_text("".join(
        f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in files
    ))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["validate", "prepare", "verify", "checksums"])
    parser.add_argument("value")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--source-commit", default="")
    parser.add_argument("--tooling-commit", default="")
    args = parser.parse_args()
    try:
        if args.operation == "validate":
            print(validate_tag(args.value))
        elif args.operation == "prepare":
            print(prepare_source(args.value, args.root, args.source_commit, args.tooling_commit))
        elif args.operation == "verify":
            verify_package(Path(args.value), args.root)
            print("QPKG footer and payload verified against source.")
        else:
            write_checksums(Path(args.value))
    except (ValueError, OSError, tarfile.TarError) as error:
        message = str(error)
        if os.environ.get("GITHUB_ACTIONS") == "true":
            escaped = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
            print(f"::error title=Release validation::{escaped}", file=sys.stderr)
        else:
            print(f"Release validation failed: {message}", file=sys.stderr)
        sys.exit(1)
