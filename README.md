# slide-gen-lab

「生成→そのまま提出」レベルのスライドを決定論的に出力するパイプラインの検証プロジェクト。
2つの独立したシステムで同一の9枚デッキ(調査報告)を生成し、PowerPoint実レンダリングで品質を検証済み。

## 構成

| パス | 内容 |
|---|---|
| `content.json` | デッキ内容(スライド構造の共有データ。sysA の content.py から生成) |
| `sysA_pptx/` | システムA: Python + python-pptx。Pillowで游ゴシックの実寸を測って配置 |
| `sysA_pptx/diagrams*.py` | 表現力検証: AWS構成図・関係者調整図・体制図・チェブロンフロー・ロードマップ・2軸マップ |
| `sysA_pptx/generate_from_json.py` | `content.json` を直接入力にしてPPTXを生成 |
| `sysB_pptxgenjs/` | システムB: Node + PptxGenJS。全角1em/半角0.53emのヒューリスティック+PPT側autofit保険 |
| `sysC_marp/` | システムC: Marp。content.json→Markdown変換(md_gen.py)+自作テーマ(corp.css) |
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

ここで使う構造化データは `content.json`。`context.json` ではない。

**生成AIに実行させるパターン**

1. AIに `sysA_pptx/content.py` または `content.json` の既存形式に沿って、スライド内容を作らせる。
2. `content.py` を更新した場合は `python sysA_pptx/export_content.py` で `content.json` を同期する。
3. AIに次のコマンドを実行させる。

```powershell
python sysA_pptx/generate_from_json.py content.json out\deck_from_json.pptx
powershell -ExecutionPolicy Bypass -File render.ps1 -PptxPath out\deck_from_json.pptx -OutDir out\png_from_json
python contact_sheet.py out\png_from_json
python sysA_pptx\check_layout.py out\deck_from_json.pptx
```

4. `check_layout.py` がNG、またはPNG目視で崩れがある場合は、AIに `content.py` / `content.json` を直させて再実行する。

**人間が手動実行するパターン**

1. `content.json` を用意する。既存の `content.json` をコピーして、`meta` と `slides` だけ差し替えるのが最短。
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

1. AI(どのLLMでも可)に `content.py` の既存形式でスライドの文言を書かせる — AIの仕事はここだけ
2. `python generate.py` (基本) / `python generate2.py` (図解入り拡張) で生成
3. `render.ps1` でPNG化 → 目視(またはマルチモーダルAIに検査させる) → 問題があればcontent.pyを直して再生成

**新しいレイアウト種別が必要な場合のみ** renderer関数のコーディングが発生する(CLAUDE.mdの設計原則を参照)。

## 社内テンプレート化の方針

このリポジトリでは、全スライドを万能の宣言レイアウトエンジンに寄せるより、
提出品質まで詰めた **renderer カタログ** を増やす方針を優先する。

- LLMの役割: `content.py` / `content_ext.py` の既存スキーマに沿って、文言・項目・強調を構造化する。
- Python rendererの役割: スライド種別ごとの余白、文字実測、配線、注記、描画順を決定論的に保証する。
- 共通化するもの: テキスト実測、自然高さパッキング、ラベルマスク、表・カード・ロードマップなどの小さな配置ヘルパー。
- 共通化しすぎないもの: 高密度な構成図の最終的な絵作り。必要なら renderer 内に座標を閉じ込めて手で詰める。

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
