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
