"""高密度AWS構成図: マルチAZ本番構成(表現力の限界検証)。

ポイント: プリセットのカギ線コネクタは折れ位置を制御できず他ノードを
貫通しうるため、ウェイポイント明示のroute()で配線レーンを自分で決める。
"""
from pptx.enum.shapes import MSO_CONNECTOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

from generate import GRAY, MARGIN, NAVY, add_text, header
from diagrams import (EDGE_GAP, ICON_R, LINE, add_arrow, arrow_label,
                      container, icon_node, left_of, right_of)

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
    # レーン定義: 列X(流れ順)・行Y(サービス段)・配線専用レーン
    C = {"user": 0.95, "edge": 2.6, "fg_a": 5.35, "alb": 7.0, "fg_c": 8.7,
         "svc": 11.55}
    R = {"dns": 2.58, "alb": 3.05, "s3": 3.4, "web": 4.2, "fg": 4.4,
         "cw": 5.3, "rds": 5.5}
    LANE = {"north": 2.2,       # VPCの上を通る水平レーン(CF→ALB)
            "west": 3.45,       # VPCの左を通る垂直レーン
            "loop_a": 4.35,     # AZ-a内のFG→RDS折り返し
            "loop_c": 9.7,      # AZ-c内のFG→RDS折り返し
            "east": 10.7}       # VPCとsvc列の間の垂直レーン
    CLOUD = (1.85, 1.8, 10.9, 4.78)
    VPC = (3.75, 2.6, 6.55, 3.82)
    vpc_right = VPC[0] + VPC[2]
    # コンテナ(3階層: Cloud > VPC > AZ)
    container(slide, *CLOUD, "AWS Cloud", LINE)
    container(slide, *VPC, "VPC", NAVY, dash=None)
    container(slide, 3.9, 3.85, 2.95, 2.42, "AZ-a (private)", AZ_GRAY, dash="dash")
    container(slide, 7.2, 3.85, 2.95, 2.42, "AZ-c (private)", AZ_GRAY, dash="dash")
    # ノード(サブネット内はラベル1段でスペース節約)
    icon_node(slide, C["user"], R["web"], "users.png", "社内ユーザー")
    icon_node(slide, C["edge"], R["dns"], "route53.png", "Route 53")
    icon_node(slide, C["edge"], R["web"], "cloudfront.png", "CloudFront")
    icon_node(slide, C["alb"], R["alb"], "alb.png", "ALB")
    icon_node(slide, C["fg_a"], R["fg"], "fargate.png", "Fargate")
    icon_node(slide, C["fg_c"], R["fg"], "fargate.png", "Fargate")
    icon_node(slide, C["fg_a"], R["rds"], "rds.png", "RDS (primary)")
    icon_node(slide, C["fg_c"], R["rds"], "rds.png", "RDS (standby)")
    icon_node(slide, C["svc"], R["s3"], "s3.png", "Amazon S3", "成果物/静的配信")
    icon_node(slide, C["svc"], R["cw"], "cloudwatch.png", "CloudWatch", "監視・ログ")
    # 配線(直角レーン)
    route(slide, [(right_of(C["user"]), R["web"]), (left_of(C["edge"]), R["web"])])
    route(slide, [(C["edge"], 3.24), (C["edge"], R["web"] - ICON_R - EDGE_GAP)],
          dash="dash")                                             # R53→CF(ラベルの下から)
    arrow_label(slide, C["edge"], 3.53, "名前解決", w=1.0, size=8)
    route(slide, [(right_of(C["edge"]), R["web"]), (LANE["west"], R["web"]),
                  (LANE["west"], LANE["north"]), (C["alb"], LANE["north"]),
                  (C["alb"], R["alb"] - ICON_R - EDGE_GAP)])       # CF→ALB(上面へ)
    arrow_label(slide, 5.2, LANE["north"], "HTTPS", w=1.0)
    route(slide, [(left_of(C["alb"]), R["alb"]), (C["fg_a"], R["alb"]),
                  (C["fg_a"], R["fg"] - ICON_R - EDGE_GAP)])       # ALB→FG-a
    route(slide, [(right_of(C["alb"]), R["alb"]), (C["fg_c"], R["alb"]),
                  (C["fg_c"], R["fg"] - ICON_R - EDGE_GAP)])       # ALB→FG-c
    route(slide, [(C["fg_a"] - ICON_R, R["fg"]), (LANE["loop_a"], R["fg"]),
                  (LANE["loop_a"], R["rds"]), (C["fg_a"] - ICON_R, R["rds"])])
    route(slide, [(C["fg_c"] + ICON_R, R["fg"]), (LANE["loop_c"], R["fg"]),
                  (LANE["loop_c"], R["rds"]), (C["fg_c"] + ICON_R, R["rds"])])
    add_arrow(slide, C["fg_a"] + ICON_R, R["rds"], C["fg_c"] - ICON_R, R["rds"],
              dash="dash", both=True)                              # RDS同期
    arrow_label(slide, (C["fg_a"] + C["fg_c"]) / 2, R["rds"] - 0.18, "同期",
                w=0.8, size=8)
    route(slide, [(C["fg_c"] + ICON_R, R["fg"] - 0.15), (LANE["east"], R["fg"] - 0.15),
                  (LANE["east"], R["s3"]), (left_of(C["svc"]), R["s3"])])  # FG-c→S3
    arrow_label(slide, 10.0, R["fg"] - 0.34, "成果物", w=0.9, size=8)
    route(slide, [(vpc_right, R["cw"]), (left_of(C["svc"]), R["cw"])], dash="dash")
    add_text(slide, MARGIN, 6.68, 6.0, 0.25,
             "※ 両AZのFargateからS3へ書き込む(図は片側のみ表記)", 8.5, color=GRAY)
    if spec.get("note"):
        from generate import note_line
        note_line(slide, spec["note"])