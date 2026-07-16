# pptxdsl

「生成 → そのまま提出」できる品質のスライドを、決定論的に出力するパイプライン。

![パイプライン全体像](docs/pipeline-overview.png)

生成AIはスキーマに沿って `content.json` を書くだけ。座標・余白・フォントはコード側(renderer / レイアウトエンジン)が
実測ベースで決定し、schema検証 → エンジン自己検証 → 機械検知 → 実レンダリング目視の多段ゲートで
「そのまま提出」品質を担保する。NGはどの段からも `content.json` の修正に差し戻される
(表現力が足りない場合のみ `extend`: `EXTENDING.md` に従うエンジン拡張ループ)。

## 構成

| パス | 内容 |
|---|---|
| `content.json` | 新規デッキの入力データ。生成AIまたは人間がschemaに沿って作成する |
| `CONTENT_SCHEMA.md` | `content.json` の中立スキーマ。生成AIにはこれと `AI_DECK_PROMPT.md` を渡す |
| `AI_DECK_PROMPT.md` | 生成AIに `content.json` を書かせる依頼文の穴埋めテンプレート |
| `docs/architecture.md` | レイアウタ構成、責務境界、拡張判断、品質保証の設計文書 |
| `EXTENDING.md` | 新しいtype・エンジン機能を追加するときの不変条件と手順(AI向け拡張ガイド) |
| `DESIGN_CUSTOMIZATION.md` | 配色・表紙・既存renderer・複数テーマ対応など、デザイン変更時の修正箇所一覧 |
| `docs/cover-footer-customization.md` | 表紙・フッターだけをユーザー別設定JSONで変更する手順とschema |
| `slidegen/` | 本体。Python + python-pptx。Pillowで游ゴシックの実寸を測って配置 |
| `slidegen/assets/cover/` | ユーザーが差し替える表紙背景画像。PNG/JPEGを配置する |
| `slidegen/assets/images/` | 本文へ大きく配置する生成画像・提供画像・利用許諾済み画像 |
| `slidegen/generate_from_json.py` | `content.json` → PPTX 生成(生成前にschema検証を自動実行) |
| `slidegen/validate_content.py` | `content.json` のschema機械検証(必須フィールド・件数制約・廃止typeの拒否) |
| `slidegen/check_layout.py` | 生成済みPPTXの重なり・はみ出しを機械検知する品質ゲート |
| `slidegen/layout_fit.py` | 標準配置・裁量余白圧縮・要素縮小・明示停止の共通契約 |
| `slidegen/diagram_layout.py` | グリッド仕様から構成図の座標・配線を計算するレイアウトエンジン |
| `slidegen/content*.py` | 基本・拡張・パターンギャラリーの回帰検証用サンプル |
| `render.ps1` / `contact_sheet.py` | PPTX→PNG書き出し(PowerPoint COM)と一覧画像への合成。目視レビュー用 |
| `out/` | PPTX・PNG・検証レポート・一時JSONなどの生成物。`.gitignore` 対象 |

**出力先ルール:** 実行時に生成するファイルはすべて `out/` 配下へ保存する。`docs/` を設ける場合は、
保守対象の説明文書と、その文書から参照する掲載素材だけを置く。実験結果、PR確認画像、一時JSON、
検証レポートを `docs/` に出力しない。

## セットアップ

1. リポジトリを clone
2. `pip install python-pptx pillow`(Python 3.10+)
3. 前提: Windows + 游ゴシック(`slidegen/textfit.py` が環境変数`WINDIR`配下のフォントを参照)
4. 目視用に PowerPoint(`render.ps1` が使用。生成自体には不要)

アイコン素材(AWS 13種 + Fluent 72種)は `slidegen/assets/icons/` に**同梱済み**なので追加作業は不要
(出典・ライセンスは [slidegen/assets/CREDITS.md](slidegen/assets/CREDITS.md))。増やす場合のみ:

- AWS: [公式アイコンデッキ(PPTX)](https://aws.amazon.com/jp/architecture/icons/)を入手し、
  `python slidegen/extract_aws_icons.py "<公式デッキのパス>"`を実行
- Fluent([Fluent UI System Icons](https://github.com/microsoft/fluentui-system-icons)、MIT): `pip install svglib reportlab rlPyCairo` のうえ `slidegen/fetch_fluent_icons.py` の ICONS に追記して実行

## 使い方

新しいデッキを作る主経路は「生成AIに `content.json` を書かせる → コマンドで生成・検証」。

### 1. content.json を用意する

**生成AIに書かせる(推奨)**

1. `AI_DECK_PROMPT.md` の依頼文テンプレートをコピーし、資料テーマ・想定読者・目的・必須内容・
   情報源・枚数目安の各入力欄を具体値で埋める。
2. 埋めたテンプレートと `CONTENT_SCHEMA.md` を生成AI(どのLLMでも可)に渡し、`content.json` を書かせる。
   既存の `content.json` / `slidegen/content.py` はサンプルなので参照させない。
3. 出力を `content.json` としてプロジェクト直下に保存する。

**手動で書く**: `CONTENT_SCHEMA.md` に沿って直接 `content.json` を用意してもよい。

構成図(システム構成・ネットワーク図など)は `diagram` type を使い、グリッド仕様(列・行・ノード・エッジ)を書く。
座標の数値は書かず、`diagram_layout.py` が計算する。ノードの `icon` は必須で、同梱Fluent/AWSアイコンから選ぶ。
`aws` / `aws2` は廃止済みの旧type名であり、互換性のあるエラーを返すためvalidatorにのみ残している。
新しい構成図は `diagram` を使う。

`cards` typeは、KPI・選択肢・事例など各項目が独立して比較できる場合に使う。サマリ・事例は `style: "editorial"`、KPIは `style: "metrics"` を選ぶ。情報が少ないことだけを理由に白箱を並べたり、フェーズ名や図のノードなど別の構造に属する要素をカード化したりしない。

表紙以外では、必要なスライドにだけ任意の `lead` を指定できる。leadはタイトル直下の要旨として描画され、
指定時だけ各rendererの本文領域が下がる。詳しい用途とJSON例は `CONTENT_SCHEMA.md` を参照する。

画像を主役にするページは `image` typeを使う。生成AIで作った画像、利用者提供画像、利用許諾済みのWeb画像を
`slidegen/assets/images/`へ配置し、`content.json`から相対パスで参照する。縦横比を保つ表示方法や
出典・代替テキストの指定は `CONTENT_SCHEMA.md` を参照する。

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
サンプルデッキ自体を再生成するなら `python slidegen/generate.py out\sample.pptx`(基本)、
`python slidegen/generate2.py out\sample_extended.pptx`(図解入り)を使う。

既存レイアウトのデザインを変更する場合は [`DESIGN_CUSTOMIZATION.md`](DESIGN_CUSTOMIZATION.md) を参照する。
配色・フォント・表紙などのテーマ差し替えと、新しいレイアウト追加では修正範囲が異なる。
