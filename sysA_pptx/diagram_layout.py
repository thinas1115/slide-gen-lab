"""宣言的レイアウトエンジン: グリッド仕様から図解の座標を計算する。

AIが書くのは離散的な仕様(セル・メンバー・経由チャネル名)のみ。
座標はすべて本エンジンが決定論的に導出するため、いつ誰が(どのモデルが)
仕様を書いても同じ図になる。仕様の形式は diagram_specs.py を参照。
"""
from generate import BODY_TOP, BODY_W, MARGIN, note_line
from diagrams import (ACCENT, EDGE_GAP, ICON_R, LINE, NAVY, add_arrow,
                      arrow_label, container, icon_node)
from diagrams3 import route
from textfit import text_width_in

AREA = (MARGIN + 0.15, BODY_TOP + 0.28, MARGIN + BODY_W - 0.15, 6.78)
LABEL_W = 2.1          # icon_nodeのラベル幅
TITLE_H = 0.33         # アイコン下端からタイトル行下端まで
SUB_H = 0.26
CONT_HEAD = 0.30       # コンテナラベルの余白(上辺に追加)
SLOT_PITCH = 0.26      # 同一辺から複数エッジを出すときの間隔
COLORS = {"line": LINE, "navy": NAVY, "accent": ACCENT}


def _linspace(a, b, n):
    if n == 1:
        return [(a + b) / 2]
    return [a + i * (b - a) / (n - 1) for i in range(n)]


GAP = 0.06             # 行間の最小クリアランス
OVERLAP_MIN = 0.1      # コンテナ帯と前行の「横方向重なり」判定しきい値


class Layout:
    def __init__(self, spec, reserve_note=False):
        self.spec = spec
        x0, y0, x1, y1 = spec.get("area", AREA)
        if reserve_note:
            y1 -= 0.30          # 右下の出典注記スペースを確保
        cols, rows = spec["cols"], spec["rows"]
        self.cols, self.rows = cols, rows
        self.area = (x0, y0, x1, y1)
        # 端の列のラベルが領域内に収まるよう内側に寄せて等配置
        self.col_x = dict(zip(cols, _linspace(x0 + LABEL_W / 2,
                                              x1 - LABEL_W / 2, len(cols))))
        self._auto_rows()
        self.cont_rect = {}
        self._resolve_containers()

    def _half_w(self, name):
        """ノードの実効半幅(アイコンとタイトル実測幅の大きい方)。"""
        n = self.spec["nodes"][name]
        tw = text_width_in(n["title"], 10.5, "bold") + 0.1
        return max(ICON_R + 0.12, min(LABEL_W, tw) / 2)

    def _auto_rows(self):
        """内容(ラベル深さ・コンテナ帯)に応じて行位置を自動計算する。"""
        nodes = self.spec["nodes"]
        x0, y0, x1, y1 = self.area
        by_row = {r: [n for n, v in nodes.items() if v["row"] == r]
                  for r in self.rows}

        def bot_ext(r):     # 行中心→ラベル下端
            return ICON_R + TITLE_H + (SUB_H if any(
                nodes[n].get("sub") for n in by_row[r]) else 0)

        def x_range(names):
            lo = min(self.col_x[nodes[n]["col"]] - self._half_w(n) for n in names)
            hi = max(self.col_x[nodes[n]["col"]] + self._half_w(n) for n in names)
            return lo, hi

        # コンテナごとの葉ノード・行範囲・横範囲・帯の厚み
        conts = {c["name"]: c for c in self.spec.get("containers", [])}

        def leaves(c):
            out = []
            for m in c["members"]:
                out += leaves(conts[m[1:]]) if m.startswith("@") else [m]
            return out

        bands = []
        for c in self.spec.get("containers", []):
            ls = leaves(c)
            idx = [self.rows.index(nodes[n]["row"]) for n in ls]
            pad = c.get("pad", 0.3)
            pad_x = c.get("pad_x", pad)
            lo, hi = x_range(ls)
            bands.append(dict(top=min(idx), bot=max(idx), x=(lo - pad_x, hi + pad_x),
                              band=pad + CONT_HEAD, bband=pad * 0.6))
        top_stack = sum(b["band"] for b in bands if b["top"] == 0)
        bot_stack = sum(b["bband"] for b in bands if b["bot"] == len(self.rows) - 1)
        # 行ピッチ: 前行ラベル深さ + (横方向に重なるコンテナ帯) + アイコン上半分
        pitches = []
        for i in range(1, len(self.rows)):
            extra = 0.0
            prev = by_row[self.rows[i - 1]]
            for b in (b for b in bands if b["top"] == i):
                if any(min(x_range([n])[1], b["x"][1]) -
                       max(x_range([n])[0], b["x"][0]) > OVERLAP_MIN
                       for n in prev):        # ノード単位で重なり判定
                    extra += b["band"]
            pitches.append(bot_ext(self.rows[i - 1]) + extra + ICON_R + GAP)
        first = y0 + top_stack + ICON_R
        avail = y1 - first - bot_ext(self.rows[-1]) - bot_stack
        need = sum(pitches)
        if need > avail > 0:                     # 収まらなければ等比圧縮
            pitches = [p * avail / need for p in pitches]
        else:                                    # 余りは45%を上に配って重心を上げる
            first += (avail - need) * 0.45
        ys = [first]
        for p in pitches:
            ys.append(ys[-1] + p)
        self.row_y = dict(zip(self.rows, ys))

    # ---- ノード ----
    def node_center(self, name):
        n = self.spec["nodes"][name]
        return self.col_x[n["col"]], self.row_y[n["row"]]

    def _label_bottom(self, name):
        n = self.spec["nodes"][name]
        cy = self.row_y[n["row"]]
        return cy + ICON_R + TITLE_H + (SUB_H if n.get("sub") else 0)

    def node_box(self, name):
        """アイコン+ラベルの外接矩形(コンテナ計算用)。幅はタイトル実測。"""
        cx, cy = self.node_center(name)
        half_w = self._half_w(name)
        return (cx - half_w, cy - ICON_R, cx + half_w, self._label_bottom(name))

    def port(self, name, side, offset=0.0):
        """アイコン縁の矢印端点。bottomはラベルの下から出す。"""
        cx, cy = self.node_center(name)
        if side == "left":
            return (cx - ICON_R - EDGE_GAP, cy + offset)
        if side == "right":
            return (cx + ICON_R + EDGE_GAP, cy + offset)
        if side == "top":
            return (cx + offset, cy - ICON_R - EDGE_GAP)
        return (cx + offset, self._label_bottom(name) + 0.03)

    # ---- コンテナ ----
    def _resolve_containers(self):
        for c in reversed(self.spec.get("containers", [])):
            rects = [self.cont_rect[m[1:]] if m.startswith("@")
                     else self.node_box(m) for m in c["members"]]
            pad = c.get("pad", 0.3)
            pad_x = c.get("pad_x", pad)   # 左右だけ広げたい時に上下(行間計算)を巻き込まない
            self.cont_rect[c["name"]] = (
                min(r[0] for r in rects) - pad_x,
                min(r[1] for r in rects) - pad - CONT_HEAD,
                max(r[2] for r in rects) + pad_x,
                max(r[3] for r in rects) + pad * 0.6)

    # ---- チャネル(配線レーン) ----
    def channel(self, name):
        kind, ref = self.spec["channels"][name]
        if kind == "outside_container":
            # 「列の隙間」ではなく「特定コンテナ(またはノード群)のすぐ外側」を
            # 指すレーン。同じ列を共有するノード間のローカルループに使う
            # (列基準のチャネルを流用すると、隣接する無関係な列まで大回りして
            # 他コンテナの境界線を貫通する。実際に2箇所で発生した不具合)。
            ref_id, side = ref
            if isinstance(ref_id, (list, tuple)):
                # コンテナ化されていないノード群: 自前で外接矩形を計算
                boxes = [self.node_box(n) for n in ref_id]
                r = (min(b[0] for b in boxes), min(b[1] for b in boxes),
                     max(b[2] for b in boxes), max(b[3] for b in boxes))
            else:
                r = self.cont_rect[ref_id]
            gap = 0.12
            axis, pos = {"left": ("v", r[0] - gap), "right": ("v", r[2] + gap),
                        "top": ("h", r[1] - gap), "bottom": ("h", r[3] + gap)}[side]
            return axis, pos
        seq, pos = (self.cols, self.col_x) if "col" in kind else (self.rows, self.row_y)
        i = seq.index(ref)
        if kind in ("left_of_col", "above_row"):
            prev = pos[seq[i - 1]] if i else \
                (self.area[0] - 0.1 if "col" in kind else self.area[1] - 0.15)
            return ("v" if "col" in kind else "h", (prev + pos[ref]) / 2)
        nxt = pos[seq[i + 1]] if i + 1 < len(seq) else \
            (self.area[2] + 0.1 if "col" in kind else self.area[3] + 0.1)
        return ("v" if "col" in kind else "h", (pos[ref] + nxt) / 2)

    # ---- エッジ ----
    def _sides(self, e):
        src, dst = e["from"], e["to"]
        scx = (self.cont_rect[src[1:]][2] if src.startswith("@")
               else self.node_center(src)[0])
        scy = (self.row_y[e["from_row"]] if src.startswith("@")
               else self.node_center(src)[1])
        tcx, tcy = self.node_center(dst)
        dx, dy = tcx - scx, tcy - scy
        exit_d = e.get("exit") or ("right" if dx > 0.01 else
                                   "left" if dx < -0.01 else
                                   ("bottom" if dy > 0 else "top"))
        enter_d = e.get("enter") or ("left" if dx > 0.01 else
                                     "right" if dx < -0.01 else
                                     ("top" if dy > 0 else "bottom"))
        return exit_d, enter_d

    def route_edges(self, edges):
        """全エッジの経路を計算。同一辺・同一方向の多重エッジのみスロットでずらす。

        (node, side)だけをキーにすると、あるノードに「その辺から入るエッジ」と
        「その辺から出るエッジ」がたまたま1本ずつあるだけの場合まで同じグループに
        入り、無関係な2本を不要にオフセットしてジグザグな経路を作ってしまう
        (実際に発生した不具合)。in/outを区別してキーに含める。
        """
        sides = [self._sides(e) for e in edges]
        usage = {}
        for e, (xd, ed) in zip(edges, sides):
            if not e["from"].startswith("@"):
                usage.setdefault((e["from"], xd, "out"), []).append(id(e))
            usage.setdefault((e["to"], ed, "in"), []).append(id(e))

        def off(key, eid):
            ids = usage.get(key, [])
            n = len(ids)
            return (ids.index(eid) - (n - 1) / 2) * SLOT_PITCH if n > 1 else 0.0

        result = []
        for e, (exit_d, enter_d) in zip(edges, sides):
            src, dst = e["from"], e["to"]
            if src.startswith("@"):
                r = self.cont_rect[src[1:]]
                p0 = (r[2] if exit_d == "right" else r[0],
                      self.row_y[e["from_row"]])
            else:
                p0 = self.port(src, exit_d, off((src, exit_d, "out"), id(e)))
            p1 = self.port(dst, enter_d, off((dst, enter_d, "in"), id(e)))
            pts, cur = [p0], p0
            for ch in e.get("via", []):
                axis, v = self.channel(ch)
                cur = (v, cur[1]) if axis == "v" else (cur[0], v)
                pts.append(cur)
            if enter_d in ("left", "right"):
                if abs(cur[1] - p1[1]) > 0.01:
                    if not e.get("via") and abs(cur[0] - p1[0]) > 0.01:
                        cur = ((cur[0] + p1[0]) / 2, cur[1])   # 自動Z
                        pts.append(cur)
                    pts.append((cur[0], p1[1]))
            else:
                if abs(cur[0] - p1[0]) > 0.01:
                    if not e.get("via") and abs(cur[1] - p1[1]) > 0.01:
                        cur = (cur[0], (cur[1] + p1[1]) / 2)
                        pts.append(cur)
                    pts.append((p1[0], cur[1]))
            pts.append(p1)
            result.append([p for i, p in enumerate(pts)
                           if i == 0 or p != pts[i - 1]])
        return result

    # ---- 意味情報を使った自己検証(check_layout.pyでは検出不可能な領域) ----
    def _container_leaves(self):
        conts = {c["name"]: c for c in self.spec.get("containers", [])}

        def leaves(c):
            out = []
            for m in c["members"]:
                out += leaves(conts[m[1:]]) if m.startswith("@") else [m]
            return out
        return {name: set(leaves(c)) for name, c in conts.items()}

    @staticmethod
    def _crossings(pts, rect):
        """折れ線ptsが矩形rectの境界を横切った回数。"""
        def inside(p):
            return rect[0] < p[0] < rect[2] and rect[1] < p[1] < rect[3]
        states = [inside(p) for p in pts]
        return sum(a != b for a, b in zip(states, states[1:]))

    def _exempt_containers(self, e):
        """このエッジのviaが outside_container(コンテナ名, ...) を明示的に
        経由している場合、そのコンテナは「意図的な迂回」として境界越境を許可する。
        (ノード群指定 [..] は実コンテナではないので対象外)
        """
        out = set()
        for ch in e.get("via", []):
            kind, ref = self.spec["channels"][ch]
            if kind == "outside_container" and not isinstance(ref[0], (list, tuple)):
                out.add(ref[0])
        return out

    def validate_edges(self, edges, routed):
        """コンテナ所属が同じノード同士のエッジが、そのコンテナの境界を
        不要に横切っていないかを検証する。列基準のチャネルを性質の違う
        配線(ローカルループ等)に流用すると起きる不具合(過去に2回発生)を、
        画像を見なくても生成時点で検出するための仕組み。
        via で outside_container(そのコンテナ, ...) を明示的に使っている
        エッジは、意図的な迂回として2回分の越境まで許可する。
        """
        leaves = self._container_leaves()
        errors = []
        for e, pts in zip(edges, routed):
            src, dst = e["from"], e["to"]
            if src.startswith("@") or dst.startswith("@"):
                continue
            exempt = self._exempt_containers(e)
            for cname, members in leaves.items():
                s_in, d_in = src in members, dst in members
                expected = 0 if s_in == d_in else 1
                if cname in exempt:
                    expected += 2
                actual = self._crossings(pts, self.cont_rect[cname])
                if actual > expected:
                    errors.append(
                        f"edge {src}->{dst} crosses container '{cname}' boundary "
                        f"{actual} time(s) (expected <= {expected}). "
                        f"列基準チャネルを流用していないか、またはoutside_containerの"
                        f"via指定漏れを確認してください。")
        if errors:
            raise ValueError("diagram_layout: 配線がコンテナ境界を貫通しています:\n  "
                             + "\n  ".join(errors))


def render_diagram(slide, spec, note=None):
    lay = Layout(spec, reserve_note=bool(note))
    edges = spec.get("edges", [])
    routed = lay.route_edges(edges)
    lay.validate_edges(edges, routed)
    for c in spec.get("containers", []):
        r = lay.cont_rect[c["name"]]
        container(slide, r[0], r[1], r[2] - r[0], r[3] - r[1], c["label"],
                  COLORS.get(c.get("color", "line"), LINE), dash=c.get("dash"))
    for name, n in spec["nodes"].items():
        cx, cy = lay.node_center(name)
        icon_node(slide, cx, cy, n["icon"], n["title"], n.get("sub"))
    for e, pts in zip(edges, routed):
        if len(pts) == 2 and e.get("both"):
            add_arrow(slide, *pts[0], *pts[1], dash=e.get("dash"), both=True)
        else:
            route(slide, pts, dash=e.get("dash"))
        if e.get("label"):
            segs = list(zip(pts[:-1], pts[1:]))
            a, b = (segs[e["label_seg"]] if "label_seg" in e else
                    max(segs, key=lambda s: abs(s[1][0] - s[0][0])
                        + abs(s[1][1] - s[0][1])))
            # 水平セグメントは線の上側にずらす(近接ノードとの干渉回避)。
            # 垂直セグメントは線上に置き、白背景で線をマスクする。
            dy = -0.17 if abs(b[1] - a[1]) < 0.01 else 0.0
            arrow_label(slide, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + dy,
                        e["label"], w=e.get("label_w", 1.1), size=8.5)
    if note:
        note_line(slide, note)
