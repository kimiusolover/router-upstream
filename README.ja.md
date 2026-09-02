# router-upstream

[English README](README.md)

Router OS が利用する上流プロジェクトのソースマップ、同期方針、下流パッチのメタデータを管理します。

ソースロックは入力の同一性と完全性を示すものであり、特定ボードとの互換性、ファームウェアイメージ、フラッシュ、RF 動作を許可するものではありません。

ビルド消費側は、`status: locked`、不変リビジョン、ローカルキャッシュ、SHA-256 が一致する入力だけを受け入れ、ダウンロード・ミラー選択・移動参照の解決を行いません。詳細は [POLICY.ja.md](POLICY.ja.md) を参照してください。

## Upstream sync bot

`sync/upstream-sync` は、取得済みの候補 source lock を fail-closed で検証します。
候補と一致するローカル archive、候補の不変 Git revision を持つクリーンな checkout、
および任意の downstream patch を受け取り、patch は一時 worktree で
`git am --3way` により試験します。成功しても出力は `needs-review` report のみです。

ネットワーク取得、lock の書換え、PR の作成・マージ、firmware build、署名、配布、
flash、RF 設定は行いません。private cache や checkout を必要とする検証は GitHub
Actions には載せず、開発機で明示的に実行します。

## MIPS クロスコンパイル層

`toolchains/mipsel-24kc-musl.yaml` は、`ramips/mt7621` 向けの
MIPS little-endian / musl クロスビルド境界です。これはホスト用バイナリを
ターゲットに流用する機能ではありません。`cross/verify-toolchain` は、ロック済み
ツールチェーン入力のローカル・キャッシュ、抽出済みの compiler、triplet、sysroot
がすべて一致する時だけホスト上のビルドに使用可能と報告します。ネットワーク取得や
ホストの libc・ヘッダへのフォールバックは行いません。

ロック完了後にだけ、明示的なコマンドを実行できます。

```sh
cross/verify-toolchain --record toolchains/mipsel-24kc-musl.yaml \
  --upstream-dir . --source-cache /path/to/cache \
  --execute -- make -C /path/to/router-packages build-hostapd
```

検証器は archive を毎回隔離した一時ディレクトリへ展開してから compiler と sysroot を
確認します。この実行では `CROSS_COMPILE`、`CC`、`SYSROOT`、
`PKG_CONFIG_SYSROOT_DIR`、`PKG_CONFIG_LIBDIR` を検証済み root にだけ設定し、
`PKG_CONFIG_DIR` と `PKG_CONFIG_PATH` を空にして host の `.pc` ファイルを
探索しません。

現在のレコードは `pending-verification` です。正規のツールチェーン archive を
source lock として固定し、ABI と sysroot をレビューするまで、MIPS 向けビルドは
意図的に拒否されます。これは AX23V の boot、flash、Wi-Fi、RF の許可ではありません。

## AX23V ターゲットゲート

AX23V は AX23 v1 の別名ではありません。`targets/ax23v-v1.yaml` は専用の
cross-build ゲートで、初期状態は `pending-verification` です。AX23V で MIPS 層を
使うには、機種固有の hardware evidence、kernel source lock、kernel release、config
SHA-256、vermagic、platform target、ABI がすべて locked かつ一致しなければなりません。

`cross/verify-ax23v-build` を使うと、このゲートを必ず通してから MIPS toolchain を
起動します。cross-build が通っても image、flash、RF 送信フラグは常に `false` のままです。
