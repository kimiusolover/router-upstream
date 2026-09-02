# router-upstream の運用方針

[English README](README.md)

- 上流入力は、正規の URL、不変リビジョン、キャッシュ名、SHA-256、HTTPS の来歴、レビュー根拠を持つロック済み成果物として扱います。
- `latest`、`master`、ミラー、文書 URL、ビルド時のネットワーク取得はロック済み入力ではありません。
- 同期自動化は変更候補を提示するだけで、自動マージ、ビルド、署名、フラッシュ、公開を行いません。
- パッチの適用可能性やソース同一性は、機種サポートや安全な配備の証明にはなりません。
- クロスツールチェーンも上流入力です。ホストの実行ファイル、host libc、host header を
  ターゲット成果物に流用せず、ロック済み archive と一致する compiler / triplet /
  sysroot だけを使います。MIPS 層は `mipsel` / `musl` / 対象 ABI を固定できない限り
  `pending-verification` のままとし、ビルドを拒否します。
