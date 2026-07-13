# アイコン素材のクレジット表記

このディレクトリのアイコンは、スライド生成パイプラインがアーキテクチャ図・構成図を
描画するための素材であり、以下の出典・条件に基づいて同梱している。

## AWS Architecture Icons (`*.png`)

- 出典: [AWS Architecture Icons](https://aws.amazon.com/architecture/icons/)
  (AWS公式アイコンデッキから `extract_aws_icons.py` で無改変抽出)
- © Amazon Web Services, Inc. or its affiliates. AWS および関連アイコンは
  Amazon Web Services, Inc. の商標です
- アイコンデッキの利用ガイダンスに基づき、アーキテクチャ図の作成および技術資料への
  組み込み用途で使用する。**改変(比率・色・要素の追加削除)禁止**
- 準拠: [AWS商標ガイドラインおよびライセンス条項](https://d1.awsstatic.com/onedam/marketing-channels/website/public/legal/trademark-guidelines/AWS_Trademark_Guidelines_and_License_Terms_(2024-07-18)_JA-JP.pdf)
- 本リポジトリは AWS による後援・承認・提携を受けたものではありません
- 最新版・追加アイコンが必要な場合は公式デッキを入手して `extract_aws_icons.py` を実行する

## Fluent UI System Icons (`fluent/*.png`)

- 出典: [microsoft/fluentui-system-icons](https://github.com/microsoft/fluentui-system-icons)
- © Microsoft Corporation — [MIT License](https://github.com/microsoft/fluentui-system-icons/blob/main/LICENSE)
- `fetch_fluent_icons.py` でSVGを取得し、塗り色をスライド配色(#1F3864)に変更のうえ
  PNG化したもの(MITライセンスは改変・再配布を許諾)
- 追加アイコンが必要な場合は `fetch_fluent_icons.py` の `ICONS` に追記して実行する
