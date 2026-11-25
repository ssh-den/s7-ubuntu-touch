die() {
    printf '%s\n' "$*" >&2
    exit 1
}

[[ $(uname -s)/$(uname -m) == Linux/x86_64 ]] || die "Use a Linux amd64 build environment."
[[ ! -f config/local.env ]] || source config/local.env
work=${WORK_DIR:-$root/work}
kernel=${KERNEL:-3.18}
[[ $kernel =~ ^[0-9]+\.[0-9]+$ ]] || die "Invalid kernel series: $kernel"
release_dir=$root/releases/$release
kernel_dir=$root/kernel/$kernel
[[ -f $release_dir/profile.sh ]] || die "Unknown release: $release"
[[ -f $kernel_dir/profile.sh ]] || die "Unknown kernel series: $kernel"
[[ $kernel != 4.4 || $release == 26.04 ]] || die "Kernel 4.4 is available for release 26.04."
boot_console=${S7_BOOT_CONSOLE:-0}
[[ $boot_console == 0 || ( $boot_console == 1 && $kernel == 4.4 ) ]] ||
    die "S7_BOOT_CONSOLE=1 requires the Linux 4.4 profile."

mkdir -p "$work"
work=$(cd "$work" && pwd -P)
cache=$work/inputs
scratch=$work/build/$release/$kernel
output=$work/out/$release/$kernel
[[ $boot_console == 0 ]] || output+=-console
export LC_ALL=C.UTF-8 TZ=UTC SOURCE_DATE_EPOCH=1795392000
export KBUILD_BUILD_TIMESTAMP='Mon Nov 23 00:00:00 UTC 2026'
export KBUILD_BUILD_USER=builder KBUILD_BUILD_HOST=s7-builder KBUILD_BUILD_VERSION=1
export LOCALVERSION=
export PYTHONDONTWRITEBYTECODE=1
umask 022

source "$root/build/inputs.sh"

fetch_sources() {
    mkdir -p "$cache"
    exec 9>"$cache/.lock"
    flock -x 9
    fetch_git "$port_url" "$port_commit"
    fetch_git "$tools_url" "$tools_commit"
    fetch_git "$kernel_url" "$kernel_commit"
    if [[ $kernel == 3.18 ]]; then
        while read -r name url commit; do
            fetch_git "$url" "$commit"
        done < "$halium_dir/tools.git"
    fi
    fetch_files "$halium_dir/files.sha256"
    fetch_files "$release_dir/files.sha256"
}

lock_build_inputs() {
    mkdir -p "$scratch"
    exec 8>"$scratch/.lock"
    flock -x 8
    [[ -f $cache/.lock ]] || die "Run make fetch RELEASE=$release first."
    exec 9<"$cache/.lock"
    flock -s 9
}

build_firmware() {
    lock_build_inputs
    verify_files "$halium_dir/files.sha256"
    verify_files "$release_dir/files.sha256"
    source "$halium_dir/build.sh"
    build_adaptation
    S7_KERNEL_SERIES=$kernel S7_HALIUM_VERSION=$halium S7_KERNEL_COMMIT=$kernel_commit \
        S7_PORT_COMMIT=$port_commit S7_TOOLS_COMMIT=$tools_commit \
        python3 -IB "$release_dir/system.py" "$cache" "$scratch/adaptation" "$output"
}
