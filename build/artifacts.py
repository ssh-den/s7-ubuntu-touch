"""Artifact checksums and atomic output publication."""
from contextlib import contextmanager
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory


BUNDLE_RECEIPT = "s7-build.json"
BOOT = "boot.img"
OVERLAY = "device_herolte.tar.xz"
SYSTEM = "ubuntu.img"
ARTIFACTS = {BOOT, OVERLAY, SYSTEM, "recovery.img"}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def verify(path, digest):
    if sha(path) != digest:
        raise ValueError(f"SHA-256 mismatch: {path}")


def read_receipt(directory, name):
    report = json.loads((directory / name).read_text())
    if not isinstance(report, dict) or not isinstance(report.get("files"), dict):
        raise ValueError(f"Invalid build receipt: {directory / name}")
    if not report["files"] or report["files"].keys() - ARTIFACTS:
        raise ValueError(f"Invalid artifacts: {directory / name}")
    return report


@contextmanager
def locked_output(output):
    output.parent.mkdir(parents=True, exist_ok=True)
    with (output.parent / f".{output.name}.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def check_managed(directory, name, files):
    if directory.is_symlink() or {p.name for p in directory.iterdir()} - (set(files) | {name, "SHA256SUMS"}):
        raise ValueError(f"Unmanaged files in {directory}")


def publish(output, name, identity, produce):
    """Build in a sibling directory and publish only a complete, verified result."""
    if output.name in ("", "..") or output.is_symlink():
        raise ValueError(f"Invalid output directory: {output}")
    previous = output.parent / f".{output.name}.previous"
    with locked_output(output):
        if previous.exists():
            backup = read_receipt(previous, name)
            check_managed(previous, name, backup["files"])
            if output.exists():
                read_receipt(output, name)
                shutil.rmtree(previous)
            else:
                previous.rename(output)
        if output.exists():
            report = read_receipt(output, name)
            files = report.pop("files")
            if report == identity:
                try:
                    checksums = (output / "SHA256SUMS").read_text()
                    expected = dict(files, **{name: sha(output / name)})
                    if checksums == checksum_text(expected):
                        for file, digest in files.items():
                            verify(output / file, digest)
                        return
                except (OSError, ValueError):
                    pass
            check_managed(output, name, files)
        with TemporaryDirectory(prefix=f".{output.name}-", dir=output.parent) as folder:
            work = Path(folder)
            stage = work / "result"
            stage.mkdir()
            produce(work, stage)
            files = {path.name: sha(path) for path in sorted(stage.iterdir())}
            if not files or files.keys() - ARTIFACTS:
                raise ValueError("Build produced an unexpected set of files")
            (stage / name).write_text(json.dumps(dict(identity, files=files), indent=2) + "\n")
            checksums = dict(files, **{name: sha(stage / name)})
            (stage / "SHA256SUMS").write_text(checksum_text(checksums))
            if output.exists():
                check_managed(output, name, read_receipt(output, name)["files"])
                output.rename(previous)
            try:
                stage.rename(output)
            except BaseException:
                if previous.exists() and not output.exists():
                    previous.rename(output)
                raise
            if previous.exists():
                shutil.rmtree(previous)


def checksum_text(files):
    return "".join(f"{digest}  {name}\n" for name, digest in files.items())
