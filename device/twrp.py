#!/usr/bin/env python3
"""Install a local herolte build via root ADB in TWRP."""
import argparse
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
from artifacts import BOOT, SYSTEM, BUNDLE_RECEIPT, read_receipt, sha


MODELS = {"SM-G930F", "SM-G930FD", "SM-G930W8", "SM-G930X",
          "SM-G930K", "SM-G930L", "SM-G930S"}
NODES = {"BOOT": "/dev/block/sda5", "SYSTEM": "/dev/block/sda14",
         "USERDATA": "/dev/block/sda18"}
MIB = 1024 ** 2


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


class Recovery:
    def __init__(self, serial):
        self.adb = [os.environ.get("ADB", "adb"), "-s", serial]
        self.serial = serial
        if run(*self.adb, "get-state", stdout=subprocess.PIPE).stdout.strip() not in (
            b"recovery", b"device"
        ):
            raise ValueError("Expected ADB in recovery")
        marker = self.shell('if test -d /twres && test "$(id -u)" = 0; then printf TWRP_READY; fi')
        if marker != "TWRP_READY":
            raise ValueError("Expected a root ADB shell in TWRP")
        probe = subprocess.run([*self.adb, "shell", "-n", "-T", "exit 7"])
        if probe.returncode != 7:
            raise ValueError("ADB shell-v2 with remote exit status is required")
        device, model, loader = self.shell(
            "getprop ro.product.device; getprop ro.product.model; getprop ro.bootloader"
        ).splitlines()
        if model == "omni_herolte":
            match = re.fullmatch(r"(G930[A-Z]{1,2})[A-Z]{2}[US][A-Z0-9][A-Z]{3}[A-Z0-9]", loader)
            model = "SM-" + match[1] if match else ""
        if not re.fullmatch(r"herolte[a-z0-9_]*", device) or model not in MODELS:
            raise ValueError(f"Expected Exynos herolte, found {device} {model}")
        self.model = model

    def shell(self, command):
        return run(*self.adb, "shell", "-n", "-T", command, stdout=subprocess.PIPE,
                   text=True).stdout.strip()

    def partition_size(self, part):
        path = NODES[part]
        alias = f"/dev/block/platform/155a0000.ufs/by-name/{part}"
        size = int(self.shell(
            f'test "$(readlink -f {alias})" = {path} && test -b {path} && blockdev --getsize64 {path}'
        ))
        if size <= 0 or (part == "BOOT" and size != 40 * MIB):
            raise ValueError(f"Unexpected {part} size {size}")
        return size

    def require_unmounted(self, part):
        device = self.device_number(part)
        for number, _, point in self.mounts():
            if number == device:
                raise ValueError(f"{part} is mounted at {point}. Unmount it in TWRP.")

    def device_number(self, part):
        return self.shell(f"cat /sys/class/block/{Path(NODES[part]).name}/dev")

    def mounts(self):
        return [line.split()[2:5] for line in self.shell("cat /proc/self/mountinfo").splitlines()]

    def check_userdata(self):
        path = NODES["USERDATA"]
        self.partition_size("USERDATA")
        device = self.device_number("USERDATA")
        data_mounts = [(number, root) for number, root, point in self.mounts() if point == "/data"]
        if data_mounts and data_mounts != [(device, "/")]:
            raise ValueError("Unexpected filesystem mounted at /data")
        mount = "d=/data"
        if not data_mounts:
            mount = f"""d=$(mktemp -d /tmp/s7-data.XXXXXX)
            trap 'rmdir "$d"' EXIT
            mount -t ext4 -o ro,noload {path} "$d"
            trap 'umount "$d"; rmdir "$d"' EXIT"""
        self.shell(f"""set -eu
            test ! -e /dev/disk/by-partlabel/UT_SYSTEM_SD
            test ! -e /dev/disk/by-partlabel/UT_USERDATA_SD
            status=0
            grep -Eq '^PARTNAME=UT_(SYSTEM|USERDATA)_SD$' /sys/class/block/*/uevent || status=$?
            if test "$status" != 1; then
                echo "Could not rule out an SD partition that takes precedence" >&2
                exit 1
            fi
            if ! blkid {path} | grep -q 'TYPE="ext4"'; then
                echo "USERDATA must be accessible as ext4" >&2
                exit 1
            fi
            {mount}
            for p in rootfs.img ubuntu.img halium-rootfs; do
                if test -e "$d/$p"; then
                    echo "USERDATA contains $p, which takes precedence over SYSTEM" >&2
                    exit 1
                fi
            done""")

    def remote_digest(self, part, size):
        # TWRP's head can truncate byte limits above 4 GiB. Use it only on the last block.
        path = NODES[part]
        blocks, tail = divmod(size, MIB)
        read_blocks = f'dd if={path} bs={MIB} count={blocks} 2>"$d/dd.log"'
        if tail:
            read_blocks += (
                f' && dd if={path} of="$d/tail" bs={MIB} skip={blocks} count=1 2>>"$d/dd.log"'
                f' && head -c {tail} "$d/tail"'
            )
        result = self.shell(f"""set -eu
            d=$(mktemp -d /tmp/s7-read.XXXXXX)
            trap 'rm -rf "$d"' EXIT
            {{ {read_blocks} && touch "$d/ok"; }} | sha256sum
            if ! test -e "$d/ok"; then cat "$d/dd.log" >&2; exit 1; fi""").split()[0]
        if not re.fullmatch(r"[a-f0-9]{64}", result):
            raise ValueError(f"Invalid {part} readback checksum")
        return result

    def backup(self, part, directory, size):
        self.require_unmounted(part)
        print(f"Backing up {part} ({size} bytes)", flush=True)
        path = directory / f"{part}.img"
        partial = path.with_suffix(".partial")
        digest = hashlib.sha256()
        count = 0
        zero_block = bytes(MIB)
        with partial.open("xb") as out, subprocess.Popen(
            [*self.adb, "shell", "-n", "-T", f"dd if={NODES[part]} bs={MIB}"],
            stdout=subprocess.PIPE
        ) as proc:
            while data := proc.stdout.read(MIB):
                count += len(data)
                digest.update(data)
                if data == zero_block:
                    out.seek(len(data), os.SEEK_CUR)
                else:
                    out.write(data)
                if count % (1024 * MIB) == 0:
                    print(f"{part} backup {count // MIB} MiB", flush=True)
            if proc.wait() or count != size:
                raise ValueError(f"Incomplete {part} backup ({count}/{size} bytes)")
            out.truncate(size)
            out.flush()
            os.fsync(out.fileno())
        result = digest.hexdigest()
        if result != self.remote_digest(part, size):
            raise ValueError(f"{part} backup differs from partition")
        partial.rename(path)
        return result

    def flash(self, part, image, size, digest):
        self.require_unmounted(part)
        print(f"Writing {part} ({size} bytes)", flush=True)
        # ADB's pipe may return short reads. dd writes each chunk in sequence.
        with image.open("rb") as stream:
            run(*self.adb, "shell", "-T", f"dd of={NODES[part]} bs={MIB} && sync", stdin=stream)
        if self.remote_digest(part, size) != digest:
            raise ValueError(f"{part} readback SHA-256 mismatch")
        print(f"{part} readback SHA-256 {digest}", flush=True)


def build_images(directory):
    receipt = read_receipt(directory, BUNDLE_RECEIPT)
    if receipt.get("schema") != 1 or receipt.get("device") != "herolte":
        raise ValueError("Expected a local herolte build receipt")
    manifest = (directory / "SHA256SUMS").read_text().splitlines()
    files = receipt["files"]
    images = {}
    for part, name, offset, magic in (
        ("SYSTEM", SYSTEM, 1080, b"\x53\xef"), ("BOOT", BOOT, 0, b"ANDROID!")
    ):
        path = directory / name
        size = path.stat().st_size
        digest = sha(path)
        if files.get(name) != digest or manifest.count(f"{digest}  {name}") != 1:
            raise ValueError(f"Build checksum mismatch for {path}")
        with path.open("rb") as image:
            image.seek(offset)
            if image.read(len(magic)) != magic:
                raise ValueError(f"Unexpected image format for {path}")
        images[part] = (path, size, digest)
    return images


def backup_images(directory, device):
    identity = (directory / "device.txt").read_text().splitlines()
    if identity != [device.model, device.serial]:
        raise ValueError("Backup belongs to a different phone")
    manifest = (directory / "SHA256SUMS").read_text().splitlines()
    images = {}
    for part in ("SYSTEM", "BOOT"):
        path = directory / f"{part}.img"
        size = path.stat().st_size
        if size != device.partition_size(part):
            raise ValueError(f"{part} backup has the wrong size")
        digest = sha(path)
        if manifest.count(f"{digest}  {path.name}") != 1:
            raise ValueError(f"{part} backup checksum mismatch")
        images[part] = (path, size, digest)
    return images


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", required=True, help="ADB serial shown by adb devices")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--bundle", type=Path, help="local build output directory")
    source.add_argument("--restore", type=Path, help="restore SYSTEM and BOOT from a backup")
    parser.add_argument("--backup-dir", type=Path, default=Path("work/flash-backups"))
    parser.add_argument("--reuse-backup", type=Path, help="use a previous backup to retry installation")
    parser.add_argument("--execute", action="store_true", help="write SYSTEM and BOOT")
    args = parser.parse_args()
    if args.reuse_backup and not args.bundle:
        parser.error("--reuse-backup requires --bundle")

    device = Recovery(args.serial)
    images = build_images(args.bundle) if args.bundle else backup_images(args.restore, device)
    sizes = {part: device.partition_size(part) for part in images}
    for part, (_, size, _) in images.items():
        if size > sizes[part]:
            raise ValueError(f"{part} image needs {size} bytes, partition holds {sizes[part]}")
        device.require_unmounted(part)
    if args.bundle:
        device.check_userdata()
        if args.reuse_backup:
            backup_images(args.reuse_backup, device)
    print(f"TWRP preflight passed on {device.model} ({device.serial})", flush=True)
    if not args.execute:
        return
    if args.bundle and not args.reuse_backup:
        args.backup_dir.mkdir(parents=True, exist_ok=True)
        if shutil.disk_usage(args.backup_dir).free < sum(sizes.values()):
            raise ValueError("Insufficient space for full partition backups")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        backup = args.backup_dir / stamp
        backup.mkdir(mode=0o700)
        print(f"Backup directory {backup}", flush=True)
        (backup / "device.txt").write_text(f"{device.model}\n{device.serial}\n")
        with (backup / "SHA256SUMS").open("x") as checksums:
            for part in reversed(images):
                digest = device.backup(part, backup, sizes[part])
                checksums.write(f"{digest}  {part}.img\n")
                checksums.flush()
                os.fsync(checksums.fileno())
    for part, image in images.items():
        device.flash(part, *image)
    print("Write verified. The phone is still in TWRP.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        sys.exit(f"TWRP install stopped: {exc}")
