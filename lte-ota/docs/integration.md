# 既存アプリへの組込みと運用上の制約

以下のソース・ツールのパスはレシピのルート `lte-ota/` を基準にしています。

PlatformIOではプロジェクトの `lib/WioOtaAgent` へ
`src/`、`scripts/`、`library.json`、`library.properties`、`LICENSE.txt` をコピーするか、
`lib_deps` に `WioOtaAgent=symlink:///absolute/path/to/lte-ota` を指定します。
Arduino IDEでは[レシピのライブラリ導入手順](../README.md#software)で作る1つのZIPを使います。

PlatformIOのボード・Core・サイズ上限は付属 `platformio.ini` に合わせ、
`lib_archive = no` と `-DWIO_OTA_ENABLE_ED25519` を設定します。
後者は署名検証実装のリンク指定であり、署名を必須にする設定とは別です。
Arduino IDE／CLIではnRF52840向け署名実装が自動的にビルドされます。

[共通スケッチ](../examples/CellularStatusOta/CellularStatusOta.ino)の `setup()`、`checkOta()`、
`decideUpdate()` を組み込みの基準にしてください。

- アプリでLTE接続とPDP contextを準備してから `Agent::check()` を呼びます。
- `Config` で対象HW、manifest取得先、許可するfirmwareホスト・ポートを指定します。
- 通常運用では `security.require_signature=true` と公開鍵・key IDを設定します。
  アンチロールバックと段階配信も使う場合は、現在の版と永続化した最高適用版、安定した端末IDを渡します。
- `Agent` は大きなmanifestバッファを保持するため静的領域へ置きます。
  設定は生成時にコピーされるので、後から外側の `Config` だけを書き換えても反映されません。
  設定から参照する文字列や公開鍵は、Agentを使う間ずっと有効な領域へ置きます。
- アプリの判定コールバックは技術的検証・セキュリティ判定の後に呼ばれます。

| コールバックの戻り値 | 動作 |
|---|---|
| `Decision::kNoUpdate` | 更新なし。取得しない |
| `Decision::kReject` | アプリの条件で対象外。取得しない |
| `Decision::kDefer` | 端末状態などにより延期 |
| `Decision::kDownloadAndVerify` | Bank 1へ取得・検証した後、適用登録せず破棄 |
| `Decision::kApply` | 取得・検証後、モデム停止・適用登録・再起動 |

`APP_VERSION` はサンプルの識別方法で、ライブラリ必須のビルドフラグではありません。
更新判定はアプリ内定数や適用済みリリースIDなどで実装できます。
ただしアンチロールバックを使う場合は数値の現在バージョンと最高適用バージョンを正しく管理します。

日次確認や再試行もアプリの責任です。例えば起動時と24時間ごとに確認し、
`Result::kFailed` と `Result::kDeferred` は1時間後に再試行します。
連続稼働中の間隔には `millis()` の差分、再起動をまたぐ時刻指定にはRTC等と永続化した最終確認時刻を使います。
このライブラリ自体にスケジューラはありません。

`check()` は同期・非再入APIです。同じモデムを別処理から同時に操作せず、
時間制約のある処理を先に止め、SoftDeviceを無効化できる状態で呼びます。
更新適用時は戻らず再起動します。それ以外の結果ではアプリ側でモデムやPSMの通常設定へ戻します。
UFS保存の完了が90秒を超えた場合は、遅れて届く完了応答を45秒まで排出してから一時ファイルの削除を試みます。
HTTP設定、GET/READ、ファイルopen/close/deleteのタイムアウトや本文処理の中断では、
遅延応答や未読データを次回のATコマンドへ混入させないため、
Agentは戻る前にセルラーモジュールを停止します。その場合は `lastHttpRecoveryAttempted()` がtrueになり、
次のOTA確認前にアプリ側でセルラーモジュールの起動、LTE接続、PDP有効化をやり直す必要があります。
停止にも失敗した場合は `lastHttpRecoveryFailed()` がtrueとなり、`lastError()` は
`kModemPowerOffFailed` を返します。失敗時の詳細は `lastHttpError()`、`lastHttpCleanupError()`、
`lastWriterError()`、`lastSecurityError()` から取得できます。

## セキュリティと制約

署名付きmanifestのSHA-256と取得イメージを照合し、検証完了後にのみ適用登録します。
本文全体の検証はBank 1への書込み後に完了するため、未検証データが一時的に保存されることはあります。
CRC16とSHA-256だけの未署名format 1は破損検出用であり、配信者認証には使えません。
署名必須または段階配信を有効にした運用ではformat 2が必要です。

`VersionStore` はInternalFSへ最高適用版を保存し、新アプリの `setup()` 到達後に更新します。
業務処理の正常性を保証するヘルスチェックではありません。
保存領域は自動フォーマットしません。マウント済み領域に記録が両方ない場合は新規として開始し、
片方だけ正常ならその版から復旧します。既存記録があるのに正常なものが一つもない場合や、
領域をマウントできない場合はエラーを返し、サンプルはOTAを実行しません。
`begin()` に失敗したまま `recordCurrentVersion()` を呼んでも書き込みません。

初めて使う端末でInternalFSが未初期化なら、初回USB導入時に保存領域を準備してください。
Coreの `InternalFS.begin()` はマウント失敗時に領域全体を消去・初期化するため、
既存ファイルも過去の適用履歴もないと確認した新規端末の初回準備にだけ使います。
通常のOTAアプリやエラー処理には追加しないでください。
稼働済み端末でエラーが出た場合は、記録を消して再開せず、保存データと既知の適用版を確認して復旧します。
既存アプリとInternalFSを共有する場合は、操作の同時実行、記録ファイル名の衝突、
他の処理によるフォーマット・記録削除を避けてください。削除済みの履歴をライブラリが復元することはできません。
鍵の更新では、旧鍵で署名する更新アプリへ新しい公開鍵を入れ、その展開を確認してから配信側の鍵を切り替えます。
現在のConfigが受け付ける公開鍵は1つです。

通信はHTTP・固定Content-Lengthが前提で、HTTPS、chunked transfer、途中再開には未対応です。
HTTP本文は暗号化されません。再試行では先頭から取得します。
署名検証はアプリ内Agentの機能で、bootloaderのsecure bootではありません。
USB DFU／SWDによる書換えや秘密鍵漏えいは保護範囲外です。
起動できない更新アプリからの自動ロールバック、更新結果の遠隔通知、端末群の配信管理画面も含みません。


## 配信ツールの条件

`rollout` は0〜10000で、2500なら25%、10000なら全対象端末です。
端末IDと `release_id` から対象を決めるため、同じリリースIDで配信率を増やすと対象集合が増えます。
URL・version・rolloutなど署名対象の値を変更するときはJSONを手編集せず再署名します。
生成ツールは端末側と同じく `http://`、host 127 bytes以下、path 255 bytes以下を受け付けます。
`--version` はアプリの `APP_VERSION` と合わせます。DFU ZIPの `application_version` とは別で、ツールはアプリの版を自動取得しません。
`--firmware-output` は `--output` と併用し、署名・検証・両ファイルの準備が終わってから置き換えます。
途中で置換に失敗した場合は既存の2ファイルを元に戻します。Arduino ZIP生成も一時ファイルで完成させてから置き換えます。

[レシピへ戻る](../README.md)
