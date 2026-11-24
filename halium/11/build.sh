build_adaptation() {
    local port_checkout=$scratch/port kernel_src=$scratch/kernel adaptation_dir=$scratch/adaptation
    local halium_output_dir=$scratch/halium cache_dir=$scratch/objects/downloads
    local name url commit compiler wrapper patch_file compiled_defconfig
    rm -rf "$port_checkout" "$kernel_src" "$adaptation_dir" "$halium_output_dir" "$scratch/objects"
    checkout_git "$port_commit" "$port_checkout"
    checkout_git "$kernel_commit" "$kernel_src"
    checkout_git "$tools_commit" "$port_checkout/build"

    for patch_file in "$kernel_dir"/patches/*.patch "$release_dir"/kernel/"$kernel"/*.patch; do
        [[ ! -f $patch_file ]] || git -C "$kernel_src" apply "$patch_file"
    done
    compiled_defconfig=$(prepare_kernel_config "$kernel_src")
    mkdir -p "$cache_dir" "$halium_output_dir" "$adaptation_dir"
    ln -s "$kernel_src" "$cache_dir/kernel-samsung-universal8890"
    cp "$cache/halium-boot-ramdisk.img" "$cache_dir/"
    while read -r name url commit; do
        checkout_git "$commit" "$cache_dir/$name"
        [[ $name == *-4.9 ]] || continue
        compiler=${name%-4.9}
        # The legacy compiler wrappers need an explicit Python 3 interpreter in the build image.
        for wrapper in "bin/$compiler-gcc" "bin/$compiler-g++" "$compiler/bin/as"; do
            if head -n 1 "$cache_dir/$name/$wrapper" | grep -aq '^#![[:space:]]*/usr/bin/python$'; then
                sed -i '1c#!/usr/bin/env python3' "$cache_dir/$name/$wrapper"
            fi
        done
    done < "$halium_dir/tools.git"

    (
        cd "$port_checkout"
        bash ./prepare_overlays.sh herolte
        printf '\ndeviceinfo_kernel_defconfig="%s"\n' "$compiled_defconfig" >> deviceinfo
        find ramdisk-overlay -exec touch -h -d "@$SOURCE_DATE_EPOCH" {} +
        export PATH="$root/build/bin:$PATH"
        export HOSTCFLAGS='-Wall -Wmissing-prototypes -Wstrict-prototypes -O2 -fomit-frame-pointer -fcommon'
        bash ./build.sh -b "$scratch/objects" -o "$halium_output_dir"
    )

    local tree=$scratch/objects/tmp
    cp "$tree/partitions/boot.img" "$adaptation_dir/"
    if [[ -f $tree/partitions/recovery.img ]]; then
        cp "$tree/partitions/recovery.img" "$adaptation_dir/"
    fi
    tar --sort=name --mtime="@$SOURCE_DATE_EPOCH" --owner=0 --group=0 --numeric-owner \
        -C "$tree" -cf - system | xz --threads=1 > "$adaptation_dir/device_herolte.tar.xz"
}
