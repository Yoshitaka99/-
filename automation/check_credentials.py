"""APIキーの疎通確認。投稿はしない（課金される書き込みを発生させない）。

使い方:
  export X_API_KEY=... X_API_SECRET=... X_ACCESS_TOKEN=... X_ACCESS_TOKEN_SECRET=...
  export ANTHROPIC_API_KEY=...
  python check_credentials.py
"""
import os
import sys

OK = "✅"
NG = "❌"


def check_x():
    names = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"]
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        print(f"{NG} X: 環境変数が未設定: {', '.join(missing)}")
        return False
    from requests_oauthlib import OAuth1Session

    session = OAuth1Session(
        os.environ["X_API_KEY"],
        client_secret=os.environ["X_API_SECRET"],
        resource_owner_key=os.environ["X_ACCESS_TOKEN"],
        resource_owner_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
    )
    resp = session.get("https://api.twitter.com/2/users/me")
    if resp.status_code == 200:
        user = resp.json()["data"]
        print(f"{OK} X: @{user['username']} として認証成功")
        return True
    print(f"{NG} X: 認証失敗 {resp.status_code}: {resp.text[:300]}")
    if resp.status_code == 403:
        print("   → アプリのUser authentication settingsで『Read and Write』を有効化した後、")
        print("     Access Token を再生成しましたか？（権限変更前のトークンはReadのみ）")
    if resp.status_code == 402 or "credits" in resp.text.lower():
        print("   → 従量課金のクレジット残高を確認してください（developer console）")
    return False


def check_anthropic():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(f"{NG} Anthropic: ANTHROPIC_API_KEY が未設定")
        return False
    from anthropic import Anthropic

    try:
        Anthropic().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{"role": "user", "content": "ping"}],
        )
        print(f"{OK} Anthropic: 認証成功")
        return True
    except Exception as e:
        print(f"{NG} Anthropic: {e}")
        return False


if __name__ == "__main__":
    results = [check_x(), check_anthropic()]
    if all(results):
        print(f"\n{OK} 全て疎通OK。DRY RUNで pipeline.py を実行できます:")
        print("   cd automation && python pipeline.py")
        sys.exit(0)
    sys.exit(1)
