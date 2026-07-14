"""図解系スライド第2弾: プロセスタイムライン・ロードマップ・2軸マップ。"""
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from generate import (ACCENT, BODY_TOP, BODY_BOTTOM, BODY_W, CORAL, GRAY,
                      LIGHT, MARGIN, NAVY, RULE, TEXT, WHITE, ZEBRA, add_rect,
                      add_text, header, note_line)
from diagrams import LINE, add_arrow, arrow_label
from textfit import fit_font_size

MID = RGBColor(0x9D, 0xC3, 0xE6)


# ---- 番号付きプロセスタイムライン ----
def s_process(slide, spec, page):
    header(slide, spec["kicker"], spec["title"])
    steps = spec["steps"]
    n = len(steps)
    left, usable_w = 0.78, 11.72
    w = usable_w / n
    line_y = 2.48
    add_rect(slide, left + w / 2, line_y, usable_w - w, 0.035, RULE)
    for i, st in enumerate(steps):
        x = left + i * w
        cx = x + w / 2
        emph = i in spec.get("emph", [])
        color = CORAL if emph else (ACCENT if i % 2 == 0 else NAVY)
        sp = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, Inches(cx - 0.28), Inches(line_y - 0.26),
            Inches(0.56), Inches(0.56))
        sp.fill.solid()
        sp.fill.fore_color.rgb = color
        sp.line.fill.background()
        sp.shadow.inherit = False
        add_text(slide, cx - 0.28, line_y - 0.19, 0.56, 0.32, f"{i + 1:02d}",
                 11, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        add_text(slide, x + 0.12, 2.98, w - 0.24, 0.42, st["name"], 14.5,
                 bold=True, color=NAVY, align=PP_ALIGN.CENTER)
        size, _ = fit_font_size(st["desc"], w - 0.38, 1.55, 11.5, min_pt=9.5,
                                spacing=1.2)
        add_text(slide, x + 0.19, 3.58, w - 0.38, 1.55, st["desc"], size,
                 color=TEXT, align=PP_ALIGN.CENTER, spacing=1.2)
        add_rect(slide, x + 0.42, 5.45, w - 0.84, 0.035, color)
        add_text(slide, x + 0.15, 5.62, w - 0.3, 0.3, st["actor"], 9.5,
                 bold=True, color=color, align=PP_ALIGN.CENTER)
        if i < n - 1:
            add_rect(slide, x + w - 0.015, 3.0, 0.012, 2.4, RULE)
    if spec.get("note"):
        note_line(slide, spec["note"])


# ---- ロードマップ(ガントライト) ----
def s_roadmap(slide, spec, page):
    header(slide, spec["kicker"], spec["title"])
    months = spec["months"]
    label_w = 2.6
    grid_x = MARGIN + label_w
    grid_w = BODY_W - label_w
    mw = grid_w / len(months)
    top, hdr_h = BODY_TOP + 0.5, 0.46
    rows = spec["phases"]
    row_h = 1.15
    grid_h = hdr_h + len(rows) * row_h
    # 月ヘッダー
    for j, m in enumerate(months):
        add_rect(slide, grid_x + j * mw, top, mw - 0.02, hdr_h,
                 NAVY if j % 2 == 0 else ACCENT)
        add_text(slide, grid_x + j * mw, top + 0.07, mw - 0.02, 0.3, m, 10.5,
                 bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    # 縦グリッド線(バー・ラベルより先に描いて背面に置く)
    grid_h = hdr_h + len(rows) * row_h
    for j in range(1, len(months)):
        ln = add_arrow(slide, grid_x + j * mw, top + hdr_h,
                       grid_x + j * mw, top + grid_h, width=0.5)
        ln.line.color.rgb = RULE
        ln.line._get_or_add_ln().remove(ln.line._get_or_add_ln().find(
            "{http://schemas.openxmlformats.org/drawingml/2006/main}tailEnd"))
    # 行と帯
    for i, ph in enumerate(rows):
        ry = top + hdr_h + i * row_h
        add_rect(slide, MARGIN, ry, label_w - 0.1, row_h - 0.12,
                 WHITE if i % 2 == 0 else ZEBRA)
        add_rect(slide, MARGIN, ry, 0.07, row_h - 0.12,
                 ACCENT if i % 2 == 0 else CORAL)
        add_text(slide, MARGIN + 0.15, ry + 0.16, label_w - 0.4, 0.35, ph["name"],
                 11.5, bold=True, color=NAVY)
        add_text(slide, MARGIN + 0.15, ry + 0.54, label_w - 0.4, 0.35, ph["goal"],
                 8.5, color=GRAY)
        x1 = grid_x + ph["start"] * mw + 0.06
        x2 = grid_x + ph["end"] * mw - 0.06
        add_rect(slide, x1, ry + 0.26, x2 - x1, 0.46,
                 ACCENT if i % 2 == 0 else NAVY)
        add_text(slide, x1 + 0.12, ry + 0.32, x2 - x1 - 0.24, 0.32, ph["bar"], 9.5,
                 bold=True, color=WHITE)
    # マイルストーン(菱形)
    for ms in spec["milestones"]:
        mx = grid_x + ms["at"] * mw
        my = top + hdr_h + ms["row"] * row_h + 0.49
        d = 0.17
        sp = slide.shapes.add_shape(MSO_SHAPE.DIAMOND, Inches(mx - d / 2),
                                    Inches(my - d / 2), Inches(d), Inches(d))
        sp.fill.solid()
        sp.fill.fore_color.rgb = CORAL
        sp.line.fill.background()
        sp.shadow.inherit = False
        lcx = min(mx, MARGIN + BODY_W - 0.9)  # 右マージンをはみ出さない
        # バーの下段に白背景マスク付きで置く(背面のグリッド線を隠す)
        arrow_label(slide, lcx, my + 0.4, ms["label"], w=1.8, size=8.5)
    if spec.get("note"):
        note_line(slide, spec["note"])


# ---- 2軸ポジショニングマップ ----
def s_matrix(slide, spec, page):
    header(slide, spec["kicker"], spec["title"])
    ox, oy = 3.6, 6.35          # 原点(左下)
    aw, ah = 6.2, 4.15          # 軸の長さ
    # 象限背景(右上を強調)
    add_rect(slide, ox + aw / 2, oy - ah, aw / 2, ah / 2, LIGHT)
    # 軸
    add_arrow(slide, ox, oy, ox + aw, oy, width=1.75)
    add_arrow(slide, ox, oy, ox, oy - ah, width=1.75)
    add_text(slide, ox + aw - 2.5, oy - 0.44, 2.4, 0.3, spec["x_axis"], 10.5,
             bold=True, color=TEXT, align=PP_ALIGN.RIGHT)
    add_text(slide, ox - 0.42, oy - ah - 0.38, 3.0, 0.3, spec["y_axis"], 10.5,
             bold=True, color=TEXT)
    add_text(slide, ox + aw / 2 + 0.14, oy - ah + 0.1, 1.6, 0.3,
             spec["target_label"], 9.5, bold=True, color=ACCENT)
    # プロット
    for p in spec["points"]:
        px = ox + p["x"] * aw
        py = oy - p["y"] * ah
        r = 0.13
        sp = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(px - r), Inches(py - r),
                                    Inches(2 * r), Inches(2 * r))
        sp.fill.solid()
        sp.fill.fore_color.rgb = CORAL if p.get("emph") else ACCENT
        sp.line.color.rgb = WHITE
        sp.line.width = Pt(1.0)
        sp.shadow.inherit = False
        dx, dy = p.get("lx", 0.0), p.get("ly", -0.36)
        add_text(slide, px - 0.9 + dx, py + dy, 1.8, 0.28, p["name"], 9.5,
                 bold=bool(p.get("emph")), color=CORAL if p.get("emph") else TEXT,
                 align=PP_ALIGN.CENTER)
    if spec.get("note"):
        note_line(slide, spec["note"])
