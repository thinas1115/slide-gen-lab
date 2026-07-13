# AI向け: 新規デッキ作成プロンプト

このリポジトリで新しい説明資料を作るときは、生成AIにこの内容を渡す。

## 依頼文テンプレート

あなたは `slide-gen-lab` のスライド内容作成担当です。
`CONTENT_SCHEMA.md` に従って、新しい `content.json` を作成してください。
既存の `content.json` / `sysA_pptx/content.py` は動作確認用のサンプルなので、参照しないでください。

今回作る資料:

- テーマ: `<ここにテーマを書く>`
- 想定読者: `<例: 社内の企画部門、役員、開発チーム>`
- 目的: `<例: 概要理解、導入判断、比較検討、教育>`
- 必ず含めたい内容: `<箇条書きで入力>`
- 使ってよい情報源: `<添付資料、URL、メモなど。なければ「ユーザー提供情報のみ」>`
- 枚数目安: `<例: 6〜10枚>`

出力要件:

1. `CONTENT_SCHEMA.md` と同じJSON構造で出力する。
2. `meta.title`, `meta.footer`, `slides[*].title`, `slides[*].kicker`, 本文はすべて今回のテーマに合わせて新規作成する。
3. 既存サンプルの題材・文言・固有名詞・数値を流用しない。
4. 実在の構成・組織・数値が分からない場合は、勝手に具体化しない。代わりに「要確認」または一般的な概念説明にする。
5. 構成図(システム構成・ネットワーク構成など)は `diagram` type を使い、`CONTENT_SCHEMA.md` のグリッド仕様(列・行・ノード・エッジ)を**今回のテーマに合わせて新規に**書く。**座標やサイズの数値は一切書かない**(レイアウトエンジンが計算する)。ノードの `icon` は省略してよい(汎用図形ノードになる)。指定する場合は `CONTENT_SCHEMA.md` に載っている `fluent/〜.png`(サーバ・ルータ・FW等の汎用19種)から選ぶ。存在しないファイル名を発明しない。
6. `aws` / `aws2` は使わない。サンプル固定図のため `generate_from_json.py` が機械的に拒否する。
7. `type` は `CONTENT_SCHEMA.md` に載っているものだけ使う。件数制約(hubのring 6件、roadmapのphases 最大3件など)も `validate_content.py` が機械検証する。
8. JSON以外の説明文を付けない。

対応済み `type`:

- `title`
- `bullets`
- `cards`
- `table`
- `twocol`
- `chart`
- `process`
- `roadmap`
- `matrix`
- `hub`
- `org`
- `diagram` (構成図。グリッド仕様から自動レイアウト、座標記述は禁止)

## 実行コマンド

生成されたJSONを `content.json` として保存してから実行する。

```powershell
python sysA_pptx/validate_content.py content.json
python sysA_pptx/generate_from_json.py content.json out\deck_from_json.pptx
python sysA_pptx\check_layout.py out\deck_from_json.pptx
powershell -ExecutionPolicy Bypass -File render.ps1 -PptxPath out\deck_from_json.pptx -OutDir out\png_from_json
python contact_sheet.py out\png_from_json
```

1行目の検証は `generate_from_json.py` も生成前に自動実行する(NGなら生成されない)。
検証エラーが出たら、エラーメッセージ(`slides[番号] (type=種別): 内容` 形式)をそのままAIに渡して `content.json` を直させる。

`out\png_from_json\sheet.png` を確認し、内容がテーマから逸れていないか、既存サンプルの題材が混ざっていないか、文字溢れや重なりがないかを見る。
