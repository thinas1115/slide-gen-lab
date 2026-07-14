"""content.json をレンダリング前に機械検証する。

使い方:
  python slidegen/validate_content.py content.json

generate_from_json.py が生成前に自動で呼ぶため、通常は単体実行しなくてよい。
エラーメッセージは「slides[i] (type=xxx): 内容」の形式で、生成AIにそのまま
渡して content.json を直させることを想定した粒度にしてある。

ここで強制する件数上限は「これを超えるとrendererが実際に崩れる」値。
CONTENT_SCHEMA.md の「〜が安全」より広いものもあるが、超えたら確実に
溢れる・欠ける値(roadmapのphases 4件、hubのring 6件以外など)は
ここで止める。
"""
import json
import sys
from pathlib import Path

from generate import BODY_W

# サンプル専用type: 図の中身(ノード・ラベル・座標)が全てコード内固定で、
# content.json からは差し替えられない。新規資料でこれを使うと
# 「タイトルだけ新規テーマ、中身は既存サンプルのAWS構成図」になる
# (実際に別環境の生成AIがこれをやり、サンプル文言が新規資料に混入した)。
SAMPLE_ONLY = {"aws", "aws2"}

# noteを実際に描画するtype。それ以外に書いても黙って無視される。
NOTE_TYPES = {"table", "chart", "process", "roadmap", "matrix", "hub", "org",
              "diagram"}


def _is_str(v):
    return isinstance(v, str) and v.strip() != ""


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


class _Slide:
    """1スライド分の検証ヘルパー。エラーを共通形式で溜める。"""

    def __init__(self, idx, spec, errors):
        self.idx, self.spec, self.errors = idx, spec, errors

    def err(self, msg):
        t = self.spec.get("type", "?")
        self.errors.append(f"slides[{self.idx}] (type={t}): {msg}")

    def req_str(self, key):
        if not _is_str(self.spec.get(key)):
            self.err(f'"{key}" (文字列) が必要です')
            return False
        return True

    def req_list(self, key, min_n, max_n, what):
        v = self.spec.get(key)
        if not isinstance(v, list) or not (min_n <= len(v) <= max_n):
            self.err(f'"{key}" は{what}の配列 ({min_n}〜{max_n}件) が必要です'
                     f' (現在: {len(v) if isinstance(v, list) else "配列でない"})')
            return None
        return v


def _v_title(s):
    s.req_str("title")
    s.req_str("subtitle")


def _v_bullets(s):
    items = s.req_list("bullets", 1, 6, "[本文, null]")
    for i, b in enumerate(items or []):
        if not (isinstance(b, list) and len(b) == 2 and _is_str(b[0])):
            s.err(f'bullets[{i}] は ["本文", null] の2要素配列にしてください')


def _v_cards(s):
    items = s.req_list("cards", 2, 4, "[見出し, 本文]")
    for i, c in enumerate(items or []):
        if not (isinstance(c, list) and len(c) == 2
                and _is_str(c[0]) and _is_str(c[1])):
            s.err(f'cards[{i}] は ["見出し", "本文"] の2要素配列にしてください')


def _v_table(s):
    # 列数上限8: 既存サンプルの7列表が提出品質で通っている実績に合わせる
    cols = s.req_list("columns", 2, 8, "列名")
    widths = s.req_list("col_widths", 2, 8, "列幅(インチ)")
    rows = s.req_list("rows", 1, 8, "行")
    if cols and widths:
        if len(cols) != len(widths):
            s.err(f"columns ({len(cols)}件) と col_widths ({len(widths)}件) の"
                  f"要素数を揃えてください")
        elif all(_is_num(w) for w in widths):
            total = sum(widths)
            if abs(total - BODY_W) >= 0.6:
                s.err(f"col_widths の合計 {total:.2f} が本文幅 {BODY_W:.2f} と"
                      f"0.6以上ずれています(合計を約{BODY_W:.1f}にする)")
        else:
            s.err("col_widths は数値の配列にしてください")
    for i, row in enumerate(rows or []):
        if not (isinstance(row, list) and cols and len(row) == len(cols)
                and all(isinstance(c, str) for c in row)):
            s.err(f"rows[{i}] は columns と同じ要素数の文字列配列にしてください")


def _v_twocol(s):
    for side in ("left", "right"):
        p = s.spec.get(side)
        if not isinstance(p, dict):
            s.err(f'"{side}" (heading と bullets を持つオブジェクト) が必要です')
            continue
        if not _is_str(p.get("heading")):
            s.err(f'{side}.heading (文字列) が必要です')
        b = p.get("bullets")
        if not (isinstance(b, list) and 1 <= len(b) <= 6
                and all(_is_str(x) for x in b)):
            s.err(f"{side}.bullets は文字列の配列 (1〜6件) にしてください")


def _v_chart(s):
    ch = s.spec.get("chart")
    if not isinstance(ch, dict):
        s.err('"chart" (categories と series を持つオブジェクト) が必要です')
        return
    cats = ch.get("categories")
    if not (isinstance(cats, list) and 1 <= len(cats) <= 6
            and all(_is_str(c) for c in cats)):
        s.err("chart.categories は文字列の配列 (1〜6件) にしてください")
        cats = None
    series = ch.get("series")
    if not (isinstance(series, list) and 1 <= len(series) <= 2):
        s.err("chart.series は [系列名, 値配列] の配列 (1〜2件) にしてください")
        return
    for i, sr in enumerate(series):
        ok = (isinstance(sr, list) and len(sr) == 2 and _is_str(sr[0])
              and isinstance(sr[1], list) and all(_is_num(v) for v in sr[1]))
        if not ok:
            s.err(f'series[{i}] は ["系列名", [数値, ...]] にしてください')
        elif cats and len(sr[1]) != len(cats):
            s.err(f"series[{i}] の値 ({len(sr[1])}件) を categories "
                  f"({len(cats)}件) と同数にしてください")


def _v_process(s):
    steps = s.req_list("steps", 3, 6, "工程")
    for i, st in enumerate(steps or []):
        if not (isinstance(st, dict) and _is_str(st.get("name"))
                and _is_str(st.get("desc")) and _is_str(st.get("actor"))):
            s.err(f"steps[{i}] には name / desc / actor (文字列) が必要です")
    emph = s.spec.get("emph")
    if emph is not None and steps:
        if not (isinstance(emph, list)
                and all(isinstance(i, int) and 0 <= i < len(steps) for i in emph)):
            s.err(f"emph は steps の0始まりindex (0〜{len(steps) - 1}) の配列に"
                  f"してください")


def _v_roadmap(s):
    months = s.req_list("months", 4, 8, "月ラベル")
    # phases 4件以上は行高1.15in×4+ヘッダーで本文下端を確実に超える
    phases = s.req_list("phases", 1, 3, "フェーズ")
    n_m = len(months) if months else 0
    for i, ph in enumerate(phases or []):
        if not (isinstance(ph, dict) and _is_str(ph.get("name"))
                and _is_str(ph.get("goal")) and _is_str(ph.get("bar"))
                and _is_num(ph.get("start")) and _is_num(ph.get("end"))):
            s.err(f"phases[{i}] には name / goal / bar (文字列) と "
                  f"start / end (数値) が必要です")
            continue
        if months and not (0 <= ph["start"] < ph["end"] <= n_m):
            s.err(f"phases[{i}] の start={ph['start']} / end={ph['end']} は "
                  f"0 <= start < end <= {n_m} (月数) にしてください")
    ms = s.spec.get("milestones")
    if not isinstance(ms, list):
        s.err('"milestones" (配列。不要なら []) が必要です')
        return
    for i, m in enumerate(ms):
        if not (isinstance(m, dict) and _is_num(m.get("at"))
                and isinstance(m.get("row"), int) and _is_str(m.get("label"))):
            s.err(f"milestones[{i}] には at (数値) / row (整数) / label (文字列)"
                  f" が必要です")
            continue
        if months and not 0 <= m["at"] <= n_m:
            s.err(f"milestones[{i}] の at={m['at']} は 0〜{n_m} にしてください")
        if phases and not 0 <= m["row"] < len(phases):
            s.err(f"milestones[{i}] の row={m['row']} は 0〜{len(phases) - 1} "
                  f"(phasesのindex) にしてください")


def _v_matrix(s):
    for key in ("x_axis", "y_axis", "target_label"):
        s.req_str(key)
    points = s.req_list("points", 1, 8, "点")
    for i, p in enumerate(points or []):
        if not (isinstance(p, dict) and _is_str(p.get("name"))
                and _is_num(p.get("x")) and _is_num(p.get("y"))):
            s.err(f"points[{i}] には name (文字列) と x / y (数値) が必要です")
            continue
        if not (0.0 <= p["x"] <= 1.0 and 0.0 <= p["y"] <= 1.0):
            s.err(f"points[{i}] の x={p['x']} / y={p['y']} は 0.0〜1.0 にして"
                  f"ください (lx / ly と違い比率指定)")
        for k in ("lx", "ly"):
            if k in p and not _is_num(p[k]):
                s.err(f"points[{i}].{k} は数値 (インチ) にしてください")


def _v_hub(s):
    s.req_str("hub")
    # rendererの周辺ノード配置は6件固定。少ないと欠け、多いと黙って切り捨てられる
    ring = s.req_list("ring", 6, 6, "周辺ノード")
    for i, r in enumerate(ring or []):
        if not (isinstance(r, dict) and _is_str(r.get("name"))
                and _is_str(r.get("label"))):
            s.err(f"ring[{i}] には name / label (文字列) が必要です")


def _v_org(s):
    for key in ("top", "pm"):
        p = s.spec.get(key)
        if not (isinstance(p, dict) and _is_str(p.get("name"))
                and _is_str(p.get("sub"))):
            s.err(f'"{key}" には name / sub (文字列) が必要です')
    teams = s.req_list("teams", 1, 3, "チーム")
    for i, t in enumerate(teams or []):
        if not (isinstance(t, dict) and _is_str(t.get("name"))
                and _is_str(t.get("sub"))):
            s.err(f"teams[{i}] には name / sub (文字列) が必要です")
            continue
        members = t.get("members", [])
        if not (isinstance(members, list) and len(members) <= 3
                and all(_is_str(m) for m in members)):
            s.err(f"teams[{i}].members は文字列の配列 (最大3件) にしてください")
    ex = s.spec.get("external")
    if not (isinstance(ex, dict) and _is_str(ex.get("name"))
            and _is_str(ex.get("sub")) and _is_str(ex.get("label"))):
        s.err('"external" には name / sub / label (文字列) が必要です')


_EDGE_SIDES = {"left", "right", "top", "bottom"}
_CHANNEL_KINDS = {"left_of_col", "right_of_col", "above_row", "below_row",
                  "outside_container"}


def _v_diagram(s):
    """構成図のグリッド仕様の構造検証。

    ここで見るのはJSONとしての整合(参照切れ・型違い)まで。行間に収まるか・
    配線がコンテナを貫通しないか等の実現可能性は、レンダリング時に
    diagram_layout.py エンジン自身が対処方法つきのエラーで検出する。
    """
    d = s.spec.get("diagram")
    if not isinstance(d, dict):
        s.err('"diagram" (cols/rows/nodes/edges を持つオブジェクト) が必要です。'
              '座標は書かない(グリッド仕様のみ)')
        return
    if "spec" in s.spec or "spec" in d:
        s.err('"spec" (サンプル図の名前参照) は使えません。diagram の中に'
              'グリッド仕様をインラインで書いてください')
    if "area" in d:
        s.err("diagram.area は指定できません。描画領域は行数からエンジンが"
              "自動計算します")
    cols, rows = d.get("cols"), d.get("rows")
    for key, v in (("cols", cols), ("rows", rows)):
        if not (isinstance(v, list) and v and all(_is_str(c) for c in v)):
            s.err(f"diagram.{key} は文字列の配列 (1件以上) が必要です")
    nodes = d.get("nodes")
    if not (isinstance(nodes, dict) and nodes):
        s.err("diagram.nodes (ノード名 → {col, row, title} のオブジェクト) が"
              "必要です")
        return
    for name, n in nodes.items():
        if not isinstance(n, dict):
            s.err(f"nodes.{name} はオブジェクトにしてください")
            continue
        if not _is_str(n.get("title")):
            s.err(f"nodes.{name}.title (文字列) が必要です")
        if isinstance(cols, list) and n.get("col") not in cols:
            s.err(f"nodes.{name}.col={n.get('col')!r} が diagram.cols に"
                  f"ありません")
        if isinstance(rows, list) and n.get("row") not in rows:
            s.err(f"nodes.{name}.row={n.get('row')!r} が diagram.rows に"
                  f"ありません")
        if "icon" in n and not _is_str(n["icon"]):
            s.err(f"nodes.{name}.icon は文字列 (省略可。省略時は汎用図形ノード)"
                  f" にしてください")
        elif "icon" in n:
            assets = (Path(__file__).parent / "assets").resolve()
            icon_path = (assets / n["icon"]).resolve()
            try:
                icon_path.relative_to(assets)
            except ValueError:
                s.err(f"nodes.{name}.icon は slidegen/assets/ 内の相対パスに"
                      f"してください")
            else:
                if not icon_path.is_file():
                    s.err(f"nodes.{name}.icon={n['icon']!r} が assets/ にありません。"
                          f"Fluent一覧は fetch_fluent_icons.py --list で確認してください")
    cont_names = set()
    containers = d.get("containers", [])
    if not isinstance(containers, list):
        s.err("diagram.containers は配列にしてください")
        containers = []
    for i, c in enumerate(containers):
        if not (isinstance(c, dict) and _is_str(c.get("name"))
                and _is_str(c.get("label")) and isinstance(c.get("members"), list)):
            s.err(f"containers[{i}] には name / label (文字列) と members (配列)"
                  f" が必要です")
            continue
        for key in ("pad", "pad_x"):
            if key in c:
                s.err(f"containers[{i}].{key} は指定できません。余白は入れ子構造と"
                      "行数からエンジンが自動計算します")
        cont_names.add(c["name"])
    for i, c in enumerate(containers):
        for m in c.get("members", []):
            ref_ok = (m[1:] in cont_names if isinstance(m, str) and m.startswith("@")
                      else m in nodes)
            if not ref_ok:
                s.err(f"containers[{i}].members の {m!r} が nodes / @コンテナ名 "
                      f"に見つかりません")
    channels = d.get("channels", {})
    if not isinstance(channels, dict):
        s.err("diagram.channels はオブジェクトにしてください")
        channels = {}
    for name, ch in channels.items():
        if not (isinstance(ch, list) and len(ch) == 2
                and ch[0] in _CHANNEL_KINDS):
            s.err(f"channels.{name} は [種類, 基準] の2要素配列にしてください "
                  f"(種類: {', '.join(sorted(_CHANNEL_KINDS))})")
    edges = d.get("edges")
    if not (isinstance(edges, list) and edges):
        s.err("diagram.edges ({from, to} の配列、1件以上) が必要です")
        return
    for i, e in enumerate(edges):
        if not isinstance(e, dict):
            s.err(f"edges[{i}] はオブジェクトにしてください")
            continue
        for key in ("from", "to"):
            v = e.get(key)
            ref_ok = (v[1:] in cont_names if isinstance(v, str) and v.startswith("@")
                      else v in nodes)
            if not ref_ok:
                s.err(f"edges[{i}].{key}={v!r} が nodes / @コンテナ名 に"
                      f"見つかりません")
        for key in ("exit", "enter"):
            if key in e and e[key] not in _EDGE_SIDES:
                s.err(f"edges[{i}].{key} は {', '.join(sorted(_EDGE_SIDES))} の"
                      f"いずれかにしてください")
        for v in e.get("via", []):
            if v not in channels:
                s.err(f"edges[{i}].via の {v!r} が diagram.channels に"
                      f"ありません")


VALIDATORS = {
    "title": _v_title, "bullets": _v_bullets, "cards": _v_cards,
    "table": _v_table, "twocol": _v_twocol, "chart": _v_chart,
    "process": _v_process, "roadmap": _v_roadmap, "matrix": _v_matrix,
    "hub": _v_hub, "org": _v_org, "diagram": _v_diagram,
}


def validate(deck):
    """デッキ全体を検証し、エラーメッセージのリストを返す(空 = 合格)。"""
    errors = []
    meta = deck.get("meta")
    if not isinstance(meta, dict):
        errors.append('トップレベルに "meta" (オブジェクト) が必要です')
    else:
        for key in ("title", "footer", "date", "author"):
            if not _is_str(meta.get(key)):
                errors.append(f'meta.{key} (文字列) が必要です')
    slides = deck.get("slides")
    if not (isinstance(slides, list) and slides):
        errors.append('トップレベルに "slides" (1件以上の配列) が必要です')
        return errors
    for idx, spec in enumerate(slides):
        if not isinstance(spec, dict):
            errors.append(f"slides[{idx}]: オブジェクトにしてください")
            continue
        s = _Slide(idx, spec, errors)
        t = spec.get("type")
        if t in SAMPLE_ONLY:
            s.err('サンプル専用typeです。図の中身がコード内固定のため、新規'
                  '資料のテーマには差し替わりません。構成図は type: "diagram" '
                  'でグリッド仕様(座標なし)を書いてください')
            continue
        if t not in VALIDATORS:
            s.err(f"未対応のtypeです。使用可能: {', '.join(sorted(VALIDATORS))}")
            continue
        if t != "title":
            s.req_str("kicker")
            s.req_str("title")
        if "note" in spec and t not in NOTE_TYPES:
            s.err(f'"note" は {", ".join(sorted(NOTE_TYPES))} でのみ描画され'
                  f"ます (このtypeでは無視されるため削除してください)")
        VALIDATORS[t](s)
    return errors


def main(json_path):
    deck = json.loads(Path(json_path).read_text(encoding="utf-8"))
    errors = validate(deck)
    if errors:
        print(f"NG: {json_path} に {len(errors)} 件の問題", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        raise SystemExit(1)
    print(f"OK: {json_path} ({len(deck['slides'])} slides) 検証通過")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "content.json")
