from functools import partial
import io
from pathlib import Path
import subprocess
import sys
import tarfile
from tempfile import NamedTemporaryFile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "build"))
from release import build_release
from system_image import add_layer

HERE = Path(__file__).resolve().parent
RELEASE = "24.04-2.2"
ROOTFS_BUILD = "140"
LOMIRI = "usr/share/lomiri"
PATCHES = {
    f"{LOMIRI}/Shell.qml": HERE / "patches/lomiri-shell.patch",
    f"{LOMIRI}/Stage/Stage.qml": HERE / "patches/lomiri-stage.patch",
}
OVERLAY = HERE / "overlay"


def patch_qml(patch_path, original):
    with NamedTemporaryFile() as source:
        source.write(original)
        source.flush()
        result = subprocess.run(
            ["patch", "--batch", "--forward", "--fuzz=0", "--silent", "--reject-file=-",
             "--output=-", "--input", patch_path, source.name],
            stdout=subprocess.PIPE, check=True,
        )
    return result.stdout


def add_file(archive, name, data, mode=0o644):
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mode = mode
    archive.addfile(info, io.BytesIO(data))


def add_directory(archive, name, existing):
    if name not in existing:
        info = tarfile.TarInfo(name)
        info.type = tarfile.DIRTYPE
        info.mode = 0o755
        archive.addfile(info)
        existing.add(name)


def render(archive, inputs, adaptation):
    transforms = {name: partial(patch_qml, patch) for name, patch in PATCHES.items()}
    add_layer(archive, inputs["rootfs"], transforms)
    if transforms:
        raise ValueError(f"Missing Lomiri sources in OTA: {', '.join(transforms)}")
    for path in (inputs["device"], adaptation):
        add_layer(archive, path)

    existing = set(archive.getnames())
    for path in sorted(OVERLAY.rglob("*")):
        name = path.relative_to(OVERLAY).as_posix()
        if path.is_dir():
            add_directory(archive, name, existing)
        elif path.is_file():
            mode = 0o755 if path.suffix == ".sh" else 0o644
            add_file(archive, name, path.read_bytes(), mode)

    for name in ("etc", "etc/system-image", "etc/system-image/config.d"):
        add_directory(archive, name, existing)
    add_file(archive, "etc/system-image/channel.ini", f"""[service]
base: system-image.ubports.com
http_port: 80
https_port: 443
channel: local/herolte/24.04
device: herolte
build_number: 1
version_detail: tag={RELEASE},rootfs={ROOTFS_BUILD},device=herolte-halium11,version=1
""".encode())
    link = tarfile.TarInfo("etc/system-image/config.d/01_channel.ini")
    link.type = tarfile.SYMTYPE
    link.linkname = "../channel.ini"
    archive.addfile(link)


if __name__ == "__main__":
    assets = (*PATCHES.values(), *(path for path in sorted(OVERLAY.rglob("*")) if path.is_file()))
    build_release(Path(__file__).resolve(), RELEASE, 4000, render, assets)
