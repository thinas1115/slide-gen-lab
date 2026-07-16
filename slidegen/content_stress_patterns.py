"""段階的縮小が実際に発動する大規模入力の検証デッキ。"""


TABLE_ROWS = [
    [
        f"領域 {i + 1}",
        "運用部門と開発部門で確認する。" * 2,
        "運用部門と開発部門で確認する。" * 2,
        "運用部門と開発部門で確認する。" * 2,
    ]
    for i in range(5)
]


def _large_diagram():
    nodes = {
        "user": {"col": "edge", "row": "north", "icon": "fluent/people.png",
                 "title": "社内利用者"},
        "dns": {"col": "ingress", "row": "north", "icon": "fluent/globe.png",
                "title": "DNS"},
        "config": {"col": "app_a", "row": "north", "icon": "fluent/settings.png",
                   "title": "構成管理"},
        "idp": {"col": "app_b", "row": "north", "icon": "fluent/key.png",
                "title": "ID基盤"},
        "audit": {"col": "data", "row": "north", "icon": "fluent/history.png",
                  "title": "監査サービス"},
        "cdn": {"col": "edge", "row": "web", "icon": "fluent/cloud.png",
                "title": "CDN"},
        "waf": {"col": "ingress", "row": "web", "icon": "fluent/shield.png",
                "title": "WAF"},
        "alb": {"col": "app_a", "row": "web", "icon": "fluent/gateway.png",
                "title": "ロードバランサ"},
        "api": {"col": "app_b", "row": "web", "icon": "fluent/app.png",
                "title": "業務API"},
        "portal": {"col": "data", "row": "web", "icon": "fluent/browser.png",
                   "title": "業務ポータル"},
        "notify": {"col": "edge", "row": "async", "icon": "fluent/mail.png",
                   "title": "通知サービス"},
        "queue": {"col": "ingress", "row": "async", "icon": "fluent/task.png",
                  "title": "処理キュー"},
        "worker_a": {"col": "app_a", "row": "async", "icon": "fluent/server.png",
                     "title": "ワーカーA"},
        "worker_b": {"col": "app_b", "row": "async", "icon": "fluent/server.png",
                     "title": "ワーカーB"},
        "cache": {"col": "data", "row": "async", "icon": "fluent/storage.png",
                  "title": "キャッシュ"},
        "archive": {"col": "edge", "row": "storage", "icon": "fluent/archive.png",
                    "title": "長期保管"},
        "backup": {"col": "ingress", "row": "storage", "icon": "fluent/sync.png",
                   "title": "バックアップ"},
        "db_a": {"col": "app_a", "row": "storage", "icon": "fluent/database.png",
                 "title": "DB Primary"},
        "db_b": {"col": "app_b", "row": "storage", "icon": "fluent/database.png",
                 "title": "DB Standby"},
        "monitor": {"col": "data", "row": "storage", "icon": "fluent/monitor.png",
                    "title": "統合監視"},
    }
    return {
        "cols": ["edge", "ingress", "app_a", "app_b", "data"],
        "rows": ["north", "web", "async", "storage"],
        "nodes": nodes,
        "containers": [
            {"name": "cloud", "label": "業務クラウド",
             "members": ["dns", "config", "idp", "audit", "cdn", "notify",
                         "archive", "@public", "@private"]},
            {"name": "public", "label": "公開サービス",
             "members": ["waf", "alb", "api", "portal"], "dash": "dash"},
            {"name": "private", "label": "非公開サービス",
             "members": ["queue", "worker_a", "worker_b", "cache", "backup",
                         "db_a", "db_b", "monitor"], "dash": "dash"},
        ],
        "channels": {
            "public_entry": ["outside_container", ["public", "top_inside"]],
            "private_entry": ["outside_container", ["private", "top_inside"]],
            "left_of_app_a": ["left_of_col", "app_a"],
            "right_of_app_b": ["right_of_col", "app_b"],
            "private_right": ["outside_container", ["private", "right"]],
            "cloud_right": ["outside_container", ["cloud", "right"]],
            "public_left": ["outside_container", ["public", "left"]],
        },
        "edges": [
            {"from": "user", "to": "dns", "label": "DNS"},
            {"from": "dns", "to": "cdn", "exit": "left", "enter": "right",
             "via": ["public_left"], "dash": "dash"},
            {"from": "cdn", "to": "waf", "label": "HTTPS"},
            {"from": "waf", "to": "alb"},
            {"from": "alb", "to": "api"},
            {"from": "api", "to": "portal"},
            {"from": "config", "to": "alb", "exit": "bottom", "enter": "top",
             "via": ["public_entry"], "dash": "dash"},
            {"from": "idp", "to": "api", "exit": "bottom", "enter": "top",
             "via": ["public_entry"], "label": "認証", "dash": "dash"},
            {"from": "api", "to": "queue", "exit": "bottom", "enter": "top",
             "via": ["private_entry"]},
            {"from": "api", "to": "worker_a", "exit": "bottom", "enter": "top",
             "via": ["private_entry"]},
            {"from": "api", "to": "worker_b", "exit": "bottom", "enter": "top",
             "via": ["private_entry"]},
            {"from": "queue", "to": "notify"},
            {"from": "worker_b", "to": "cache"},
            {"from": "worker_a", "to": "db_a", "exit": "left", "enter": "left",
             "via": ["left_of_app_a"]},
            {"from": "worker_b", "to": "db_b", "exit": "right", "enter": "right",
             "via": ["right_of_app_b"]},
            {"from": "db_a", "to": "db_b", "both": True, "dash": "dash",
             "label": "同期"},
            {"from": "db_a", "to": "backup"},
            {"from": "backup", "to": "archive"},
            {"from": "audit", "to": "monitor", "exit": "right", "enter": "right",
             "via": ["cloud_right"], "dash": "dash"},
            {"from": "cache", "to": "monitor", "exit": "right", "enter": "right",
             "via": ["private_right"], "dash": "dash"},
        ],
    }


LARGE_DIAGRAM = _large_diagram()

STRESS_PATTERN_DECK = {
    "meta": {
        "title": "段階的縮小ストレス検証",
        "footer": "段階的縮小ストレス検証",
        "date": "2026年7月",
        "author": "業務改善検討チーム",
    },
    "slides": [
        {
            "type": "table",
            "kicker": "大規模表",
            "title": "5領域の責任分担と判断基準を一覧化する",
            "lead": "セル内の情報量を増やし、余白圧縮とフォント縮小の発動を確認します。",
            "columns": ["領域", "対象", "確認事項", "判断基準"],
            "col_widths": [1.6, 2.6, 4.0, 4.0],
            "rows": TABLE_ROWS,
        },
        {
            "type": "diagram",
            "kicker": "大規模構成図",
            "title": "20機能の同期・非同期・監視経路を1枚で俯瞰する",
            "lead": "分岐・合流・縦接続・外周迂回・入れ子境界を含む構成で縮小耐性を確認します。",
            "diagram": LARGE_DIAGRAM,
        },
    ],
}
