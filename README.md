# slide-gen-lab

「生成 → そのまま提出」できる品質のスライドを、決定論的に出力するパイプライン。

![パイプライン全体像](docs/pipeline-overview.png)

生成AIはスキーマに沿って `content.json` を書くだけ。座標・余白・フォントはコード側(renderer / レイアウトエンジン)が
実測ベースで決定し、schema検証 → エンジン自己検証 → 機械検知 → 実レンダリング目視の多段ゲートで
「そのまま提出」品質を担保する。NGはどの段からも `content.json` の修正に差し戻される
(表現力が足りない場合のみ `extend`: `EXTENDING.md` に従うエンジン拡張ループ)。

## 構成

| パス | 内容 |
|---|---|
| `content.json` | デッキ内容(スライド構造の共有データ。`slidegen/content.py` から生成) |
| `CONTENT_SCHEMA.md` | `content.json` の中立スキーマ。生成AIにはこれと `AI_DECK_PROMPT.md` を渡す |
| `AI_DECK_PROMPT.md` | 生成AIに `content.json` を書かせる依頼文の穴埋めテンプレート |
| `EXTENDING.md` | 新しいtype・エンジン機能を追加するときの不変条件と手順(AI向け拡張ガイド) |
| `DESIGN_CUSTOMIZATION.md` | 配色・表紙・既存renderer・複数テーマ対応など、デザイン変更時の修正箇所一覧 |
| `slidegen/` | 本体。Python + python-pptx。Pillowで游ゴシックの実寸を測って配置 |
| `slidegen/generate_from_json.py` | `content.json` → PPTX 生成(生成前にschema検証を自動実行) |
| `slidegen/validate_content.py` | `content.json` のschema機械検証(必須フィールド・件数制約・サンプル専用typeの拒否) |
| `slidegen/check_layout.py` | 生成済みPPTXの重なり・はみ出しを機械検知する品質ゲート |
| `slidegen/diagram_layout.py` | グリッド仕様から構成図の座標・配線を計算するレイアウトエンジン |
| `render.ps1` / `contact_sheet.py` | PPTX→PNG書き出し(PowerPoint COM)と一覧画像への合成。目視レビュー用 |
| `archive/` | 比較検証を終えた旧実装(凍結)。`sysB_pptxgenjs`=Node+PptxGenJS、`sysC_marp`=Marp |
| `out/` | 生成物(PPTX/PNG)。`.gitignore` 対象 |

## セットアップ

1. リポジトリを clone
2. `pip install python-pptx pillow`(Python 3.10+)
3. 前提: Windows + 游ゴシック(`slidegen/textfit.py` が `C:\Windows\Fonts\YuGoth*.ttc` を参照。別OSはこの数行を変更)
4. 目視用に PowerPoint(`render.ps1` が使用。生成自体には不要)

アイコン素材(AWS 13種 + Fluent 72種)は `slidegen/assets/` に**同梱済み**なので追加作業は不要
(出典・ライセンスは [assets/CREDITS.md](slidegen/assets/CREDITS.md))。増やす場合のみ:

- AWS: [公式アイコンデッキ(PPTX)](https://aws.amazon.com/jp/architecture/icons/) を入手し `slidegen/extract_aws_icons.py` の SRC を変えて実行
- Fluent([Fluent UI System Icons](https://github.com/microsoft/fluentui-system-icons)、MIT): `pip install svglib reportlab rlPyCairo` のうえ `slidegen/fetch_fluent_icons.py` の ICONS に追記して実行

## 使い方

新しいデッキを作る主経路は「生成AIに `content.json` を書かせる → コマンドで生成・検証」。

### 1. content.json を用意する

**生成AIに書かせる(推奨)**

1. `AI_DECK_PROMPT.md` の依頼文テンプレートをコピーし、`<...>` の空欄(テーマ・想定読者・目的など)を今回の内容で埋める。
2. 埋めたテンプレートと `CONTENT_SCHEMA.md` を生成AI(どのLLMでも可)に渡し、`content.json` を書かせる。
   既存の `content.json` / `slidegen/content.py` はサンプルなので参照させない。
3. 出力を `content.json` としてプロジェクト直下に保存する。

**手動で書く**: `CONTENT_SCHEMA.md` に沿って直接 `content.json` を用意してもよい。

構成図(システム構成・ネットワーク図など)は `diagram` type を使い、グリッド仕様(列・行・ノード・エッジ)を書く。
座標の数値は書かず、`diagram_layout.py` が計算する。ノードの `icon` は必須で、同梱Fluent/AWSアイコンから選ぶ。
`aws` / `aws2` はサンプル固定図のため `generate_from_json.py` が機械的に拒否する。

`cards` typeは、KPI・選択肢・事例など各項目が独立して比較できる場合に使う。情報が少ないことだけを理由に白箱を並べたり、フェーズ名や図のノードなど別の構造に属する要素をカード化したりしない。

### 2. 生成・検証する

```powershell
python slidegen/generate_from_json.py content.json out\deck.pptx      # schema検証 → 生成
python slidegen/check_layout.py out\deck.pptx                          # 重なり・はみ出しの機械検知
powershell -ExecutionPolicy Bypass -File render.ps1 -PptxPath out\deck.pptx -OutDir out\png
python contact_sheet.py out\png                                        # out\png\sheet.png を目視
```

- schema検証は `generate_from_json.py` が生成前に自動実行する(NGなら生成しない)。
  エラーは `slides[番号] (type=種別): 内容` 形式なので、そのまま生成AIに渡して直させる。
- `check_layout.py` のNG、またはPNG目視での崩れ(テキスト溢れ・要素重なり・行頭禁則・線とラベルの衝突)も、
  同様に `content.json` を直して再実行する。

新しいレイアウト種別が必要になったときだけ、renderer / レイアウタのコーディングが発生する(→ `EXTENDING.md`)。
サンプルデッキ自体を再生成するなら `python slidegen/generate.py out\sample.pptx`(基本)/ `generate2.py`(図解入り)。

既存レイアウトのデザインを変更する場合は [`DESIGN_CUSTOMIZATION.md`](DESIGN_CUSTOMIZATION.md) を参照する。
配色・フォント・表紙などのテーマ差し替えと、新しいレイアウト追加では修正範囲が異なる。

## 設計方針(レイアウタ・カタログ)

全スライドを万能の宣言レイアウトエンジンに寄せるより、提出品質まで詰めた **レイアウタのカタログ**を増やす方針。
カタログの品目は「renderer関数」ではなく「**ジャンル別レイアウタ**」と考える(詳細は `EXTENDING.md` のレイヤーモデル)。

- LLMの役割: スキーマに沿って文言・項目・構造(グリッド仕様のセル名等)を構造化する。
- レイアウタの役割: 余白・文字実測・配線・注記・描画順を決定論的に保証する。
- 共通化するもの: テキスト実測、描画部品(箱・矢印・ラベルマスク)、schema検証、品質ゲート。
- 共通化しないもの: **レイアウト計算そのもの**。グリッド図解・ガント・散布・縦詰め・ツリーは
  別々の制約システムなので、ジャンルごとに小さなレイアウタを持つ。1つのエンジンに寄せると前提が壊れて複雑化だけが進む。

**モデル依存度の目安**: 文言作成=低(主要LLMなら可)/ 既存種別での再生成=ゼロ(決定論的)/
新レイアウト実装=中 / レンダ画像を見た欠陥検出=高(マルチモーダル必須)。

## 品質を支える仕組み

1. **配置前のテキスト実測**: 置く前に折り返し行数を計算し、入らなければフォント縮小/高さ調整。
   日本語の禁則(行頭「、。」禁止)も折り返し計算に組み込み、run に `lang="ja-JP"` を設定してPowerPoint側の禁則も有効化する。
2. **自然高さパッキング**: 要素を領域に均等分散させず、内容の自然高さ + 一定gapで詰めてやや上寄せに置く(均等分散は間延びして見える)。
3. **描画 → 目視のQAループ**: PowerPoint COMでPNG化し、溢れ・重なり・禁則を実物で確認してから完成とする。
