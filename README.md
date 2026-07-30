# surocash-machines — SuroCash 機種カタログ

iOSアプリ「スロ収支帳（SuroCash）」が起動時に取得する、機種検索用データです。
**ここを更新すると、アプリを更新（再審査）しなくても全ユーザーの検索候補が最新化されます。**

## ファイル

| ファイル | 役割 |
|---|---|
| `machines.json` | アプリが取得する本番データ（自動生成物・直接編集しない） |
| `manual_seed.json` | **手入力の機種リスト（これが「正」）**。機種を足すときはここを編集 |
| `scripts/generate_machines.py` | `manual_seed.json` から `machines.json` を生成 |
| `.github/workflows/update-machines.yml` | 定期・push時に自動生成してコミット |

アプリの取得先（固定URL）:
`https://raw.githubusercontent.com/yamashitagames49-cpu/surocash-machines/main/machines.json`

## 機種を追加する（いちばん簡単な運用）

1. `manual_seed.json` に1行足す（例）:
   ```json
   { "name": "スマスロ 新台の名前", "type": "slot", "maker": "メーカー名" }
   ```
   - `type` は `"slot"`（スロット）か `"pachinko"`（パチンコ）。
   - `maker` は分からなければ `""` でOK。
2. コミット（GitHubのWeb上で編集→Commitでも可）。
3. push すると **GitHub Actions が自動で `machines.json` を再生成**してコミットします。
4. 数分後、アプリが次に起動したときに新しい機種が検索できます（アプリ更新は不要）。

## 自動更新のしくみ

- `.github/workflows/update-machines.yml` が **毎週月曜 00:00 UTC** と **push時** に実行され、
  `machines.json` を最新化します（Actions タブから手動実行も可能）。
- 手動実行時のオプションで **Wikipedia の公式API（MediaWiki API）から機種を補完** できますが、
  カバレッジは限定的でノイズも入り得るため既定はOFFです。品質重視なら `manual_seed.json` の
  手入力運用が確実です。

## メモ

- `machines.json` は自動生成物なので直接編集しても、次回生成で上書きされます。必ず `manual_seed.json` を編集してください。
- スキーマ: `{ "version": 1, "updatedAt": "YYYY-MM-DD", "machines": [ { "name", "type", "maker" } ] }`
