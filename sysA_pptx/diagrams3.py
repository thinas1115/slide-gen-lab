"""直角配線ユーティリティ。

ポイント: プリセットのカギ線コネクタは折れ位置を制御できず他ノードを
貫通しうるため、ウェイポイント明示のroute()で配線レーンを決める。
(旧ハンドコード版 s_aws2 は diagram_layout.py + diagram_specs.py に移行済み)
"""
from pptx.enum.shapes import MSO_CONNECTOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

from diagrams import LINE, add_arrow


def _plain_line(slide, x1, y1, x2, y2, *, color=LINE, width=1.25, dash=None):
    conn = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    conn.line.color.rgb = color
    conn.line.width = Pt(width)
    conn.shadow.inherit = False
    if dash:
        ln = conn.line._get_or_add_ln()
        ln.insert(0, ln.makeelement(qn("a:prstDash"), {"val": dash}))
    return conn


def route(slide, pts, *, dash=None, width=1.25):
    """ウェイポイント列を直線で結び、最終セグメントだけ矢印にする。"""
    for (x1, y1), (x2, y2) in zip(pts[:-2], pts[1:-1]):
        _plain_line(slide, x1, y1, x2, y2, dash=dash, width=width)
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    add_arrow(slide, x1, y1, x2, y2, dash=dash, width=width)

