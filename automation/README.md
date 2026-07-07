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

### 1. X APIキーの取得（2026年2月〜は従量課金制）

X APIは2026年2月に旧無料枠が廃止され、新規は**pay-per-use（従量課金）**のみ。
審査なし・セルフサービスで即日取得できる。

1. 運用するXアカウントでログインした状態で [developer.x.com](https://developer.x.com) にアクセスし、
   開発者利用規約に同意（電話番号・メール認証済みのアカウントが必要）
2. デベロッパーコンソールでプロジェクト＋アプリを作成
3. アプリの **User authentication settings** を設定:
   - App permissions: **Read and Write**（これを忘れると投稿が403になる）
   - Type of App: Web App / Automated App or Bot
   - Callback URL / Website URL: 適当な自サイトURLでよい（例: このリポジトリのURL）
4. **Keys and tokens** タブで取得（権限変更後にAccess Tokenを**再生成**すること）:
   - API Key / API Key Secret
   - Access Token / Access Token Secret（「Created with Read and Write permissions」表示を確認)
5. コンソールでクレジットをチャージ（$5〜10で数ヶ月分。下記コスト参照）

**運用コスト目安**: 投稿$0.015/件。1日3投稿×30日 = 90件 ≒ **月$1.35**。
※URL付き投稿は$0.20/件と13倍高いため、config の `source_link_reply` は既定off。
Claude API側は1日3回の生成で月$1前後（Sonnet使用時）。**合計で月$2〜3程度**。

### 2. 疎通確認

```bash
cd automation && pip install -r requirements.txt
export X_API_KEY=... X_API_SECRET=... X_ACCESS_TOKEN=... X_ACCESS_TOKEN_SECRET=... ANTHROPIC_API_KEY=...
python check_credentials.py   # 課金される書き込みはせず認証だけ確認
python pipeline.py            # DRY RUN: state/queue/ に投稿案が出る
```

### 3. GitHubに登録

**Settings → Secrets and variables → Actions**:
- Secrets: `ANTHROPIC_API_KEY`, `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`
- Variables: `AUTOPOST_DRY_RUN` = `true`（レビュー期間後に `false` へ）

### 4. Xのアカウント設定

設定 → アカウント → 「自動化されたアカウント」ラベルを設定
（X運営ポリシー上、自動投稿アカウントは明示が必要）。

ジャンルや投稿の型を変えるときは `config.yaml` を編集。

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
