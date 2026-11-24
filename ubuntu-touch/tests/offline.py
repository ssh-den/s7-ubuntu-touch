"""Validate release recipes offline using synthetic build inputs."""

import os
import runpy
import subprocess
import sys
import tarfile
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "build"))
import release
from artifacts import sha, verify


def layer(path, files):
    """Create a synthetic system layer for offline testing."""
    with tarfile.open(path, "w:xz") as archive:
        for name, data in files.items():
            member = tarfile.TarInfo(f"system/{name}")
            member.size = len(data)
            archive.addfile(member, BytesIO(data))
    return path


def run_release(work, version, render, make_image):
    """Build a release from fixtures and verify its artifact checksums."""
    recipe = work / version / "system.py"
    recipe.parent.mkdir()
    recipe.write_text("fixture")
    inputs = work / "inputs"
    (recipe.parent / "files.sha256").write_text(
        "".join(f"{sha(path)} {path.name} fixture\n" for path in sorted(inputs.iterdir()))
    )
    output = work / f"out-{version}"
    argv = [str(recipe), str(inputs), str(work / "adaptation"), str(output)]
    with patch.object(sys, "argv", argv), patch.object(release, "make_ext4", make_image):
        # Verify that an unchanged build reuses existing artifacts.
        for _ in range(2):
            release.build_release(recipe, version, 1, render)
    for line in (output / "SHA256SUMS").read_text().splitlines():
        checksum, name = line.split()
        verify(output / name, checksum)
    return output


def main():
    os.environ["SOURCE_DATE_EPOCH"] = "1795392000"
    subprocess.run(["bash", ROOT / "s7", "--help"], check=True)
    for path in ROOT.rglob("*.py"):
        if "work" not in path.relative_to(ROOT).parts:
            compile(path.read_text(), str(path), "exec")

    focal = runpy.run_path(str(ROOT / "releases/20.04/system.py"))
    noble = runpy.run_path(str(ROOT / "releases/24.04/system.py"))
    shell = "usr/share/lomiri/Shell.qml"
    stage = "usr/share/lomiri/Stage/Stage.qml"
    fake_patch = """--- old
+++ new
@@ -1 +1 @@
-original
+patched
"""
    with TemporaryDirectory() as directory:
        work = Path(directory)
        inputs = work / "inputs"
        adaptation = work / "adaptation"
        inputs.mkdir()
        adaptation.mkdir()
        layer(inputs / "rootfs-test.tar.xz", {shell: b"original\n", stage: b"original\n"})
        layer(inputs / "device-test.tar.xz", {"var/lib/lxc/android/system.img": b"gsi"})
        layer(inputs / "version-test.tar.xz", {"etc/focal-version": b"1560"})
        layer(adaptation / "device_herolte.tar.xz", {"opt/adaptation": b"overlay"})
        (adaptation / "boot.img").write_bytes(b"boot")
        patch_file = work / "lomiri.patch"
        patch_file.write_text(fake_patch)

        renders = []

        def make_image(payload, image, size, filesystem_uuid):
            """Validate the payload and simulate deterministic image creation."""
            with tarfile.open(payload) as archive:
                names = archive.getnames()
                renders.append(set(names))
                if "etc/system-image/channel.ini" in renders[-1]:
                    assert archive.extractfile(shell).read() == b"patched\n"
                    for path in (
                                "etc/system-image/config.d/01_channel.ini",
                                "etc/systemd/user/pulseaudio.service.d/90-herolte-audio.conf"
                    ):
                        # Ensure parent directories precede their files in the archive.
                        for parent in Path(path).parents:
                            if parent.parts:
                                name = parent.as_posix()
                                assert archive.getmember(name).isdir()
                                assert names.index(name) < names.index(path)
            image.write_bytes(sha256(payload.read_bytes() + filesystem_uuid.bytes).digest())

        run_release(work, "20.04", focal["render"], make_image)
        assert len(renders) == 1 and "etc/focal-version" in renders[-1]

        # Remove the Focal-specific version layer before testing Noble.
        (inputs / "version-test.tar.xz").unlink()

        # Use synthetic patches to test the Noble patching workflow.
        with patch.dict(noble["render"].__globals__, PATCHES={shell: patch_file, stage: patch_file}):
            run_release(work, "24.04", noble["render"], make_image)
        assert len(renders) == 2
        assert {
            "etc/systemd/user/pulseaudio.service.d/90-herolte-audio.conf",
            "etc/system-image/channel.ini",
            "opt/adaptation",
            "usr/share/lomiri/herolte_navigation.py",
            "var/lib/lxc/android/android-rootfs.img",
        } <= renders[-1]
        assert "etc/focal-version" not in renders[-1]
    print("Offline release checks passed.")


if __name__ == "__main__":
    main()
