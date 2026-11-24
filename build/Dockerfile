FROM debian@sha256:ab3b3c8c5159eebfca4376430132d53c4d425f869c765ecbe47177a030da575d

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 TZ=UTC

RUN rm /etc/apt/sources.list.d/debian.sources \
    && echo 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20261123T000000Z/ trixie main' > /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        bc bison build-essential ca-certificates cpio curl e2fsprogs fakeroot file flex \
        gawk git kmod libelf-dev libssl-dev patch python-is-python3 python3 rsync xz-utils zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
