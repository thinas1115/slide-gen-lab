# カスタム表紙背景

利用者が差し替える表紙背景のPNG/JPEGを配置する。

同梱の`cover-background.png`は、プロジェクト所有者がOpenAIのgpt-imageで生成した既定背景で、
プロジェクト本体と同じMIT Licenseで提供する。生成元と条件は
[`../CREDITS.md`](../CREDITS.md)を参照する。

表紙設定を指定しない場合は、この画像が標準表紙の背景として使われる。単色背景へ戻す場合は、
設定JSONで`cover.background_image`に`null`を指定する。

設定JSONの `cover.background_image` には、設定JSON自身からの相対パスを書く。
