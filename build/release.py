"""Compose and publish a firmware bundle from verified inputs."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
from uuid import UUID

from artifacts import BOOT, BUNDLE_RECEIPT, OVERLAY, SYSTEM, publish, sha, verify
from system_image import make_ext4


def build_release(recipe, release, size_mib, render, assets=()):
    parser = argparse.ArgumentParser(description=f"Build Ubuntu Touch {release} SYSTEM.")
    for option in ("inputs", "adaptation", "output"):
        parser.add_argument(option, type=Path)
    args = parser.parse_args()
    manifest = recipe.with_name("files.sha256")
    try:
        inputs = {}
        hashes = {}
        for line in manifest.read_text().splitlines():
            digest, name, _url = line.split()
            verify(args.inputs / name, digest)
            inputs[name.split("-", 1)[0]] = args.inputs / name
            hashes[name] = digest

        names = [BOOT, OVERLAY]
        if (args.adaptation / "recovery.img").is_file():
            names.append("recovery.img")
        artifacts = {name: sha(args.adaptation / name) for name in names}
        identity = {
            "schema": 1,
            "device": "herolte",
            "release": release,
            "kernel_series": os.environ.get("S7_KERNEL_SERIES"),
            "halium": os.environ.get("S7_HALIUM_VERSION"),
            "source_commits": {
                name: os.environ.get(f"S7_{name.upper()}_COMMIT")
                for name in ("kernel", "port", "tools")
            },
            "system_size_mib": size_mib,
            "ota_sha256": hashes,
            "adaptation_sha256": artifacts,
            "recipe_sha256": {
                file.name: sha(file)
                for file in (recipe, manifest, Path(__file__),
                             Path(__file__).with_name("system_image.py"), *assets)
            },
        }
        digest = sha256(json.dumps(identity, sort_keys=True).encode()).digest()
        filesystem_uuid = UUID(bytes=digest[:16], version=4)

        def produce(work, stage):
            for name, checksum in artifacts.items():
                shutil.copyfile(args.adaptation / name, stage / name)
                verify(stage / name, checksum)
            payload = work / "system.tar"
            with tarfile.open(payload, "w", format=tarfile.PAX_FORMAT) as archive:
                render(archive, inputs, stage / OVERLAY)
            for path in inputs.values():
                verify(path, hashes[path.name])
            make_ext4(payload, stage / SYSTEM, size_mib * 1024**2, filesystem_uuid)

        publish(args.output, BUNDLE_RECEIPT, identity, produce)
    except (OSError, ValueError, KeyError, tarfile.TarError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Firmware assembly failed: {exc}\n")
