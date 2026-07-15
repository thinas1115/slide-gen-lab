"""システムA: python-pptx + テキスト実測によるスライド生成。"""
import re
import sys

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

from content import DECK
from textfit import fit_font_size, line_height_in, wrap_text

# ---- テーマ ----
NAVY = RGBColor(0x18, 0x2C, 0x43)
ACCENT = RGBColor(0x0D, 0x78, 0x70)
CORAL = RGBColor(0xC7, 0x58, 0x3E)
LIGHT = RGBColor(0xDF, 0xEB, 0xE8)
TEXT = RGBColor(0x20, 0x27, 0x29)
GRAY = RGBColor(0x66, 0x6E, 0x70)
WHITE = RGBColor(0xFF, 0xFF, 0xFC)
ZEBRA = RGBColor(0xEC, 0xEA, 0xE4)
CANVAS = RGBColor(0xF7, 0xF5, 0xEF)
RULE = RGBColor(0xD1, 0xCF, 0xC8)
FONT = "Yu Gothic"
SLIDE_W, SLIDE_H = 13.333, 7.5
MARGIN = 0.55
BODY_W = SLIDE_W - MARGIN * 2
BODY_TOP, BODY_BOTTOM = 1.58, 6.85


def set_run(run, size, *, bold=False, color=TEXT):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = FONT
    rPr = run._r.get_or_add_rPr()
    rPr.set("lang", "ja-JP")
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set("typeface", FONT)


def add_text(slide, x, y, w, h, text, size, *, bold=False, color=TEXT,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.3,
             wrap=True):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        set_run(p.add_run(), size, bold=bold, color=color)
        p.runs[0].text = line
    return tb


def add_rect(slide, x, y, w, h, fill, *, line=None, round_=False):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if round_ else MSO_SHAPE.RECTANGLE
    sp = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    if round_:
        sp.adjustments[0] = 0.06
    sp.fill.solid()
    sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = Pt(0.75)
    sp.shadow.inherit = False
    return sp


def header(slide, kicker, title):
    add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, CANVAS)
    add_text(slide, 0.72, 0.27, 4.8, 0.32, kicker, 11.5, bold=True, color=ACCENT)
    size = 27
    lines = wrap_text(title, 11.9, size, "bold")
    while len(lines) > 1 and size > 18:
        size -= 0.5
        lines = wrap_text(title, 11.9, size, "bold")
    if len(lines) > 1:
        size, lines = fit_font_size(
            title, 11.9, 0.86, 18, min_pt=16, weight="bold", spacing=1.08)
    add_text(slide, 0.72, 0.67, 11.9, 0.86, "\n".join(lines), size,
             bold=True, color=NAVY, spacing=1.12)


def page_label(page):
    """Return a stable page marker shared by every generator entry point."""
    total = len(DECK["slides"])
    digits = max(2, len(str(total)))
    return f"{page:0{digits}d} / {total:0{digits}d}"


def footer(slide, page):
    total = len(DECK["slides"])
    digits = max(2, len(str(total)))
    add_rect(slide, 0.72, 6.92, 11.9, 0.01, RULE)
    add_text(slide, 0.72, 7.01, 7.8, 0.25, DECK["meta"]["footer"], 8.2,
             color=GRAY, anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, 11.38, 6.98, 0.64, 0.28, f"{page:0{digits}d}", 11,
             bold=True, color=NAVY, align=PP_ALIGN.RIGHT)
    add_text(slide, 12.04, 6.99, 0.58, 0.26, f"/ {total:0{digits}d}", 8.2,
             color=GRAY, align=PP_ALIGN.RIGHT)


def note_line(slide, note):
    add_text(slide, MARGIN, 6.62, BODY_W, 0.25, note, 8.5, color=GRAY, align=PP_ALIGN.RIGHT)


# ---- スライド種別 ----
def s_title(slide, spec, page):
    meta = DECK["meta"]
    total = len(DECK["slides"])

    add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, NAVY)
    add_text(slide, 0.9, 0.68, 3.2, 0.3, "SLIDE PATTERN LIBRARY", 10,
             bold=True, color=LIGHT)
    add_text(slide, 9.78, 0.68, 2.62, 0.3, meta["date"], 10,
             color=LIGHT, align=PP_ALIGN.RIGHT)

    title_size, title_lines = fit_font_size(
        spec["title"], 8.05, 2.15, 42, min_pt=34, weight="bold", spacing=1.06)
    title_h = max(1.0, len(title_lines) * line_height_in(title_size, 1.08) + 0.1)
    add_text(slide, 0.9, 1.72, 8.05, title_h, "\n".join(title_lines), title_size,
             bold=True, color=WHITE, spacing=1.08)

    subtitle_y = min(4.72, 1.72 + title_h + 0.38)
    subtitle_size, subtitle_lines = fit_font_size(
        spec["subtitle"], 8.0, 0.8, 17.5, min_pt=15, spacing=1.2)
    add_text(slide, 0.94, subtitle_y, 8.0, 0.8, "\n".join(subtitle_lines),
             subtitle_size, color=LIGHT, spacing=1.2)

    # The right rail is informative, not decorative: it frames the deck's scope.
    add_rect(slide, 9.45, 1.68, 0.012, 3.82, LIGHT)
    rail = [
        ("SCOPE", f"{total:02d} patterns"),
        ("OUTPUT", "PowerPoint"),
        ("QUALITY", "Generate / Validate / Review"),
    ]
    for i, (label, value) in enumerate(rail):
        y = 1.82 + i * 1.12
        add_text(slide, 9.82, y, 2.25, 0.25, label, 8.8,
                 bold=True, color=LIGHT)
        add_text(slide, 9.82, y + 0.34, 2.35, 0.45, value, 13.5,
                 bold=True, color=WHITE)

    add_text(slide, 0.9, 6.5, 4.8, 0.3, meta["author"], 10.5,
             bold=True, color=WHITE)


def s_bullets(slide, spec, page):
    header(slide, spec["kicker"], spec["title"])
    bullets = spec["bullets"]
    area_h = BODY_BOTTOM - BODY_TOP - 0.22
    tx = 1.68
    tw = 10.15
    size, gap = 18, 0.48
    while size > 12:
        heights = [len(wrap_text(t, tw, size)) * line_height_in(size, 1.22)
                   for t, _ in bullets]
        total = sum(heights) + gap * (len(bullets) - 1)
        if total <= area_h:
            break
        size -= 0.5
    y = BODY_TOP + 0.38 + max(0.0, (area_h - total) * 0.22)
    for i, ((text, _), bh) in enumerate(zip(bullets, heights), 1):
        add_text(slide, 0.78, y - 0.07, 0.62, 0.45, f"{i:02d}", 15,
                 bold=True, color=GRAY, align=PP_ALIGN.RIGHT)
        add_text(slide, tx, y, tw, bh + 0.08, text, size, spacing=1.22)
        if i < len(bullets):
            add_rect(slide, tx, y + bh + 0.15, tw, 0.012, RULE)
        y += bh + gap


def s_cards(slide, spec, page):
    """Render purpose-specific cards instead of one universal panel pattern."""
    header(slide, spec["kicker"], spec["title"])
    cards = spec["cards"]
    n = len(cards)
    style = spec.get("style", "editorial")
    left, usable_w = 0.78, 11.78

    if style == "metrics":
        gap = 0.56
        cw = (usable_w - gap * (n - 1)) / n
        ch, top = 3.0, BODY_TOP + 0.76
        body_size = min(
            fit_font_size(body, cw - 0.2, ch - 1.35, 13.5, min_pt=11,
                          spacing=1.2)[0]
            for _, body in cards)
        for i, (head, body) in enumerate(cards):
            x = left + i * (cw + gap)
            label, value = _split_metric_head(head)
            add_text(slide, x, top, cw, 0.34, label, 12.5,
                     bold=True, color=NAVY)
            value_size = fit_font_size(value, cw, 0.76, 34, min_pt=26,
                                       weight="bold")[0]
            add_text(slide, x, top + 0.48, cw, 0.76, value, value_size,
                     bold=True, color=ACCENT)
            add_text(slide, x, top + 1.55, cw, ch - 1.55, body,
                     body_size, color=TEXT, spacing=1.2)
            if i < n - 1:
                add_rect(slide, x + cw + gap / 2, top + 0.04, 0.012, ch - 0.08, RULE)
        return

    if style == "editorial" and n == 4:
        lead_head, lead_body = cards[0]
        top = BODY_TOP + 0.46
        add_text(slide, 0.8, top, 0.58, 0.36, "01", 15,
                 bold=True, color=GRAY)
        add_text(slide, 1.52, top - 0.03, 3.95, 0.56, lead_head,
                 23, bold=True, color=NAVY)
        lead_size, lead_lines = fit_font_size(
            lead_body, 4.1, 2.05, 16, min_pt=13, spacing=1.28)
        add_text(slide, 1.52, top + 0.76, 4.1, 2.05,
                 "\n".join(lead_lines), lead_size, color=TEXT, spacing=1.28)

        right_x, right_w = 6.42, 5.92
        row_h = 1.31
        for i, (head, body) in enumerate(cards[1:], 2):
            y = top + (i - 2) * row_h
            add_text(slide, right_x, y + 0.02, 0.5, 0.32, f"{i:02d}", 12.5,
                     bold=True, color=GRAY)
            add_text(slide, right_x + 0.68, y, right_w - 0.68, 0.38, head,
                     16, bold=True, color=NAVY)
            body_size, body_lines = fit_font_size(
                body, right_w - 0.72, 0.56, 12.5, min_pt=11, spacing=1.15)
            add_text(slide, right_x + 0.68, y + 0.48, right_w - 0.72, 0.56,
                     "\n".join(body_lines), body_size, color=TEXT, spacing=1.15)
            if i < n:
                add_rect(slide, right_x + 0.68, y + 1.14, right_w - 0.68, 0.012, RULE)
        return

    cols = 2 if n == 4 else n
    rows = 2 if n == 4 else 1
    gap_x, gap_y = 0.72, 0.44
    cw = (usable_w - gap_x * (cols - 1)) / cols
    area_h = BODY_BOTTOM - BODY_TOP - 0.62
    ch = ((area_h - gap_y) / 2 if rows == 2 else min(3.32, area_h))
    top = BODY_TOP + (0.42 if rows == 2 else 0.72)
    body_size = min(
        fit_font_size(body, cw - 0.92, ch - 0.72, 14, min_pt=11,
                      spacing=1.2)[0]
        for _, body in cards)
    for i, (head, body) in enumerate(cards):
        row, col = divmod(i, cols)
        x = left + col * (cw + gap_x)
        y = top + row * (ch + gap_y)
        add_text(slide, x, y + 0.02, 0.58, 0.36, f"{i + 1:02d}", 14,
                 bold=True, color=GRAY)
        add_text(slide, x + 0.72, y, cw - 0.72, 0.42, head,
                 16.5, bold=True, color=NAVY)
        add_text(slide, x + 0.72, y + 0.58, cw - 0.82, ch - 0.64, body,
                 body_size, color=TEXT, spacing=1.2)
        if row == 0:
            add_rect(slide, x + 0.72, y + ch + gap_y / 2, cw - 0.72, 0.012, RULE)


def _split_metric_head(head):
    match = re.match(r"^(.*?)[\s　]+([+\-−]?[0-9][0-9,.]*\s*(?:%|分|件|倍|pt)?)$", head)
    if match:
        return match.group(1).strip(), match.group(2).replace("−", "-").strip()
    return head, ""


def s_table(slide, spec, page):
    header(slide, spec["kicker"], spec["title"])
    cols, rows = spec["columns"], spec["rows"]
    widths = spec["col_widths"]
    assert abs(sum(widths) - BODY_W) < 0.6, f"列幅合計={sum(widths)}"
    size = 13.5
    pad = 0.14
    hdr_h = 0.72
    avail = BODY_BOTTOM - BODY_TOP - 0.15 - hdr_h - (0.3 if spec.get("note") else 0)
    min_row_h = min(1.04, max(0.64, avail / max(1, len(rows))))
    while size >= 10.5:
        row_hs = []
        for row in rows:
            need = max(
                fit_font_size(c, widths[j] - pad * 2, 10, size, min_pt=size)[1].__len__()
                * line_height_in(size, 1.15) for j, c in enumerate(row))
            row_hs.append(max(need + pad * 2, min_row_h))
        if sum(row_hs) <= avail:
            break
        size -= 0.5
    table_h = hdr_h + sum(row_hs)
    top = BODY_TOP + 0.38 + max(0.0, (avail - table_h) * 0.12)
    gt = slide.shapes.add_table(len(rows) + 1, len(cols), Inches(MARGIN),
                                Inches(top), Inches(BODY_W), Inches(table_h))
    table = gt.table
    table.first_row = False
    table.horz_banding = False
    for j, wdt in enumerate(widths):
        table.columns[j].width = Emu(int(Inches(wdt)))
    table.rows[0].height = Emu(int(Inches(hdr_h)))
    for i, rh in enumerate(row_hs):
        table.rows[i + 1].height = Emu(int(Inches(rh)))
    for j, name in enumerate(cols):
        _cell(table.cell(0, j), name, size, bold=True, color=WHITE, fill=NAVY,
              center=j != len(cols) - 1 and j != 0)
    for i, row in enumerate(rows):
        fill = WHITE if i % 2 else ZEBRA
        for j, val in enumerate(row):
            _cell(table.cell(i + 1, j), val, size,
                  bold=(j == 0), color=NAVY if j == 0 else TEXT, fill=fill,
                  center=0 < j < len(cols) - 1 and len(val) <= 6)
    if spec.get("note"):
        note_line(slide, spec["note"])


def _cell(cell, text, size, *, bold=False, color=TEXT, fill=WHITE, center=False):
    cell.fill.solid()
    cell.fill.fore_color.rgb = fill
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    cell.margin_left = cell.margin_right = Inches(0.09)
    cell.margin_top = cell.margin_bottom = Inches(0.04)
    tf = cell.text_frame
    tf.word_wrap = True
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER if center else PP_ALIGN.LEFT
        p.line_spacing = 1.15
        set_run(p.add_run(), size, bold=bold, color=color)
        p.runs[0].text = line


def s_twocol(slide, spec, page):
    """Render a purposeful before/after comparison, not generic cards."""
    header(slide, spec["kicker"], spec["title"])
    gap = 0.46
    left = 0.76
    cw = (11.82 - gap) / 2
    max_ch = BODY_BOTTOM - BODY_TOP - 0.15
    panels = [spec["left"], spec["right"]]
    tw = cw - 0.76
    size, bgap = 14, 0.32
    while size > 11:
        cont = [sum(len(wrap_text(b, tw, size)) * line_height_in(size, 1.2) + bgap
                    for b in p["bullets"]) - bgap for p in panels]
        if max(cont) <= max_ch - 1.38:
            break
        size -= 0.5
    body_h = max(cont) + 0.28
    top = BODY_TOP + 0.34
    for i, p in enumerate(panels):
        x = left + i * (cw + gap)
        fill = ZEBRA if i == 0 else LIGHT
        add_rect(slide, x, top, cw, min(max_ch - 0.14, body_h + 1.38), fill)
        add_text(slide, x + 0.36, top + 0.28, cw - 0.72, 0.25,
                 "BEFORE" if i == 0 else "AFTER", 9.5,
                 bold=True, color=GRAY if i == 0 else ACCENT)
        add_text(slide, x + 0.36, top + 0.67, cw - 0.72, 0.48,
                 p["heading"], 18, bold=True, color=NAVY)
        y = top + 1.42
        for b in p["bullets"]:
            bh = len(wrap_text(b, tw, size)) * line_height_in(size, 1.2)
            add_text(slide, x + 0.36, y - 0.01, 0.24, 0.3, "—", 12,
                     bold=True, color=GRAY if i == 0 else ACCENT)
            add_text(slide, x + 0.7, y, tw, bh + 0.08, b, size,
                     color=TEXT, spacing=1.2)
            y += bh + bgap


def s_chart(slide, spec, page):
    header(slide, spec["kicker"], spec["title"])
    cd = CategoryChartData()
    cd.categories = spec["chart"]["categories"]
    for name, vals in spec["chart"]["series"]:
        cd.add_series(name, vals)
    gf = slide.shapes.add_chart(
        XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.9), Inches(BODY_TOP + 0.22),
        Inches(11.8), Inches(BODY_BOTTOM - BODY_TOP - 0.48), cd)
    ch = gf.chart
    ch.has_title = False
    ch.has_legend = True
    ch.legend.position = XL_LEGEND_POSITION.BOTTOM
    ch.legend.include_in_layout = False
    ch.font.size = Pt(12)
    ch.font.name = FONT
    plot = ch.plots[0]
    plot.has_data_labels = True
    plot.data_labels.font.size = Pt(11.5)
    plot.gap_width = 76
    ch.value_axis.major_gridlines.format.line.color.rgb = RULE
    ch.value_axis.major_gridlines.format.line.width = Pt(0.6)
    ch.value_axis.format.line.fill.background()
    ch.category_axis.format.line.fill.background()
    for s, colr in zip(ch.series, (GRAY, ACCENT)):
        s.format.fill.solid()
        s.format.fill.fore_color.rgb = colr
    if spec.get("note"):
        note_line(slide, spec["note"])


RENDER = {"title": s_title, "bullets": s_bullets, "cards": s_cards,
          "table": s_table, "twocol": s_twocol, "chart": s_chart}


def main(out_path):
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W)
    prs.slide_height = Inches(SLIDE_H)
    blank = prs.slide_layouts[6]
    total = len(DECK["slides"])
    for idx, spec in enumerate(DECK["slides"], 1):
        slide = prs.slides.add_slide(blank)
        RENDER[spec["type"]](slide, spec, idx)
        if spec["type"] != "title":
            footer(slide, idx)
    prs.save(out_path)
    print(f"saved: {out_path} ({total} slides)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../out/sysA_deck.pptx")
