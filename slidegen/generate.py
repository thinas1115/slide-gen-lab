"""システムA: python-pptx + テキスト実測によるスライド生成。"""
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
NAVY = RGBColor(0x17, 0x27, 0x3D)
ACCENT = RGBColor(0x0B, 0x7A, 0x75)
CORAL = RGBColor(0xD9, 0x5D, 0x46)
LIGHT = RGBColor(0xD9, 0xE8, 0xE3)
TEXT = RGBColor(0x20, 0x27, 0x29)
GRAY = RGBColor(0x6C, 0x73, 0x72)
WHITE = RGBColor(0xFF, 0xFD, 0xF8)
ZEBRA = RGBColor(0xE9, 0xE5, 0xDB)
CANVAS = RGBColor(0xF4, 0xF0, 0xE7)
RULE = RGBColor(0xC9, 0xC4, 0xB9)
FONT = "Yu Gothic"
SLIDE_W, SLIDE_H = 13.333, 7.5
MARGIN = 0.55
BODY_W = SLIDE_W - MARGIN * 2
BODY_TOP, BODY_BOTTOM = 1.62, 6.85


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
    add_rect(slide, 0, 0, 0.14, SLIDE_H, NAVY)
    add_rect(slide, 0.14, 0, 0.055, 1.22, CORAL)
    add_text(slide, 0.66, 0.31, 4.0, 0.3, kicker, 10.5, bold=True, color=ACCENT)
    size, lines = fit_font_size(
        title, 11.85, 0.86, 24, min_pt=18, weight="bold", spacing=1.12)
    add_text(slide, 0.66, 0.66, 11.85, 0.86, "\n".join(lines), size,
             bold=True, color=NAVY, spacing=1.12)
    add_rect(slide, 0.66, 1.56, 0.72, 0.04, CORAL)
    add_rect(slide, 1.46, 1.57, 0.34, 0.02, ACCENT)


def page_label(page):
    """Return a stable page marker shared by every generator entry point."""
    total = len(DECK["slides"])
    digits = max(2, len(str(total)))
    return f"{page:0{digits}d} / {total:0{digits}d}"


def footer(slide, page):
    total = len(DECK["slides"])
    digits = max(2, len(str(total)))
    add_rect(slide, 0.66, 7.06, 0.34, 0.035, ACCENT)
    add_text(slide, 1.12, 6.99, 7.8, 0.3, DECK["meta"]["footer"], 8.5,
             color=GRAY, anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, 11.48, 6.91, 0.75, 0.38, f"{page:0{digits}d}", 15,
             bold=True, color=NAVY, align=PP_ALIGN.RIGHT)
    add_text(slide, 12.26, 7.02, 0.48, 0.25, f"/ {total:0{digits}d}", 8.5,
             bold=True, color=ACCENT, align=PP_ALIGN.RIGHT)


def note_line(slide, note):
    add_text(slide, MARGIN, 6.62, BODY_W, 0.25, note, 8.5, color=GRAY, align=PP_ALIGN.RIGHT)


# ---- スライド種別 ----
def s_title(slide, spec, page):
    meta = DECK["meta"]
    total = len(DECK["slides"])

    add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, NAVY)
    add_rect(slide, 12.64, 0, 0.69, SLIDE_H, CORAL)
    add_rect(slide, 12.46, 0, 0.18, SLIDE_H, ACCENT)

    add_text(slide, 0.82, 0.68, 2.8, 0.3, meta["date"], 10.5,
             bold=True, color=LIGHT)
    add_rect(slide, 0.82, 1.17, 0.72, 0.06, CORAL)

    title_size, title_lines = fit_font_size(
        spec["title"], 8.7, 2.05, 46, min_pt=32, weight="bold", spacing=1.08)
    title_h = max(1.0, len(title_lines) * line_height_in(title_size, 1.08) + 0.1)
    add_text(slide, 0.82, 1.55, 8.7, title_h, "\n".join(title_lines), title_size,
             bold=True, color=WHITE, spacing=1.08)

    subtitle_y = min(4.55, 1.55 + title_h + 0.3)
    subtitle_size, subtitle_lines = fit_font_size(
        spec["subtitle"], 8.25, 0.9, 17, min_pt=13, spacing=1.22)
    add_text(slide, 0.86, subtitle_y, 8.25, 0.9, "\n".join(subtitle_lines),
             subtitle_size, color=LIGHT, spacing=1.22)

    add_rect(slide, 0.82, 6.2, 7.9, 0.015, ACCENT)
    add_text(slide, 0.82, 6.45, 6.0, 0.3, meta["author"], 11,
             bold=True, color=WHITE)

    add_text(slide, 9.55, 0.65, 1.55, 1.45, f"{page:02d}", 72,
             bold=True, color=CANVAS, align=PP_ALIGN.RIGHT)
    add_text(slide, 11.18, 1.52, 0.72, 0.3, f"/ {total:02d}", 10.5,
             bold=True, color=CORAL, align=PP_ALIGN.RIGHT)

    add_rect(slide, 9.84, 3.7, 2.05, 1.5, ACCENT)
    add_rect(slide, 10.34, 4.17, 1.55, 1.49, NAVY, line=WHITE)
    add_rect(slide, 9.84, 5.2, 0.62, 0.62, CORAL)
    add_rect(slide, 11.27, 5.05, 0.62, 0.62, CANVAS)
    add_text(slide, 9.2, 6.52, 2.7, 0.3, meta["footer"], 8.5,
             color=LIGHT, align=PP_ALIGN.RIGHT)


def s_bullets(slide, spec, page):
    header(slide, spec["kicker"], spec["title"])
    bullets = spec["bullets"]
    area_h = BODY_BOTTOM - BODY_TOP - 0.22
    tx = 1.62
    tw = 10.55
    size, gap = 16.5, 0.36
    while size > 12:
        heights = [len(wrap_text(t, tw, size)) * line_height_in(size, 1.22)
                   for t, _ in bullets]
        total = sum(heights) + gap * (len(bullets) - 1)
        if total <= area_h:
            break
        size -= 0.5
    y = BODY_TOP + 0.25 + max(0.0, (area_h - total) * 0.32)
    for i, ((text, _), bh) in enumerate(zip(bullets, heights), 1):
        add_text(slide, 0.68, y - 0.02, 0.66, 0.45, f"{i:02d}", 18,
                 bold=True, color=CORAL, align=PP_ALIGN.RIGHT)
        add_rect(slide, 1.46, y + 0.03, 0.035, max(0.35, bh - 0.02), ACCENT)
        add_text(slide, tx, y, tw, bh + 0.08, text, size, spacing=1.22)
        add_rect(slide, tx, y + bh + 0.1, tw, 0.012, RULE)
        y += bh + gap


def s_cards(slide, spec, page):
    """Render purpose-specific cards instead of one universal panel pattern."""
    header(slide, spec["kicker"], spec["title"])
    cards = spec["cards"]
    n = len(cards)
    style = spec.get("style", "editorial")
    left, usable_w = 0.76, 11.82

    if style == "metrics":
        gap = 0.28
        cw = (usable_w - gap * (n - 1)) / n
        ch, top = 2.72, BODY_TOP + 0.92
        body_size = min(
            fit_font_size(body, cw - 0.58, ch - 1.3, 13, min_pt=11,
                          spacing=1.2)[0]
            for _, body in cards)
        fills = (WHITE, LIGHT, WHITE, ZEBRA)
        for i, (head, body) in enumerate(cards):
            x = left + i * (cw + gap)
            add_rect(slide, x, top, cw, ch, fills[i % len(fills)])
            accent = CORAL if i == 0 else ACCENT
            add_rect(slide, x + cw - 0.3, top + 0.22, 0.12, 0.12, accent)
            add_text(slide, x + 0.28, top + 0.38, cw - 0.58, 0.62, head,
                     18, bold=True, color=NAVY)
            add_text(slide, x + 0.28, top + 1.25, cw - 0.58, ch - 1.5, body,
                     body_size, color=TEXT, spacing=1.2)
            add_rect(slide, x + 0.28, top + ch - 0.25, 0.72, 0.035, accent)
        return

    cols = 2 if n == 4 else n
    rows = 2 if n == 4 else 1
    gap_x, gap_y = 0.3, 0.26
    cw = (usable_w - gap_x * (cols - 1)) / cols
    area_h = BODY_BOTTOM - BODY_TOP - 0.44
    ch = ((area_h - gap_y) / 2 if rows == 2 else min(3.32, area_h))
    top = BODY_TOP + (0.24 if rows == 2 else 0.72)
    body_size = min(
        fit_font_size(body, cw - 0.62, ch - 1.02, 13, min_pt=10.5,
                      spacing=1.2)[0]
        for _, body in cards)
    fills = (WHITE, LIGHT, WHITE, ZEBRA)
    for i, (head, body) in enumerate(cards):
        row, col = divmod(i, cols)
        x = left + col * (cw + gap_x)
        y = top + row * (ch + gap_y)
        add_rect(slide, x, y, cw, ch, fills[i % len(fills)])
        accent = CORAL if i % 3 == 0 else ACCENT
        add_rect(slide, x + 0.28, y + 0.3, 0.14, 0.14, accent)
        add_text(slide, x + 0.55, y + 0.23, cw - 0.82, 0.5, head,
                 15.5, bold=True, color=NAVY)
        add_text(slide, x + 0.28, y + 0.88, cw - 0.56, ch - 1.08, body,
                 body_size, color=TEXT, spacing=1.2)


def s_table(slide, spec, page):
    header(slide, spec["kicker"], spec["title"])
    cols, rows = spec["columns"], spec["rows"]
    widths = spec["col_widths"]
    assert abs(sum(widths) - BODY_W) < 0.6, f"列幅合計={sum(widths)}"
    size = 12.5
    pad = 0.11
    hdr_h = 0.56
    avail = BODY_BOTTOM - BODY_TOP - 0.15 - hdr_h - (0.3 if spec.get("note") else 0)
    min_row_h = min(0.58, max(0.36, avail / max(1, len(rows))))
    while size >= 9.5:
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
    top = BODY_TOP + 0.1 + max(0.0, (avail - table_h) * 0.35)
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
        fill = ZEBRA if i % 2 else WHITE
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
    """Render a flat comparison; the center rule carries the grouping."""
    header(slide, spec["kicker"], spec["title"])
    gap = 0.72
    left = 0.78
    cw = (11.78 - gap) / 2
    max_ch = BODY_BOTTOM - BODY_TOP - 0.15
    panels = [spec["left"], spec["right"]]
    tw = cw - 0.48
    size, bgap = 13.5, 0.3
    while size > 11:
        cont = [sum(len(wrap_text(b, tw, size)) * line_height_in(size, 1.2) + bgap
                    for b in p["bullets"]) - bgap for p in panels]
        if max(cont) <= max_ch - 1.38:
            break
        size -= 0.5
    body_h = max(cont) + 0.28
    top = BODY_TOP + 0.22
    add_rect(slide, left + cw + gap / 2 - 0.008, top + 0.12, 0.016,
             min(max_ch - 0.2, body_h + 1.22), RULE)
    for i, p in enumerate(panels):
        x = left + i * (cw + gap)
        marker = CORAL if i == 0 else ACCENT
        add_text(slide, x, top, 0.72, 0.4, f"{i + 1:02d}", 18,
                 bold=True, color=marker)
        add_text(slide, x + 0.78, top - 0.02, cw - 0.78, 0.48,
                 p["heading"], 17, bold=True, color=NAVY)
        add_rect(slide, x, top + 0.62, cw - 0.08, 0.018, RULE)
        y = top + 0.9
        for b in p["bullets"]:
            bh = len(wrap_text(b, tw, size)) * line_height_in(size, 1.2)
            add_rect(slide, x, y + 0.11, 0.18, 0.045, marker)
            add_text(slide, x + 0.3, y, tw, bh + 0.08, b, size,
                     color=TEXT, spacing=1.2)
            y += bh + bgap


def s_chart(slide, spec, page):
    header(slide, spec["kicker"], spec["title"])
    cd = CategoryChartData()
    cd.categories = spec["chart"]["categories"]
    for name, vals in spec["chart"]["series"]:
        cd.add_series(name, vals)
    add_rect(slide, 0.66, BODY_TOP + 0.18, 12.0,
             BODY_BOTTOM - BODY_TOP - 0.42, WHITE)
    gf = slide.shapes.add_chart(
        XL_CHART_TYPE.BAR_CLUSTERED, Inches(1.05), Inches(BODY_TOP + 0.42),
        Inches(11.15), Inches(BODY_BOTTOM - BODY_TOP - 0.9), cd)
    ch = gf.chart
    ch.has_title = False
    ch.has_legend = True
    ch.legend.position = XL_LEGEND_POSITION.BOTTOM
    ch.legend.include_in_layout = False
    ch.font.size = Pt(11)
    ch.font.name = FONT
    plot = ch.plots[0]
    plot.has_data_labels = True
    plot.data_labels.font.size = Pt(10.5)
    plot.gap_width = 92
    for s, colr in zip(ch.series, (CORAL, ACCENT)):
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
