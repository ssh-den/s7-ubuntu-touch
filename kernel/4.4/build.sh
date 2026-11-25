build_kernel() {
    local kernel_src=$scratch/kernel kernel_objects=$scratch/kernel-objects
    local jobs=${S7_JOBS:-$(nproc)}
    [[ $jobs =~ ^[1-9][0-9]*$ ]] || die "S7_JOBS must be a positive integer."
    command -v aarch64-linux-gnu-gcc >/dev/null || die "Install gcc-aarch64-linux-gnu."
    command -v arm-linux-gnueabihf-gcc >/dev/null || die "Install gcc-arm-linux-gnueabihf."
    if [[ ! -d $kernel_src ]]; then
        local checkout
        checkout=$(mktemp -d "$scratch/.kernel-XXXXXXXX")
        checkout_git "$kernel_commit" "$checkout" KernelSU
        mv "$checkout" "$kernel_src"
    fi
    [[ $(git -C "$kernel_src" rev-parse HEAD) == "$kernel_commit" ]] ||
        die "Kernel checkout has the wrong revision: $kernel_src"

    local patch_file
    for patch_file in "$kernel_dir"/patches/*.patch; do
        if ! git -C "$kernel_src" apply --reverse --check "$patch_file" 2>/dev/null; then
            git -C "$kernel_src" apply "$patch_file"
        fi
    done

    mkdir -p "$kernel_objects"
    local cmdline=console=tty0
    local -a fragments=("$kernel_dir/halium.cfg")
    if [[ $boot_console == 1 ]]; then
        fragments+=("$kernel_dir/boot-console.cfg")
        cmdline+=" ignore_loglevel fbcon=font:SUN12x22 systemd.show_status=1 systemd.log_target=kmsg"
    fi
    local -a kmake=(make -C "$kernel_src" O="$kernel_objects" ARCH=arm64
        CROSS_COMPILE=aarch64-linux-gnu- CROSS_COMPILE_ARM32=arm-linux-gnueabihf-
        HOSTCFLAGS="-Wall -Wmissing-prototypes -Wstrict-prototypes -O2 -fomit-frame-pointer -fcommon")
    "${kmake[@]}" exynos8890-herolte_defconfig
    (
        cd "$kernel_objects"
        "$kernel_src/scripts/kconfig/merge_config.sh" -m .config "${fragments[@]}"
        "$kernel_src/scripts/config" --set-str CMDLINE "$cmdline"
    )
    "${kmake[@]}" olddefconfig
    local setting
    while IFS= read -r setting; do
        grep -Fxq "$setting" "$kernel_objects/.config" ||
            die "Kernel configuration dropped: $setting"
    done < <(cat "${fragments[@]}")
    grep -Fxq "CONFIG_CMDLINE=\"$cmdline\"" "$kernel_objects/.config" ||
        die "Kernel configuration dropped the command line."

    "${kmake[@]}" -j"$jobs" Image dtb.img
}
