"""全自動パイプライン: リサーチ → 生成 → 減点チェック → ジッター → 投稿 → 記録。

使い方:
  python pipeline.py            # config の dry_run_default に従う（既定: 投稿せずキュー出力）
  DRY_RUN=false python pipeline.py   # 実投稿
"""
import datetime
import json
import os
import random
import time
from pathlib import Path

import generate
import research
from post import post_to_x, reply_to_x

ROOT = Path(__file__).parent
STATE = ROOT / "state"


def now_jst():
    return datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=9))
    )


def main():
    cfg = generate.load_config()
    env = os.environ.get("DRY_RUN", "").lower()
    dry_run = cfg["posting"]["dry_run_default"] if env == "" else env != "false"

    # 1. リサーチ
    research.run()

    # 2. 生成 + 減点チェック
    result = generate.run()
    if result is None:
        return
    chosen = result["candidates"][result["selected"]]

    # 3. 時刻ジッター（機械的に規則正しい投稿時刻はアルゴの自動化検出シグナル）
    if not dry_run:
        jitter = random.randint(0, cfg["posting"]["jitter_minutes_max"] * 60)
        print(f"[pipeline] ジッター {jitter//60}分{jitter%60}秒 待機")
        time.sleep(jitter)

    # 4. 投稿 or キュー
    record = {
        "at": now_jst().isoformat(),
        "text": chosen["text"],
        "type": chosen["type"],
        "signal": chosen["signal"],
        "source_url": result["source_url"],
        "source_title": result["source_title"],
        "dry_run": dry_run,
    }
    if dry_run:
        queue = STATE / "queue"
        queue.mkdir(parents=True, exist_ok=True)
        fname = queue / f"{now_jst().strftime('%Y%m%d-%H%M')}.json"
        fname.write_text(json.dumps(record, ensure_ascii=False, indent=2))
        print(f"[pipeline] DRY RUN: {fname} に書き出し（投稿はしていない）")
    else:
        data = post_to_x(chosen["text"])
        record["tweet_id"] = data["id"]
        # 元ネタのリンクはリプ欄へ（本文にURLを置かない原則）。
        # URL付き投稿は$0.20/件と高額なので config で明示的に有効化した場合のみ
        if cfg["posting"].get("source_link_reply"):
            try:
                reply_to_x(f"元ネタはこちら\n{result['source_url']}", data["id"])
            except Exception as e:
                print(f"[pipeline] リプ欄リンク失敗（本体は投稿済み）: {e}")

    # 5. 記録（ネタの再利用防止）
    STATE.mkdir(exist_ok=True)
    with (STATE / "posted.jsonl").open("a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print("[pipeline] 完了")


if __name__ == "__main__":
    main()
