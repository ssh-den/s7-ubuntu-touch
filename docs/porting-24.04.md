# Porting Ubuntu Touch 24.04 to the Galaxy S7

The Samsung Galaxy S7 (Exynos, `herolte`) already had a working
Ubuntu Touch 20.04 port based on Linux 3.18, Halium 11, and Samsung
vendor components providing hardware support.

The Ubuntu Touch 24.04 port replaces the Ubuntu userspace while
retaining the existing hardware adaptation stack. The original
porting work was carried out on the SM-G930F.

## Build architecture

### Ubuntu and Android userspace

The [24.04 build recipe](../releases/24.04/system.py) uses the shared
Ubuntu Touch 24.04-2.2 ARM64 Android9+ root filesystem published
through the UBports OTA index for X00TD.

Only the Ubuntu root filesystem is taken from the X00TD index.
The Android Generic System Image (GSI) is taken from the Galaxy S7
Focal OTA build 1560, where it was paired with the Samsung vendor
components. Retaining this combination keeps the Android hardware
adaptation based on Halium 11.

### Boot and system images

The [Halium build](../halium/11/build.sh) produces the boot image
containing the Galaxy S7 kernel, ramdisk, and device tree. It also
produces the device layer containing the Samsung vendor image and
device-specific configuration.

The 24.04 build recipe:

1. Extracts the Ubuntu root filesystem.
2. Applies the Lomiri patches.
3. Adds the Android GSI and device layer.
4. Applies the Noble-specific overlay.
5. Configures a local update channel.
6. Generates a 4,000 MiB ext4 system image using filesystem features
   supported by the Linux 3.18 kernel.

The [release manifest](../releases/24.04/files.sha256) pins both
downloaded archives by their SHA-256 checksums.

## Noble-specific changes

### USB ADB and FunctionFS

On the original kernel, ADB could work in recovery while the Noble
ADB daemon appeared offline over USB.

Noble's `adbd` uses asynchronous FunctionFS operations that were
not supported by the Samsung kernel driver.

The [FunctionFS AIO patch](../releases/24.04/kernel/3.18/functionfs-aio-pages.patch)
adds support for these operations while preserving the existing
synchronous I/O path and ADB authorization.

Writable userspace pages are pinned when an asynchronous read is
submitted, allowing a background worker to copy received data
through kernel mappings after submission.

This patch is applied to the kernel used in the boot image.

### Hardware navigation keys

The Galaxy S7's physical Home key and capacitive Back and Recent
keys require device-specific handling in Lomiri.

The Samsung Recent key reports Linux input event code `254`, which
is not exposed as a shortcut by Noble's XKB mapping.

The following changes provide hardware navigation support:

- [Lomiri Shell patch](../releases/24.04/patches/lomiri-shell.patch)

  Opens the launcher on Home key release and suppresses duplicate
  Home events from the upstream monitor. Back dismisses the active
  Lomiri panel, launcher, or overview where applicable. Otherwise,
  the existing key mapper handles the event.

- [Navigation helper](../releases/24.04/overlay/usr/share/lomiri/herolte_navigation.py)

  Reads hardware key events through evdev without exclusively
  grabbing the input devices and forwards them to Lomiri through
  PyOtherSide.

- [Lomiri Stage patch](../releases/24.04/patches/lomiri-stage.patch)

  Exposes the application overview so that it can be toggled using
  the Recent key.

The Shell patch also controls capacitive key lighting and requests
haptic feedback for the Back and Recent keys.

The key lights turn off after three seconds or when the display
is switched off. Navigation actions and haptic feedback are
disabled while the screen is locked.

### Audio HAL

The Samsung Audio HAL wrapper depends on Android's `libaudiohal.so`.

If libhybris cannot locate this library, the PulseAudio Android
card fails to initialize, leaving the built-in speaker unavailable.

The [PulseAudio service drop-in](../releases/24.04/overlay/etc/systemd/user/pulseaudio.service.d/90-herolte-audio.conf)
adds `/system/lib64` to the library search path for the service.

### Light HAL

The previous Light HAL startup hook relied on `lxc-attach`.
This operation was denied on Noble, resulting in a startup delay.

The [replacement startup hook](../releases/24.04/overlay/usr/libexec/lxc-android-config/device-hacks.d/wait_for_lighthal.sh)
checks service registration directly through the HIDL service
manager using `/dev/hwbinder`.

The hook waits for up to ten seconds.

### GNSS HAL

Earlier bring-up work identified a separate startup delay in the
GNSS registration hook.

This behavior requires further verification on newly built images.

## Porting to another release or kernel

### Repository layout

Release-specific and hardware-specific build inputs are maintained
separately.

| Path | Purpose |
| --- | --- |
| `releases/<version>/` | Release manifests, system image recipes, and userspace changes |
| `releases/<version>/kernel/<series>/` | Release-specific kernel patches |
| `kernel/<series>/` | Kernel revisions and configurations |
| `halium/<version>/` | Hardware adaptation build inputs |

Select the kernel profile using `KERNEL=<series>`.

### Updating Ubuntu Touch

When introducing a new Ubuntu Touch release:

1. Pin the shared ARM64 root filesystem from the appropriate
   UBports OTA index.
2. Verify compatibility with the existing Android system image
   and Samsung vendor components.
3. Review the Lomiri patches against the new upstream sources.
4. Verify the evdev, PyOtherSide, and Qt Feedback dependencies.
5. Review device-specific overlays and service configuration.

The build fails if a QML patch cannot be applied.

### Current status

> [!NOTE]
> Earlier bring-up results apply to previous images and do not
> establish the runtime behavior of images produced by the
> current build pipeline.
>
> The current pipeline has passed offline checks and patch
> application against its pinned inputs.
>
> A full firmware build, reproducibility verification, and
> on-device validation are still pending.
