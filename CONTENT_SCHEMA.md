# content.json schema

`content.json` はスライドの内容だけを持つ。座標、余白、フォント、色、描画順は renderer 側で決める。

既存の `content.json` は動作確認用のサンプルデッキなので、新規資料の題材作成には使わない。
生成AIに渡す参照資料は、このschemaと `AI_DECK_PROMPT.md` を基本にする。

## Top Level

```json
{
  "meta": {
    "title": "資料タイトル",
    "footer": "フッター文言",
    "date": "YYYY年M月",
    "author": "作成者"
  },
  "slides": []
}
```

## Common Fields

`title` 以外のスライドは、基本的に `kicker` と `title` を持つ。

```json
{
  "type": "cards",
  "kicker": "短い分類ラベル",
  "title": "スライドタイトル"
}
```

## Supported Slide Types

### title

```json
{
  "type": "title",
  "title": "資料タイトル",
  "subtitle": "サブタイトル"
}
```

### bullets

```json
{
  "type": "bullets",
  "kicker": "分類",
  "title": "タイトル",
  "bullets": [
    ["箇条書き本文", null]
  ]
}
```

### cards

```json
{
  "type": "cards",
  "kicker": "分類",
  "title": "タイトル",
  "cards": [
    ["カード見出し", "カード本文"]
  ]
}
```

### table

```json
{
  "type": "table",
  "kicker": "分類",
  "title": "タイトル",
  "columns": ["列1", "列2"],
  "col_widths": [3.0, 8.7],
  "rows": [
    ["値1", "値2"]
  ],
  "note": "任意の注記"
}
```

`col_widths` の合計はおおむね `11.8` inch にする。

### twocol

```json
{
  "type": "twocol",
  "kicker": "分類",
  "title": "タイトル",
  "left": {
    "heading": "左見出し",
    "bullets": ["本文"]
  },
  "right": {
    "heading": "右見出し",
    "bullets": ["本文"]
  }
}
```

### chart

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

`emph` は強調する工程の0始まりindex。

### roadmap

```json
{
  "type": "roadmap",
  "kicker": "分類",
  "title": "タイトル",
  "months": ["1月", "2月", "3月"],
  "phases": [
    {"name": "Phase 1", "goal": "目的", "bar": "バー内文言", "start": 0, "end": 1.5}
  ],
  "milestones": [
    {"at": 1.5, "row": 0, "label": "判定"}
  ]
}
```

### matrix

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

`x` と `y` は `0.0` から `1.0`。
ラベルが近い場合は `lx` / `ly` で位置を微調整できる。

### hub

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

`ring` は6件を想定。

### org

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

### aws / aws2

`aws` と `aws2` は、現時点では固定構成の表現力検証用renderer。
対象システムの実構成が提供されていない新規資料では使わない。
