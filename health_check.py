# health_check.py
from curl_cffi import requests
from config import IG_APP_ID, IG_SESSION_ID

TEST_USERNAME = "da_chien_huang"

def check_health() -> bool:
    print("  檢查 IG REST API...")
    rest_ok = _check_rest_api()
    if rest_ok:
        print("  健康檢查通過")
    else:
        print("  警告：REST API 異常，可能 IP 被封")
    return rest_ok

def _check_rest_api() -> bool:
    url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={TEST_USERNAME}"
    headers = {
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "x-ig-app-id": IG_APP_ID,
        "cookie": f"sessionid={IG_SESSION_ID}",
    }
    try:
        response = requests.get(
            url, headers=headers, impersonate="chrome120", timeout=15
        )
        if response.status_code == 200:
            user = response.json().get("data", {}).get("user", {})
            if user.get("id"):
                print(f"    REST API 正常")
                return True
        print(f"    REST API 異常：HTTP {response.status_code}")
        return False
    except Exception as e:
        print(f"    REST API 連線失敗：{e}")
        return False