# scraper.py
# 負責從 IG 抓取資料
# 分兩個函數：
#   1. get_recent_reels()  → 掃網紅主頁，取得最新 Reels 清單
#   2. get_reel_detail()   → 抓單篇 Reels 的詳細資料

import time
import random
import re
from curl_cffi import requests
from config import (
    IG_APP_ID, IG_DOC_ID,
    SCRAPER_DELAY_MIN, SCRAPER_DELAY_MAX
)

# ============================================================
# 共用的 Headers（模擬真實 Chrome 瀏覽器）
# ============================================================
BASE_HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "x-ig-app-id": IG_APP_ID,
    "accept-language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
}

def _random_delay():
    """隨機等待幾秒，避免被 IG 封鎖"""
    delay = random.uniform(SCRAPER_DELAY_MIN, SCRAPER_DELAY_MAX)
    print(f"  等待 {delay:.1f} 秒...")
    time.sleep(delay)

def get_recent_reels(username: str) -> list[dict]:
    """
    掃描某個網紅的 IG 主頁，回傳最近幾篇 Reels 的基本資料
    使用 REST API，不需要 doc_id，比較穩定

    回傳格式：
    [
        {"shortcode": "ABC123", "url": "https://..."},
        ...
    ]
    """
    print(f"正在掃描 @{username} 的主頁...")

    url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
    headers = {
        **BASE_HEADERS,
        "referer": f"https://www.instagram.com/{username}/",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            impersonate="chrome120",
            timeout=15
        )

        if response.status_code != 200:
            print(f"  錯誤：HTTP {response.status_code}")
            return []

        data = response.json()

        # 從回傳資料裡找 Reels 貼文
        edges = (
            data.get("data", {})
                .get("user", {})
                .get("edge_owner_to_timeline_media", {})
                .get("edges", [])
        )

        reels = []
        for edge in edges:
            node = edge.get("node", {})
            # 只收錄影片類型（Reels 是影片）
            if node.get("__typename") != "GraphVideo" and not node.get("is_video"):
                continue
            shortcode = node.get("shortcode")
            if not shortcode:
                continue
            reels.append({
                "shortcode": shortcode,
                "url": f"https://www.instagram.com/reels/{shortcode}/",
            })

        print(f"  找到 {len(reels)} 篇影片貼文")
        return reels

    except Exception as e:
        print(f"  抓取 @{username} 主頁時發生錯誤：{e}")
        return []

def get_reel_detail(shortcode: str, username: str) -> dict | None:
    """
    抓取單篇 Reels 的詳細資料（文案、時間、長度、tagged 帳號）
    使用 GraphQL API + doc_id

    回傳格式：
    {
        "username": "...",
        "shortcode": "...",
        "url": "...",
        "caption": "...",
        "post_time": "2024-01-01 12:00:00",
        "video_duration": 30.5,
        "tagged_brands": "@brand1 @brand2",
        "ai_reason": ""   ← 先空著，analyzer.py 會填進來
    }
    """
    print(f"  正在抓取 Reels 詳細資料：{shortcode}")

    api_url = (
        f"https://www.instagram.com/graphql/query/"
        f"?doc_id={IG_DOC_ID}"
        f'&variables={{"shortcode":"{shortcode}"}}'
    )
    headers = {
        **BASE_HEADERS,
        "referer": f"https://www.instagram.com/reels/{shortcode}/",
    }

    try:
        response = requests.get(
            api_url,
            headers=headers,
            impersonate="chrome120",
            timeout=15
        )

        if response.status_code != 200:
            print(f"    錯誤：HTTP {response.status_code}")
            return None

        data = response.json()
        node = data.get("data", {}).get("xdt_shortcode_media")

        if not node:
            print(f"    找不到資料，doc_id 可能已過期")
            return None

        # 抓文案
        edges = node.get("edge_media_to_caption", {}).get("edges", [])
        caption = edges[0]["node"]["text"] if edges else ""

        # 抓發文時間
        timestamp = node.get("taken_at_timestamp", 0)
        post_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

        # 抓影片長度
        video_duration = node.get("video_duration", 0)

        # 抓被 tag 的帳號（品牌方通常會被 tag）
        tagged_users = node.get("edge_media_to_tagged_user", {}).get("edges", [])
        tagged_brands = " ".join([
            f"@{e['node']['user']['username']}"
            for e in tagged_users
        ])

        return {
            "username": username,
            "shortcode": shortcode,
            "url": f"https://www.instagram.com/reels/{shortcode}/",
            "caption": caption,
            "post_time": post_time,
            "video_duration": video_duration,
            "tagged_brands": tagged_brands,
            "ai_reason": "",   # 等 analyzer.py 填入
        }

    except Exception as e:
        print(f"    抓取詳細資料時發生錯誤：{e}")
        return None

def scrape_influencer(username: str) -> list[dict]:
    """
    對某個網紅執行完整的抓取流程：
    1. 掃主頁取得 Reels 清單
    2. 逐一抓每篇的詳細資料
    3. 回傳所有詳細資料的清單
    """
    print(f"\n開始抓取 @{username}")

    # 第一步：掃主頁
    reels = get_recent_reels(username)
    if not reels:
        return []

    _random_delay()

    # 第二步：逐一抓詳細資料
    details = []
    for reel in reels:
        detail = get_reel_detail(reel["shortcode"], username)
        if detail:
            details.append(detail)
        _random_delay()

    print(f"@{username} 完成，共抓到 {len(details)} 篇資料")
    return details