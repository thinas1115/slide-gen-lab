"""Fluent UI System Icons (MIT) を取得し、図解用PNGに変換して assets/fluent/ に置く。

使い方:
  python fetch_fluent_icons.py          # ICONS 全部
  python fetch_fluent_icons.py server database   # 指定分のみ

- 出典: https://github.com/microsoft/fluentui-system-icons (MITライセンス)。
  PowerPointの「挿入 > アイコン」と同じデザイン体系のアイコンセット。
- python-pptx はSVGを挿入できない(PIL依存)ため、svglib+reportlab でPNG化する。
  依存: pip install svglib reportlab rlPyCairo
  (rlPyCairo は reportlab 4.x のPNG描画バックエンド。無いと RenderPMError になる)
- 生成したPNGは assets/CREDITS.md のクレジット表記とともにリポジトリに同梱する
  (MITライセンス。リカラー等の改変も許諾範囲内)。
- diagram仕様からは "icon": "fluent/server.png" のように参照する。

アイコンを増やしたいときは ICONS に 出力名: リポジトリのassetsフォルダ名 を
追加する。フォルダ名は https://github.com/microsoft/fluentui-system-icons/tree/main/assets
で探す(例: "Lock Closed" のようにスペース入り)。
"""
import io
import re
import sys
import urllib.request
from pathlib import Path

from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg

# 出力名 → fluentui-system-icons/assets/ のフォルダ名
ICONS = {
    "server": "Server",
    "router": "Router",
    "shield": "Shield",            # FW・セキュリティ
    "database": "Database",
    "desktop": "Desktop",
    "laptop": "Laptop",
    "people": "People",
    "person": "Person",
    "building": "Building",
    "branch": "Building Multiple",  # 拠点・支社
    "cloud": "Cloud",
    "globe": "Globe",              # インターネット
    "alert": "Alert",
    "mail": "Mail",
    "phone": "Phone",
    "wrench": "Wrench",            # 保守・運用
    "lock": "Lock Closed",
    "switch": "Arrow Swap",        # L2/L3スイッチ・経路交換
    "monitor": "Pulse",            # 監視・ヘルスチェック
}

BASE = ("https://raw.githubusercontent.com/microsoft/fluentui-system-icons/"
        "main/assets/{folder}/SVG/ic_fluent_{slug}_24_regular.svg")
COLOR = "#1F3864"   # generate.py の NAVY と合わせる
PX = 256            # 出力PNGの一辺(スライド上は0.62in≒60-120px で使うので十分)
OUT_DIR = Path(__file__).parent / "assets" / "fluent"


def fetch_svg(folder: str) -> str:
    slug = folder.lower().replace(" ", "_")
    url = BASE.format(folder=urllib.request.quote(folder), slug=slug)
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode("utf-8")


def to_png(svg_text: str, out_path: Path):
    # Fluentのパス色(#212121 / currentColor)をスライドの配色に置換
    svg_text = svg_text.replace("#212121", COLOR).replace("currentColor", COLOR)
    m = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg_text)
    natural = int(m.group(1)) if m else 24
    drawing = svg2rlg(io.StringIO(svg_text))
    scale = PX / natural
    drawing.scale(scale, scale)
    drawing.width = drawing.height = PX
    renderPM.drawToFile(drawing, str(out_path), fmt="PNG")


def main(names):
    targets = {n: ICONS[n] for n in names} if names else ICONS
    unknown = [n for n in (names or []) if n not in ICONS]
    if unknown:
        raise SystemExit(f"未定義のアイコン名: {unknown}. ICONS に追加してください。"
                         f" 定義済み: {', '.join(sorted(ICONS))}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for out_name, folder in targets.items():
        out_path = OUT_DIR / f"{out_name}.png"
        to_png(fetch_svg(folder), out_path)
        print(f"wrote {out_path} ({folder})")
    print(f"done: {len(targets)} icons -> {OUT_DIR}")


if __name__ == "__main__":
    main(sys.argv[1:])
