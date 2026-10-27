# HW v1.0のブートローダーを確認する

[レシピの手順4](../README.md#prepare-device)で行う初回確認です。
対応dual-bank bootloaderとS140 7.3.0が必要です。PCへCoreを導入する操作と、実機のbootloader更新は別です。

## 1. 実機を読み取り確認する

1. PCにUSB接続し、RESETをダブルクリックしてDFUモードへ入ります。
2. `BOOT` ボリュームの `INFO_UF2.TXT` を開き、識別子とSoftDeviceを控えます。DFUへ入っただけではアプリを書き換えません。
3. 導入元・導入記録と次の組合せを照合します。

| 項目 | 元PRのHW v1.0で検証した値 |
|---|---|
| Bootloader識別子 | `0.9.1-33-g3cb5c65-dirty` |
| SoftDevice | S140 7.3.0 |
| Arduinoボードパッケージ | SeeedJP nRF52 Boards 1.5.1 |
| 配布ZIP | `Seeed_Wio_BG770A_bootloader-0.9.1_s140_7.3.0.zip` |
| ZIPのSHA-256 | `ba308f0f028706225764719d470b6facd7bd5e643f11b1781e5aa6a09106b8a5` |

これは特定の検証済みイメージの識別情報です。`0.9.1` や `S140 7.3.0` の表示だけではdual-bank対応を判定できません。
`INFO_UF2.TXT` も完全なFlash検証ではありません。導入元が不明、識別子や構成が異なる場合は、そのbootloaderの更新仕様・メモリ配置を確認するか、次の条件を満たして検証済みパッケージへ移行します。

レシピのWriterはapplication `0x27000`、Bank 1 `0x88000`、bootloader `0xf4000`、settings `0xff000` を前提にします。
互換性を確認できなければOTAへ進みません。既に組合せが確認できていれば再書込みせず、[保存領域の確認](internalfs.md)へ進みます。

## 2. 移行が必要な場合だけ実施する

**既存アプリが失われる前提で、復旧用アプリ・設定のバックアップと安定した給電を用意します。**
製品稼働中や保存データの扱いが不明な端末では止めてください。USB DFUで復旧できなくなるとSWD/J-Link等が必要になる場合があります。
このレシピの編集・検証作業では、以下の実機操作は実行していません。

1. Arduino IDEのボードパッケージを **SeeedJP nRF52 Boards 1.5.1** に固定します。
2. PCのCoreディレクトリで `bootloader/Seeed_Wio_BG770A/Seeed_Wio_BG770A_bootloader-0.9.1_s140_7.3.0.zip` を探します。標準のCoreディレクトリは次の場所です（インストール方法で異なる場合はIDEの詳細出力で確認）。

| OS | Coreディレクトリ |
|---|---|
| macOS | `~/Library/Arduino15/packages/SeeedJP/hardware/nrf52/1.5.1` |
| Linux | `~/.arduino15/packages/SeeedJP/hardware/nrf52/1.5.1` |
| Windows | `%LOCALAPPDATA%\Arduino15\packages\SeeedJP\hardware\nrf52\1.5.1` |

3. ファイルを変更せずハッシュを確認します。以下の `/path/to/...` を実在するZIPのパスへ置き換えます。

```bash
python3 -c 'import hashlib, pathlib, sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' \
  /path/to/Seeed_Wio_BG770A_bootloader-0.9.1_s140_7.3.0.zip
```

4. 上のSHA-256と一致する場合だけ進みます。不一致ならZIPを上書きしたりチェックを省略せず、パッケージの導入元を確認します。
5. IDEでボードをWio BG770A、Board Versionを1.0、SoftDeviceをS140 7.3.0、Programmerを **Bootloader DFU for Bluefruit nRF52** に設定し、対象のポートを選びます。J-Linkの全消去手順と混同しないでください。
6. 「ツール」→「ブートローダを書き込む」を実行します。自動でUSB DFUへ入れない場合はRESETをダブルクリックし、DFUポートを選び直します。
7. 完了後、DFUモードで `INFO_UF2.TXT` を再確認します。識別子・SoftDeviceが一致しなければアプリ導入やOTAに進みません。
8. [InternalFSの確認・初回準備](internalfs.md)へ進み、その後[公開鍵と初回アプリの導入](../README.md#signing-key)へ戻ります。bootloader更新だけではLTE OTAは始まりません。

## 根拠と出典

手順は[元の移行文書（固定コミット）](https://github.com/takao2704/wio_cellular/blob/873ded2438b8083a7f001cde241c6e2962187a54/extras/lte-ota-agent/docs/bootloader-migration.md)から取り込みました。
旧文書のアプリ導入リンクへ戻らず、このレシピ内で続行できます。過去の実測は[検証履歴](validation.md)を参照してください。

ハッシュは手元のCore 1.5.1で確認し、ZIPのGit blob SHA `cb6037e3d4103a9b0b8e2b6e2142f7904295c931` が
[公式Coreの固定コミットの同梱ZIP](https://github.com/SeeedJP/Adafruit_nRF52_Arduino/blob/514f28ee405952ecc58558b5e0608a2b63d9901a/bootloader/Seeed_Wio_BG770A/Seeed_Wio_BG770A_bootloader-0.9.1_s140_7.3.0.zip)と一致することも確認しました。
IDEの選択ファイルは同Coreの [platform.txt](https://github.com/SeeedJP/Adafruit_nRF52_Arduino/blob/514f28ee405952ecc58558b5e0608a2b63d9901a/platform.txt)、USB DFUコマンドは [programmers.txt](https://github.com/SeeedJP/Adafruit_nRF52_Arduino/blob/514f28ee405952ecc58558b5e0608a2b63d9901a/programmers.txt)に基づきます。
一般的なDFU操作は[Seeed公式ユーザーマニュアル](https://seeedjp.github.io/Wiki/Wio_BG770A/user-manual.html)を参照してください。

[レシピへ戻る](../README.md)
