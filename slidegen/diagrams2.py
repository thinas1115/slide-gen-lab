"""図解系スライド第2弾: プロセスタイムライン・ロードマップ・2軸マップ。"""
import re

from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from generate import (ACCENT, CORAL, GRAY, LIGHT, NAVY, RULE, TEXT, WHITE,
                      ZEBRA, ContentArea, add_rect, add_text, header, note_line)
from diagrams import add_arrow
from layout_fit import FitError, ensure_within, fit_text_or_raise
from textfit import text_width_in
from timeline_layout import (fit_program_roadmap, fit_roadmap, pack_activities,
                             resolve_marker, resolve_span)

PROGRAM_LINE_PT = 1.4


def _grid_line(slide, x1, y1, x2, y2):
    """表の罫線を本文より先に描き、後続のラベルマスクを有効にする。"""
    line = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    line.line.color.rgb = RULE
    line.line.width = Pt(0.6)
    line.shadow.inherit = False
    return line


def _activity_line(slide, x1, y, x2, color):
    """工程表の作業期間を描く。矩形ではなく固定pt幅で見え方を揃える。"""
    line = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y), Inches(x2), Inches(y))
    line.line.color.rgb = color
    line.line.width = Pt(PROGRAM_LINE_PT)
    line.shadow.inherit = False
    return line


def _fit_single_line(renderer, field, text, width, max_pt, min_pt, *, bold=False):
    """工程表ラベルを折り返さず、幅へ収まるサイズまで縮小する。"""
    size = max_pt
    weight = "bold" if bold else "regular"
    while size >= min_pt - 0.01:
        if text_width_in(text, size, weight) <= width:
            return size
        size -= 0.5
    raise FitError(
        f"{renderer}.{field}: 1行ラベルが最小フォント{min_pt:g}ptでも"
        f"幅{width:.2f}inに収まりません。文言を短くするか期間を広げてください。"
    )


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


# ---- ロードマップ(フェーズ単位) ----
def s_roadmap(slide, spec, page):
    area = header(slide, spec["kicker"], spec["title"], spec.get("lead"))
    months = spec["months"]
    if not 3 <= len(months) <= 12:
        raise FitError(
            "roadmap: 期間は3〜12件までです。期間をまとめるか分割してください。")
    label_x, label_w = 0.72, 2.65
    grid_x, grid_w = label_x + label_w, 9.22
    mw = grid_w / len(months)
    rows = spec["phases"]
    if not 1 <= len(rows) <= 6:
        raise FitError(
            "roadmap: フェーズは1〜6件までです。フェーズを分割してください。")
    fitted = fit_roadmap(area.height, len(rows), has_note=bool(spec.get("note")))
    values = fitted.values
    top = area.top + values["top_gap"]
    hdr_h, row_h = values["header_h"], values["row_h"]
    grid_h = hdr_h + len(rows) * row_h
    add_rect(slide, label_x, top, label_w, hdr_h, NAVY)
    add_text(slide, label_x + 0.18, top + 0.08, label_w - 0.36, 0.28,
             "フェーズ", values["period_pt"], bold=True, color=WHITE)
    add_rect(slide, grid_x, top, grid_w, hdr_h, NAVY)
    for j, m in enumerate(months):
        month_size, _ = fit_text_or_raise(
            "roadmap", f"months[{j}]", m, mw, 0.3, values["period_pt"],
            min_pt=values["period_pt"], weight="bold", spacing=1.1)
        add_text(slide, grid_x + j * mw, top + 0.08, mw, 0.3,
                 m, month_size,
                 bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        if j:
            add_rect(slide, grid_x + j * mw, top + 0.08, 0.01, hdr_h - 0.16, GRAY)
    for i in range(len(rows)):
        ry = top + hdr_h + i * row_h
        add_rect(slide, label_x, ry, label_w + grid_w, row_h,
                 WHITE if i % 2 == 0 else ZEBRA)
    for j in range(len(months) + 1):
        _grid_line(slide, grid_x + j * mw, top + hdr_h,
                   grid_x + j * mw, top + grid_h)
    for i in range(len(rows) + 1):
        _grid_line(slide, label_x, top + hdr_h + i * row_h,
                   label_x + label_w + grid_w, top + hdr_h + i * row_h)
    for i, ph in enumerate(rows):
        ry = top + hdr_h + i * row_h
        phase_name = re.sub(r"^Phase\s*\d+\s*", "", ph["name"], flags=re.I)
        phase_name = phase_name or ph["name"]
        name_h = min(0.27, row_h * 0.42)
        goal_h = min(0.20, row_h * 0.30)
        add_text(slide, label_x + 0.12, ry + row_h * 0.18, 0.34, name_h,
                 f"{i + 1:02d}", values["name_pt"], bold=True,
                 color=ACCENT)
        phase_size, _ = fit_text_or_raise(
            "roadmap", f"phases[{i}].name", phase_name,
            label_w - 0.62, name_h, values["name_pt"], min_pt=8.5,
            weight="bold", spacing=1.1)
        add_text(slide, label_x + 0.52, ry + row_h * 0.12,
                 label_w - 0.64, name_h,
                 phase_name, phase_size, bold=True, color=NAVY)
        goal_size, _ = fit_text_or_raise(
            "roadmap", f"phases[{i}].goal", ph["goal"],
            label_w - 0.64, goal_h, values["goal_pt"],
            min_pt=7.0, spacing=1.05)
        add_text(slide, label_x + 0.52, ry + row_h * 0.56,
                 label_w - 0.64, goal_h,
                 ph["goal"], goal_size, color=GRAY)
        start, end = resolve_span(ph, months)
        x1 = grid_x + start * mw + 0.05
        x2 = grid_x + end * mw - 0.05
        bar_y = ry + row_h * 0.24
        add_rect(slide, x1, bar_y, x2 - x1, values["bar_h"],
                 ACCENT if i != 1 else NAVY)
        bar_size, _ = fit_text_or_raise(
            "roadmap", f"phases[{i}].bar", ph["bar"],
            x2 - x1 - 0.18, values["bar_h"] - 0.04,
            values["bar_pt"], min_pt=7.5, weight="bold", spacing=1.05)
        add_text(slide, x1 + 0.09, bar_y + 0.035, x2 - x1 - 0.18,
                 values["bar_h"] - 0.04,
                 ph["bar"], bar_size,
                 bold=True, color=WHITE)
    for ms in spec["milestones"]:
        mx = grid_x + resolve_marker(ms["at"], months) * mw
        ry = top + hdr_h + ms["row"] * row_h
        my = ry + min(0.09, row_h * 0.14)
        d = min(0.15, values["bar_h"] * 0.58)
        sp = slide.shapes.add_shape(MSO_SHAPE.DIAMOND, Inches(mx - d / 2),
                                    Inches(my - d / 2), Inches(d), Inches(d))
        sp.fill.solid()
        sp.fill.fore_color.rgb = CORAL
        sp.line.fill.background()
        sp.shadow.inherit = False
        label_w = min(1.5, max(0.72, mw * 1.6))
        lcx = min(max(mx, grid_x + label_w / 2), grid_x + grid_w - label_w / 2)
        label_size, _ = fit_text_or_raise(
            "roadmap", "milestones.label", ms["label"], label_w,
            min(0.18, row_h * 0.28), values["milestone_pt"],
            min_pt=6.8, spacing=1.0)
        label = add_text(slide, lcx - label_w / 2, ry + row_h * 0.68,
                         label_w, min(0.18, row_h * 0.28), ms["label"],
                         label_size, color=TEXT, align=PP_ALIGN.CENTER,
                         spacing=1.0)
        label.fill.solid()
        label.fill.fore_color.rgb = WHITE if ms["row"] % 2 == 0 else ZEBRA
    if spec.get("note"):
        note_line(slide, spec["note"])


# ---- 複数テーマ・複数作業のプログラム工程表 ----
def s_program_roadmap(slide, spec, page):
    area = header(slide, spec["kicker"], spec["title"], spec.get("lead"))
    periods = spec["periods"]
    tracks = spec["tracks"]
    if not 3 <= len(periods) <= 12:
        raise FitError(
            "program_roadmap: 期間は3〜12件までです。期間をまとめてください。")
    if not 1 <= len(tracks) <= 6:
        raise FitError(
            "program_roadmap: テーマは1〜6件までです。複数スライドへ分割してください。")

    packed = [pack_activities(track["activities"], periods) for track in tracks]
    lane_counts = [lane_count for _placements, lane_count in packed]
    fitted = fit_program_roadmap(
        area.height, lane_counts, has_note=bool(spec.get("note")))
    values = fitted.values

    label_x, track_col_w = 0.72, 2.78
    grid_x, grid_w = label_x + track_col_w, 9.09
    period_w = grid_w / len(periods)
    top = area.top + values["top_gap"]
    header_h = values["header_h"]
    row_heights = [
        2 * values["track_pad"] + count * values["lane_pitch"]
        for count in lane_counts
    ]
    grid_h = header_h + sum(row_heights) + values["track_gap"] * (len(tracks) - 1)

    add_rect(slide, label_x, top, track_col_w, header_h, NAVY)
    add_text(slide, label_x + 0.18, top + 0.07, track_col_w - 0.36, 0.28,
             "テーマ", values["period_pt"], bold=True, color=WHITE)
    add_rect(slide, grid_x, top, grid_w, header_h, NAVY)
    for index, period in enumerate(periods):
        size, _ = fit_text_or_raise(
            "program_roadmap", f"periods[{index}]", period,
            period_w - 0.04, 0.28, values["period_pt"],
            min_pt=7.5, weight="bold", spacing=1.0)
        add_text(slide, grid_x + index * period_w, top + 0.07,
                 period_w, 0.28, period, size, bold=True, color=WHITE,
                 align=PP_ALIGN.CENTER, spacing=1.0)

    row_tops = []
    cursor = top + header_h
    for index, row_h in enumerate(row_heights):
        row_tops.append(cursor)
        add_rect(slide, label_x, cursor, track_col_w + grid_w, row_h,
                 WHITE if index % 2 == 0 else ZEBRA)
        cursor += row_h + values["track_gap"]

    body_top = top + header_h
    for index in range(len(periods) + 1):
        _grid_line(slide, grid_x + index * period_w, body_top,
                   grid_x + index * period_w, top + grid_h)
    for index, row_top in enumerate(row_tops):
        _grid_line(slide, label_x, row_top,
                   label_x + track_col_w + grid_w, row_top)
        track = tracks[index]
        row_h = row_heights[index]
        add_text(slide, label_x + 0.12, row_top + 0.11, 0.38, 0.25,
                 f"{index + 1:02d}", values["track_pt"], bold=True,
                 color=ACCENT)
        track_size = _fit_single_line(
            "program_roadmap", f"tracks[{index}].name", track["name"],
            track_col_w - 0.66, values["track_pt"], 8.5, bold=True)
        add_text(slide, label_x + 0.52, row_top + 0.09,
                 track_col_w - 0.66, min(0.28, row_h - 0.14),
                 track["name"], track_size, bold=True, color=NAVY,
                 spacing=1.0, wrap=False)

        placements, _lane_count = packed[index]
        lane_neighbors = {}
        for lane in range(_lane_count):
            lane_items = sorted(
                (placement for placement in placements if placement.lane == lane),
                key=lambda placement: (placement.start, placement.end),
            )
            for position, placement in enumerate(lane_items):
                previous = lane_items[position - 1] if position else None
                following = lane_items[position + 1] if position + 1 < len(lane_items) else None
                lane_neighbors[placement.index] = (previous, following)
        for placement in placements:
            activity = placement.activity
            lane_top = (row_top + values["track_pad"]
                        + placement.lane * values["lane_pitch"])
            x1 = grid_x + placement.start * period_w + 0.035
            x2 = grid_x + placement.end * period_w - 0.035
            color = CORAL if activity.get("emph") else ACCENT
            _activity_line(slide, x1, lane_top + 0.035, x2, color)
            text_h = values["lane_pitch"] - 0.07
            previous, following = lane_neighbors[placement.index]
            left_bound = grid_x if previous is None else (
                grid_x + (previous.end + placement.start) * period_w / 2)
            right_bound = grid_x + grid_w if following is None else (
                grid_x + (placement.end + following.start) * period_w / 2)
            available_label_w = right_bound - left_bound
            activity_label_w = min(1.45, available_label_w)
            label_center = (x1 + x2) / 2
            activity_label_x = min(
                max(label_center - activity_label_w / 2, left_bound),
                right_bound - activity_label_w,
            )
            activity_size = _fit_single_line(
                "program_roadmap",
                f"tracks[{index}].activities[{placement.index}].label",
                activity["label"], activity_label_w - 0.04,
                values["activity_pt"], 7.5,
                bold=bool(activity.get("emph")))
            label = add_text(
                slide, activity_label_x + 0.02, lane_top + 0.07,
                activity_label_w - 0.04, text_h, activity["label"], activity_size,
                bold=bool(activity.get("emph")), color=TEXT,
                align=PP_ALIGN.CENTER, spacing=1.0, wrap=False)
            label.fill.solid()
            label.fill.fore_color.rgb = WHITE if index % 2 == 0 else ZEBRA
    _grid_line(slide, label_x, cursor - values["track_gap"],
               label_x + track_col_w + grid_w, cursor - values["track_gap"])
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
