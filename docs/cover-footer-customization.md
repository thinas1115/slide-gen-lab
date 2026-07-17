# 表紙・フッター設定

表紙とフッターだけをユーザーごとに変更する場合は、`content.json` とは別の設定JSONを使う。
本文renderer、構成図レイアウト、本文領域の座標は変更されない。

## 実行方法

設定例を指定して生成する。

```powershell
python slidegen/generate_from_json.py content.json out/deck.pptx --cover-footer-config examples/cover_footer.json
python slidegen/check_layout.py out/deck.pptx
```

`--cover-footer-config` を省略すると、従来と同じ表紙・フッターで生成する。
個人や部署専用の設定をリポジトリへ登録しない場合は、リポジトリ直下の
`cover_footer.local.json` を使用できる。このファイルは `.gitignore` 対象だが、
自動読込はしないためCLIで明示する。

```powershell
python slidegen/generate_from_json.py content.json out/deck.pptx --cover-footer-config cover_footer.local.json
```

カスタム表紙背景は `slidegen/assets/cover/` に配置する。ルートの
`cover_footer.local.json` からは `slidegen/assets/cover/<ファイル名>`、同梱の
`examples/cover_footer.json` からは `../slidegen/assets/cover/<ファイル名>` で参照する。

同じオプションは次のgeneratorでも使用できる。

- `slidegen/generate.py`
- `slidegen/generate2.py`
- `slidegen/generate_patterns.py`

## content.jsonとの責任分担

`content.json` の `meta` は資料ごとに変わる内容を持つ。

| 項目 | 用途 |
|---|---|
| `meta.title` | 資料名。フッター設定の `{title}` から参照できる |
| `meta.footer` | 資料固有のフッター文言。`{footer}` から参照できる |
| `meta.date` | 表紙の日付と `{date}` |
| `meta.author` | 表紙の作成者と `{author}` |

表紙・フッター設定JSONは、表示する要素、固定文言、配色、表紙背景画像を持つ。資料内容とブランド設定を
分離することで、同じ `content.json` を利用者別の表紙・フッターで再生成できる。

## 設定項目

### cover

| 項目 | 型 | 既定値 / 説明 |
|---|---|---|
| `eyebrow` | string | 左上の文書区分。既定値は空文字。最大48文字 |
| `show_date` | boolean | 右上の日付を表示する。既定値は `true` |
| `show_author` | boolean | 左下の作成者を表示する。既定値は `true` |
| `show_rail` | boolean | 右側の補足情報を表示する。既定値は `false` |
| `rail` | array | `label` / `value` の組。0〜3件 |
| `background_image` | string / null | 表紙背景のPNG/JPEG。設定JSONからの相対パスを推奨。絶対パスも使用可能 |
| `background_color` | string | 表紙背景の6桁HEX色 |
| `title_color` | string | タイトル・作成者・rail値の6桁HEX色 |
| `secondary_color` | string | サブタイトル・日付・rail線の6桁HEX色 |

### footer

| 項目 | 型 | 既定値 / 説明 |
|---|---|---|
| `text` | string | 左側の文言。最大100文字 |
| `show_divider` | boolean | 本文との境界線を表示する |
| `show_text` | boolean | 左側の文言を表示する |
| `show_page_number` | boolean | 現在ページを表示する |
| `show_total` | boolean | 総ページ数も表示する |
| `text_color` | string | 左側文言・総ページ数の6桁HEX色 |
| `page_color` | string | 現在ページの6桁HEX色 |
| `divider_color` | string | 境界線の6桁HEX色 |

設定JSONは部分指定できる。省略した項目には標準設定が使われる。
`background_image` を指定すると、画像の縦横比を維持したまま中央基準で表紙全面へトリミングする。
画像を指定しない場合は `background_color` が使われる。画像上の文字が読めるよう、画像に合わせて
`title_color` と `secondary_color` も指定する。背景には16:9で十分な解像度の画像を推奨する。
画像は生成時にPPTXへ埋め込まれるため、生成後の閲覧時に元画像は不要。
標準表紙は、タイトル、サブタイトル、日付、作成者だけを表示する。右側の補足情報を使う場合は
`DATE / ORGANIZATION / OWNER` に統一する。

- `DATE`: `{date}` を指定する。右上の日付と重複するため `show_date` は `false` にする。
- `ORGANIZATION`: 会社名、部門名、チーム名を表紙設定へ固定値で記載する。資料ごとに生成AIへ作文させない。
- `OWNER`: `{author}` を指定する。左下の作成者と重複するため `show_author` は `false` にする。

`ORGANIZATION`と`OWNER`の値は最大3行。JSON文字列内の`\n`で改行位置を指定でき、改行を
指定しない長い文言も幅に合わせて自動折り返しする。会社名・部門名・チーム名、または氏名・役職を
別の行へ分ける。4行以上になる場合は文字を潰して描画せず、生成を停止する。`DATE`などそれ以外の
補足値は1行で表示する。

`SCOPE`へページ数やパターン数、`OUTPUT`へPowerPointやPDF、`QUALITY`へ生成・検証工程を書く例は、
受け手の判断情報にならないため使用しない。左上の`eyebrow`は「経営会議資料」「計画書」「レビュー版」
など文書区分が必要な場合だけ使い、タイトルの英訳や言い換えは書かない。補足情報自体が不要なら、
装飾のために空欄を残さず `show_rail`を`false`のまま使う。

```json
{
  "cover": {
    "eyebrow": "社内検討資料",
    "background_image": "../slidegen/assets/cover/cover-background.png",
    "title_color": "FFFFFF",
    "secondary_color": "E5ECEA",
    "show_date": false,
    "show_author": false,
    "show_rail": true,
    "rail": [
      {"label": "DATE", "value": "{date}"},
      {"label": "ORGANIZATION", "value": "業務企画本部\n業務改革部\n業務改善推進チーム"},
      {"label": "OWNER", "value": "{author}\nテンプレート整備責任者"}
    ]
  },
  "footer": {
    "text": "{title}",
    "show_total": false
  }
}
```

## プレースホルダー

`cover.eyebrow`、`cover.rail[*].label`、`cover.rail[*].value`、`footer.text` では
次のプレースホルダーを使える。

- `{title}`
- `{footer}`
- `{date}`
- `{author}`
- `{page}`
- `{total}`

数値にはPythonの書式指定を使用できる。例: `{page:02d}`、`{total:02d}`。
未対応のプレースホルダー、6桁HEX以外の色、4件以上のrail、未知の設定項目は
PPTX生成前にエラーになる。

## 意図的に設定対象にしないもの

- 表紙・フッターの座標とサイズ
- 本文領域の上下端
- スライドタイトル、カード、表、図解など本文rendererの配色
- 構成図のノード・配線・コンテナ
- フォント

これらまで変更すると表紙・フッターの個人設定ではなく全体テーマ変更になり、全rendererの
再検証が必要になる。全体テーマを変更する場合は `DESIGN_CUSTOMIZATION.md` を参照する。
