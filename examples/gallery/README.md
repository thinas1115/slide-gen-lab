# サンプルスライドギャラリー

[pattern_gallery.pptx](pattern_gallery.pptx)は、cloneした利用者が対応レイアウトの見た目を
PowerPointで確認するための配布用ギャラリーです。

## 扱い

- 人間がレイアウト選定とデザイン確認に使う。
- 新しい資料を作る生成AIには渡さない。
- ギャラリーの題材、文言、数値、ページ順を`content.json`へ流用しない。
- rendererの開発時は、回帰検証と目視QAに使用する。

生成AIへ渡す資料は、記入済みの`AI_DECK_PROMPT.md`、`CONTENT_SCHEMA.md`、
`docs/type-selection-guide.md`です。

## 更新

renderer、テーマ、ギャラリー内容を変更した場合は、次のコマンドで配布用PPTXを更新します。

```powershell
python slidegen/generate_patterns.py examples\gallery\pattern_gallery.pptx
python slidegen/check_layout.py examples\gallery\pattern_gallery.pptx
```

PNGや一覧画像など、配布しない確認用生成物は`out/`へ保存します。
