# 出典・検証履歴

このレシピは [SeeedJP/wio_cellular PR #64](https://github.com/SeeedJP/wio_cellular/pull/64)
の [コミット `e8946f8`](https://github.com/takao2704/wio_cellular/commit/e8946f83867ccd951a61ee7cb7052b08cc74f1fe)
から移植しました。元の著者・著者日時と元コミットへの参照を取り込みコミットに保持し、
レシピ用の配置・リンク変更は別コミットにしています。ライブラリ、スケッチ、配布ツールの実装は同一です。
MITライセンスとSeeed K.K.の著作表示は [LICENSE.txt](../LICENSE.txt) に保持しています。
以下の実機結果は元 PR での検証履歴であり、この移植およびレシピ再編集で実機への書込みやOTAを再実施したものではありません。

`src/` にmanifest・更新制御、HTTP/UFS転送、Bank 1書込みの実装をまとめています。
公開ヘッダ名とC++ APIは維持していますが、独立した3パッケージとしては配布しません。
`tools/` は配布ファイル生成用です。ホスト回帰テスト、明示的な実機停止試験設定と実行手順は、
[contributor forkの固定コミット](https://github.com/takao2704/wio_cellular/tree/3ba27170f6aea24827b5798a7fbef9f112bd8142/extras/lte-ota/tests)に保存しています。
本家向けツリーには、利用時に必要なサンプル、ライブラリ本体と配布ツールだけを含めます。

## レシピ再編集時のホスト検証

2026-10-23の再編集では次を確認しました。実機の書込み・フォーマット・bootloader更新・OTAは行っていません。

| 対象 | 結果 |
|---|---|
| PlatformIO initial / update | 両方成功。各171,404 bytes、上限397,312 bytes |
| Arduino CLI APP_VERSION=1 / 2 | 両方成功。各171,240 bytes |
| 生成したArduino ZIP内のスケッチ | コンパイル成功。171,240 bytes。ZIPにローカル鍵が含まれないことを確認 |
| InternalFS準備例 | Markdownから抽出し、false / trueをCore 1.5.1でコンパイル成功。実機実行なし |
| 元スナップショットの回帰テスト | 現行ファイルの独立コピーに対しC++実行ファイル6本、Pythonテスト19件が成功 |
| 文書 | 相対リンク・アンカー・シェル構文・参照ファイルと `git diff --check` を確認 |
| 実装・著作表示 | 元PRからのライブラリ・通常スケッチ・ビルド設定・配布ツール・LICENSE.txtに変更なし |

準備例のFlash使用量は検査用49,468 bytes、明示初期化用57,416 bytesでした。
ビルドには実運用鍵ではなく、無視対象の公開鍵ヘッダにテンプレートをコピーして使っています。これらの生成物は配信用ではありません。
Coreの `used` 属性に関する既存の警告と、テンプレートのコメント継続に関するPlatformIO警告は残ります。
回帰テストは固定スナップショットの `tools/run_native_tests.sh` と `tests/` を検証用の独立ディレクトリに取り出し、
レシピの現行ファイルをコピーして実行しました。実機試験用の環境は実行していません。

**未確認なのは、再編集後のレシピを初めから実機で通すことです。**
bootloader識別・必要時の移行、新規端末の保存領域準備と通常RESET後の確認、Arduino IDE GUIからの初回USB導入、
版2の署名配信、LTE適用後の版と最高適用版の保持は、対象を確認した実機試験が必要です。
上のホスト結果は、これらの成功や電源断耐性を保証するものではありません。

## 元PR当時の実機検証

保存記録の破損時処理を修正した単一ライブラリ構成を、HW v1.0の1台で再検証しました。
稼働中のアプリ版9からArduino CLI生成の版10へ、その版10からPlatformIO生成の版11へ、
USBでアプリを書き戻さずにLTE OTAしています。いずれも署名付きmanifestとサービスFQDNを使い、
全量取得・イメージ検証・再起動・新アプリ起動・更新なし判定を確認しました。

事前レビュー後のHTTP/UFS回復処理を含むArduino CLI生成の版12（174,400 bytes、
SHA-256 `d875549002dc742b201482bdc5719dca8fad9f5da6a39f82a061dbf4f0ff708c`）も、
版11からLTE OTAしました。Harvest Filesへ置いたイメージの読戻し一致を確認してから署名済みmanifestを公開し、
版12の起動、`current=12`・`highest=12` の読戻し、同じmanifestの更新なし判定を確認しています。
さらに通常RESET後も `loaded=12`・`current=12`・`highest=12` が維持され、再ダウンロードされませんでした。

版11の初回取得では、モデム内ファイルへの保存が設定した90秒を超えて失敗しました。
このとき更新は適用されず、通常RESET後の再試行で取得・適用に成功しています。
版11の最終RESET後は、保存済み版11、実行中の版11、最高適用版11を読み戻し、同じmanifestを更新なしと判定しました。
また、版10への更新直後にはPDPコンテキスト取得がタイムアウトし、WioのRESETではBG770Aがリセットされないため、
USB電源の入れ直しで復旧しました。アプリ側で短期再試行やモデム復旧を設計する際の運用上の注意点です。
版12配信の初回も、版11側のモデム内ファイル保存がタイムアウトして安全に終了しました。
通常RESETだけでは残ったモデム状態からLTE初期化できなかったため、USB電源を入れ直して再試行し、更新に成功しています。
結果の要約は[PR #64](https://github.com/SeeedJP/wio_cellular/pull/64)に記載しています。
破損記録の検出、延期、取得検証のみ、失敗後の再利用は、
[forkに保存したPC上の回帰テスト](https://github.com/takao2704/wio_cellular/tree/3ba27170f6aea24827b5798a7fbef9f112bd8142/extras/lte-ota/tests/native)で確認しています。

旧構成での[実機検証記録](https://github.com/takao2704/wio_cellular/blob/873ded2438b8083a7f001cde241c6e2962187a54/extras/lte-ota-agent/docs/validation/README.md)はforkの固定コミットに保存しています。
Arduino IDE GUIのコンパイル・USB書込みや障害試験は、この過去の記録と区別してください。
日付付きの実測記録や生ログは本家向けツリーには含めません。
新構成で実機の破損レコード注入や電源断試験は実施していません。
GUI生成バイナリ同士のLTE OTA、HW v1.1、多台数の段階配信、
bootloader反映・settings・不揮発レコード書込み中の電源断は未検証です。

[レシピへ戻る](../README.md)
