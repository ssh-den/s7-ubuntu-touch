git_cache() {
    printf '%s/git/%s\n' "$cache" "$1"
}

fetch_git() {
    local url=$1 commit=$2 repo
    [[ $commit =~ ^[0-9a-f]{40}$ ]] || die "Invalid Git commit: $commit"
    repo=$(git_cache "$commit")
    git init --bare --quiet "$repo"
    if ! git -C "$repo" cat-file -e "$commit^{commit}" 2>/dev/null; then
        git -C "$repo" fetch --quiet --depth=1 "$url" "$commit"
    fi
    git -C "$repo" update-ref refs/heads/pinned "$commit"
}

checkout_git() {
    local commit=$1 destination=$2 ignored_submodule=${3:-} repo submodules
    repo=$(git_cache "$commit")
    [[ -d $repo ]] || die "Missing Git input $commit. Run make fetch RELEASE=$release."
    git -c core.autocrlf=false clone --quiet --shared --no-checkout "$repo" "$destination"
    local objects=$destination/.git/objects
    realpath --relative-to="$objects" "$repo/objects" > "$objects/info/alternates"
    git -C "$destination" -c core.autocrlf=false checkout --quiet --detach "$commit"
    if [[ -f $destination/.gitmodules ]]; then
        submodules=$(git -C "$destination" ls-files --stage | awk '$1 == 160000 {print $4}')
        [[ -n $ignored_submodule && $submodules == "$ignored_submodule" ]] ||
            die "Record submodule sources explicitly for $commit."
    fi
}

verify_file() {
    local digest=$1 path=$2
    printf '%s  %s\n' "$digest" "$path" | sha256sum --check --status 2>/dev/null
}

fetch_files() {
    local manifest=$1 digest name url path
    while read -r digest name url; do
        path=$cache/$name
        if ! verify_file "$digest" "$path"; then
            curl --fail --location --silent --show-error --retry 3 --output "$path.part" "$url"
            verify_file "$digest" "$path.part" || die "SHA-256 mismatch: $name"
            mv "$path.part" "$path"
        fi
    done < "$manifest"
}

verify_files() {
    local manifest=$1 digest name url
    while read -r digest name url; do
        verify_file "$digest" "$cache/$name" || die "Missing or invalid input: $name"
    done < "$manifest"
}
