"""高密度AWS構成図: マルチAZ本番構成(表現力の限界検証)。

ポイント: プリセットのカギ線コネクタは折れ位置を制御できず他ノードを
貫通しうるため、ウェイポイント明示のroute()で配線レーンを自分で決める。
"""
from pptx.enum.shapes import MSO_CONNECTOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

from generate import GRAY, MARGIN, NAVY, add_text, header
from diagrams import LINE, add_arrow, arrow_label, container, icon_node

AZ_GRAY = LINE


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


def s_aws2(slide, spec, page):
    header(slide, spec["kicker"], spec["title"])
    # コンテナ(3階層: Cloud > VPC > AZ)
    container(slide, 1.85, 1.8, 10.9, 4.78, "AWS Cloud", LINE)
    container(slide, 3.75, 2.6, 6.55, 3.82, "VPC", NAVY, dash=None)
    container(slide, 3.9, 3.85, 2.95, 2.42, "AZ-a (private)", AZ_GRAY, dash="dash")
    container(slide, 7.2, 3.85, 2.95, 2.42, "AZ-c (private)", AZ_GRAY, dash="dash")
    # ノード(サブネット内はラベル1段でスペース節約)
    icon_node(slide, 0.95, 4.2, "users.png", "社内ユーザー")
    icon_node(slide, 2.6, 2.58, "route53.png", "Route 53")
    icon_node(slide, 2.6, 4.2, "cloudfront.png", "CloudFront")
    icon_node(slide, 7.0, 3.05, "alb.png", "ALB")
    icon_node(slide, 5.35, 4.4, "fargate.png", "Fargate")
    icon_node(slide, 8.7, 4.4, "fargate.png", "Fargate")
    icon_node(slide, 5.35, 5.5, "rds.png", "RDS (primary)")
    icon_node(slide, 8.7, 5.5, "rds.png", "RDS (standby)")
    icon_node(slide, 11.55, 3.4, "s3.png", "Amazon S3", "成果物/静的配信")
    icon_node(slide, 11.55, 5.3, "cloudwatch.png", "CloudWatch", "監視・ログ")
    # 配線(直角レーン)
    route(slide, [(1.32, 4.2), (2.23, 4.2)])                       # user→CF
    route(slide, [(2.6, 3.24), (2.6, 3.83)], dash="dash")          # R53→CF(ラベルの下から)
    arrow_label(slide, 2.6, 3.53, "名前解決", w=1.0, size=8)
    route(slide, [(2.97, 4.2), (3.45, 4.2), (3.45, 2.2),
                  (7.0, 2.2), (7.0, 2.68)])                        # CF→ALB(上面へ)
    arrow_label(slide, 5.2, 2.2, "HTTPS", w=1.0)
    route(slide, [(6.63, 3.05), (5.35, 3.05), (5.35, 4.03)])       # ALB→FG-a
    route(slide, [(7.37, 3.05), (8.7, 3.05), (8.7, 4.03)])         # ALB→FG-c
    route(slide, [(5.04, 4.4), (4.35, 4.4), (4.35, 5.5), (5.04, 5.5)])  # FG-a→RDS-a
    route(slide, [(9.01, 4.4), (9.7, 4.4), (9.7, 5.5), (9.01, 5.5)])    # FG-c→RDS-c
    conn = add_arrow(slide, 5.66, 5.5, 8.39, 5.5, dash="dash", both=True)  # RDS同期
    arrow_label(slide, 7.02, 5.32, "同期", w=0.8, size=8)
    route(slide, [(9.01, 4.25), (10.7, 4.25), (10.7, 3.4), (11.18, 3.4)])  # FG-c→S3
    arrow_label(slide, 10.0, 4.06, "成果物", w=0.9, size=8)
    route(slide, [(10.3, 5.3), (11.18, 5.3)], dash="dash")         # VPC→CW
    add_text(slide, MARGIN, 6.68, 6.0, 0.25,
             "※ 両AZのFargateからS3へ書き込む(図は片側のみ表記)", 8.5, color=GRAY)
    if spec.get("note"):
        from generate import note_line
        note_line(slide, spec["note"])