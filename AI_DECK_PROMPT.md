# AI向け: 新規デッキ作成プロンプト

新しい説明資料を作るときに、生成AIへ渡す依頼文の**穴埋めテンプレート**。

使い方:

1. 下の「依頼文テンプレート」全体をコピーする。
2. 「資料要件」にある6つの入力欄を、作成対象の資料に合わせて具体値で埋める。
   **空欄のまま渡さない**(何を作るか伝わらず、サンプルの焼き直しになる)。
3. 埋めたテンプレートと `CONTENT_SCHEMA.md` の中身を、生成AIに渡す。

## 依頼文テンプレート

あなたは `pptxdsl` のスライド内容作成担当です。
`CONTENT_SCHEMA.md` に従って、新しい `content.json` を作成してください。
既存の `content.json` / `slidegen/content.py` は動作確認用のサンプルなので、参照しないでください。

資料要件:

- テーマ: `<ここにテーマを書く>`
- 想定読者: `<例: 社内の企画部門、役員、開発チーム>`
- 目的: `<例: 概要理解、導入判断、比較検討、教育>`
- 必ず含めたい内容: `<箇条書きで入力>`
- 使ってよい情報源: `<添付資料、URL、メモなど。なければ「ユーザー提供情報のみ」>`
- 枚数目安: `<例: 6〜10枚>`

出力要件:

1. `CONTENT_SCHEMA.md` と同じJSON構造で出力する。
2. `meta.title`, `meta.footer`, `slides[*].title`, `slides[*].kicker`, 本文はすべて「資料要件」の
   テーマ・想定読者・目的に合わせて新規作成する。
3. 既存サンプルの題材・文言・固有名詞・数値を流用しない。
4. 実在の構成・組織・数値が分からない場合は、勝手に具体化しない。代わりに「要確認」または一般的な概念説明にする。
5. 構成図(システム構成・ネットワーク構成など)は `diagram` type を使い、`CONTENT_SCHEMA.md` の
   グリッド仕様(列・行・ノード・エッジ)を**「資料要件」のテーマと情報源に基づいて新規に**書く。
   **座標やサイズの数値は一切書かない**(レイアウトエンジンが計算する)。全ノードの `icon` は必須。
   同梱済みのFluent 72種またはAWSアイコンから選び、存在しないファイル名を発明しない。
6. `aws` / `aws2` は廃止済みの旧type名なので使わない。構成図は `diagram` で新規に書く。
7. `cards` は、KPI・選択肢・事例など、各項目が独立して比較できる場合に使う。サマリ・事例は `style: "editorial"`、KPIは `style: "metrics"` を選ぶ。情報量が少ないことだけを理由に使わず、フェーズ名や図のノードなど別の構造に属する要素をカード化しない。
8. 表紙以外では、タイトルと本文の間に要旨が必要な場合だけ任意の `lead` を使う。結論・前提・読み方を1〜2行で書き、タイトルの言い換えや本文の繰り返しは書かない。不要なスライドにはフィールド自体を付けない。
9. 写真、イラスト、画面キャプチャなど、1枚のビジュアル自体が主メッセージになる場合は `image` を使う。
   画像生成・利用者提供・Web検索のいずれでも、利用可能な画像を先に `slidegen/assets/images/` へ用意し、
   存在する相対パスだけを書く。画像が未提供なら架空のパスを作らず、必要な画像の要件を資料要件に対する確認事項として扱う。
   Web画像は取得元・権利者・利用条件を確認し、`source`へ記録する。
10. `type` は `CONTENT_SCHEMA.md` に載っているものだけ使う。件数制約も `validate_content.py` が機械検証する。フェーズ単位の計画は `roadmap`、複数テーマ内の並行作業は `program_roadmap` を使い分ける。
11. JSON以外の説明文を付けない。

対応済み `type`:

- `title`
- `bullets`
- `cards`
- `table`
- `twocol`
- `chart`
- `image` (生成・提供・検索画像を本文領域へ大きく配置)
- `process`
- `roadmap`
- `program_roadmap`
- `matrix`
- `hub`
- `org`
- `diagram` (構成図。グリッド仕様から自動レイアウト、座標記述は禁止)

## 実行コマンド

生成されたJSONを `content.json` として保存してから実行する。

```powershell
python slidegen/validate_content.py content.json
python slidegen/generate_from_json.py content.json out\deck_from_json.pptx
python slidegen\check_layout.py out\deck_from_json.pptx
powershell -ExecutionPolicy Bypass -File render.ps1 -PptxPath out\deck_from_json.pptx -OutDir out\png_from_json
python contact_sheet.py out\png_from_json
```

1行目の検証は `generate_from_json.py` も生成前に自動実行する(NGなら生成されない)。
検証エラーが出たら、エラーメッセージ(`slides[番号] (type=種別): 内容` 形式)をそのままAIに渡して `content.json` を直させる。

`out\png_from_json\sheet.png` を確認し、内容がテーマから逸れていないか、既存サンプルの題材が混ざっていないか、文字溢れや重なりがないかを見る。
