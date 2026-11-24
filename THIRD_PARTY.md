# Third-party sources and licenses

The repository's [MIT License](LICENSE) applies to the build scripts.
Third-party components and patches remain subject to their respective
licenses.

## Included patches

The applicable GNU General Public Licenses for the included patches
are available in the [LICENSES](LICENSES/) directory.

| Patch | License | Upstream sources |
| --- | --- | --- |
| FunctionFS AIO | `GPL-2.0-only` | [Samsung kernel license](https://github.com/ubports/kernel-samsung-universal8890/blob/e697e3acd8b23f3e5a7ee2b9b23e766491430f8a/COPYING), [Android Common 3.18 FunctionFS](https://android.googlesource.com/kernel/common/+/bf1bc247eeeca3a2cbc964b85ef1a0977ce1e1b8/drivers/usb/gadget/function/f_fs.c) |
| Lomiri Shell and Stage | `GPL-3.0-only` | [Lomiri Shell](https://gitlab.com/ubports/development/core/lomiri/-/blob/d69afa1afca66af4883d2aa23571633a20790136/qml/Shell.qml), [Lomiri Stage](https://gitlab.com/ubports/development/core/lomiri/-/blob/d69afa1afca66af4883d2aa23571633a20790136/qml/Stage/Stage.qml) |

## Build dependencies

The following third-party inputs are fetched according to the pinned
source and download manifests.

| Component | License information |
| --- | --- |
| Samsung port scripts and modified `mkbootimg` | [Apache-2.0](https://gitlab.com/ubports/porting/community-ports/android11/samsung-galaxy-s7/samsung-exynos8890/-/blob/796ea91faa1fea85ba070b55fea11a900f01be35/LICENSE). The upstream checkout also contains device-specific binary images whose redistribution terms have not been verified. |
| Halium adaptation build tools | No `LICENSE` or `COPYING` file is present in the pinned upstream tree. The build fetches the tools directly from their upstream repository. |
| AOSP GCC toolchains | GPLv2 and component-specific license notices included in the pinned distributions. See [AArch64 COPYING](https://android.googlesource.com/platform/prebuilts/gcc/linux-x86/aarch64/aarch64-linux-android-4.9/+/961622e926a1b21382dba4dd9fe0e5fb3ee5ab7c/COPYING) and [ARM COPYING](https://android.googlesource.com/platform/prebuilts/gcc/linux-x86/arm/arm-linux-androideabi-4.9/+/09518d29069cf5993d0ef25c96a09bc851819b54/COPYING). |
| AOSP AVB | See the upstream [license notices](https://android.googlesource.com/platform/external/avb/+/342b0af8402a12b4c8cce6af5b54653beab1b05c/LICENSE). |
| Halium boot ramdisk | `GPL-3.0-or-later` for the [initramfs scripts](https://github.com/Halium/initramfs-tools-halium/blob/ed0b24c9256741a534612c7128e407ab90c905ac/debian/copyright). The binary archive contains additional components subject to their respective licenses. |
| Ubuntu Touch OTA layers | Component-specific license terms. See [Ubuntu Touch release sources](#ubuntu-touch-release-sources) below. |
| Debian build environment | Component-specific license terms. Package copyright and license notices are available under `/usr/share/doc/<package>/copyright`. See the pinned [Debian snapshot](https://snapshot.debian.org/archive/debian/20261123T000000Z/). |

## Ubuntu Touch release sources

The following upstream system-image indexes provide the archive paths
and SHA-256 checksums pinned in the release manifests.

| Release | Upstream index |
| --- | --- |
| Ubuntu Touch 20.04 (Focal) | [Build 1560 — herolte](https://system-image.ubports.com/20.04/arm64/android9plus/devel/herolte/index.json) |
| Ubuntu Touch 24.04 (Noble) | [Release 24.04-2.2 — X00TD](https://system-image.ubports.com/24.04-2.x/arm64/android9plus/stable/X00TD/index.json) |

Individual components within these archives remain subject to their
respective licenses.

## Redistribution

> [!IMPORTANT]
> Generated firmware images combine components distributed under
> different license terms, including device-specific binaries.
>
> The repository's MIT License does not grant redistribution rights
> for third-party components.
>
> Before distributing or publishing generated images, review the
> applicable license terms and ensure compliance with all relevant
> redistribution requirements, including source code availability
> and copyright notices where required.

## License verification

This document records the available upstream license information
and identifies known gaps. It does not constitute a comprehensive
license audit or confirmation of redistribution rights.
