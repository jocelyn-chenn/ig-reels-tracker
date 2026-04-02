# health_check.py
# 在每天執行前，先確認 IG API 是否正常
# 如果 doc_id 過期或 IP 被封，這裡會偵測到並印出警告

from curl_cffi import requests
from config import IG_APP_ID, IG_DOC_ID

# 用一個固定的公開帳號做測試（IG 官方帳號，一定存在）
TEST_USERNAME = "instagram"

def check_health() -> bool:
    """
    回傳 True 表示 API 正常
    回傳 False 表示有問題，需要注意
    """
    print("  檢查 IG REST API...")
    rest_ok = _check_rest_api()

    print("  檢查 IG GraphQL API（doc_id）...")
    graphql_ok = _check_graphql_api()

    if rest_ok and graphql_ok:
        print("  健康檢查通過")
        return True
    else:
        if not rest_ok:
            print("  警告：REST API 異常，可能 IP 被封或帳號需要登入")
        if not graphql_ok:
            print("  警告：GraphQL API 異常，doc_id 可能已過期")
            print("  請參考說明文件更新 config.py 裡的 IG_DOC_ID")
        return False

def _check_rest_api() -> bool:
    """測試能不能抓到 IG 使用者資料"""
    url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={TEST_USERNAME}"
    headers = {
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "x-ig-app-id": IG_APP_ID,
    }
    try:
        response = requests.get(
            url,
            headers=headers,
            impersonate="chrome120",
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            user = data.get("data", {}).get("user", {})
            if user.get("id"):
                print(f"    REST API 正常（測試帳號：@{TEST_USERNAME}）")
                return True
        print(f"    REST API 回傳異常：HTTP {response.status_code}")
        return False
    except Exception as e:
        print(f"    REST API 連線失敗：{e}")
        return False

def _check_graphql_api() -> bool:
    """測試 doc_id 是否還有效"""
    # 用 instagram 帳號的一篇固定貼文做測試
    TEST_SHORTCODE = "C8EECPup-ED"
    api_url = (
        f"https://www.instagram.com/graphql/query/"
        f"?doc_id={IG_DOC_ID}"
        f'&variables={{"shortcode":"{TEST_SHORTCODE}"}}'
    )
    headers = {
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "x-ig-app-id": IG_APP_ID,
        "referer": f"https://www.instagram.com/reels/{TEST_SHORTCODE}/",
    }
    try:
        response = requests.get(
            api_url,
            headers=headers,
            impersonate="chrome120",
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            node = data.get("data", {}).get("xdt_shortcode_media")
            if node:
                print(f"    GraphQL API 正常（doc_id 有效）")
                return True
        print(f"    GraphQL API 回傳異常：HTTP {response.status_code}")
        return False
    except Exception as e:
        print(f"    GraphQL API 連線失敗：{e}")
        return False