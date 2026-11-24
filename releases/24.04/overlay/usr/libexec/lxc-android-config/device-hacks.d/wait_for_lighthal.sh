#!/bin/sh
# Noble can query Halium's HIDL service manager without entering the container.
if timeout 10 /usr/bin/python3 - <<'PY'
from time import sleep

import gbinder

manager = gbinder.ServiceManager("/dev/hwbinder")
light = "android.hardware.light@2.0::ILight/default"
while light not in (manager.list_sync() or ()):
    sleep(0.25)
PY
then
    echo "Android Light HAL is registered"
else
    echo "Timed out waiting for Android Light HAL" >&2
fi
