# InternalFSを確認し、新規端末だけ初回準備する

[レシピの手順4](../README.md#prepare-device)で、bootloaderの確認後、初回OTAアプリの導入前に行います。
OTAサンプルはInternalFSに最高適用版を保存します。読み出せないときはOTAを止め、保存領域を自動フォーマットしません。

## APIの違いと消去の影響

SeeedJP Core 1.5.1では以下の違いがあります。

| 呼出し | 動作 |
|---|---|
| `InternalFS.Adafruit_LittleFS::begin()` | マウントを試みる。失敗してもフォーマットしない。OTAの `VersionStore::begin()` が使用 |
| `InternalFS.begin()` | マウント失敗時、InternalFSの全セクタを消去・フォーマットしてから再マウントする |

後者が消すのはnRF52840のInternalFS領域（Core 1.5.1では `0xED000` から7ページ、28 KiB）です。
OTA履歴だけでなく、この領域を共有するアプリ設定・ファイルもすべて失われます。消えた最高適用版をOTAライブラリは復元できません。
単なるマウント失敗から、未初期化と破損を自動判別することはできません。

## 1. 準備用スケッチでマウントを確認する

以下をArduino IDEの新しいスケッチ `InternalFsPreparation/InternalFsPreparation.ino` に保存します。
レシピと同じHW v1.0 / S140 7.3.0 / Print Port Serial (USB-CDC)の設定を使います。
これは通信やOTAをしない独立した準備用スケッチです。USB書込み自体は既存アプリを置き換えます。
OTAサンプルの `setup()` へコピーしないでください。

初回は **`ALLOW_NEW_DEVICE_INITIALIZATION = false` のまま** コンパイル・USB書込みし、
115200 bps、改行LFのシリアルモニタを開きます。モニタを開くまで処理は待機します。

```cpp
#include <Adafruit_TinyUSB.h>
#include <Arduino.h>
#include <Adafruit_LittleFS.h>
#include <InternalFileSystem.h>

// Keep false for inspection. Enable ONLY for a known new, disposable device.
constexpr bool ALLOW_NEW_DEVICE_INITIALIZATION = false;

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);

  if (InternalFS.Adafruit_LittleFS::begin()) {
    Serial.println("MOUNT_OK: existing filesystem kept; no format requested");
    InternalFS.end();
    return;
  }
  Serial.println("MOUNT_FAILED: uninitialized OR damaged; not proof of empty storage");
  if (!ALLOW_NEW_DEVICE_INITIALIZATION) {
    Serial.println("STOP: inspection only; no format requested");
    return;
  }

  Serial.println("NEW DEVICE ONLY: all InternalFS data may be erased");
  Serial.println("Type ERASE NEW DEVICE and newline to initialize, or disconnect");
  while (!Serial.available()) delay(10);
  Serial.setTimeout(10000);
  String confirmation = Serial.readStringUntil('\n');
  confirmation.trim();
  if (confirmation != "ERASE NEW DEVICE") {
    Serial.println("STOP: confirmation did not match; no format requested");
    return;
  }

  // Core API formats on mount failure; reached only after explicit opt-in.
  if (!InternalFS.begin()) {
    Serial.println("INIT_FAILED: stop; investigate without repeated erasure");
    return;
  }
  InternalFS.end();
  if (!InternalFS.Adafruit_LittleFS::begin()) {
    Serial.println("REMOUNT_FAILED: stop; do not proceed to OTA");
    return;
  }
  Serial.println("INIT_OK: mounted again; replace this preparation sketch");
  InternalFS.end();
}

void loop() { delay(100); }
```

| 結果 | 次の操作 |
|---|---|
| `MOUNT_OK` | 保存領域を消さず終了。新規端末なら初期化を省略して手順3へ。既存端末は既存データ・最高適用版を維持する計画を確認 |
| `MOUNT_FAILED` | ここで止まる。履歴不明・使用済み・保存ファイルありなら初期化せず、バックアップや既知の適用版、元アプリでの読出し方法を確認 |

`MOUNT_OK` は保存ファイルやOTA版レコードの正常性まで保証しません。それは通常アプリの `VersionStore` が確認します。
この準備用スケッチはOTAの版レコードを作りません。

## 2. 未初期化と判断できる新規端末の場合だけ初期化する

未使用の検証用端末など、管理履歴から **保存すべきファイル・設定・過去のOTA適用履歴が一切ない** と確認できた場合に限ります。
新しいアプリを書き込んだ、以前のファイルが見えない、という理由だけでは条件を満たしません。

1. 上の確認結果が `MOUNT_FAILED` であり、上記の条件を満たすことを確認します。
2. 準備用スケッチだけの定数を `true` に変更し、コンパイルして対象端末へUSB書込みします。
3. シリアルモニタで消去の影響を読み、対象がその新規端末であることを再確認して `ERASE NEW DEVICE` と改行を送ります。送らなければ消去経路へ進みません。
4. `INIT_OK` を確認します。`INIT_FAILED` / `REMOUNT_FAILED` の場合は再消去を繰り返さず止めます。
5. 定数を `false` に戻した確認用スケッチをUSBで書き込み、通常RESET後にも `MOUNT_OK` になることを確認します。初期化を有効にしたスケッチを端末に残しません。

上のコードはCore APIと照合し、検査用（false）・初期化用（true）ともコンパイル確認するための例です。
この文書の編集時には実機の初期化・消去を行っていません。

## 3. 通常のOTAアプリで保存を確認する

[レシピの公開鍵準備と版1の導入](../README.md#signing-key)へ戻ります。必ず署名鍵・公開鍵の準備も済ませます。
新規端末の初回は `security state loaded=0 current=1 highest=1`、次の通常RESETでは `loaded=1 current=1 highest=1` が目安です。
これはコードから導いた説明例で、今回の実測ではありません。

- `internal filesystem mount failed`：マウントできない状態。初期化手順を通常のリトライ処理へ組み込まないでください。
- `no valid version record; explicit recovery required`：既存レコードが壊れている、または読めません。削除やフォーマットでアンチロールバックを解除せず、保存データ・既知の適用版から復旧を検討します。
- `version record write failed` / `version record read-back failed`：記録できません。電源・保存領域・Coreの組合せを調べ、OTAへ進まないでください。

`/wio-ota-version-a.bin` と `/wio-ota-version-b.bin` が両方存在しない場合だけ新規履歴として扱います。
片方が正常ならその版から復旧します。両方とも正常な記録がない異常状態ではOTAを止めます。
通常OTAコードのこの判断と、`VersionStore::begin()` の失敗時に書込みを拒否する動作は変更していません。

## 確認した実装

- [公式CoreのInternalFileSystem.cpp](https://github.com/SeeedJP/Adafruit_nRF52_Arduino/blob/514f28ee405952ecc58558b5e0608a2b63d9901a/libraries/InternalFileSytem/src/InternalFileSystem.cpp)：領域と消去を伴う `begin()`。`InternalFileSytem` は公式リポジトリ内の実際のディレクトリ名です。
- [公式CoreのAdafruit_LittleFS.cpp](https://github.com/SeeedJP/Adafruit_nRF52_Arduino/blob/514f28ee405952ecc58558b5e0608a2b63d9901a/libraries/Adafruit_LittleFS/src/Adafruit_LittleFS.cpp)：フォーマットしないマウントと `end()`。
- [VersionStore](../src/WioOtaVersionStore.cpp) / [通常サンプル](../examples/CellularStatusOta/CellularStatusOta.ino)：保存状態の確認とOTAをスキップする条件。

[レシピへ戻る](../README.md)
