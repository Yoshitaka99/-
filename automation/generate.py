"""ポスト生成: Skillの生成ルール+実ポストコーパスをシステムプロンプトに埋め、
当日の元ネタから候補を生成 → 減点チェック → 最良1本を選ぶ。
"""
import datetime
import json
import os
import re
import sys
from pathlib import Path

import yaml
from anthropic import Anthropic

ROOT = Path(__file__).parent
SKILL = ROOT.parent / ".claude" / "skills" / "x-impressions-playbook"


def load_config():
    return yaml.safe_load((ROOT / "config.yaml").read_text())


def weighted_length(text: str) -> int:
    """Xの重み付き文字数（全角=2、半角=1の近似）。"""
    return sum(2 if ord(c) > 0x7F else 1 for c in text)


def quality_gate(text: str, cfg) -> list[str]:
    """減点チェック。違反リストを返す（空=合格）。"""
    problems = []
    if re.search(r"https?://", text):
        problems.append("本文にURLがある（リンクはリプ欄へ）")
    for phrase in cfg["generation"]["banned_phrases"]:
        if phrase in text:
            problems.append(f"ベイト表現: {phrase}")
    if weighted_length(text) > cfg["generation"]["max_weighted_length"]:
        problems.append(f"長すぎる（重み付き{weighted_length(text)}）")
    if text.count("#") > 2:
        problems.append("ハッシュタグ過多")
    return problems


def build_system_prompt(cfg) -> str:
    rules = (SKILL / "references" / "generation-rules.md").read_text()
    corpus = (SKILL / "references" / "post-corpus.md").read_text()
    persona = cfg["account"]["persona"]
    return f"""あなたはX(旧Twitter)のポスト作成エンジンです。

## ペルソナ
ジャンル: {cfg['account']['genre']}
{persona}

## 生成ルール（厳守）
{rules}

## Few-Shot（型のリズムだけ借りる。内容・固有名詞は絶対に流用しない）
{corpus}

## 全自動モード固有の制約
- 与えられた元ネタ（実在ニュース）に含まれる事実だけを使う。数字・固有名詞の捏造は禁止。
- 実体験が必要な型（実績スクショ型・経歴型・原体験型）は使わない。
- 誰かを欺く内容、特定個人への攻撃は書かない。
- 出力はJSONのみ。"""


def generate(news_items, cfg):
    client = Anthropic()  # ANTHROPIC_API_KEY
    weekday = datetime.datetime.now(datetime.timezone.utc).astimezone(
        datetime.timezone(datetime.timedelta(hours=9))
    ).weekday()
    today_type = cfg["generation"]["weekday_types"][weekday]
    user_msg = f"""今日の型: {today_type}

今日の元ネタ候補（注目資本の大きい順）:
{json.dumps(news_items, ensure_ascii=False, indent=2)}

手順:
1. 元ネタから今日の型に最も合う1つを選ぶ（日本の読者に関係が翻訳しやすいもの優先）
2. 共通エンジンの思考手順（感情選択→1行目5機能→本文→最終行→減点チェック）で{cfg['generation']['candidates']}案生成
3. 各案を自己採点し、最良を selected に指定

次のJSONだけを出力:
{{"source_url": "選んだ元ネタのURL", "source_title": "…",
 "candidates": [{{"text": "ポスト全文", "type": "型名", "signal": "狙うシグナル", "reason": "なぜ伸びる想定か1行"}}],
 "selected": 0}}"""

    resp = client.messages.create(
        model=cfg["generation"]["model"],
        max_tokens=2000,
        system=build_system_prompt(cfg),
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = resp.content[0].text
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError(f"JSONが取れない: {raw[:200]}")
    return json.loads(match.group(0))


def run():
    cfg = load_config()
    news = json.loads((ROOT / "state" / "research-latest.json").read_text())
    if not news:
        print("[generate] 元ネタなし。今日はスキップ")
        return None
    result = generate(news, cfg)
    # 減点チェック: 合格する候補まで selected を繰り下げる
    order = [result["selected"]] + [
        i for i in range(len(result["candidates"])) if i != result["selected"]
    ]
    for idx in order:
        text = result["candidates"][idx]["text"]
        problems = quality_gate(text, cfg)
        if not problems:
            result["selected"] = idx
            break
        print(f"[generate] 候補{idx}が減点チェックNG: {problems}", file=sys.stderr)
    else:
        print("[generate] 全候補NG。今日は投稿しない", file=sys.stderr)
        return None
    out = ROOT / "state" / "candidate-latest.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    chosen = result["candidates"][result["selected"]]
    print(f"[generate] 採用({chosen['type']} / {chosen['signal']}):\n{chosen['text']}")
    return result


if __name__ == "__main__":
    run()
