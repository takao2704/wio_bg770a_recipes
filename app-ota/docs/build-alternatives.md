# Arduino CLI・PlatformIOを使う場合

[主手順](../README.md)はArduino IDE向けです。このページはアプリのビルド・初回USB書込み・更新ZIP出力だけの代替です。
ボード・SIM・ブートローダー・InternalFS・鍵の準備は省略せず、主手順1〜5を完了してください。
PlatformIOだけを使う場合、Arduino用ライブラリZIPのインストールは不要ですが、ブートローダーとInternalFSの準備には主手順のArduino環境を使えます。
すべて `app-ota` ディレクトリから実行し、初回も次回も同じ公開鍵・署名必須設定を保持します。

## Arduino CLI

Core 1.5.1、WioCellular 0.3.15、ArduinoJson 7.0.4が同CLIから利用できることを `arduino-cli core list` / `arduino-cli lib list` で確認します。
`--library .` はこのソースをWioOtaAgentとして指定します。同名の旧ライブラリは併用しません。

```bash
arduino-cli compile \
  --fqbn SeeedJP:nrf52:wio_bg770a:board_version=1_0,softdevice=s140v7,debug_output=serial \
  --library . --build-property compiler.cpp.extra_flags=-DAPP_VERSION=1 \
  --output-dir dist/arduino-initial examples/CellularStatusOta
```

初回だけ、`arduino-cli board list` で対象ポートを確認し、`<WIO_PORT>` を実在するWioのポートへ置き換えて書き込みます。
既存アプリを置き換える操作です。自動でDFUへ移れない場合はRESETをダブルクリックし、DFUポートを選びます。

```bash
arduino-cli upload \
  --fqbn SeeedJP:nrf52:wio_bg770a:board_version=1_0,softdevice=s140v7,debug_output=serial \
  --port <WIO_PORT> --input-dir dist/arduino-initial examples/CellularStatusOta
```

[主手順6](../README.md#first-app)と同じ版1・LTE・保存状態を確認した後、更新用をコンパイルします。
CLIの `-DAPP_VERSION=2` がヘッダのデフォルト値より優先されます。IDEへ戻る場合はヘッダ内の版も確認してください。

```bash
arduino-cli compile \
  --fqbn SeeedJP:nrf52:wio_bg770a:board_version=1_0,softdevice=s140v7,debug_output=serial \
  --library . --build-property compiler.cpp.extra_flags=-DAPP_VERSION=2 \
  --output-dir dist/arduino-update examples/CellularStatusOta
```

更新用ZIPは **`dist/arduino-update/CellularStatusOta.ino.zip`** です。
更新版はUSBで書き込まず、[主手順7の署名・配信ファイル生成](../README.md#update-image)の入力ZIPをこのパスに置き換えます。

## PlatformIO

[platformio.ini](../examples/CellularStatusOta/platformio.ini)のCoreとplatformは固定コミットを参照し、
`WioOtaAgent=symlink://../..` でレシピ内ライブラリを使います。同じ `.ino` を直接ビルドします。
この環境では `ota_sketch_config.h` を読まず、iniの `initial` が `APP_VERSION=1`、`update` が `APP_VERSION=2` です。
両方とも `WIO_OTA_SECURE` と主手順5で生成した公開鍵ヘッダが必要です。

```bash
pio run -d examples/CellularStatusOta -e initial
```

初回だけ対象ポートを確認し、プレースホルダーを置き換えてUSBで書き込みます。

```bash
pio run -d examples/CellularStatusOta -e initial -t upload --upload-port <WIO_PORT>
```

[主手順6](../README.md#first-app)と同じ動作を確認した後、更新用をビルドします。

```bash
pio run -d examples/CellularStatusOta -e update
```

更新用ZIPは **`examples/CellularStatusOta/.pio/build/update/firmware.zip`** です。
`update` のuploadは行わず、[主手順7の署名・配信ファイル生成](../README.md#update-image)の入力ZIPをこのパスに置き換えます。

いずれも版1→2は新規端末向けの例です。稼働済み端末は現在・最高適用版を超える番号を使い、履歴を消して旧版を通さないでください。
これらのビルドはホストで検証しますが、この文書の再編集後のUSB書込みやLTE OTAは未実施です。

[レシピへ戻る](../README.md)
