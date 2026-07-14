"""content.json から Marp 用 Markdown (deck.md) を生成する。"""
import json
from pathlib import Path

ROOT = Path(__file__).parent
DECK = json.loads((ROOT.parent.parent / "content.json").read_text(encoding="utf-8"))

CHART_MAX = 600  # 軸の最大値(分)


def esc(s: str) -> str:
    return s.replace("\n", "<br>")


def head(spec) -> list[str]:
    return [f'<div class="kicker">{spec["kicker"]}</div>', "", f"# {spec['title']}", ""]


def s_title(spec):
    m = DECK["meta"]
    return [
        "<!-- _class: titlepage -->",
        '<div class="tp-band" style="top:0"></div>',
        '<div class="tp-wrap">',
        '<div class="tp-rule"></div>',
        f'<div class="tp-title">{spec["title"]}</div>',
        f'<p class="tp-sub">{spec["subtitle"]}</p>',
        "</div>",
        f'<div class="tp-meta">{m["date"]}&emsp;{m["author"]}</div>',
        '<div class="tp-band" style="bottom:0"></div>',
    ]


def s_bullets(spec):
    out = head(spec)
    out += [f"- {t}" for t, _ in spec["bullets"]]
    return out


def s_cards(spec):
    out = head(spec) + ['<div class="cards">']
    for title, body in spec["cards"]:
        out += ['<div class="card">', f"<h3>{title}</h3>", f"<p>{body}</p>", "</div>"]
    out.append("</div>")
    return out


def s_table(spec):
    out = head(spec)
    out.append("| " + " | ".join(spec["columns"]) + " |")
    out.append("|" + "|".join("---" for _ in spec["columns"]) + "|")
    for row in spec["rows"]:
        out.append("| " + " | ".join(esc(c) for c in row) + " |")
    if spec.get("note"):
        out += ["", f'<div class="note">{spec["note"]}</div>']
    return out


def s_twocol(spec):
    out = head(spec) + ['<div class="cols">']
    for p in (spec["left"], spec["right"]):
        out += ['<div class="panel">', f"<h3>{p['heading']}</h3>", "<ul>"]
        out += [f"<li>{b}</li>" for b in p["bullets"]]
        out += ["</ul>", "</div>"]
    out.append("</div>")
    return out


def s_chart(spec):
    (n1, conv), (n2, ai) = spec["chart"]["series"]
    out = head(spec) + ['<div class="chart">']
    for i, cat in enumerate(spec["chart"]["categories"]):
        wc = conv[i] / CHART_MAX * 880
        wa = ai[i] / CHART_MAX * 880
        out += [
            '<div class="row">',
            f'<div class="cat">{esc(cat)}</div>',
            f'<div class="bar ai" style="width:{wa:.0f}px">{ai[i]}</div>',
            "</div>",
            '<div class="row gap">',
            '<div class="cat"></div>',
            f'<div class="bar conv" style="width:{wc:.0f}px">{conv[i]}</div>',
            "</div>",
        ]
    out += [
        '<div class="legend">'
        f'<span class="sw" style="background:#2e75b6"></span>{n2}'
        f'<span class="sw" style="background:#bfbfbf"></span>{n1}'
        "</div>",
        "</div>",
    ]
    if spec.get("note"):
        out += ["", f'<div class="note">{spec["note"]}</div>']
    return out


RENDER = {"title": s_title, "bullets": s_bullets, "cards": s_cards,
          "table": s_table, "twocol": s_twocol, "chart": s_chart}

lines = [
    "---",
    "marp: true",
    "theme: corp",
    "paginate: true",
    f"footer: {DECK['meta']['footer']}",
    "---",
    "",
]
for i, spec in enumerate(DECK["slides"]):
    if i:
        lines += ["", "---", ""]
    lines += RENDER[spec["type"]](spec)

out = ROOT / "deck.md"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote {out} ({out.stat().st_size} bytes)")
