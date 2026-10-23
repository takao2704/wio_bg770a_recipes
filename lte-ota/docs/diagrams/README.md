# OTAレシピの図

[レシピ本文](../../README.md)に埋め込む横長の図です。両図とも **1800 × 900 px**。

- `architecture.svg` / `architecture.png`：PC → SORACOM → 端末の全体構成。
- `update-flow.svg` / `update-flow.png`：上段①〜④、下段⑤〜⑧の順で読む更新フロー。
- `generate.py`：配置・ラベル・矢印を編集するPython 3ソース（標準ライブラリのみ）。SVG自体も編集できますが、再生成時に上書きされるため変更はソースへ反映してください。
- `render-png.cjs`：SVGを一時的なChromeプロファイルで描画し、PNGを生成するスクリプト。

図はコードを説明する模式図です。実機の画面や検証結果ではありません。配置を変える場合も、[本文のコード参照](../../README.md#更新はこの順に進む)と照合してください。署名検証はfirmware取得前、全量ハッシュ照合はBank 1への書込み後です。bootloaderはBank 1からBank 0へコピーし、自動ロールバックは行いません。

## 再生成

このリポジトリのルートから実行します。Python 3、Node.js、Chromeが必要です。描画用依存はリポジトリ外の一時ディレクトリに入れます。

```bash
python3 lte-ota/docs/diagrams/generate.py
diagram_deps="$(mktemp -d)"
PUPPETEER_SKIP_DOWNLOAD=true npm install --prefix "$diagram_deps" --no-audit --no-fund puppeteer@23.11.1
NODE_PATH="$diagram_deps/node_modules" \
  CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' \
  node lte-ota/docs/diagrams/render-png.cjs
```

`CHROME_PATH` は使用するOSのChrome実行ファイルへ変更してください。日本語フォント（macOSのHiragino Kaku Gothic ProN、またはNoto Sans CJK JP）が必要です。フォント差で文字幅が変わるため、PNGを開いて文字の切れ、重なり、矢印の始点・終点を確認してください。SVG、PNG、編集ソースは一緒にコミットします。
