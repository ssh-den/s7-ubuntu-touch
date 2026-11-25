# Third-party sources and licenses

The repository's [MIT License](LICENSE) applies to the build scripts.
Third-party components and patches remain subject to their respective licenses.
The applicable GNU licenses for the included patches are in [LICENSES](LICENSES/).

| Included patch | License | Upstream |
| --- | --- | --- |
| FunctionFS AIO | GPL-2.0-only | [Samsung kernel license](https://github.com/ubports/kernel-samsung-universal8890/blob/e697e3acd8b23f3e5a7ee2b9b23e766491430f8a/COPYING), [Android Common 3.18 FunctionFS](https://android.googlesource.com/kernel/common/+/bf1bc247eeeca3a2cbc964b85ef1a0977ce1e1b8/drivers/usb/gadget/function/f_fs.c) |
| Linux 4.4 AppArmor and KernelSU build changes | GPL-2.0-only | [8890q kernel license](https://github.com/8890q/android_kernel_samsung_universal8890/blob/dcadf09ba0cd4215c5e1ad4bff2bf6edc4f85db2/COPYING) |
| Linux 4.4 `close_range()` fix | GPL-2.0-only | [Linux file descriptor table handling](https://linux.googlesource.com/linux/kernel/git/torvalds/linux/+/cdb3033e191fd03da2d7da23b9cd448dfa180a8e/fs/file.c) |
| Lomiri Shell and Stage | GPL-3.0-only | [Lomiri Shell](https://gitlab.com/ubports/development/core/lomiri/-/blob/d69afa1afca66af4883d2aa23571633a20790136/qml/Shell.qml), [Lomiri Stage](https://gitlab.com/ubports/development/core/lomiri/-/blob/d69afa1afca66af4883d2aa23571633a20790136/qml/Stage/Stage.qml) |

The source and download manifests fetch these inputs at build time.

| Input | License information |
| --- | --- |
| Samsung port scripts and modified mkbootimg | [Apache-2.0](https://gitlab.com/ubports/porting/community-ports/android11/samsung-galaxy-s7/samsung-exynos8890/-/blob/796ea91faa1fea85ba070b55fea11a900f01be35/LICENSE). The same checkout contains device-specific binary images whose redistribution terms were not verified. |
| Halium adaptation build tools | The pinned tree has no LICENSE or COPYING file. The build fetches it from its upstream repository. |
| AOSP GCC toolchains | GPLv2 and component notices in the pinned distributions. [AArch64 COPYING](https://android.googlesource.com/platform/prebuilts/gcc/linux-x86/aarch64/aarch64-linux-android-4.9/+/961622e926a1b21382dba4dd9fe0e5fb3ee5ab7c/COPYING), [ARM COPYING](https://android.googlesource.com/platform/prebuilts/gcc/linux-x86/arm/arm-linux-androideabi-4.9/+/09518d29069cf5993d0ef25c96a09bc851819b54/COPYING). |
| AOSP AVB | [Component license notices](https://android.googlesource.com/platform/external/avb/+/342b0af8402a12b4c8cce6af5b54653beab1b05c/LICENSE). |
| Halium boot ramdisk | [GPL-3.0-or-later for the initramfs scripts](https://github.com/Halium/initramfs-tools-halium/blob/ed0b24c9256741a534612c7128e407ab90c905ac/debian/copyright). The binary archive contains components with their own licenses. |
| Ubuntu Touch OTA layers | Component-specific terms. The [Focal 1560 index](https://system-image.ubports.com/20.04/arm64/android9plus/devel/herolte/index.json), [Noble 24.04-2.2 index](https://system-image.ubports.com/24.04-2.x/arm64/android9plus/stable/X00TD/index.json), and [Resolute daily index](https://system-image.ubports.com/26.04-1.x/arm64/android9plus/daily/algiz_h16/index.json) supply the archive paths and SHA-256 values pinned in the release manifests. |
| Debian build environment | Component-specific terms. Debian provides package notices under `/usr/share/doc/<package>/copyright`. [Debian snapshot](https://snapshot.debian.org/archive/debian/20261123T000000Z/). |

## Redistribution

> [!IMPORTANT]
> Generated firmware images combine components under separate licenses,
> including device-specific binaries. Redistribution rights for third-party
> components depend on their own license terms.
>
> Before publishing an image, review those terms and meet any applicable
> requirements, including providing source code and copyright notices where
> required.

## License verification

This document records available upstream license information and known gaps.
A comprehensive license audit and confirmation of redistribution rights are
outside its scope.
