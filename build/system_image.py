"""Shared Halium OTA layer handling and ext4 image creation."""
import io
from pathlib import PurePosixPath
import os
import subprocess
import tarfile


EXT4_FEATURES = (
    "none,has_journal,ext_attr,resize_inode,dir_index,filetype,extent,64bit,"
    "flex_bg,sparse_super,large_file,huge_file,dir_nlink,extra_isize,metadata_csum"
)


def system_path(name):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Invalid OTA path: {name!r}")
    if path.parts[:1] != ("system",) or len(path.parts) == 1:
        return None
    parts = path.parts[1:]
    # Focal is usr-merged. Preserve the top-level symlinks, but normalize
    # entries below them (the published rootfs appends files under lib/modules).
    if len(parts) > 1 and parts[0] in ("bin", "sbin", "lib"):
        parts = ("usr", *parts)
    relative = str(PurePosixPath(*parts))
    # The upstream OTA builder also normalizes the older Halium GSI filename.
    if relative == "var/lib/lxc/android/system.img":
        return "var/lib/lxc/android/android-rootfs.img"
    return relative


def add_layer(archive, source, transforms=None):
    """Copy a layer, removing applied transforms so the caller can detect missing files."""
    print(f"SYSTEM: {source.name}", flush=True)
    command = ["xz", "-T0", "-dc", "--", source]
    with subprocess.Popen(command, stdout=subprocess.PIPE) as decoder:
        with tarfile.open(fileobj=decoder.stdout, mode="r|", bufsize=1024 * 1024) as layer:
            for member in layer:
                name = system_path(member.name)
                if name is None:
                    continue
                member.name = name
                member.pax_headers.pop("path", None)
                if member.islnk():
                    member.linkname = system_path(member.linkname)
                    if member.linkname is None:
                        raise ValueError(f"Hardlink outside SYSTEM: {name}")
                    member.pax_headers.pop("linkpath", None)
                contents = layer.extractfile(member) if member.isfile() else None
                if member.issparse():
                    member.pax_headers = {
                        key: value for key, value in member.pax_headers.items()
                        if not key.startswith("GNU.sparse.")
                    }
                    member.type = tarfile.REGTYPE
                    member.sparse = None
                if transforms and name in transforms:
                    if contents is None:
                        raise ValueError(f"Expected a regular file in the OTA: {name}")
                    data = transforms.pop(name)(contents.read())
                    contents = io.BytesIO(data)
                    member.size = len(data)
                    member.pax_headers.pop("size", None)
                    # Qt compares the source mtime with the compiled cache in USERDATA.
                    member.mtime = max(int(os.environ["SOURCE_DATE_EPOCH"]), int(member.mtime) + 1)
                    member.pax_headers.pop("mtime", None)
                archive.addfile(member, contents)
        # tar may stop before the end padding. Finish decoding and check the CRC.
        while decoder.stdout.read(1024 * 1024):
            pass
        if decoder.wait():
            raise subprocess.CalledProcessError(decoder.returncode, command)


def make_ext4(payload, image, size, filesystem_uuid):
    with image.open("xb") as stream:
        stream.truncate(size)
    env = dict(os.environ, E2FSPROGS_FAKE_TIME=os.environ["SOURCE_DATE_EPOCH"])
    subprocess.run([
        "mke2fs", "-q", "-F", "-t", "ext4", "-b", "4096", "-i", "16384", "-I", "256",
        "-O", EXT4_FEATURES, "-U", str(filesystem_uuid),
        "-E", f"root_owner=0:0,hash_seed={filesystem_uuid},lazy_itable_init=0,lazy_journal_init=0",
        "-d", payload, image,
    ], check=True, env=env)
    subprocess.run(["e2fsck", "-fn", image], check=True)
