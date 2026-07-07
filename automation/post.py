"""X API v2 への投稿。無料枠（月500ポスト）で1日1〜3本は十分収まる。

必要な環境変数（X Developer Portal のアプリで Read and Write 権限を付与して取得）:
  X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET
"""
import os

from requests_oauthlib import OAuth1Session


def post_to_x(text: str) -> dict:
    session = OAuth1Session(
        os.environ["X_API_KEY"],
        client_secret=os.environ["X_API_SECRET"],
        resource_owner_key=os.environ["X_ACCESS_TOKEN"],
        resource_owner_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
    )
    resp = session.post("https://api.twitter.com/2/tweets", json={"text": text})
    if resp.status_code != 201:
        raise RuntimeError(f"投稿失敗 {resp.status_code}: {resp.text}")
    data = resp.json()["data"]
    print(f"[post] 投稿成功: https://x.com/i/status/{data['id']}")
    return data


def reply_to_x(text: str, in_reply_to: str) -> dict:
    """リプ欄にリンクを貼る用（本文にURLを置かない原則の実装）。"""
    session = OAuth1Session(
        os.environ["X_API_KEY"],
        client_secret=os.environ["X_API_SECRET"],
        resource_owner_key=os.environ["X_ACCESS_TOKEN"],
        resource_owner_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
    )
    resp = session.post(
        "https://api.twitter.com/2/tweets",
        json={"text": text, "reply": {"in_reply_to_tweet_id": in_reply_to}},
    )
    if resp.status_code != 201:
        raise RuntimeError(f"リプ投稿失敗 {resp.status_code}: {resp.text}")
    return resp.json()["data"]
