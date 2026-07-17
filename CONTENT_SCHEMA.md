# content.json schema

`content.json` はスライド内容を表すJSON。座標、余白、フォント、色、描画順は renderer が決める。

重要: 「content.jsonだけで生成できる」とは、各 `type` が要求する必須フィールドをすべて持つJSONを用意する、という意味。自由文だけでは生成できない。

既存の `content.json` と `slidegen/content.py` はサンプルデッキ。新規資料の題材作成には使わない。

## 機械検証

このschemaの必須フィールドと件数制約は `slidegen/validate_content.py` が機械的に検証する。
`generate_from_json.py` は生成前に自動で検証し、NGなら生成せずエラー一覧を出す。
件数制約を通過しても、実際の文言量によってはrendererの収容判定で生成を停止する。rendererは
標準配置、裁量余白の圧縮、ジャンルごとに定めた文字・図形の縮小を順に試し、提出品質を保つ
最小値でも収まらない場合は黙って溢れさせない。エラーに従って文言を短くする、項目を減らす、
スライドを分割する、または新しいレイアウタを実装する。`content.json`へ座標やサイズを追加して回避しない。
単体で検証だけ行う場合:

```powershell
python slidegen/validate_content.py content.json
```

エラーメッセージは `slides[番号] (type=種別): 内容` の形式。生成AIにそのまま渡して直させる。

## トップレベル

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

## 共通ルール

- `slides[*].type` は必須。
- `type: "title"` 以外は `kicker` と `title` が必須。
- `type: "title"` 以外は `lead` (string) を任意指定できる。タイトル直下に要旨を置き、指定時だけ本文開始位置が下がる。未指定時の本文位置は変わらない。
- `lead` は本文を読む前に伝える結論・前提・読み方を1〜2行で書く。単なるタイトルの言い換えや本文項目の列挙には使わない。文字数の固定上限はないが、最小フォントでも領域へ収まらない場合は生成を停止する。
- JSONなので、Pythonのタプルではなく配列を使う。
- `note` (右下の注記) が描画されるのは `table` / `chart` / `process` / `roadmap` / `program_roadmap` / `matrix` / `hub` / `org` / `diagram` のみ。それ以外のtypeに書いても無視される(validatorがエラーにする)。
- 構成図は `diagram` type で書く(グリッド仕様のみ、座標の数値は書かない)。
- `aws` / `aws2` は廃止済みの旧type名であり、`generate_from_json.py` は受け付けない(validatorが拒否する)。

```json
{
  "type": "bullets",
  "kicker": "検討結果",
  "title": "標準化により資料作成の手戻りを減らせる",
  "lead": "先に共通の型を定め、例外だけを個別設計する方針が有効です。",
  "bullets": [
    ["レビュー観点を揃えられる", null],
    ["再生成しても配置が変わらない", null]
  ]
}
```

## 対応type

### title

用途: 表紙。

必須:

- `type`: `"title"`
- `title`: string
- `subtitle`: string

制約:

- `title`は資料の主題を端的に示す。
- `subtitle`は対象範囲または目的を1文で示し、タイトルを言い換えない。
- ページ数、PowerPoint/PDFなどのファイル形式、生成・検証工程は記載しない。
- 日付、組織名、責任者は表紙・フッター設定側で表示し、`title` / `subtitle`へ重複して書かない。

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

- `bullets` は3〜5件程度が安全(validatorの上限は6件)。
- 各要素は `["本文", null]` の2要素配列。2要素目は互換用の予約フィールドで現状未使用。
  `null` 固定にする(文字列だけを直接並べるとエラーになる)。

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

用途: 独立したサマリ、KPI、選択肢、事例の比較。出力は枠線に頼らないフラットな編集的カードになる。

必須:

- `type`: `"cards"`
- `kicker`: string
- `title`: string
- `cards`: `[heading, body]` の配列

任意:

- `style`: `"editorial"`(既定) / `"metrics"`

制約:

- `cards` は3〜4件が安全(validatorの範囲は2〜4件)。
- 件数に応じて横並び幅が自動計算される。
- 各項目が独立して比較できる場合に使う。フェーズ名や図のノードなど、別の構造に属する要素には使わない。
- `editorial`: サマリ・選択肢・事例向け。2〜3件は横並び、4件は先頭を主項目、残り3件を補助項目として描画する。
- `metrics`: KPI向け。数値を含む見出しを大きく扱う横並びカードとして描画する。

```json
{
  "type": "cards",
  "style": "editorial",
  "kicker": "分類",
  "title": "タイトル",
  "cards": [
    ["要点見出し", "要点本文"],
    ["要点見出し", "要点本文"]
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

- `columns`, `col_widths`, 各 `rows[*]` の要素数は同じにする(2〜8列)。
- `col_widths` の合計はおおむね `12.2` inch(本文幅 `BODY_W` = 12.23。差が `0.6` 未満なら通る)。
- 行数は3〜6行程度が安全(validatorの上限は8行)。

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
- 左右を枠付きパネルにせず、中央罫線とタイポグラフィで比較関係を示す。

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
- 系列は1〜2件(validator強制)、カテゴリは3〜5件程度が安全(validatorの上限は6件)。

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

### image

用途: 写真、イラスト、画面キャプチャ、生成画像など、1枚の画像を本文の主役として大きく見せる。

必須:

- `type`: `"image"`
- `kicker`: string
- `title`: string
- `image`: `slidegen/assets/`からの相対PNG/JPEGパス。本文画像は`images/<ファイル名>`を推奨

任意:

- `fit`: `"contain"`または`"cover"`。既定値は`"contain"`
- `shadow`: boolean。`true`なら画像へ外側の「オフセット: 右下」影を付ける。既定値は`false`
- `alt`: 画像を見られない受け手向けの代替説明。PPTX内の画像説明へ設定する

挙動:

- `contain`は画像全体を表示し、余白が生じても縦横比を維持する。画面キャプチャ、図版、資料画像に向く。
- `cover`は本文枠全体を埋め、中央を基準に上下または左右をトリミングする。写真や背景的なビジュアルに向く。
- 画像は引き伸ばさない。leadで利用可能領域が減った場合は、裁量余白、画像の順で縮小し、最小値でも
  収まらなければ生成を停止する。
- 本文画像の下にcaption/source枠は置かない。画像の説明が必要な場合は`lead`を使う。
- URLを直接指定しない。画像生成、手元の画像、Web検索のいずれでも、使用可能なファイルを先に
  `slidegen/assets/images/`へ置いてから参照する。
- Web画像は取得元と利用条件を確認する。リポジトリへ同梱する場合は
  `slidegen/assets/CREDITS.md`にも出典とライセンスを記録する。

```json
{
  "type": "image",
  "kicker": "利用イメージ",
  "title": "完成後の業務画面を大きく見せる",
  "lead": "利用者が最初に確認する情報と操作導線を示します。",
  "image": "images/product-screen.png",
  "fit": "cover",
  "shadow": true,
  "alt": "主要指標と操作ボタンが並ぶ業務ダッシュボード画面"
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

- `steps` は4〜5件が安全(validatorの範囲は3〜6件)。

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

用途: フェーズ単位のガント風ロードマップ。1フェーズにつき1本のバーを置く。

必須:

- `type`: `"roadmap"`
- `kicker`: string
- `title`: string
- `months`: string の配列
- `phases`: object の配列
- `phases[*].name`: string
- `phases[*].goal`: string
- `phases[*].bar`: string
- `phases[*].start`: number または `months` 内の期間ラベル
- `phases[*].end`: number または `months` 内の期間ラベル
- `milestones`: object の配列
- `milestones[*].at`: number または `months` 内の期間ラベル
- `milestones[*].row`: number
- `milestones[*].label`: string

制約:

- `months` は重複しない3〜12件。月以外に四半期、週、工程名なども使える。
- `phases` は1〜6件。4件以上ではrendererが余白・行高・文字を段階的に縮小する。
- 数値の `start`, `end`, `at` は期間列の境界index。12期間なら `0` から `12` の範囲。
- 期間ラベルの `start` は該当列の開始、`end` は該当列を含む終了、`at` は該当列の中央として扱う。
- 数値indexと期間ラベルは混在できるが、AI生成では読みやすい期間ラベル指定を推奨する。
- `milestones[*].row` は対応する `phases` の0始まりindex。不要なら `"milestones": []`。

```json
{
  "type": "roadmap",
  "kicker": "分類",
  "title": "タイトル",
  "months": ["4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月", "1月", "2月", "3月"],
  "phases": [
    {"name": "Phase 1", "goal": "目的", "bar": "バー内文言", "start": "4月", "end": "6月"}
  ],
  "milestones": [
    {"at": "6月", "row": 0, "label": "判定"}
  ]
}
```

### program_roadmap

用途: 複数テーマに複数作業があり、同じ時間軸で並行関係を示すプログラム工程表。
作業期間が重なる場合はrendererが同一テーマ内のレーンを自動で増やす。

必須:

- `type`: `"program_roadmap"`
- `kicker`: string
- `title`: string
- `periods`: 重複しないstringの配列
- `tracks`: objectの配列
- `tracks[*].name`: string
- `tracks[*].activities`: objectの配列
- `tracks[*].activities[*].label`: string
- `tracks[*].activities[*].start`: number または `periods` 内の期間ラベル
- `tracks[*].activities[*].end`: number または `periods` 内の期間ラベル

任意:

- `tracks[*].activities[*].emph`: boolean。重要作業を強調する
- `note`: string

制約:

- `periods` は3〜12件、`tracks` は1〜6件。
- 各`activities`は1〜8件、全テーマ合計24件まで。
- 月ヘッダーは`periods`の単位のまま変えず、作業線の開始・終了だけを1/4期間単位で動かせる。
- 数値の`start` / `end`は0.25刻みの期間境界index。12か月なら`0`から`12`の範囲。
  `0`は最初の月の開始、`0.25`は最初の月の1/4経過、`0.5`は月半ば、
  `0.75`は3/4経過、`1`は次月の開始を表す。
- 期間ラベルの`start`は該当月の開始、`end`は該当月を含む終了として従来どおり扱う。
- 0.25刻み以外の数値はvalidatorが拒否する。
- 同じテーマ内で重なる作業は入力順や座標指定ではなく、期間の重なりから自動レーン配置する。
- 最小設定でも収まらない場合は、テーマまたは同時並行作業を減らしてスライドを分割する。

```json
{
  "type": "program_roadmap",
  "kicker": "年間計画",
  "title": "複数テーマの並行作業を年間計画として俯瞰する",
  "periods": ["4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月", "1月", "2月", "3月"],
  "tracks": [
    {
      "name": "利用部門の拡大",
      "activities": [
        {"label": "対象業務の選定", "start": 0.25, "end": 2.75},
        {"label": "追加部門へ展開", "start": 7.5, "end": 12, "emph": true}
      ]
    },
    {
      "name": "運用基盤の再設計",
      "activities": [
        {"label": "移行方針の策定", "start": "6月", "end": "9月"},
        {"label": "新環境の構築", "start": "7月", "end": "10月"}
      ]
    }
  ],
  "note": "作業期間の重なりからレーン数を自動計算する。"
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
- `quadrants`: `[左下, 右下, 左上, 右上]` の4文字列
- `note`: string

制約:

- `x`, `y` は `0.0` から `1.0` の比率(validator強制)。
- 点は4〜7件程度が安全(validatorの上限は8件)。
- ラベルが重なる場合は `lx` / `ly` で位置を調整する。**単位はインチ**(x/yと違い比率ではない)。点の中心からのオフセットで、`lx` 正=右、`ly` 正=下。省略時は点の上 (`ly=-0.36`) に出る。

```json
{
  "type": "matrix",
  "kicker": "分類",
  "title": "タイトル",
  "x_axis": "横軸ラベル",
  "y_axis": "縦軸ラベル",
  "target_label": "強調領域ラベル",
  "quadrants": ["左下", "右下", "左上", "右上"],
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
- `ring[*].icon`: string。`icons/fluent/〜.png` を指定する

任意:

- `ring[*].sub`: string
- `note`: string

制約:

- `ring` はちょうど6件(validator強制)。rendererの周辺ノード配置が6件固定のため、5件では欠け、7件では黙って切り捨てられる。

```json
{
  "type": "hub",
  "kicker": "分類",
  "title": "タイトル",
  "hub": "中央ラベル",
  "ring": [
      {"name": "周辺ノード", "sub": "補足", "label": "関係ラベル", "icon": "icons/fluent/team.png"}
  ]
}
```

### org

用途: 組織図・プロジェクト体制図・責任分担図。複数の責任者、複数階層、
分岐・合流、助言関係、横連携を表現できる。

必須:

- `type`: `"org"`
- `kicker`: string
- `title`: string
- `org.nodes`: ノードID → object
  - `name`: 表示名
- `org.levels`: 上位から順に並べた階層の配列。各階層はノードIDの配列

任意:

- `org.nodes[*].sub`: 役割・責任範囲などの補足
- `org.nodes[*].members`: メンバー名・担当名の配列
- `org.nodes[*].style`: `"primary" | "accent" | "standard" | "external"`
- `org.edges`: 関係の配列
  - `from` / `to`: 接続するノードID
  - `kind`: `"reporting" | "advice" | "collaboration"`。省略時は`reporting`
  - `label`: 関係ラベル。`advice`と`collaboration`だけに指定できる
- `note`: string

制約:

- `levels` は1〜6階層、1階層あたり1〜5ノード。
- すべてのノードを`levels`のいずれか1階層へ1回だけ配置する。
- `members` は各ノード0〜4件。
- `reporting`は上位階層から下位階層へ接続する。1段飛ばし、複数親、複数子を指定できる。
- 隣接階層の`reporting`は、同じ連結成分の親群と子群を1本の共有幹へまとめる。
  一般的な体制図と同じく、親ごと・子ごとに横線を重ねない。
- `advice`と`collaboration`は点線。`collaboration`は双方向矢印になる。
- 座標・箱サイズ・線の経由点は書かない。レイアウタが階層数と情報量から自動計算する。
- 標準配置で収まらない場合は、階層間余白の圧縮、箱と文字の縮小を順に行う。
  提出品質を保つ最小値でも収まらない場合は生成を停止する。

```json
{
  "type": "org",
  "kicker": "分類",
  "title": "タイトル",
  "org": {
    "nodes": {
      "owner_a": {"name": "事業責任者", "sub": "投資判断", "style": "primary"},
      "owner_b": {"name": "技術責任者", "sub": "技術判断", "style": "primary"},
      "pm": {"name": "プログラムPM", "sub": "全体統括", "style": "accent"},
      "advisor": {"name": "外部専門家", "sub": "助言", "style": "external"},
      "team_a": {"name": "業務設計", "sub": "要件・運用", "members": ["企画", "現場"]},
      "team_b": {"name": "開発", "sub": "実装・試験", "members": ["アプリ", "基盤"]}
    },
    "levels": [
      ["owner_a", "owner_b"],
      ["pm", "advisor"],
      ["team_a", "team_b"]
    ],
    "edges": [
      {"from": "owner_a", "to": "pm"},
      {"from": "owner_b", "to": "pm"},
      {"from": "advisor", "to": "pm", "kind": "advice", "label": "助言"},
      {"from": "pm", "to": "team_a"},
      {"from": "pm", "to": "team_b"},
      {"from": "team_a", "to": "team_b", "kind": "collaboration", "label": "連携"}
    ]
  }
}
```

### diagram

用途: システム構成図・ネットワーク構成図など、ノードと配線の図。

**座標・サイズの数値は一切書かない。** グリッド仕様(列・行・メンバー列挙)だけを書き、座標は `diagram_layout.py` エンジンが決定論的に計算する。「9.55のような数値を書きたくなったら仕様の書き方が間違っている」が設計思想。

必須:

- `type`: `"diagram"`
- `kicker`: string
- `title`: string
- `diagram.cols`: 列名の配列(左から順)
- `diagram.rows`: 行名の配列(上から順)
- `diagram.nodes`: ノード名 → object
  - `col` / `row`: 所属セル(cols/rowsの名前)
  - `title`: 表示名
  - `sub`: 補足ラベル(任意)
  - `icon`: `slidegen/assets/` からの相対PNGパス(必須)。同梱Fluent/AWSアイコンから選ぶ
    - Fluentアイコン(`icons/fluent/<名前>.png`、72種同梱済み)。次の名前だけを使い、ファイル名を発明しない。`python slidegen/fetch_fluent_icons.py --list` でも確認できる
      - インフラ・端末: `server` `router` `database` `desktop` `laptop` `tablet` `phone` `printer` `hard_drive` `storage`
      - ネットワーク・クラウド: `cloud` `globe` `wifi` `ethernet` `link` `gateway` `sync` `upload` `download` `switch`
      - セキュリティ: `shield` `shield_lock` `shield_check` `lock` `key` `certificate`
      - 人物・組織・拠点: `people` `team` `person` `contact` `organization` `briefcase` `building` `branch` `factory` `store` `warehouse` `home`
      - アプリ・データ・文書: `app` `browser` `terminal` `code` `bot` `ai` `folder` `document` `file_data` `archive`
      - コミュニケーション・業務: `mail` `chat` `video` `call` `send` `calendar` `task` `cart` `money` `chart`
      - 運用・状態: `alert` `warning` `info` `check` `search` `clock` `history` `settings` `toolbox` `wrench` `monitor`
      - 物理移動: `truck` `car` `airplane`
    - AWSアイコン(同梱済み): `icons/aws/alb.png` `icons/aws/bedrock.png` `icons/aws/cloudfront.png` `icons/aws/cloudwatch.png` `icons/aws/dynamodb.png` `icons/aws/ecr.png` `icons/aws/fargate.png` `icons/aws/rds.png` `icons/aws/route53.png` `icons/aws/s3.png` `icons/aws/sqs.png` `icons/aws/user.png` `icons/aws/users.png` のみ。増やす場合は `extract_aws_icons.py`
- `diagram.edges`: object の配列
  - `from` / `to`: ノード名(または `@コンテナ名`)
  - `label` / `label_w`: 線上ラベルと幅(任意)
  - `exit` / `enter`: 発着辺 `"left" | "right" | "top" | "bottom"`(任意。省略時は位置関係から自動)
  - `via`: 経由チャネル名の配列(任意)
  - `dash`: `"dash"` で点線、`both`: true で双方向(任意)

任意:

- `diagram.containers`: 外接枠。object の配列(外側から順)
  - `name` / `label` / `members`(ノード名または `@子コンテナ名` の列挙)
  - `color` / `dash`
- `diagram.channels`: 配線レーン。`名前: [種類, 基準]` のobject
  - 種類: `"left_of_col"` / `"right_of_col"` / `"above_row"` / `"below_row"` / `"outside_container"`
  - `outside_container` の基準は `[コンテナ名, "left"|"right"|"top"|"bottom"|"top_inside"]`
  - 同じ列を共有するノード間のローカルループ(折り返し)には必ず `outside_container` を使う
- `note`: string

```json
{
  "type": "diagram",
  "kicker": "新構成",
  "title": "新基盤の構成",
  "diagram": {
    "cols": ["user", "gw", "app"],
    "rows": ["main"],
    "nodes": {
      "pc": {"col": "user", "row": "main", "icon": "icons/fluent/desktop.png", "title": "利用者端末"},
      "fw": {"col": "gw", "row": "main", "icon": "icons/fluent/shield.png", "title": "ファイアウォール"},
      "web": {"col": "app", "row": "main", "icon": "icons/fluent/server.png", "title": "業務サーバ", "sub": "アプリ本体"}
    },
    "containers": [
      {"name": "dc", "label": "データセンター", "members": ["fw", "web"]}
    ],
    "channels": {},
    "edges": [
      {"from": "pc", "to": "fw", "label": "HTTPS", "label_w": 1.0},
      {"from": "fw", "to": "web"}
    ]
  }
}
```

制約:

- 参照整合(col/rowの存在、edges/membersのノード参照、viaのチャネル参照)はvalidatorが検証する。
- 描画領域とコンテナ余白は、行数とコンテナの入れ子構造からエンジンが自動計算する。`area` / `pad` / `pad_x` は入力できない。
- 行間に収まるか・配線がコンテナを貫通しないか等は、生成時にエンジン自身が対処方法つきのエラーで検出する(収まらない場合は行数・sub・ラベルを減らす)。
- ノードは10個程度・4行程度までが安全(それ以上は縦に収まらずエラーになる)。
- 名前付きテンプレート参照はない。仕様は必ず `diagram` にインラインで書く。

## 廃止済みtype名

### aws / aws2

`aws` と `aws2` は、固定構成図rendererで使われていた廃止済みtype名。renderer一覧には登録されていない。

**`generate_from_json.py` はこの2つのtypeを受け付けない**(validate_content.py が生成前に拒否する)。ドキュメント上の禁止ではなく機械的に通らない。

構成図が必要な場合は `diagram` type でグリッド仕様を新規に書く。回帰検証用のサンプル図も
`diagram_specs.py` または `content_patterns.py` のインライン仕様から生成する。
