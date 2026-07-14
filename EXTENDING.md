# EXTENDING.md — AI向け: renderer / エンジン拡張ガイド

対象読者: このリポジトリに**新しいスライド種別や図解機能を追加するAI**(Claude / Codex / Copilot 等)。
`content.json` を書くだけなら [AI_DECK_PROMPT.md](AI_DECK_PROMPT.md) + [CONTENT_SCHEMA.md](CONTENT_SCHEMA.md) を読む(このファイルは不要)。
既存rendererの配色・表紙・造形を変更する場合は [DESIGN_CUSTOMIZATION.md](DESIGN_CUSTOMIZATION.md) を読む。

このリポジトリは「生成→そのまま提出」を成立させるため、**AIとコードの分業線**を固定している:

- **AIが書くもの**: 離散的な構造(スライドの文言、type、グリッド仕様のセル名・メンバー列挙)
- **コードが決めるもの**: 座標・サイズ・余白・フォント・折り返し・描画順の**すべての数値**

拡張するときもこの線を動かさない。「contentに数値を書けば解決する」拡張は必ず設計ミス。

## レイヤーモデル — 何が再利用でき、何がジャンル専用か

拡張の設計判断はこの4層で考える。**再利用資産はL0/L2/L3であって、L1ではない。**

| レイヤー | 中身 | 再利用性 |
|---|---|---|
| L0 測定・描画プリミティブ | textfit(実測) / add_text / add_rect / box_node / add_arrow / arrow_label / container / route | ◎ 全typeで共有 |
| L1 レイアウト計算 | diagram_layout(グリッド図解) / roadmap(ガント) / matrix(散布) / bullets・cards・twocol(縦詰め) / org(ツリー) / hub(放射) | **△ ジャンル内のみ** |
| L2 AI境界 | content.jsonスキーマ + validate_content + AI_DECK_PROMPT | ◎ typeが増えても同じ仕組み |
| L3 品質ゲート | check_layout + render.ps1 + contact_sheet + 目視ループ | ◎ 何を作っても同じゲート |

**L1に関する鉄則: レイアウトは1つの問題ではない。** グリッド配置・ツリー・放射・ガント・縦詰めは
別々の制約システムであり(graphviz/ELK/d3がジャンル別アルゴリズムの集合体なのと同じ理由)、
1つのエンジンに寄せようとするとエンジンの前提が壊れて複雑化だけが進む。

- **やること**: 新しいジャンルが必要になったら、L0部品の上に**小さな専用レイアウタ**を書く
  (ツリーなら50〜100行で足りる)。カタログの品目は「renderer関数」ではなく
  「ジャンル別レイアウタ」と考える。
- **やらないこと**: 既存レイアウタに別ジャンルを混ぜる拡張。例えば diagram_layout の機構
  (ポート計算・行間のラベル深さ・コンテナ外接)は「正方形アイコン+下ラベルのノードを
  グリッドに置く」前提に張り付いており、幅広ボックスや放射配置を入れるのは汎用化ではなく
  前提破壊になる(体制図・ハブ図をdiagram_layoutに統合しない判断の理由。#8参照)。
- **判断に迷ったら**: そのジャンルのレイアウトを2〜3枚、既存レイアウタの仕様語彙だけで
  書けるか試す。書けないものが多ければ別レイアウタ(#11 の実証実験方式)。

## アーキテクチャ

```
content.json ──→ validate_content.py ──→ generate_from_json.py ──→ PPTX
 (AIが作る)      (schema機械検証)          RENDER[type] で分岐         │
                                              │                        ▼
                 diagram type のみ:            │              check_layout.py (機械検知)
                 diagram_layout.py エンジン ←──┘              render.ps1 (PNG化)
                 (座標計算+自己検証)                          contact_sheet.py (俯瞰)
                                                              → 人間/AIの目視
```

| ファイル | 役割 |
|---|---|
| `slidegen/generate.py` | 基本renderer (title/bullets/cards/table/twocol/chart) + 共通ヘルパー + ページ定数 |
| `slidegen/diagrams.py` | hub/org renderer + 図解部品 (icon_node/box_node/add_arrow/arrow_label/container) |
| `slidegen/diagrams2.py` | process/roadmap/matrix renderer |
| `slidegen/diagrams3.py` | route() 直角配線 |
| `slidegen/diagram_layout.py` | 宣言的レイアウトエンジン (グリッド仕様→座標。diagram type の本体) |
| `slidegen/diagram_specs.py` | サンプル図のグリッド仕様 (aws_simple/aws_multiaz)。仕様の書き方見本 |
| `slidegen/validate_content.py` | content.json の生成前検証。typeごとの `_v_*` 関数 |
| `slidegen/generate_from_json.py` | content.json→PPTX。**新規資料の正式経路** |
| `slidegen/generate_patterns.py` + `content_patterns.py` | 全typeの検証ギャラリー |
| `slidegen/check_layout.py` | 生成済みPPTXの重なり・はみ出し機械検知 |
| `slidegen/textfit.py` | フォント実測 (游ゴシックをPillowで測る) |
| `slidegen/fetch_fluent_icons.py` / `extract_aws_icons.py` | アイコン素材の追加取得 (assets/ は同梱済み。条件は assets/CREDITS.md。Fluentは要 svglib+reportlab+rlPyCairo) |

## 絶対に守る不変条件(全て実際の不具合から学んだもの)

1. **置く前に測る**: テキストは textfit.py で折り返し・必要高さを計算してから置く。
   PowerPointの自動調整に頼らない(頼った結果が「溢れ・重なり」の常習化)。
2. **数値はrenderer/エンジンの中だけ**: content側スキーマに座標・サイズを要求するフィールドを
   作らない(例外は matrix の lx/ly のような限定的な微調整のみ。新設は原則禁止)。
3. **均等分散しない**: 要素は自然高さ+一定gapで詰めて、やや上寄りに置く
   (均等分散は間延びして「AIっぽい」見た目になる。v1で実際に発生)。
4. **配線はウェイポイント明示**: プリセットのカギ線コネクタは折れ位置を制御できず
   ノードを貫通する。route() に点列を渡す。
5. **同じ行のノードは中心Yを完全に揃える**(1pxのズレが斜め線になる)。
6. **日本語runは set_run() 経由で作る**(lang="ja-JP" を自動設定。忘れると行頭に「、。」が来る)。
7. **同じ値を2箇所で定義しない**: 行間計算と描画で使う余白定数(BOTTOM_PORT_GAP等)がずれると
   「計算上は収まるのに実際は重なる」になる(実際に発生)。
8. **エラーメッセージは日本語+対処方法つき**: このリポジトリのエラーは「生成AIに
   そのまま渡して直させる」前提。スタックトレースを見せない
   (validate_content.py / diagram_layout.py の既存メッセージの粒度に合わせる)。
9. **サンプル流用ガードを壊さない**: aws/aws2 と diagram_specs のspec名参照は
   generate_from_json 経路で拒否されている。新しい流用経路を作らない
   (別環境の生成AIがサンプルAWS図を新規資料に混入させた実事故への対策)。

## 共通部品カタログ(車輪の再発明をしない)

```python
# textfit.py — フォント実測
text_width_in(text, size_pt, weight="regular") -> float      # 1行の実測幅(インチ)
wrap_text(text, width_in, size_pt, weight="regular") -> list # 禁則込み折り返し
line_height_in(size_pt, spacing=1.3) -> float
fit_font_size(text, box_w, box_h, start_pt, min_pt=..., ...) -> (size, lines)

# generate.py — ページ部品と定数
SLIDE_W=13.333, SLIDE_H=7.5, MARGIN=0.55, BODY_W=12.233, BODY_TOP=1.62, BODY_BOTTOM=6.85
NAVY / ACCENT / CORAL / TEXT / GRAY / LIGHT / ZEBRA / WHITE / CANVAS / RULE
add_text(slide, x, y, w, h, text, size, *, bold, color, align, anchor, spacing)
add_rect(slide, x, y, w, h, fill, *, line=None, round_=False)
header(slide, kicker, title) / footer(slide, page) / note_line(slide, note)

# diagrams.py — 図解部品
icon_node(slide, cx, cy, img, title, sub)   # アイコン+下ラベル(外形0.62角)
box_node(slide, cx, cy, title, sub, color)  # アイコン無し汎用ノード(同一外形)
add_arrow(slide, x1, y1, x2, y2, *, both, dash) / arrow_label(slide, cx, cy, text, w, size)
container(slide, x, y, w, h, label, color, dash)
ICON_R=0.31, EDGE_GAP=0.06

# diagrams3.py
route(slide, pts, *, dash, width)   # 直角折れ線+終端矢印

# diagram_layout.py
Layout(spec, reserve_note=False)    # グリッド仕様→座標(port/channel/route_edges/validate_edges)
render_diagram(slide, spec, note)   # 描画一式
```

## レシピA: 新しいスライドtypeを追加する

**7点セットを必ず揃える**(1つでも欠けたらマージ不可):

1. **renderer関数**: シグネチャは `def s_xxx(slide, spec, page)`。配置場所は内容で選ぶ
   (テキスト系→generate.py、図解系→diagrams*.py)。数値はすべて関数内に閉じ込める。
2. **RENDER登録**: `generate_from_json.py` と `generate_patterns.py` の両方
   (既存サンプルデッキにも使うなら `generate2.py` も)。
3. **validator**: `validate_content.py` に `_v_xxx` を追加し `VALIDATORS` に登録。
   件数上限は「超えると実際に崩れる値」を**生成して確かめてから**決める
   (roadmap phases≤3 は4件で本文下端を超えることを実測して決めた値)。
   note を描画するなら `NOTE_TYPES` にも追加。
4. **CONTENT_SCHEMA.md**: 必須/任意フィールド・制約・JSON例のセクションを追加。
5. **AI_DECK_PROMPT.md**: 対応済みtype一覧に追加。
6. **ギャラリー**: `content_patterns.py` に検証スライドを1枚追加
   (これが将来のリグレッション検知網になる)。
7. **品質ゲート**(下記)を全部通し、PNGを目視してから完了報告。

## レシピB: diagram エンジン(diagram_layout.py)を拡張する

構造マップ:

| 場所 | 役割 |
|---|---|
| モジュール定数 | AREA/GAP/MIN_SEG/DIRECT_GAP/SLOT_PITCH 等。**コメントに設計理由と実不具合の記録あり。必読** |
| `Layout._auto_rows()` | 行位置の自動計算。行間=必須分(圧縮禁止)+裁量分(圧縮可)の2階建て |
| `Layout.port()` | ノードの矢印接続点(辺+オフセット) |
| `Layout.channel()` | 配線レーンの座標解決(列間/行間/コンテナ外側) |
| `Layout.route_edges()` | エッジ→直角経路。同一辺の多重エッジをSLOT_PITCHで分離 |
| `Layout.validate_edges()` | 意味レベル自己検証(コンテナ境界貫通・逆走・短すぎる区間) |
| `render_diagram()` | コンテナ→ノード→配線→ラベルの順に描画 |

拡張の作法:

- **語彙を増やす方向で拡張する**: 新しい配置要件は「チャネル種類の追加」「ノード形状の追加」
  「コンテナ属性の追加」のような離散的な仕様語彙として設計する。
  仕様側に数値を書かせる逃げ道を作らない(「9.55と書きたくなったらエンジンの制約計算不足」)。
- **行間計算に影響する変更は必須分/裁量分の区別を維持する**: 必須分まで圧縮すると
  ラベルがアイコンに食い込む(実際に発生)。可視性が必要な要素は必須分に入れる
  (例: 直結コネクタのDIRECT_GAP。MIN_SEGでは矢印ヘッドに埋もれて見えなかった)。
- **新しい描画パターンには対応する自己検証を足す**: check_layout.py は色・Z順・線同士の
  交差が見えない。エンジンが意味を知っている検証(validate_edges系)はエンジンに入れる。
- **エラーは行数削減・sub削除・ラベル短縮など「AIが取れる対処」を必ず添える**。

## 品質ゲート(マージ条件)

```powershell
python slidegen/validate_content.py content.json                       # 新typeのschema検証
python slidegen/generate_from_json.py content.json out\deck.pptx       # 新規資料経路
python slidegen/generate_patterns.py out\pattern_gallery.pptx          # ギャラリー(全type)
python slidegen\check_layout.py out\pattern_gallery.pptx               # exit 0 必須
powershell -ExecutionPolicy Bypass -File render.ps1 -PptxPath out\pattern_gallery.pptx -OutDir out\png_pg
python contact_sheet.py out\png_pg                                      # → sheet.png を目視
```

- チェッカーの限界: 白マスクラベルの枠線またぎ・線同士の交差・色/Z順は検知できない。
  **PNG目視は省略不可**。変更したスライドはフル解像度(`render.ps1` 既定1600px)でも確認する。
- 出力先pptxをPowerPointで開いたままだと PermissionError。閉じてから実行。
- コンソールの日本語はcp932で文字化けすることがある。判定に使う出力は
  ファイルにリダイレクトしてから読む(**読めない出力を根拠に成功と報告しない**)。

## 既知の落とし穴(実際に起きた不具合の索引)

詳細は各ファイルのコメントに「実際に発生した不具合」として残してある。grepで探せる。

| 症状 | 原因と対策の場所 |
|---|---|
| 要素が間延びして不自然 | 均等分散をやめ自然高さパッキングに (generate.py s_bullets) |
| 行頭に「、。」 | set_run の lang="ja-JP" (generate.py) |
| ラベルが次行アイコンに食い込む | 行間の必須分/裁量分の分離 (diagram_layout._auto_rows) |
| 縦線がアイコン縁と平行に走る | top/bottom辺をSLOT_PITCHオフセット対象から除外 (route_edges) |
| 矢印が逆向きに見える | MIN_SEG_CLAMP と最終区間の向き検証 (_validate_segment_lengths) |
| 隣接ノード間の線が消える | 直結コネクタはDIRECT_GAPを必須分で確保 (_auto_rows) |
| GAPを増やしても行間が広がらない | 圧縮モードでは裁量分が等比で潰される。必須分に入れるかpadを削る |
| 2つの線が繋がって見える | 同一チャネル共有をやめ専用レーンに分離 (diagram_specs.py s3_lane) |
| コンテナ境界を線が貫通 | outside_container チャネル + validate_edges (diagram_layout) |
| 兄弟コンテナで縦余白が過大 | 入れ子マージンは1チェーンのみ積算 (chain_stack) |

## 開発フロー

CLAUDE.md の Issue駆動フローに従う: Issue作成 → `feature/<内容>` ブランチ → 7点セット実装 →
品質ゲート → PR(`Closes #N`)。コミットに `Co-Authored-By` は付けない。

レイアウタ関連のバックログ(着手時はこのガイドとIssue本文を読んでから):

- [#8 体制図・ハブ図を小さな専用レイアウタとして再実装](https://github.com/thinas1115/slide-gen-lab/issues/8)
- [#9 縦詰めパッキングの共有部品化 → layout type](https://github.com/thinas1115/slide-gen-lab/issues/9)
- [#11 実証実験: 第3のグリッド図解でdiagram_layoutの汎用性を検証](https://github.com/thinas1115/slide-gen-lab/issues/11)
