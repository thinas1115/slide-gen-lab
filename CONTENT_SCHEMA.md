# content.json schema

`content.json` はスライド内容を表すJSON。座標、余白、フォント、色、描画順は renderer が決める。

重要: 「content.jsonだけで生成できる」とは、各 `type` が要求する必須フィールドをすべて持つJSONを用意する、という意味。自由文だけでは生成できない。

既存の `content.json` と `sysA_pptx/content.py` はサンプルデッキ。新規資料の題材作成には使わない。

## Top Level

必須:

- `meta.title`: string
- `meta.footer`: string
- `meta.date`: string
- `meta.author`: string
- `slides`: slide object の配列

```json
{
  "meta": {
    "title": "資料タイトル",
    "footer": "フッター文言",
    "date": "2026年7月",
    "author": "作成者"
  },
  "slides": []
}
```

## Common Rules

- `slides[*].type` は必須。
- `type: "title"` 以外は `kicker` と `title` が必須。
- JSONなので、Pythonのタプルではなく配列を使う。
- 新規資料では `aws` / `aws2` を使わない。現状は固定サンプル図で、任意テーマの構成図rendererではない。

## Supported Types

### title

用途: 表紙。

必須:

- `type`: `"title"`
- `title`: string
- `subtitle`: string

```json
{
  "type": "title",
  "title": "資料タイトル",
  "subtitle": "サブタイトル"
}
```

### bullets

用途: 箇条書き、目次、要点整理。

必須:

- `type`: `"bullets"`
- `kicker`: string
- `title`: string
- `bullets`: `[text, null]` の配列

制約:

- `bullets` は3〜5件程度が安全。
- 2要素目は現状未使用。`null` にする。

```json
{
  "type": "bullets",
  "kicker": "分類",
  "title": "タイトル",
  "bullets": [
    ["箇条書き本文", null],
    ["箇条書き本文", null]
  ]
}
```

### cards

用途: サマリ、KPI、論点整理。

必須:

- `type`: `"cards"`
- `kicker`: string
- `title`: string
- `cards`: `[heading, body]` の配列

制約:

- `cards` は3〜4件程度が安全。
- 件数に応じて横並び幅が自動計算される。

```json
{
  "type": "cards",
  "kicker": "分類",
  "title": "タイトル",
  "cards": [
    ["カード見出し", "カード本文"],
    ["カード見出し", "カード本文"]
  ]
}
```

### table

用途: 比較表、評価表、一覧。

必須:

- `type`: `"table"`
- `kicker`: string
- `title`: string
- `columns`: string の配列
- `col_widths`: number の配列
- `rows`: string配列の配列

任意:

- `note`: string

制約:

- `columns`, `col_widths`, 各 `rows[*]` の要素数は同じにする。
- `col_widths` の合計はおおむね `11.8` inch。厳密には `BODY_W` との差が `0.6` 未満なら通る。
- 行数は3〜6行程度が安全。

```json
{
  "type": "table",
  "kicker": "分類",
  "title": "タイトル",
  "columns": ["項目", "説明"],
  "col_widths": [2.5, 9.2],
  "rows": [
    ["値1", "説明1"],
    ["値2", "説明2"]
  ],
  "note": "任意の注記"
}
```

### twocol

用途: Before/After、比較、メリット/注意点。

必須:

- `type`: `"twocol"`
- `kicker`: string
- `title`: string
- `left.heading`: string
- `left.bullets`: string の配列
- `right.heading`: string
- `right.bullets`: string の配列

制約:

- 左右それぞれ3〜5項目程度が安全。

```json
{
  "type": "twocol",
  "kicker": "分類",
  "title": "タイトル",
  "left": {
    "heading": "左見出し",
    "bullets": ["本文", "本文"]
  },
  "right": {
    "heading": "右見出し",
    "bullets": ["本文", "本文"]
  }
}
```

### chart

用途: 横棒グラフ。

必須:

- `type`: `"chart"`
- `kicker`: string
- `title`: string
- `chart.categories`: string の配列
- `chart.series`: `[series_name, values]` の配列

任意:

- `note`: string

制約:

- 各 `values` の長さは `categories` と同じにする。
- 系列は1〜2件、カテゴリは3〜5件程度が安全。

```json
{
  "type": "chart",
  "kicker": "分類",
  "title": "タイトル",
  "chart": {
    "categories": ["カテゴリ1", "カテゴリ2"],
    "series": [
      ["系列名", [10, 20]]
    ]
  },
  "note": "任意の注記"
}
```

### process

用途: 手順、業務フロー、導入ステップ。

必須:

- `type`: `"process"`
- `kicker`: string
- `title`: string
- `steps`: object の配列
- `steps[*].name`: string
- `steps[*].desc`: string
- `steps[*].actor`: string

任意:

- `emph`: 強調するstepの0始まりindex配列
- `note`: string

制約:

- `steps` は4〜5件が安全。

```json
{
  "type": "process",
  "kicker": "分類",
  "title": "タイトル",
  "steps": [
    {"name": "工程名", "desc": "説明", "actor": "担当"}
  ],
  "emph": [0]
}
```

### roadmap

用途: ガント風ロードマップ。

必須:

- `type`: `"roadmap"`
- `kicker`: string
- `title`: string
- `months`: string の配列
- `phases`: object の配列
- `phases[*].name`: string
- `phases[*].goal`: string
- `phases[*].bar`: string
- `phases[*].start`: number
- `phases[*].end`: number
- `milestones`: object の配列
- `milestones[*].at`: number
- `milestones[*].row`: number
- `milestones[*].label`: string

制約:

- `months` は6件が最も安定。
- `phases` は3件が前提に近い。
- `start`, `end`, `at` は月列のindex基準。6か月なら `0` から `6` の範囲。
- `milestones[*].row` は対応する `phases` の0始まりindex。

```json
{
  "type": "roadmap",
  "kicker": "分類",
  "title": "タイトル",
  "months": ["7月", "8月", "9月", "10月", "11月", "12月"],
  "phases": [
    {"name": "Phase 1", "goal": "目的", "bar": "バー内文言", "start": 0, "end": 2}
  ],
  "milestones": [
    {"at": 2, "row": 0, "label": "判定"}
  ]
}
```

### matrix

用途: 2軸マップ、ポジショニング。

必須:

- `type`: `"matrix"`
- `kicker`: string
- `title`: string
- `x_axis`: string
- `y_axis`: string
- `target_label`: string
- `points`: object の配列
- `points[*].name`: string
- `points[*].x`: number
- `points[*].y`: number

任意:

- `points[*].emph`: boolean
- `points[*].lx`: number
- `points[*].ly`: number
- `note`: string

制約:

- `x`, `y` は `0.0` から `1.0`。
- 点は4〜7件程度が安全。
- ラベルが重なる場合は `lx` / `ly` で位置を調整する。

```json
{
  "type": "matrix",
  "kicker": "分類",
  "title": "タイトル",
  "x_axis": "横軸ラベル",
  "y_axis": "縦軸ラベル",
  "target_label": "強調領域ラベル",
  "points": [
    {"name": "点ラベル", "x": 0.5, "y": 0.5, "emph": true}
  ],
  "note": "任意の注記"
}
```

### hub

用途: ステークホルダー関係図。

必須:

- `type`: `"hub"`
- `kicker`: string
- `title`: string
- `hub`: string
- `ring`: object の配列
- `ring[*].name`: string
- `ring[*].label`: string

任意:

- `ring[*].sub`: string
- `note`: string

制約:

- `ring` は6件。rendererの配置が6件前提。

```json
{
  "type": "hub",
  "kicker": "分類",
  "title": "タイトル",
  "hub": "中央ラベル",
  "ring": [
    {"name": "周辺ノード", "sub": "補足", "label": "関係ラベル"}
  ]
}
```

### org

用途: 体制図。

必須:

- `type`: `"org"`
- `kicker`: string
- `title`: string
- `top.name`: string
- `top.sub`: string
- `pm.name`: string
- `pm.sub`: string
- `teams`: object の配列
- `teams[*].name`: string
- `teams[*].sub`: string
- `external.name`: string
- `external.sub`: string
- `external.label`: string

任意:

- `teams[*].members`: string の配列
- `note`: string

制約:

- `teams` は3件が最も安定。
- `members` は各チーム0〜3件程度が安全。

```json
{
  "type": "org",
  "kicker": "分類",
  "title": "タイトル",
  "top": {"name": "最上位", "sub": "補足"},
  "pm": {"name": "中核", "sub": "補足"},
  "teams": [
    {"name": "チーム名", "sub": "役割", "members": ["メンバー"]}
  ],
  "external": {"name": "外部支援", "sub": "補足", "label": "関係ラベル"}
}
```

## Not Supported For New Decks

### aws / aws2

`aws` と `aws2` は固定サンプル図。`content.json` のノード・矢印から任意の構成図を作るrendererではない。

新規資料では使わない。
