"""図解系スライド第2弾: プロセスタイムライン・ロードマップ・2軸マップ。"""
import re

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from generate import (ACCENT, BODY_W, CANVAS, CORAL, GRAY,
                      LIGHT, MARGIN, NAVY, RULE, TEXT, WHITE, ZEBRA, ContentArea,
                      add_rect, add_text, header, note_line)
from diagrams import LINE, add_arrow, arrow_label
from layout_fit import FitError, ensure_within, fit_text_or_raise, select_fit, stepped

MID = RGBColor(0x9D, 0xC3, 0xE6)


# ---- 番号付きプロセスタイムライン ----
def s_process(slide, spec, page):
    area = header(slide, spec["kicker"], spec["title"], spec.get("lead"))
    if spec.get("note") and area.shifted:
        area = ContentArea(area.top, area.bottom - 0.30, area.shifted)
    y = area.map_y
    steps = spec["steps"]
    n = len(steps)
    if not 3 <= n <= 6:
        raise FitError(
            "process: 工程は3〜6件までです。工程を統合または分割してください。")
    left, usable_w = 0.78, 11.72
    w = usable_w / n
    line_y = y(2.42)
    add_rect(slide, left + w / 2, line_y, usable_w - w, 0.035, RULE)
    for i, st in enumerate(steps):
        x = left + i * w
        cx = x + w / 2
        emph = i in spec.get("emph", [])
        color = ACCENT if emph else NAVY
        sp = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, Inches(cx - 0.31), Inches(line_y - 0.29),
            Inches(0.62), Inches(0.62))
        sp.fill.solid()
        sp.fill.fore_color.rgb = color
        sp.line.fill.background()
        sp.shadow.inherit = False
        add_text(slide, cx - 0.31, line_y - 0.2, 0.62, 0.32, f"{i + 1:02d}",
                 11.5, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        name_size, name_lines = fit_text_or_raise(
            "process", f"steps[{i}].name", st["name"], w - 0.2, 0.42,
            15.5, min_pt=12.5, weight="bold", spacing=1.1)
        add_text(slide, x + 0.1, y(2.94), w - 0.2, 0.42,
                 st["name"], name_size,
                 bold=True, color=NAVY, align=PP_ALIGN.CENTER)
        size, desc_lines = fit_text_or_raise(
            "process", f"steps[{i}].desc", st["desc"],
            w - 0.34, 1.35, 13.5, min_pt=11.5, spacing=1.2)
        add_text(slide, x + 0.17, y(3.56), w - 0.34, 1.35,
                 st["desc"], size,
                 color=TEXT, align=PP_ALIGN.CENTER, spacing=1.2)
        add_text(slide, x + 0.15, y(5.27), w - 0.3, 0.22, "OWNER", 9.5,
                 bold=True, color=GRAY, align=PP_ALIGN.CENTER)
        actor_size, actor_lines = fit_text_or_raise(
            "process", f"steps[{i}].actor", st["actor"],
            w - 0.3, 0.3, 11.5, min_pt=9.5, weight="bold", spacing=1.1)
        add_text(slide, x + 0.15, y(5.56), w - 0.3, 0.3,
                 st["actor"], actor_size,
                 bold=True, color=color, align=PP_ALIGN.CENTER)
    ensure_within(
        "process", y(5.86) - area.top, area.height,
        guidance="工程説明を短くしてください。")
    if spec.get("note"):
        note_line(slide, spec["note"])


# ---- ロードマップ(ガントライト) ----
def s_roadmap(slide, spec, page):
    area = header(slide, spec["kicker"], spec["title"], spec.get("lead"))
    months = spec["months"]
    label_x, label_w = 0.76, 2.34
    grid_x = 3.34
    grid_w = 9.22
    mw = grid_w / len(months)
    top, hdr_h = area.top + 0.4, 0.52
    rows = spec["phases"]
    if not 1 <= len(rows) <= 3:
        raise FitError(
            "roadmap: フェーズは1〜3件までです。フェーズを統合してください。")
    available = area.bottom - top - (0.30 if spec.get("note") else 0)

    def candidates():
        for row_h in stepped(1.22, 1.04, 0.03):
            used = hdr_h + len(rows) * row_h
            yield ("standard" if row_h == 1.22 else "row_gap",
                   {"row_h": row_h}, used)

    fitted = select_fit(
        "roadmap", available, candidates(),
        guidance="フェーズ数を減らしてください。",
    )
    row_h = fitted.values["row_h"]
    grid_h = hdr_h + len(rows) * row_h
    add_rect(slide, grid_x, top, grid_w, hdr_h, NAVY)
    for j, m in enumerate(months):
        month_size, month_lines = fit_text_or_raise(
            "roadmap", f"months[{j}]", m, mw, 0.3, 10.5,
            min_pt=8.5, weight="bold", spacing=1.1)
        add_text(slide, grid_x + j * mw, top + 0.08, mw, 0.3,
                 m, month_size,
                 bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        if j:
            add_rect(slide, grid_x + j * mw, top + 0.08, 0.01, hdr_h - 0.16, GRAY)
    for j in range(1, len(months)):
        line = slide.shapes.add_connector(
            MSO_CONNECTOR.STRAIGHT, Inches(grid_x + j * mw), Inches(top + hdr_h),
            Inches(grid_x + j * mw), Inches(top + grid_h))
        line.line.color.rgb = RULE
        line.line.width = Pt(0.6)
        line.shadow.inherit = False
    for i, ph in enumerate(rows):
        ry = top + hdr_h + i * row_h
        phase_name = re.sub(r"^Phase\s*\d+\s*", "", ph["name"], flags=re.I)
        phase_name = phase_name or ph["name"]
        add_text(slide, label_x, ry + 0.16, 0.38, 0.3, f"{i + 1:02d}",
                 11.5, bold=True, color=GRAY)
        phase_size, phase_lines = fit_text_or_raise(
            "roadmap", f"phases[{i}].name", phase_name,
            label_w - 0.5, 0.34, 14, min_pt=11.5,
            weight="bold", spacing=1.1)
        add_text(slide, label_x + 0.5, ry + 0.11, label_w - 0.5, 0.34,
                 phase_name, phase_size, bold=True, color=NAVY)
        goal_size, goal_lines = fit_text_or_raise(
            "roadmap", f"phases[{i}].goal", ph["goal"],
            label_w - 0.5, 0.27, 10.5, min_pt=8.5, spacing=1.1)
        add_text(slide, label_x + 0.5, ry + 0.52, label_w - 0.5, 0.27,
                 ph["goal"], goal_size, color=GRAY)
        x1 = grid_x + ph["start"] * mw + 0.06
        x2 = grid_x + ph["end"] * mw - 0.06
        add_rect(slide, x1, ry + 0.34, x2 - x1, 0.42,
                 ACCENT if i != 1 else NAVY)
        bar_size, bar_lines = fit_text_or_raise(
            "roadmap", f"phases[{i}].bar", ph["bar"],
            x2 - x1 - 0.24, 0.3, 10.5,
            min_pt=8.5, weight="bold", spacing=1.1)
        add_text(slide, x1 + 0.12, ry + 0.39, x2 - x1 - 0.24, 0.3,
                 ph["bar"], bar_size,
                 bold=True, color=WHITE)
    for ms in spec["milestones"]:
        mx = grid_x + ms["at"] * mw
        my = top + hdr_h + ms["row"] * row_h + 0.55
        d = 0.17
        sp = slide.shapes.add_shape(MSO_SHAPE.DIAMOND, Inches(mx - d / 2),
                                    Inches(my - d / 2), Inches(d), Inches(d))
        sp.fill.solid()
        sp.fill.fore_color.rgb = CORAL
        sp.line.fill.background()
        sp.shadow.inherit = False
        lcx = min(mx, MARGIN + BODY_W - 0.9)
        label = arrow_label(slide, lcx, my + 0.38, ms["label"], w=1.8, size=9.5)
        label.fill.fore_color.rgb = CANVAS
    if spec.get("note"):
        note_line(slide, spec["note"])


# ---- 2軸ポジショニングマップ ----
def s_matrix(slide, spec, page):
    area = header(slide, spec["kicker"], spec["title"], spec.get("lead"))
    if spec.get("note") and area.shifted:
        area = ContentArea(area.top, area.bottom - 0.30, area.shifted)
    y = area.map_y
    if not 1 <= len(spec["points"]) <= 8:
        raise FitError(
            "matrix: 点は1〜8件までです。点をまとめるかスライドを分割してください。")
    ox, oy = 1.68, y(6.24)
    aw, ah = 10.5, oy - y(2.22)
    mid_x, mid_y = ox + aw / 2, oy - ah / 2

    quadrants = spec.get("quadrants")
    if quadrants:
        # Explicit region names make the highlighted quadrant semantic. Existing
        # matrix specs without them retain the neutral scatter-plot treatment.
        add_rect(slide, ox, oy - ah, aw, ah, WHITE, line=RULE)
        add_rect(slide, mid_x, oy - ah, aw / 2, ah / 2, LIGHT)
        qlabels = [
            (ox + 0.18, oy - 0.42, 2.2, quadrants[0], PP_ALIGN.LEFT, GRAY),
            (ox + aw - 2.38, oy - 0.42, 2.2, quadrants[1], PP_ALIGN.RIGHT, GRAY),
            (ox + 0.18, oy - ah + 0.18, 2.2, quadrants[2], PP_ALIGN.LEFT, GRAY),
            (ox + aw - 2.38, oy - ah + 0.18, 2.2, quadrants[3], PP_ALIGN.RIGHT, ACCENT),
        ]
        for idx, (x, y, w, label, align, color) in enumerate(qlabels):
            label_size, _ = fit_text_or_raise(
                "matrix", f"quadrants[{idx}]", label, w, 0.3, 10.5,
                min_pt=8.5, weight="bold", spacing=1.1)
            add_text(slide, x, y, w, 0.3, label, label_size, bold=True,
                     color=color, align=align)
    else:
        target_size, _ = fit_text_or_raise(
            "matrix", "target_label", spec["target_label"], 2.0, 0.3, 10.5,
            min_pt=8.5, weight="bold", spacing=1.1)
        add_text(slide, mid_x + 0.18, oy - ah + 0.16, 2.0, 0.3,
                 spec["target_label"], target_size, bold=True, color=ACCENT)

    add_arrow(slide, ox, oy, ox + aw, oy, width=1.75)
    add_arrow(slide, ox, oy, ox, oy - ah, width=1.75)
    x_axis_size, _ = fit_text_or_raise(
        "matrix", "x_axis", spec["x_axis"], 2.4, 0.3, 11.5,
        min_pt=9.5, weight="bold", spacing=1.1)
    y_axis_size, _ = fit_text_or_raise(
        "matrix", "y_axis", spec["y_axis"], 3.0, 0.3, 11.5,
        min_pt=9.5, weight="bold", spacing=1.1)
    add_text(slide, ox + aw - 2.5, oy + 0.16, 2.4, 0.3, spec["x_axis"], x_axis_size,
             bold=True, color=TEXT, align=PP_ALIGN.RIGHT)
    add_text(slide, ox - 0.02, oy - ah - 0.38, 3.0, 0.3, spec["y_axis"], y_axis_size,
             bold=True, color=TEXT)
    for p in spec["points"]:
        px = ox + p["x"] * aw
        py = oy - p["y"] * ah
        r = 0.15
        sp = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(px - r), Inches(py - r),
                                    Inches(2 * r), Inches(2 * r))
        sp.fill.solid()
        sp.fill.fore_color.rgb = CORAL if p.get("emph") else ACCENT
        sp.line.color.rgb = WHITE
        sp.line.width = Pt(1.0)
        sp.shadow.inherit = False
        dx, dy = p.get("lx", 0.0), p.get("ly", -0.36)
        point_size, point_lines = fit_text_or_raise(
            "matrix", "points.name", p["name"], 2.0, 0.3, 11,
            min_pt=9, weight="bold" if p.get("emph") else "regular",
            spacing=1.1)
        add_text(slide, px - 1.0 + dx, py + dy, 2.0, 0.3,
                 p["name"], point_size,
                 bold=bool(p.get("emph")), color=CORAL if p.get("emph") else TEXT,
                 align=PP_ALIGN.CENTER)
    ensure_within(
        "matrix", oy - area.top, area.height,
        guidance="軸ラベルまたは点の名称を短くしてください。")
    if spec.get("note"):
        note_line(slide, spec["note"])
