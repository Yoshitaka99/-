# X自動投稿パイプライン

リサーチ → ポスト生成 → 減点チェック → 投稿 → 記録 を全自動化する。生成にはSkill（`.claude/skills/x-impressions-playbook/`）の生成ルールと実ポストコーパスをそのまま使う。

```
GitHub Actions (JST 6:00 / 12:15 / 21:30 + ジッター0〜20分)
  └─ pipeline.py
       ├─ research.py   … Hacker News + RSS からAIニュース収集（無料API、使用済みURLは除外）
       ├─ generate.py   … Claude APIで曜日別の型に沿って3案生成 → 減点チェック → 最良1本
       ├─ post.py       … X API v2 で投稿（元ネタリンクはリプ欄に自動投稿）
       └─ state/        … posted.jsonl（投稿履歴・ネタ再利用防止）、queue/（DRY RUN出力）
```

## セットアップ

1. **X API**: [developer.x.com](https://developer.x.com) でアプリ作成（無料枠: 月500投稿で十分）。
   User authentication settings で **Read and Write** を有効化してから
   API Key / Secret、Access Token / Secret を発行。
2. **GitHubリポジトリの Settings → Secrets and variables → Actions** に登録:
   - Secrets: `ANTHROPIC_API_KEY`, `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`
   - Variables: `AUTOPOST_DRY_RUN` = `true`（レビュー期間が終わったら `false` に）
3. **Xのアカウント設定**: 設定 → アカウント → 「自動化されたアカウント」ラベルを設定
   （X運営ポリシー上、自動投稿アカウントは明示が必要）。
4. ジャンルや投稿の型を変えるときは `config.yaml` を編集。

## 運用の推奨手順（重要）

**いきなり全自動にしない。** 2026年のXアルゴリズムはAI量産テンプレ文・機械的な投稿を品質減点するため、以下の段階を踏む:

1. **第1週〜: DRY RUNで回す**（既定）。毎回 `automation/state/queue/` に投稿案が溜まるので、
   中身を確認して手動投稿する。違和感のある表現をconfigのペルソナ・Skillの生成ルールに反映。
2. **品質が安定したら**: `AUTOPOST_DRY_RUN=false` で実投稿に切り替え。
3. **週次レビュー（ここだけは人間の仕事）**: Xアナリティクスで当たり投稿を確認 →
   `post-corpus.md` のFew-Shotに自分の当たり投稿を追加 → 生成品質が複利で上がる。
4. **投稿後60分のリプ返信は自動化できない**（リプ往復=いいねの150倍のシグナルは人間の返信でしか稼げない。
   botの自動リプは2026年2月からAPI制限＋検出対象）。通知を見て手で返すこと。

## 自動化の限界（設計上の割り切り)

| 工程 | 自動化 | 備考 |
|---|---|---|
| リサーチ（元ネタ収集） | ✅ 全自動 | HN+RSS。X内リサーチ（min_faves検索）はAPI有料のため対象外 |
| 投稿文生成 | ✅ 全自動 | 曜日別型ローテ+減点チェック。実体験が必要な型は自動では使わない |
| 投稿・時刻 | ✅ 全自動 | 3枠+ジッターで機械的規則性を回避 |
| リプ返信（初速の主エンジン） | ❌ 手動 | 自動リプはAPI制限・アカウント評価毀損リスク |
| 週次の当たり分析→Few-Shot更新 | ❌ 手動 | ここが品質の複利。サボると生成がテンプレ化して減点され始める |
