# Ubuntu Touch for the Samsung Galaxy S7

Build Ubuntu Touch images for the Exynos Galaxy S7 (`herolte`).

## Supported releases

| Ubuntu Touch | Codename | Halium | Linux kernel |
| --- | --- | --- | --- |
| 20.04 | Focal | 11 | 3.18 |
| 24.04 | Noble | 11 | 3.18 |
| 26.04 | Resolute | 11 | 3.18 |

> [!WARNING]
> All builds are experimental and intended for testing purposes only.
> Do not install them on your primary device.
>
> Flash and use these builds at your own risk. Flashing may result in
> data loss or render your device unbootable. Always back up your
> data before flashing.
>
> This software is provided "as is", without warranty of any kind.
> See the [MIT License](LICENSE) for the full warranty disclaimer
> and limitation of liability.

## Hardware-tested build

| Ubuntu Touch | Halium | Kernel | Device | Verified |
| --- | --- | --- | --- | --- |
| 26.04.1 LTS (Resolute) | 11 | 3.18.140 | Galaxy S7 SM-G930F (`herolte`) | TWRP installation and partition readback, boot to Lomiri, USB ADB, Android graphics HAL registration |

This is an experimental port built from a pinned UBports daily rootfs.

## Build

On a Linux amd64 machine with Docker and GNU Make, run these commands from the
repository root. Set `release=20.04` for Focal or `release=24.04` for Noble.

```sh
release=26.04
make image
make fetch RELEASE="$release"
make build RELEASE="$release"
```

`make fetch` downloads the pinned sources and verifies the archives. `make build`
runs offline. The resulting `boot.img`, `ubuntu.img`, and optional
`recovery.img` are under `work/out/<release>/<kernel>/`. For the default
Linux 3.18 profile, verify the images for the selected release with this command.

```sh
(cd "work/out/$release/3.18" && sha256sum -c SHA256SUMS)
```

Set `WORK_DIR` to store downloads and builds elsewhere. Run `make test` for
offline checks that use sample files.

## Install from TWRP

Connect the Exynos Galaxy S7 in TWRP and use Python 3.8+ and Android Platform
Tools on the host. In TWRP, leave the System partition unmounted. Run
`adb devices -l` and use the device serial shown there.

```sh
./s7 twrp --serial SERIAL --bundle work/out/26.04/3.18
./s7 twrp --serial SERIAL --bundle work/out/26.04/3.18 --execute
```

The first command checks the bundle, phone and partition layout. The second
backs up SYSTEM and BOOT to `work/flash-backups/` with checksums and device
identity, writes SYSTEM first, then writes BOOT. Each write is verified from
the phone before proceeding. Have enough host disk space for both partition
backups. Set `ADB` to use an adb binary outside your PATH.

The installer expects an accessible ext4 USERDATA and keeps its contents.
It stops if a legacy rootfs on USERDATA or an SD partition would take priority
over SYSTEM during boot. After both checksums match, reboot to System from
TWRP.

To retry an interrupted installation, pass `--reuse-backup BACKUP_DIR`
with the complete backup from the earlier attempt.

To roll back from TWRP, use the backup directory printed by the installer.
The script checks the device identity, partition sizes and backup checksums.
Add `--execute` to write the two original partitions.

```sh
./s7 twrp --serial SERIAL --restore work/flash-backups/TIMESTAMP
```

## Documentation

- [Porting 26.04](docs/porting-26.04.md) records the rootfs and Android inputs,
  hardware test results, and ongoing kernel bring-up.
- [Porting 24.04 to the Galaxy S7](docs/porting-24.04.md) explains the hardware
  components reused from Focal, what each fix does, and how to check a new release.
- [Third-party sources and licenses](THIRD_PARTY.md) records upstream provenance
  and the licenses for the patches and build inputs.

## License

This project is licensed under the [MIT License](LICENSE).

Third-party components are subject to their respective licenses.
See [THIRD_PARTY.md](THIRD_PARTY.md) for details.
