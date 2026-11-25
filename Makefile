RELEASE ?= 20.04
KERNEL ?= 3.18
WORK_DIR ?= $(CURDIR)/work
IMAGE ?= s7-ubuntu-touch-builder
WORK := $(abspath $(WORK_DIR))
RUN = docker run --rm --pull=never --platform linux/amd64 --hostname s7-builder \
	--user "$$(id -u):$$(id -g)" --env HOME=/tmp \
	--mount "type=bind,source=$(CURDIR),target=/src,readonly" \
	--mount "type=bind,source=$(WORK),target=/work" --workdir /src \
	--env WORK_DIR=/work --env S7_JOBS --env S7_BOOT_CONSOLE --env KERNEL="$(KERNEL)"

.PHONY: image fetch build kernel test
image:
	docker build --platform linux/amd64 --tag "$(IMAGE)" --file build/Dockerfile build

fetch:
	mkdir -p "$(WORK)"
	$(RUN) "$(IMAGE)" ./s7 fetch "$(RELEASE)"

build:
	mkdir -p "$(WORK)"
	$(RUN) --network none "$(IMAGE)" ./s7 build "$(RELEASE)"

kernel:
	mkdir -p "$(WORK)"
	$(RUN) --network none "$(IMAGE)" ./s7 kernel "$(RELEASE)"

test:
	python3 -IB ubuntu-touch/tests/offline.py
