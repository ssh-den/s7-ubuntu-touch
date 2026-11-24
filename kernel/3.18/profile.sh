kernel_url=https://github.com/ubports/kernel-samsung-universal8890.git
kernel_commit=e697e3acd8b23f3e5a7ee2b9b23e766491430f8a

prepare_kernel_config() {
    local configs=$1/arch/arm64/configs
    local base=$configs/exynos8890-herolte_defconfig
    awk '
        /^CONFIG_[A-Za-z0-9_]+=/ {
            key=$0
            sub(/=.*/, "", key)
            lines[++count]=$0
            keys[count]=key
            last[key]=count
        }
        /^# CONFIG_[A-Za-z0-9_]+ is not set$/ {
            lines[++count]=$0
            keys[count]=$2
            last[$2]=count
        }
        END {
            for (i=1; i<=count; i++)
                if (last[keys[i]] == i)
                    print lines[i]
        }
    ' "$base" "$kernel_dir/halium.cfg" > "$configs/s7_defconfig" || return
    printf '%s\n' s7_defconfig
}
