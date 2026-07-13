# slide-gen-lab

「生成→そのまま提出」レベルのスライドを決定論的に出力するパイプラインの検証プロジェクト。
2つの独立したシステムで同一の9枚デッキ(調査報告)を生成し、PowerPoint実レンダリングで品質を検証済み。

## 構成

| パス | 内容 |
|---|---|
| `content.json` | デッキ内容(スライド構造の共有データ。sysA の content.py から生成) |
| `CONTENT_SCHEMA.md` | 新規デッキ用の中立schema。生成AIにはこちらを渡す |
| `AI_DECK_PROMPT.md` | 生成AIに新規 `content.json` を作らせるための依頼テンプレート |
| `EXTENDING.md` | AI向け拡張ガイド(新しいtype・エンジン機能を追加するときの不変条件と手順) |
| `sysA_pptx/` | システムA: Python + python-pptx。Pillowで游ゴシックの実寸を測って配置 |
| `sysA_pptx/diagrams*.py` | 表現力検証: AWS構成図・関係者調整図・体制図・チェブロンフロー・ロードマップ・2軸マップ |
| `sysA_pptx/generate_from_json.py` | `content.json` を直接入力にしてPPTXを生成(生成前にschema検証を自動実行) |
| `sysA_pptx/validate_content.py` | `content.json` のschema機械検証(必須フィールド・件数制約・サンプル専用typeの拒否) |
| `sysB_pptxgenjs/` | システムB: Node + PptxGenJS(**凍結**: 比較検証を終えたアーカイブ。sysAと同じ content.json を読む) |
| `sysC_marp/` | システムC: Marp(**凍結**: 同上。PPTX出力が画像埋め込みになる制約で不採用) |
| `render.ps1` | PPTX→PNG書き出し(PowerPoint COM)。品質検証ループ用 |
| `contact_sheet.py` | PNG化した全スライドを一覧画像に合成。レビューの初手で使う |
| `sysA_pptx/check_layout.py` | 生成済みPPTXの重なり・はみ出しを機械検知する品質ゲート |
| `out/` | 生成物。`sysA_deck.pptx`/`sysB_deck.pptx`=初版(9枚・保存版)、`sysA_deck2.pptx`=拡張版(15枚)、`sysC_deck.html/.pptx`=Marp版 |

## 使い方

```powershell
# システムA (要: python-pptx, Pillow)
cd sysA_pptx
python generate.py ..\out\sysA_deck.pptx

# システムB (要: npm install 済み)
cd sysB_pptxgenjs
node gen.js

# 品質検証: PNGに書き出して目視 (要: PowerPoint)
powershell -ExecutionPolicy Bypass -File render.ps1 -PptxPath out\sysA_deck.pptx -OutDir out\pngA
python contact_sheet.py out\pngA
python sysA_pptx\check_layout.py out\sysA_deck.pptx
```

内容を変えるときは `sysA_pptx/content.py` を編集し、`python export_content.py` で content.json を再生成する。

## 実行手順

**生成AIに実行させるパターン**

1. AIに `AI_DECK_PROMPT.md` と `CONTENT_SCHEMA.md` を渡し、新しい `content.json` を作らせる。
   既存の `content.json` / `content.py` はサンプルなので参照させない。
2. 生成された `content.json` をプロジェクト直下に置く。
3. 生成・検証コマンドを実行する。

```powershell
python sysA_pptx/validate_content.py content.json
python sysA_pptx/generate_from_json.py content.json out\deck_from_json.pptx
powershell -ExecutionPolicy Bypass -File render.ps1 -PptxPath out\deck_from_json.pptx -OutDir out\png_from_json
python contact_sheet.py out\png_from_json
python sysA_pptx\check_layout.py out\deck_from_json.pptx
```

4. `validate_content.py` がNGの場合はエラー一覧をそのままAIに渡して `content.json` を直させる
   (`generate_from_json.py` も生成前に同じ検証を自動実行する)。
   `check_layout.py` がNG、またはPNG目視で崩れがある場合も同様に直させて再実行する。

**構成図は `diagram` type で描く。** グリッド仕様(列・行・ノード・エッジ。座標の数値は書かない)を
JSONで渡すと、レイアウトエンジン(`diagram_layout.py`)が座標・配線を決定論的に計算する。
ノードの `icon` を省略すると汎用図形ノードになるため、AWSアイコンがないテーマ・環境でも描ける。
`aws` / `aws2` はサンプル固定図のため `generate_from_json.py` が機械的に拒否する
(既存サンプル図が新規資料に混入した事故への対策)。

**人間が手動実行するパターン**

1. `CONTENT_SCHEMA.md` に沿って `content.json` を用意する。
2. AWS構成図を含む場合は、先に `sysA_pptx/assets/` にアイコンを用意する。
3. 次のコマンドを実行する。

```powershell
python sysA_pptx/generate_from_json.py content.json out\deck_from_json.pptx
python sysA_pptx\check_layout.py out\deck_from_json.pptx
powershell -ExecutionPolicy Bypass -File render.ps1 -PptxPath out\deck_from_json.pptx -OutDir out\png_from_json
python contact_sheet.py out\png_from_json
```

4. 最後に `out\png_from_json\sheet.png` を見て、テキスト溢れ・要素重なり・行頭禁則・線とラベルの衝突を確認する。

既存デッキをそのまま作るだけなら、従来どおり `python sysA_pptx/generate.py out\sysA_deck.pptx`
または `python sysA_pptx/generate2.py out\sysA_deck2.pptx` でもよい。新しい内容を外から渡す運用では
`generate_from_json.py` を使う。

## 別PC・別AIでの利用手順

**セットアップ(1回だけ)**

1. このリポジトリをclone
2. `pip install python-pptx pillow` (Python 3.10+)
3. 前提: Windows + 游ゴシック(`textfit.py` が `C:\Windows\Fonts\YuGoth*.ttc` を参照。別OSはこの2〜3行を変更)
4. 品質検証用にPowerPoint(render.ps1が使用。生成自体には不要)
5. AWS図解を使う場合: [AWS公式アイコンデッキ(PPTX)](https://aws.amazon.com/jp/architecture/icons/) を入手し、
   `extract_aws_icons.py` の SRC 定数をそのパスに変えて実行 → `sysA_pptx/assets/` にアイコンが生成される
   (アイコンはライセンス配慮のためリポジトリに含めていない)

**新しいスライドを作る(定常運用)**

1. AI(どのLLMでも可)に `AI_DECK_PROMPT.md` + `CONTENT_SCHEMA.md` を渡して新しい `content.json` を書かせる — AIの仕事はここだけ。既存サンプル(`content.py` / 既存 `content.json`)は見せない
2. `python sysA_pptx/generate_from_json.py content.json out\deck.pptx` で生成(schema検証は生成前に自動実行される)
3. `render.ps1` でPNG化 → 目視(またはマルチモーダルAIに検査させる) → 問題があればcontent.jsonを直して再生成

**新しいレイアウト種別が必要な場合のみ** renderer関数のコーディングが発生する(CLAUDE.mdの設計原則を参照)。
`generate.py` / `generate2.py` は既存サンプルデッキの再生成専用。

## 社内テンプレート化の方針

このリポジトリでは、全スライドを万能の宣言レイアウトエンジンに寄せるより、
提出品質まで詰めた **renderer カタログ** を増やす方針を優先する。
カタログの品目は「renderer関数」ではなく「**ジャンル別レイアウタ**」と考える
(詳細は `EXTENDING.md` のレイヤーモデル)。

- LLMの役割: content スキーマに沿って、文言・項目・構造(グリッド仕様のセル名等)を構造化する。
- Python レイアウタの役割: スライド種別ごとの余白、文字実測、配線、注記、描画順を決定論的に保証する。
- 共通化するもの: テキスト実測、描画部品(箱・矢印・ラベルマスク)、schema検証、品質ゲート。
- 共通化しないもの: **レイアウト計算そのもの**。グリッド図解(diagram_layout)・ガント・散布・
  縦詰め・ツリーは別々の制約システムなので、ジャンルごとに小さなレイアウタを持つ。
  1つのエンジンに寄せると前提が壊れて複雑化だけが進む。

増やす優先度の高いパターンは、タイトル/目次/章扉、カード、2カラム比較、Before/After、
KPI、プロセス、タイムライン/ロードマップ、表、ランキング、調査結果、2軸マップ、
体制図、ステークホルダー図、シンプル構成図、高密度構成図。

**モデル依存度の目安**: 文言作成=低(主要LLMなら可) / 既存種別での再生成=ゼロ(決定論的) /
新レイアウト実装=中 / レンダ画像を見た欠陥検出=高(マルチモーダル必須。人間が目視して
「どこが重なっている」と伝える運用ならどのAIでも回る)。

## 「そのまま提出」を成立させている3要素

1. **配置前のテキスト実測**: 置く前に折り返し行数を計算し、入らなければフォント縮小/高さ調整。
   日本語の禁則(行頭「、。」禁止)も折り返し計算に組み込み、さらに run に `lang="ja-JP"` を
   設定してPowerPoint側の禁則も有効化する(これを忘れると行頭に句読点が来る — v1で実際に発生)。
2. **自然高さパッキング**: 要素を領域に均等分散させず、内容の自然高さ+一定gapで詰めて
   縦центーに置く(均等分散は間延びして「AIっぽい」見た目になる — v1で実際に発生)。
3. **描画→目視のQAループ**: PowerPoint COMでPNG化し、溢れ・重なり・禁則を実物で確認してから納品。

## 検証結果 (2026-07-11)

- システムA: v1で行頭禁則違反2箇所+間延び → 修正 → **v2で9枚全て提出レベル**
- システムB: Aの教訓を織り込んで実装 → **1回目で9枚全て提出レベル**
- 拡張版(表現力検証6枚): チェブロンフロー・AWS構成図・ハブ型調整図・体制図は一発OK。
  ロードマップと2軸マップはラベル重なり/はみ出しで各1回修正 → **15枚全て提出レベル**
- システムC(Marp): 見た目は再現できたが**PPTX出力は画像埋め込みで編集不可**。HTML/PDF納品向き。
  1px単位の固定配置(ヘッダー位置固定等)はCSS調整が必要(縦センター問題を1回修正)
- 詳細は Work Vault `Knowledge\生成AIスライド生成\01_自前パイプライン検証.md`
