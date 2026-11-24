"""Read the Galaxy S7 navigation buttons without grabbing their input devices."""

from contextlib import ExitStack
import os
from pathlib import Path
from select import select
from threading import Thread

from evdev import InputDevice, ecodes, list_devices
import pyotherside

KEY_LIGHT = Path("/sys/class/sec/sec_touchkey/brightness")
RECENT = 254  # Samsung KEY_RECENT has no XKB mapping.
KEY_CODES_BY_DEVICE = {
    "gpio_keys": {ecodes.KEY_HOMEPAGE},
    "sec_touchkey": {ecodes.KEY_BACK, RECENT},
}


def set_light(enabled):
    KEY_LIGHT.write_text("1\n" if enabled else "0\n")


def read_buttons(shutdown_read_fd):
    try:
        with ExitStack() as cleanup:
            inputs = {}
            for path in list_devices():
                device = InputDevice(path)
                key_codes = KEY_CODES_BY_DEVICE.get(device.name)
                if key_codes is None:
                    device.close()
                    continue
                cleanup.callback(device.close)
                inputs[device.fd] = (device, key_codes)
            if len(inputs) != len(KEY_CODES_BY_DEVICE):
                raise RuntimeError("S7 navigation input devices are missing")

            while True:
                ready, _, _ = select([shutdown_read_fd, *inputs], [], [])
                if shutdown_read_fd in ready:
                    return
                for fd in ready:
                    device, key_codes = inputs[fd]
                    for event in device.read():
                        if (event.type == ecodes.EV_KEY and event.value == 1
                                and event.code in key_codes):
                            is_recent = event.code == RECENT
                            is_capacitive = event.code != ecodes.KEY_HOMEPAGE
                            pyotherside.send("herolte-button", is_recent, is_capacitive)
    except (OSError, RuntimeError) as exc:
        pyotherside.send("herolte-navigation-error", str(exc))


def start():
    shutdown_read_fd, shutdown_write_fd = os.pipe()
    worker = Thread(target=read_buttons, args=(shutdown_read_fd,), daemon=True)

    def stop():
        # Closing the write end wakes select() on the read end.
        os.close(shutdown_write_fd)
        worker.join()
        os.close(shutdown_read_fd)
        set_light(False)

    pyotherside.atexit(stop)
    worker.start()
    set_light(False)
