# Ubuntu Touch for the Samsung Galaxy S7

Build pipeline for Ubuntu Touch on the Samsung Galaxy S7 (Exynos, `herolte`),
based on Halium 11 and the Linux 3.18 kernel.

## Supported releases

| Ubuntu Touch | Codename | Halium | Linux kernel |
| --- | --- | --- | --- |
| 20.04 | Focal | 11 | 3.18 |
| 24.04 | Noble | 11 | 3.18 |

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

## Building

### Prerequisites

- Linux (amd64/x86_64)
- Docker
- GNU Make

### Build instructions

Run the following commands from the repository root:

```sh
release=20.04

make image
make fetch RELEASE="$release"
make build RELEASE="$release"
```

To build Ubuntu Touch 24.04 (Noble), set `release=24.04` instead.

The `fetch` target downloads the pinned sources and verifies the
downloaded archives. The `build` target runs offline.

### Build artifacts

The generated images are located in `work/out/<release>/3.18/`:

- `boot.img`
- `ubuntu.img`
- `recovery.img` (if generated)
- `SHA256SUMS`

Verify the generated images against their SHA-256 checksums:

```sh
(cd "work/out/$release/3.18" && sha256sum -c SHA256SUMS)
```

To use a different location for downloads and build artifacts, set
`WORK_DIR`.

### Testing

Run offline tests using sample files:

```sh
make test
```

## Documentation

- [Porting Ubuntu Touch 24.04 to the Galaxy S7](docs/porting-24.04.md) —
  hardware components reused from Focal, porting fixes, and release
  validation.
- [Third-party sources and licenses](THIRD_PARTY.md) —
  upstream sources, provenance, and licensing information for patches
  and build inputs.

## License

This project is licensed under the [MIT License](LICENSE).

Third-party components are subject to their respective licenses.
See [THIRD_PARTY.md](THIRD_PARTY.md) for details.
