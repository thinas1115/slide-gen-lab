"""図解系スライド: AWS構成図・ステークホルダー調整図・体制図。"""
import math
from pathlib import Path

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

from generate import (ACCENT, BODY_TOP, BODY_BOTTOM, BODY_W, CANVAS, CORAL, GRAY,
                      LIGHT, MARGIN, NAVY, RULE, TEXT, WHITE, ZEBRA, add_rect, add_text,
                      header, note_line)
from textfit import line_height_in, text_width_in

ORANGE = RGBColor(0xE8, 0x7B, 0x1E)   # compute
GREEN = RGBColor(0x3F, 0x86, 0x24)    # storage
PURPLE = RGBColor(0x7D, 0x3F, 0x98)   # ML
LINE = RGBColor(0x6C, 0x73, 0x72)


def add_arrow(slide, x1, y1, x2, y2, *, color=LINE, width=1.5, both=False,
              dash=None):
    conn = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    conn.line.color.rgb = color
    conn.line.width = Pt(width)
    conn.shadow.inherit = False
    ln = conn.line._get_or_add_ln()
    heads = [("a:tailEnd", True), ("a:headEnd", both)]
    for tag, on in heads:
        if on:
            el = ln.makeelement(qn(tag), {"type": "triangle", "w": "med", "len": "med"})
            ln.append(el)
    if dash:
        d = ln.makeelement(qn("a:prstDash"), {"val": dash})
        ln.insert(0, d)
    return conn


def arrow_label(slide, cx, cy, text, w=1.6, size=9):
    """線をまたぐラベル。白背景マスクは実測テキスト幅に合わせ、wは上限として扱う
    (固定幅だと短い文字列ほど余計な範囲まで線を隠してしまうため)。
    """
    pad = 0.14
    actual_w = min(w, text_width_in(text, size) + pad)
    actual_h = line_height_in(size, 1.1) + 0.08
    tb = add_text(slide, cx - actual_w / 2, cy - actual_h / 2, actual_w, actual_h,
                  text, size, color=TEXT, align=PP_ALIGN.CENTER,
                  anchor=MSO_ANCHOR.MIDDLE)
    tb.fill.solid()
    tb.fill.fore_color.rgb = CANVAS
    return tb


def container(slide, x, y, w, h, label, color=LINE, dash=None):
    sp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                                Inches(w), Inches(h))
    sp.fill.background()
    sp.line.color.rgb = color
    sp.line.width = Pt(1.25)
    sp.shadow.inherit = False
    if dash:
        ln = sp.line._get_or_add_ln()
        ln.insert(0, ln.makeelement(qn("a:prstDash"), {"val": dash}))
    add_text(slide, x + 0.12, y + 0.06, w - 0.3, 0.28, label, 10.5, bold=True,
             color=color)


# ---- AWS構成図(公式アイコン使用) ----
ICON_DIR = Path(__file__).parent / "assets"
ICON_R = 0.31        # アイコン半径(0.62角の半分)
EDGE_GAP = 0.06      # 矢印端点とアイコン縁の隙間


def icon_node(slide, cx, cy, img, title, sub=None, size=0.62, *, label_above=False):
    """AWS公式スタイル: アイコン+直下にサービス名ラベル。"""
    p = ICON_DIR / img
    if not p.exists():
        raise FileNotFoundError(
            f"アイコン {img} が {ICON_DIR} にありません。extract_aws_icons.py で"
            f"AWS公式デッキを指定して生成するか、fetch_fluent_icons.py --list で同梱アイコンを確認して"
            f"ください。")
    slide.shapes.add_picture(str(p), Inches(cx - size / 2),
                             Inches(cy - size / 2), Inches(size), Inches(size))
    title_y = cy - size / 2 - 0.59 if label_above else cy + size / 2 + 0.05
    add_text(slide, cx - 1.05, title_y, 2.1, 0.28, title, 11,
             bold=True, color=NAVY, align=PP_ALIGN.CENTER)
    if sub:
        sub_y = cy - size / 2 - 0.31 if label_above else cy + size / 2 + 0.33
        add_text(slide, cx - 1.05, sub_y, 2.1, 0.26, sub, 9,
                 color=GRAY, align=PP_ALIGN.CENTER)


def right_of(cx):
    """アイコン右縁の矢印端点X。"""
    return cx + ICON_R + EDGE_GAP


def left_of(cx):
    return cx - ICON_R - EDGE_GAP


# (旧ハンドコード版 s_aws は diagram_layout.py + diagram_specs.py に移行済み)


# ---- ステークホルダー調整図(ハブ型) ----
def s_hub(slide, spec, page):
    header(slide, spec["kicker"], spec["title"])
    cx, cy = 6.67, 4.2
    hw, hh = 2.45, 1.05
    # 周辺ノード: (x, y, タイトル, 出す矢印ラベル, 戻り矢印ラベル)
    ring = spec["ring"]
    pos = [(2.15, 2.72), (11.18, 2.72),
           (2.15, 5.42), (11.18, 5.42),
           (6.67, 2.42), (6.67, 5.84)]

    # Connectors first: lines stay behind the icon and its labels.
    routes = []
    for (sx, sy), item in zip(pos, ring):
        dx, dy = cx - sx, cy - sy
        distance = math.hypot(dx, dy)
        ux, uy = dx / distance, dy / distance
        start_x, start_y = sx + ux * 0.34, sy + uy * 0.34
        ellipse_r = 1 / math.sqrt((ux / (hw / 2)) ** 2 + (uy / (hh / 2)) ** 2)
        end_x, end_y = cx - ux * ellipse_r, cy - uy * ellipse_r
        add_arrow(slide, start_x, start_y, end_x, end_y,
                  both=True, color=LINE, width=1.25)
        routes.append((start_x, start_y, end_x, end_y, item["label"]))

    for start_x, start_y, end_x, end_y, label in routes:
        arrow_label(slide, (start_x + end_x) / 2, (start_y + end_y) / 2,
                    label, w=2.1, size=10)

    for i, ((nx, ny), item) in enumerate(zip(pos, ring)):
        icon_node(slide, nx, ny, item["icon"], item["name"], item.get("sub"),
                  size=0.64, label_above=i == 4)

    # 中心ハブ
    sp = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - hw / 2), Inches(cy - hh / 2),
                                Inches(hw), Inches(hh))
    sp.fill.solid()
    sp.fill.fore_color.rgb = NAVY
    sp.line.fill.background()
    sp.shadow.inherit = False
    add_text(slide, cx - hw / 2, cy - 0.31, hw, 0.62, spec["hub"], 13.5, bold=True,
             color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    if spec.get("note"):
        note_line(slide, spec["note"])


# ---- 体制図 ----
def s_org(slide, spec, page):
    header(slide, spec["kicker"], spec["title"])

    def box(x, y, w, h, title, sub=None, fill=WHITE, tcolor=NAVY,
            border=LINE, members=None):
        add_rect(slide, x, y, w, h, fill, line=border)
        add_text(slide, x + 0.18, y + 0.16, w - 0.36, 0.32,
                 title, 12.5, bold=True, color=tcolor, align=PP_ALIGN.CENTER)
        if sub:
            add_text(slide, x + 0.18, y + 0.56, w - 0.36, 0.28, sub, 10,
                     color=GRAY if fill != NAVY else LIGHT, align=PP_ALIGN.CENTER)
        if members:
            add_rect(slide, x + 0.22, y + 0.94, w - 0.44, 0.01, RULE)
            add_text(slide, x + 0.2, y + 1.05, w - 0.4, 0.5,
                      "  /  ".join(members), 10, color=TEXT,
                     align=PP_ALIGN.CENTER)

    def vline(x, y1, y2):
        add_arrow(slide, x, y1, x, y2, width=1.25)

    cx = 6.67
    box(cx - 2.05, 1.86, 4.1, 0.86, spec["top"]["name"], spec["top"]["sub"],
        NAVY, WHITE, NAVY)
    vline(cx, 2.72, 3.08)
    box(cx - 2.05, 3.08, 4.1, 0.9, spec["pm"]["name"], spec["pm"]["sub"],
        WHITE, NAVY, ACCENT)
    teams = spec["teams"]
    n = len(teams)
    tw, gap = 3.25, 0.38
    total = n * tw + (n - 1) * gap
    x0 = cx - total / 2
    trunk_y = 4.35
    slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(cx), Inches(3.98),
                               Inches(cx), Inches(trunk_y)).line.color.rgb = LINE
    hl = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
                                    Inches(x0 + tw / 2), Inches(trunk_y),
                                    Inches(x0 + total - tw / 2), Inches(trunk_y))
    hl.line.color.rgb = LINE
    for i, t in enumerate(teams):
        x = x0 + i * (tw + gap)
        vline(x + tw / 2, trunk_y, 4.62)
        box(x, 4.62, tw, 1.62, t["name"], t["sub"], WHITE,
            NAVY, RULE, t.get("members", []))
    ex = spec["external"]
    box(10.6, 3.08, 2.05, 0.9, ex["name"], ex["sub"], ZEBRA, NAVY, RULE)
    add_arrow(slide, cx + 2.05, 3.53, 10.6, 3.53, dash="dash", width=1.25)
    arrow_label(slide, (cx + 2.05 + 10.6) / 2, 3.33, ex["label"], w=1.7)
    if spec.get("note"):
        note_line(slide, spec["note"])
