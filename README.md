# X Impressions Playbook Skill

X（旧Twitter）でインプレッションを最大化するための Claude Code Skill。

ろじん（@fiction_log、Levela CXO・X顧問累計900社）、駒居康樹（@koki_komai、Levela代表）の公開ノウハウと、Xアルゴリズムの公開情報（2023年オープンソースコード＋2026年Grok移行）を統合したプレイブックです。

## 構成

```
.claude/skills/x-impressions-playbook/
├── SKILL.md                          # メインのプレイブック（ワークフロー・型・チェックリスト）
└── references/
    ├── rojin-method.md               # ろじん式（元情報+解説型、リストKPI、ジャンル選定）
    ├── komai-levela-method.md        # 駒居/Levela式（ストーリーテリング、金銭フック、コンセプト設計）
    └── algorithm.md                  # アルゴリズム詳細（エンゲージメント重み、2026年変更、禁止事項）
```

## 使い方

このリポジトリを Claude Code で開くと、Skill が自動で認識されます。以下のような依頼で発動します:

- 「この内容でXのポストを書いて」
- 「このポストを添削して」
- 「Xアカウントのコンセプトを設計したい」
- 「インプレッションが伸びない理由を診断して」

## 注意

- ノウハウはすべて公開情報（note無料部、インタビュー、公式ブログ、プレスリリース、オープンソースコード）から収集したものです。有料教材の中身は含まれません。
- Levela社関連の実績数値は自己申告であり第三者検証はありません。
