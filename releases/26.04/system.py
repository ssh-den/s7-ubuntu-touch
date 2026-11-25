from io import BytesIO
import os
from pathlib import Path
import subprocess
import sys
import tarfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "build"))
from release import build_release
from system_image import add_layer

ROOTFS_BUILD = "2026-11-25T03:03:06Z_arm64_main_565_e0a2e4cc606b39d2afc5029e607ea29e3e1984b5"
ANDROID_ROOTFS = "var/lib/lxc/android/android-rootfs.img"


def verify_release(data):
    if "VERSION_ID=26.04" not in data.decode().replace('"', "").splitlines():
        raise ValueError("Expected Ubuntu 26.04 in the rootfs")
    return data


def resize_android_rootfs(path):
    # First boot rewrites build.prop and creates Samsung mount points in this ext4 image.
    # Grow past an ext4 block group boundary so the image gains both blocks and inodes.
    size = (path.stat().st_size + 1_048_575) // 1_048_576 + 128
    env = dict(os.environ, E2FSPROGS_FAKE_TIME=os.environ["SOURCE_DATE_EPOCH"])
    subprocess.run(["resize2fs", path, f"{size}M"], check=True, env=env)
    subprocess.run(["e2fsck", "-fn", path], check=True)


def render(archive, inputs, adaptation):
    transforms = {"usr/lib/os-release": verify_release}
    add_layer(archive, inputs["rootfs"], transforms)
    if transforms:
        raise ValueError("Missing usr/lib/os-release in rootfs")
    android = {ANDROID_ROOTFS: resize_android_rootfs}
    add_layer(archive, inputs["device"], file_transforms=android)
    if android:
        raise ValueError("Missing Android rootfs in the Halium layer")
    add_layer(archive, adaptation)
    names = set(archive.getnames())
    required = {"vendor.img", ANDROID_ROOTFS}
    if missing := required - names:
        raise ValueError(f"Missing herolte Android layers: {', '.join(sorted(missing))}")

    for name in ("etc/system-image", "etc/system-image/config.d"):
        if name not in names:
            directory = tarfile.TarInfo(name)
            directory.type = tarfile.DIRTYPE
            directory.mode = 0o755
            archive.addfile(directory)
    channel = f"""[service]
base: system-image.ubports.com
http_port: 80
https_port: 443
channel: local/herolte/26.04
device: herolte
build_number: 1
version_detail: tag=26.04-1.x,rootfs={ROOTFS_BUILD},device=herolte-halium11,version=1
""".encode()
    info = tarfile.TarInfo("etc/system-image/channel.ini")
    info.mode = 0o644
    info.size = len(channel)
    archive.addfile(info, BytesIO(channel))
    link = tarfile.TarInfo("etc/system-image/config.d/01_channel.ini")
    link.type = tarfile.SYMTYPE
    link.linkname = "../channel.ini"
    archive.addfile(link)


if __name__ == "__main__":
    build_release(Path(__file__).resolve(), "26.04", 5120, render)
