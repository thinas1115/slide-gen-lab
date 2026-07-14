// システムB: PptxGenJS + 文字種ヒューリスティック幅推定 + PPT側autofit保険
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const DECK = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "..", "content.json"), "utf8"));

const NAVY = "1F3864", ACCENT = "2E75B6", LIGHT = "EAF1F8", TEXT = "262626",
  GRAY = "7F7F7F", WHITE = "FFFFFF", ZEBRA = "F2F6FB", RULE = "D9D9D9";
const FONT = "Yu Gothic";
const SLIDE_W = 13.333, MARGIN = 0.55, BODY_W = SLIDE_W - MARGIN * 2;
const BODY_TOP = 1.62, BODY_BOTTOM = 6.85;

// ---- 幅推定: 全角=1em, 半角=0.53em, 安全係数1.1 ----
function textWidthIn(text, pt) {
  let em = 0;
  for (const ch of text) em += ch.codePointAt(0) > 0xff ? 1.0 : 0.53;
  return em * (pt / 72) * 1.1;
}
function wrapLines(text, widthIn, pt) {
  const lines = [];
  for (const para of text.split("\n")) {
    let cur = "";
    for (const ch of para) {
      if (!cur || textWidthIn(cur + ch, pt) <= widthIn) { cur += ch; continue; }
      if ("、。，．）」』？！：".includes(ch)) { lines.push(cur + ch); cur = ""; }
      else { lines.push(cur); cur = ch; }
    }
    lines.push(cur);
  }
  return lines.filter((l, i, a) => l !== "" || i < a.length - 1);
}
const lineH = (pt, sp = 1.3) => (pt * sp) / 72;
function fitSize(text, w, h, maxPt, minPt = 10) {
  for (let s = maxPt; s >= minPt; s -= 0.5)
    if (wrapLines(text, w, s).length * lineH(s) <= h) return s;
  return minPt;
}

const textOpts = (over) => ({
  fontFace: FONT, color: TEXT, align: "left", valign: "top",
  lineSpacingMultiple: 1.3, wrap: true, lang: "ja-JP", fit: "shrink",
  margin: 0, ...over,
});
function rect(s, x, y, w, h, color, round = false) {
  s.addShape(round ? "roundRect" : "rect",
    { x, y, w, h, fill: { color }, line: { type: "none" }, rectRadius: round ? 0.05 : 0 });
}
function header(s, kicker, title) {
  s.addText(kicker, textOpts({ x: MARGIN, y: 0.34, w: BODY_W, h: 0.3, fontSize: 11, bold: true, color: ACCENT }));
  const size = fitSize(title, BODY_W, 0.9, 20, 15);
  s.addText(title, textOpts({ x: MARGIN, y: 0.62, w: BODY_W, h: 0.9, fontSize: size, bold: true, color: NAVY, lineSpacingMultiple: 1.2 }));
  rect(s, MARGIN, 1.48, BODY_W, 0.022, ACCENT);
}
function footer(s, page) {
  rect(s, MARGIN, 7.06, BODY_W, 0.012, RULE);
  s.addText(DECK.meta.footer, textOpts({ x: MARGIN, y: 7.12, w: 8, h: 0.25, fontSize: 8, color: GRAY }));
  s.addText(String(page), textOpts({ x: SLIDE_W - MARGIN - 1.2, y: 7.12, w: 1.2, h: 0.25, fontSize: 8, color: GRAY, align: "right" }));
}
const note = (s, t) => s.addText(t, textOpts({ x: MARGIN, y: 6.62, w: BODY_W, h: 0.25, fontSize: 8.5, color: GRAY, align: "right" }));

function sTitle(s, spec) {
  rect(s, 0, 0, SLIDE_W, 0.18, NAVY);
  rect(s, MARGIN, 2.52, 0.7, 0.045, ACCENT);
  s.addText(spec.title, textOpts({ x: MARGIN, y: 2.78, w: BODY_W, h: 1.0, fontSize: 30, bold: true, color: NAVY }));
  s.addText(spec.subtitle, textOpts({ x: MARGIN, y: 3.72, w: BODY_W, h: 0.6, fontSize: 15, color: GRAY }));
  s.addText(`${DECK.meta.date}    ${DECK.meta.author}`, textOpts({ x: MARGIN, y: 6.35, w: BODY_W, h: 0.3, fontSize: 11, color: GRAY }));
  rect(s, 0, 7.32, SLIDE_W, 0.18, NAVY);
}
function sBullets(s, spec) {
  header(s, spec.kicker, spec.title);
  const areaH = BODY_BOTTOM - BODY_TOP - 0.1, tx = MARGIN + 0.42, tw = BODY_W - 0.42;
  let size = 15, gap = 0.42, heights, total;
  for (; size > 11; size -= 0.5) {
    heights = spec.bullets.map(([t]) => wrapLines(t, tw, size).length * lineH(size));
    total = heights.reduce((a, b) => a + b, 0) + gap * (spec.bullets.length - 1);
    if (total <= areaH) break;
  }
  let y = BODY_TOP + 0.1 + Math.max(0, (areaH - total) * 0.35);
  spec.bullets.forEach(([t], i) => {
    rect(s, MARGIN + 0.05, y + lineH(size) / 2 - 0.055, 0.13, 0.13, ACCENT);
    s.addText(t, textOpts({ x: tx, y, w: tw, h: heights[i] + 0.1, fontSize: size }));
    y += heights[i] + gap;
  });
}
function sCards(s, spec) {
  header(s, spec.kicker, spec.title);
  const n = spec.cards.length, gap = 0.3, cw = (BODY_W - gap * (n - 1)) / n;
  const maxCh = BODY_BOTTOM - BODY_TOP - 0.15;
  const size = Math.min(...spec.cards.map(([, b]) => fitSize(b, cw - 0.5, maxCh - 1.05, 13, 10.5)));
  const bodyH = Math.max(...spec.cards.map(([, b]) => wrapLines(b, cw - 0.5, size).length * lineH(size)));
  const ch = Math.min(maxCh, 1.0 + bodyH + 0.3), top = BODY_TOP + 0.1 + (maxCh - ch) * 0.4;
  spec.cards.forEach(([head, body], i) => {
    const x = MARGIN + i * (cw + gap);
    rect(s, x, top, cw, ch, LIGHT, true);
    rect(s, x + 0.25, top + 0.22, 0.32, 0.045, ACCENT);
    s.addText(head, textOpts({ x: x + 0.25, y: top + 0.36, w: cw - 0.5, h: 0.4, fontSize: 14.5, bold: true, color: NAVY }));
    s.addText(body, textOpts({ x: x + 0.25, y: top + 0.9, w: cw - 0.5, h: ch - 1.05, fontSize: size }));
  });
}
function sTable(s, spec) {
  header(s, spec.kicker, spec.title);
  const widths = spec.col_widths, pad = 0.09, hdrH = 0.38;
  const avail = BODY_BOTTOM - BODY_TOP - 0.15 - hdrH - (spec.note ? 0.3 : 0);
  let size = 11, rowHs;
  for (; size >= 8.5; size -= 0.5) {
    rowHs = spec.rows.map((row) => Math.max(0.32, pad * 2 + Math.max(
      ...row.map((c, j) => wrapLines(c, widths[j] - pad * 2, size).length * lineH(size, 1.15)))));
    if (rowHs.reduce((a, b) => a + b, 0) <= avail) break;
  }
  const tableH = hdrH + rowHs.reduce((a, b) => a + b, 0);
  const top = BODY_TOP + 0.1 + Math.max(0, (avail - tableH) * 0.35);
  const nc = spec.columns.length;
  const hdr = spec.columns.map((c, j) => ({
    text: c, options: { fill: { color: NAVY }, color: WHITE, bold: true,
      align: j !== 0 && j !== nc - 1 ? "center" : "left" },
  }));
  const body = spec.rows.map((row, i) => row.map((c, j) => ({
    text: c, options: { fill: { color: i % 2 ? ZEBRA : WHITE },
      align: j > 0 && j < nc - 1 && c.length <= 6 ? "center" : "left" },
  })));
  s.addTable([hdr, ...body], {
    x: MARGIN, y: top, w: BODY_W, colW: widths, rowH: [hdrH, ...rowHs],
    fontFace: FONT, fontSize: size, color: TEXT, valign: "middle", align: "left",
    border: { type: "none" }, margin: [0.04, 0.09, 0.04, 0.09], autoPage: false,
  });
  if (spec.note) note(s, spec.note);
}
function sTwocol(s, spec) {
  header(s, spec.kicker, spec.title);
  const gap = 0.35, cw = (BODY_W - gap) / 2, maxCh = BODY_BOTTOM - BODY_TOP - 0.15;
  const panels = [spec.left, spec.right], tw = cw - 0.68, bgap = 0.26;
  let size = 12.5, cont;
  for (; size > 10; size -= 0.5) {
    cont = panels.map((p) => p.bullets.reduce(
      (a, b) => a + wrapLines(b, tw, size).length * lineH(size) + bgap, -bgap));
    if (Math.max(...cont) <= maxCh - 0.68 - 0.4) break;
  }
  const bodyH = Math.max(...cont) + 0.44;
  panels.forEach((p, i) => {
    const x = MARGIN + i * (cw + gap);
    rect(s, x, BODY_TOP + 0.1, cw, 0.5, NAVY, true);
    s.addText(p.heading, textOpts({ x: x + 0.22, y: BODY_TOP + 0.1, w: cw - 0.44, h: 0.5, fontSize: 13.5, bold: true, color: WHITE, valign: "middle" }));
    rect(s, x, BODY_TOP + 0.68, cw, bodyH, LIGHT, true);
    let y = BODY_TOP + 0.9;
    for (const b of p.bullets) {
      const bh = wrapLines(b, tw, size).length * lineH(size);
      rect(s, x + 0.22, y + lineH(size) / 2 - 0.045, 0.1, 0.1, ACCENT);
      s.addText(b, textOpts({ x: x + 0.44, y, w: tw, h: bh + 0.1, fontSize: size }));
      y += bh + bgap;
    }
  });
}
function sChart(s, spec, pptx) {
  header(s, spec.kicker, spec.title);
  const labels = spec.chart.categories;
  const data = spec.chart.series.map(([name, values]) => ({ name, labels, values }));
  s.addChart(pptx.charts.BAR, data, {
    x: MARGIN + 0.3, y: BODY_TOP + 0.1, w: BODY_W - 0.6, h: BODY_BOTTOM - BODY_TOP - 0.5,
    barDir: "bar", barGapWidthPct: 120, chartColors: ["BFBFBF", ACCENT],
    showValue: true, dataLabelFontSize: 10.5, dataLabelFontFace: FONT,
    showLegend: true, legendPos: "b", legendFontSize: 11, legendFontFace: FONT,
    catAxisLabelFontSize: 11, catAxisLabelFontFace: FONT,
    valAxisLabelFontSize: 10, valAxisLabelFontFace: FONT,
  });
  if (spec.note) note(s, spec.note);
}

async function main() {
  const pptx = new pptxgen();
  pptx.defineLayout({ name: "W16x9", width: 13.333, height: 7.5 });
  pptx.layout = "W16x9";
  DECK.slides.forEach((spec, i) => {
    const s = pptx.addSlide();
    const fn = { title: sTitle, bullets: sBullets, cards: sCards, table: sTable, twocol: sTwocol, chart: sChart }[spec.type];
    fn(s, spec, pptx);
    if (spec.type !== "title") footer(s, i + 1);
  });
  const out = path.join(__dirname, "..", "out", "sysB_deck.pptx");
  await pptx.writeFile({ fileName: out });
  console.log("saved:", out);
}
main().catch((e) => { console.error(e); process.exit(1); });
