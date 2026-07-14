"""Fluentアイコン定義と同梱PNGの整合を検証する。"""
from PIL import Image

from fetch_fluent_icons import ICONS, OUT_DIR, PX


def main():
    expected = {f"{name}.png" for name in ICONS}
    actual = {path.name for path in OUT_DIR.glob("*.png")}
    assert actual == expected, (
        f"missing={sorted(expected - actual)}, extra={sorted(actual - expected)}")

    for name in sorted(expected):
        with Image.open(OUT_DIR / name) as image:
            assert image.format == "PNG", name
            assert image.size == (PX, PX), f"{name}: {image.size}"
            image.verify()
    print(f"OK: {len(expected)} Fluent icons match the catalog and are valid PNGs")


if __name__ == "__main__":
    main()
