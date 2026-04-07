# scraper.py
import time
import random
from datetime import datetime, timedelta
from curl_cffi import requests
from config import IG_APP_ID, IG_SESSION_ID, SCRAPER_DELAY_MIN, SCRAPER_DELAY_MAX, get_random_proxy

BASE_HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "x-ig-app-id": IG_APP_ID,
    "accept-language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "cookie": f"sessionid={IG_SESSION_ID}",
}

def _random_delay():
    delay = random.uniform(SCRAPER_DELAY_MIN, SCRAPER_DELAY_MAX)
    print(f"  等待 {delay:.1f} 秒...")
    time.sleep(delay)

def get_recent_reels(username: str) -> list[dict]:
    print(f"正在掃描 @{username} 的主頁...")

    cutoff = datetime.now() - timedelta(minutes=70)
    cutoff_ts = cutoff.timestamp()

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
            timeout=15,
            proxies=get_random_proxy(),
        )

        if response.status_code != 200:
            print(f"  錯誤：HTTP {response.status_code}")
            return []

        data = response.json()
        edges = (
            data.get("data", {})
                .get("user", {})
                .get("edge_owner_to_timeline_media", {})
                .get("edges", [])
        )

        reels = []
        for edge in edges:
            node = edge.get("node", {})
            if not node.get("is_video"):
                continue
            shortcode = node.get("shortcode")
            if not shortcode:
                continue

            timestamp = node.get("taken_at_timestamp", 0)

            if timestamp < cutoff_ts:
                continue

            caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
            caption = caption_edges[0]["node"]["text"] if caption_edges else ""

            tagged = node.get("edge_media_to_tagged_user", {}).get("edges", [])
            tagged_brands = " ".join([
                f"@{e['node']['user']['username']}"
                for e in tagged
            ])

            post_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            comments = node.get("edge_media_to_comment", {}).get("count", 0)

            reels.append({
                "username": username,
                "shortcode": shortcode,
                "url": f"https://www.instagram.com/reels/{shortcode}/",
                "caption": caption,
                "post_time": post_time,
                "video_duration": node.get("video_duration", 0),
                "tagged_brands": tagged_brands,
                "comments": comments,
                "ai_reason": "",
            })

        print(f"  找到 {len(reels)} 篇 70 分鐘內的新貼文")
        return reels

    except Exception as e:
        print(f"  抓取 @{username} 主頁時發生錯誤：{e}")
        return []

def scrape_influencer(username: str) -> list[dict]:
    print(f"\n開始抓取 @{username}")
    reels = get_recent_reels(username)
    _random_delay()
    print(f"@{username} 完成，共抓到 {len(reels)} 篇新貼文")
    return reels