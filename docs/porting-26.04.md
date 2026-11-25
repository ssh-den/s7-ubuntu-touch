# Ubuntu Touch 26.04 on the Exynos Galaxy S7

The experimental target is `herolte` with a Halium 11 Android container.
Linux 3.18.140 is the default build target and reached the Lomiri greeter
on the SM-G930F. Linux 4.4.302 is under development and has yet to reach
a usable graphical session on the device.
The Resolute profiles use these pinned inputs.

| Component | Source |
| --- | --- |
| Ubuntu Touch arm64 android9plus rootfs | UBports Jenkins main [build 565][jenkins], published in the [26.04 daily index][daily] at full image version 49 |
| Linux | UBports [Linux 3.18 at `e697e3ac`][kernel-3.18] or 8890q [Linux 4.4 at `dcadf09b`][kernel] |
| Halium and device vendor | Halium 11 Android system layer and existing UBports [Galaxy S7 port][port], pinned separately from the rootfs |
| Samsung boot image | The existing port's ramdisk overlay and mkbootimg. The 4.4 profile generates the DTBH from the herolte device trees. |

The daily index is for `algiz_h16` and supplies the shared rootfs layer.
The Android container, vendor image, and boot image for that device are
device-specific.

The Linux 4.4 kernel fragment enables cgroup controllers, IPC and devpts for LXC,
SquashFS for the vendor image, and AppArmor for Ubuntu Touch. It keeps CRC32C
available at boot for ext4 metadata checksums. The Samsung FIPS validation
options are disabled because their integrity checks fail on the locally built
kernel and put the Linux Crypto API into an error state before SYSTEM mounts.
The underlying UFS FMP driver remains enabled. The kernel build omits the
optional KernelSU submodule. The builder includes Debian's ARM and AArch64
cross compilers.

Linux 4.4 enables a virtual terminal console for the initramfs handoff to
systemd. The build grows the nested Halium Android ext4 image to leave free
blocks and inodes for first-boot edits to Android properties and the Samsung
mount points. The Ubuntu SYSTEM image contains this expanded Android image.
The 4.4 backport of `close_range()` bounds the close operation by the current
file descriptor table, following [upstream Linux][close-range]. This lets
systemd launch services that close all remaining descriptors.

## Build

```sh
make image
make fetch RELEASE=26.04
make build RELEASE=26.04
(cd work/out/26.04/3.18 && sha256sum -c SHA256SUMS)
```

The Linux 3.18 build applies the FunctionFS AIO fix used by the tested
Noble kernel for the USB ADB transport.

## Linux 4.4 bring-up

Select `KERNEL=4.4` to reproduce the current bring-up image for debugging.

```sh
make fetch RELEASE=26.04 KERNEL=4.4
make build RELEASE=26.04 KERNEL=4.4
(cd work/out/26.04/4.4 && sha256sum -c SHA256SUMS)
```

For kernel-only iteration, `make kernel RELEASE=26.04 KERNEL=4.4` builds `Image` and `dtb.img`
under `work/build/26.04/4.4/kernel-objects/arch/arm64/boot/`.
Set `S7_JOBS` to control build parallelism. You can also run
`./s7 fetch 26.04` and `./s7 build 26.04` directly on an amd64 Linux host
with the dependencies in [build/Dockerfile](../build/Dockerfile).

For boot diagnostics, run `S7_BOOT_CONSOLE=1 make build RELEASE=26.04 KERNEL=4.4`.
The diagnostic bundle is published under `work/out/26.04/4.4-console/`.
Its BOOT enables the framebuffer console and sends systemd status to the
kernel log. On the tested SM-G930F, the kernel attached fbcon, but the panel
kept displaying the Samsung logo. TWRP can read the verbose log from
`/proc/last_kmsg` after the next reboot.

The 4.4 profile builds BOOT and SYSTEM images and uses the existing recovery.
The Halium initramfs mounts an `ubuntu.img` stored on USERDATA when present.
Otherwise it mounts SYSTEM, where the [TWRP installer](../README.md#install-from-twrp)
writes the Ubuntu rootfs image.

The Linux 4.4 hardware test reached systemd, journald and Android init with
API level 30. LightDM started repeatedly while the panel stayed on the
Samsung logo. The kernel log recorded `226/NAMESPACE` for polkit and
accounts-daemon, read-only cgroup errors in Android init, and failed Binder
requests from Lomiri. The compositor log recorded
`failed to get hwcomposer service`. The USB gadget was unavailable during
these boots.

## SM-G930F hardware verification

For the Linux 3.18 control test, only BOOT was replaced with the Noble
3.18.140 image. Its unpacked initramfs matched the Linux 4.4 image byte for
byte. The Noble and Resolute bundles also shared the same vendor and
original Android images before the Resolute resize. On the same installed
Resolute SYSTEM, Linux 3.18 exposed the cgroup v1 controllers, brought up
USB ADB, and ran hwcomposer and the Lomiri greeter. Linux 4.4 logged a
cgroup2 `nsdelegate` error and Android controller mount failures.

The complete 26.04/3.18 bundle was then installed on the SM-G930F with
`./s7 twrp`. Both partition readback checksums matched the bundle.
After reboot, ADB reported Ubuntu Touch 26.04.1, Linux 3.18.140, active
LightDM, a running Lomiri process, and registered Android composer and
allocator HALs. The boot check still reported a failed console-setup unit.

## Updating the rootfs and the Android layer

For a newer daily, select a full image from the official [channel index][channels].
Use the shared arm64 android9plus rootfs and its SHA-256 from that image.
Update the rootfs entry in `releases/26.04/files.sha256` and the Jenkins build
identifier in `releases/26.04/system.py`. Use the same procedure with the
26.04 stable rootfs once UBports publishes it. Local test images identify
their channel as `local/herolte/26.04`. A stable migration for this port
requires publishing and testing a herolte-specific OTA.

There is a public [Halium 16 manifest][halium16] based on Android 16 and
LineageOS 23.2. To evaluate it on the S7, prepare and pin a herolte-compatible
Android container and vendor overlay in a new Halium profile. Check the
vendor HALs, Binder, initramfs, cgroups and kernel compatibility with that
profile before changing the Resolute default. The 8890q [LineageOS 24 patches][patches]
target Android source repositories and should be evaluated when building an
Android base for this device.

[jenkins]: https://ci.ubports.com/job/ubuntu-touch-rootfs/job/main/565/
[close-range]: https://linux.googlesource.com/linux/kernel/git/torvalds/linux/+/cdb3033e191fd03da2d7da23b9cd448dfa180a8e/fs/file.c
[daily]: https://system-image.ubports.com/26.04-1.x/arm64/android9plus/daily/algiz_h16/index.json
[channels]: https://system-image.ubports.com/channels.json
[kernel-3.18]: https://github.com/ubports/kernel-samsung-universal8890/tree/e697e3acd8b23f3e5a7ee2b9b23e766491430f8a
[kernel]: https://github.com/8890q/android_kernel_samsung_universal8890/tree/dcadf09ba0cd4215c5e1ad4bff2bf6edc4f85db2
[halium16]: https://github.com/Halium/android/tree/halium-16.0
[patches]: https://github.com/8890q/patches/tree/lineage-24.0
[port]: https://gitlab.com/ubports/porting/community-ports/android11/samsung-galaxy-s7/samsung-exynos8890
