# Porting Ubuntu Touch 24.04 to the Galaxy S7

The Galaxy S7 Exynos (`herolte`) already had a working Ubuntu Touch 20.04 port.
That port used Linux 3.18, a Halium 11 Android system, and Samsung vendor files
that provide hardware support. The 24.04 port replaces the Ubuntu userspace
while keeping that hardware stack. The original porting work used the
SM-G930F.

## How the images fit together

The [24.04 build recipe](../releases/24.04/system.py) starts with the shared
Ubuntu Touch 24.04-2.2 ARM64 Android9+ root filesystem. The UBports OTA index
for X00TD publishes this shared archive. The 24.04 manifest takes only that
root filesystem from the X00TD index. The Android system image (GSI) comes
from the Galaxy S7's Focal OTA 1560, where it was paired with the Samsung
vendor files. This pairing keeps the Android side at Halium 11.

The [Halium build](../halium/11/build.sh) builds BOOT with the Galaxy S7 kernel,
ramdisk, and device tree. It also produces the device layer containing the
Samsung vendor image and device configuration. The 24.04 recipe applies the
Lomiri patches to the root filesystem, then adds the GSI, the device layer,
and the Noble overlay. It writes a 4,000 MiB ext4 SYSTEM image with features
supported by the 3.18 kernel and sets a local update channel. The
[release manifest](../releases/24.04/files.sha256) pins the two downloaded
archives by SHA-256.

## Why Noble needs changes

### USB ADB in BOOT

On the original kernel, ADB could work in recovery while the Noble daemon
appeared offline over USB. Noble's `adbd` uses asynchronous FunctionFS
operations that the Samsung driver lacked. The
[FunctionFS AIO patch](../releases/24.04/kernel/3.18/functionfs-aio-pages.patch)
adds those operations and preserves the existing synchronous path and ADB
authorization. It pins writable userspace pages when a read is submitted so
a background worker can copy received data through kernel mappings after
submission.

### Navigation keys in SYSTEM

The S7's Home key and capacitive Back and Recent keys need device-specific
handling in Lomiri. Samsung's Recent key reports Linux input event code 254,
which Noble's XKB mapping does not expose as a shortcut.

- The [Shell patch](../releases/24.04/patches/lomiri-shell.patch) opens the
  launcher when Home is released and suppresses the duplicate Home event from
  the upstream monitor. Back dismisses the open Lomiri panel, launcher, or
  overview when applicable. Otherwise the existing key mapper handles it.
- The [navigation helper](../releases/24.04/overlay/usr/share/lomiri/herolte_navigation.py)
  reads the keys through evdev without taking exclusive control of the input
  devices. It sends events to Lomiri through PyOtherSide. The
  [Stage patch](../releases/24.04/patches/lomiri-stage.patch) exposes the app
  overview so Recent can toggle it.
- The Shell patch also drives the capacitive key lights and requests haptic
  feedback for Back and Recent. The lights time out after three seconds and go
  out when the display turns off. The navigation actions and haptics are
  disabled while the screen is locked.

### Speaker and Light HAL in SYSTEM

The Samsung Audio HAL wrapper needs Android's `libaudiohal.so`. If libhybris
cannot find it, PulseAudio's Android card fails to initialize and the built-in
speaker output is missing. The
[PulseAudio drop-in](../releases/24.04/overlay/etc/systemd/user/pulseaudio.service.d/90-herolte-audio.conf)
adds `/system/lib64` to the lookup path for that service.

The earlier Light HAL startup hook used `lxc-attach`, which was denied on
Noble and delayed startup. The
[replacement hook](../releases/24.04/overlay/usr/libexec/lxc-android-config/device-hacks.d/wait_for_lighthal.sh)
checks service registration directly with the HIDL service manager through
`/dev/hwbinder`. It waits up to ten seconds. The earlier port also recorded a
separate startup delay in the GNSS registration hook, which needs checking
again on a new image.

## Moving to another release or kernel

### Repository layout

| Path | Purpose |
| --- | --- |
| `releases/<version>/` | Release manifests, SYSTEM image recipes, and userspace changes |
| `releases/<version>/kernel/<series>/` | Release-specific kernel patches |
| `kernel/<series>/` | Kernel revisions and configurations |
| `halium/<version>/` | Hardware adaptation build inputs |

Select a kernel profile with `KERNEL=<series>`.

### Updating Ubuntu Touch

For a new Ubuntu Touch release, pin the shared ARM64 root filesystem from the
correct OTA index. Check that the new userspace works with the existing
Android system and vendor files. Recheck the Lomiri patch context and the
evdev, PyOtherSide, and Qt Feedback dependencies. The build stops if a QML
patch fails to apply.

Build twice in clean work directories on Linux amd64 and compare
`SHA256SUMS` before claiming byte-for-byte reproducibility. On the phone,
check boot and lock-screen behavior, USB ADB, the three navigation keys,
key lighting and feedback, the built-in speaker, and HAL startup. Earlier
bring-up results describe older images. The current pipeline has passed
offline checks and patch application against its pinned inputs, with a
full build and on-device validation still pending.
