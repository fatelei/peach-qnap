#!/usr/bin/env python3
"""Validate release versions and the contents of a QDK-built package."""
import argparse
import hashlib
import io
from pathlib import Path
import re
import tarfile


def validate_tag(tag, root):
    if not re.fullmatch(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", tag):
        raise ValueError("Use a version tag such as v0.1.1 (numeric major.minor.patch).")
    version = tag[1:]
    if len(version) > 10:
        raise ValueError("QPKG version must fit the 10-character QNAP version field.")
    match = re.search(r'^QPKG_VER="([^"]+)"$', (root / "qpkg.cfg").read_text(), re.M)
    if not match or match[1] != version:
        raise ValueError(f"Update QPKG_VER in qpkg.cfg to {version} before tagging.")
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
        for name, source in expected.items():
            if archive.extractfile("./" + name).read() != source.read_bytes():
                raise ValueError(f"Payload does not match source: {name}")
        if not archive.getmember("./peach-qnap.sh").mode & 0o111:
            raise ValueError("Launcher is not executable.")


def write_checksums(directory):
    files = sorted([*directory.glob("*.qpkg"), *directory.glob("*-source.tar.gz")])
    if len(files) != 2:
        raise ValueError("Expected exactly one QPKG and one source archive.")
    (directory / "SHA256SUMS.txt").write_text("".join(
        f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in files
    ))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["validate", "verify", "checksums"])
    parser.add_argument("value")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    if args.operation == "validate":
        print(validate_tag(args.value, args.root))
    elif args.operation == "verify":
        verify_package(Path(args.value), args.root)
        print("QPKG footer and payload verified against source.")
    else:
        write_checksums(Path(args.value))
