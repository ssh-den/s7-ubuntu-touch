from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "build"))
from release import build_release
from system_image import add_layer


def render(archive, inputs, overlay):
    for path in (inputs["rootfs"], inputs["device"], overlay, inputs["version"]):
        add_layer(archive, path)


if __name__ == "__main__":
    build_release(Path(__file__).resolve(), "20.04-1560", 3000, render)
