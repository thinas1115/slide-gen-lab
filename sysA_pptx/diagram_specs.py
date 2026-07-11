"""図解の宣言的仕様。座標は書かない(diagram_layout.pyが計算する)。

書くのは:
  cols/rows   : グリッドの列・行の並び(名前だけ)
  nodes       : ノード = (列, 行, アイコン, ラベル)
  containers  : メンバー列挙(外側から順に。@名前 で子コンテナ参照)
  channels    : 配線レーン = ("left_of_col"|"right_of_col"|"above_row"|"below_row", 基準セル)
  edges       : from/to(+必要なら exit/enter 辺, via チャネル, label)
"""

AWS_SIMPLE = {
    "cols": ["user", "alb", "ecs", "svc", "dept"],
    "rows": ["top", "mid", "bot"],
    "nodes": {
        "user": {"col": "user", "row": "mid", "icon": "users.png",
                 "title": "社内ユーザー", "sub": "ブラウザ"},
        "alb": {"col": "alb", "row": "mid", "icon": "alb.png",
                "title": "ALB", "sub": "内部LB"},
        "ecs": {"col": "ecs", "row": "mid", "icon": "fargate.png",
                "title": "ECS Fargate", "sub": "生成API (python-pptx)"},
        "bedrock": {"col": "svc", "row": "top", "icon": "bedrock.png",
                    "title": "Amazon Bedrock", "sub": "Claude (構成JSON生成)"},
        "s3": {"col": "svc", "row": "mid", "icon": "s3.png",
               "title": "Amazon S3", "sub": "テンプレート/成果物"},
        "cw": {"col": "svc", "row": "bot", "icon": "cloudwatch.png",
               "title": "CloudWatch", "sub": "ログ・監査証跡"},
        "dept": {"col": "dept", "row": "mid", "icon": "user.png",
                 "title": "利用部門", "sub": "ダウンロード"},
    },
    "containers": [
        {"name": "cloud", "label": "AWS Cloud",
         "members": ["@vpc", "bedrock", "s3", "cw"], "color": "line"},
        {"name": "vpc", "label": "VPC (private)", "members": ["alb", "ecs"],
         "color": "accent", "dash": "dash", "pad": 0.24},
    ],
    "channels": {},
    "edges": [
        {"from": "user", "to": "alb", "label": "HTTPS"},
        {"from": "alb", "to": "ecs"},
        {"from": "ecs", "to": "bedrock", "label": "構成生成", "label_seg": 0},
        {"from": "ecs", "to": "s3", "label": "読み書き"},
        {"from": "ecs", "to": "cw"},
        {"from": "s3", "to": "dept", "label": "署名URL"},
    ],
}

AWS_MULTIAZ = {
    "cols": ["user", "edge", "fg_a", "alb", "fg_c", "svc"],
    "rows": ["north", "web", "fg", "rds"],
    "nodes": {
        "user": {"col": "user", "row": "web", "icon": "users.png",
                 "title": "社内ユーザー"},
        "r53": {"col": "edge", "row": "north", "icon": "route53.png",
                "title": "Route 53"},
        "cf": {"col": "edge", "row": "web", "icon": "cloudfront.png",
               "title": "CloudFront"},
        "alb": {"col": "alb", "row": "web", "icon": "alb.png", "title": "ALB"},
        "fg_a": {"col": "fg_a", "row": "fg", "icon": "fargate.png",
                 "title": "Fargate"},
        "fg_c": {"col": "fg_c", "row": "fg", "icon": "fargate.png",
                 "title": "Fargate"},
        "rds_a": {"col": "fg_a", "row": "rds", "icon": "rds.png",
                  "title": "RDS (primary)"},
        "rds_c": {"col": "fg_c", "row": "rds", "icon": "rds.png",
                  "title": "RDS (standby)"},
        "s3": {"col": "svc", "row": "web", "icon": "s3.png",
               "title": "Amazon S3", "sub": "成果物/静的配信"},
        "cw": {"col": "svc", "row": "rds", "icon": "cloudwatch.png",
               "title": "CloudWatch", "sub": "監視・ログ"},
    },
    "containers": [
        {"name": "cloud", "label": "AWS Cloud",
         "members": ["@vpc", "r53", "cf", "s3", "cw"], "pad": 0.22},
        {"name": "vpc", "label": "VPC (private subnets)",
         "members": ["alb", "@az_a", "@az_c"], "color": "navy", "pad": 0.18},
        {"name": "az_a", "label": "AZ-a", "members": ["fg_a", "rds_a"],
         "dash": "dash", "pad": 0.14},
        {"name": "az_c", "label": "AZ-c", "members": ["fg_c", "rds_c"],
         "dash": "dash", "pad": 0.14},
    ],
    "channels": {
        "far_west": ("left_of_col", "edge"),
        "west": ("left_of_col", "fg_a"),
        "east_c": ("right_of_col", "fg_c"),
    },
    "edges": [
        {"from": "user", "to": "cf"},
        {"from": "r53", "to": "cf", "exit": "left", "enter": "left",
         "via": ["far_west"], "dash": "dash", "label": "名前解決",
         "label_w": 1.0},
        {"from": "cf", "to": "alb", "label": "HTTPS", "label_w": 1.0},
        {"from": "alb", "to": "fg_a", "enter": "top"},
        {"from": "alb", "to": "fg_c", "enter": "top"},
        {"from": "fg_a", "to": "rds_a", "exit": "left", "enter": "left",
         "via": ["west"]},
        {"from": "fg_c", "to": "rds_c", "exit": "right", "enter": "right",
         "via": ["east_c"]},
        {"from": "rds_a", "to": "rds_c", "both": True, "dash": "dash",
         "label": "同期", "label_w": 0.8},
        {"from": "fg_c", "to": "s3", "exit": "top", "label": "成果物",
         "label_seg": 0, "label_w": 0.9},
        {"from": "@vpc", "to": "cw", "from_row": "rds", "dash": "dash"},
    ],
}

DIAGRAMS = {"aws_simple": AWS_SIMPLE, "aws_multiaz": AWS_MULTIAZ}
