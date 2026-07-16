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
    cols = ["entry", "control", "service", "data", "ops"]
    rows = ["channel", "application", "platform", "operation"]
    icons = ["globe", "shield", "app", "database", "monitor"]
    row_names = ["受付", "業務", "基盤", "運用"]
    nodes = {}
    for row_index, row in enumerate(rows):
        for col_index, col in enumerate(cols):
            name = f"n{row_index}_{col_index}"
            nodes[name] = {
                "col": col,
                "row": row,
                "icon": f"fluent/{icons[col_index]}.png",
                "title": f"{row_names[row_index]}機能 {col_index + 1}",
                "sub": "処理・監視",
            }
    edges = []
    for row_index in range(len(rows)):
        for col_index in range(len(cols) - 1):
            edges.append({
                "from": f"n{row_index}_{col_index}",
                "to": f"n{row_index}_{col_index + 1}",
            })
    return {
        "cols": cols,
        "rows": rows,
        "nodes": nodes,
        "containers": [{
            "name": "platform",
            "label": "全社業務プラットフォーム",
            "members": list(nodes),
        }],
        "channels": {},
        "edges": edges,
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
            "title": "20機能を4層に分けて全体像を俯瞰する",
            "lead": "20ノードを同一ページへ配置し、余白圧縮後のアイコン縮小を確認します。",
            "diagram": LARGE_DIAGRAM,
        },
    ],
}
