# updater.py
import time
import random
from datetime import datetime
from curl_cffi import requests
from config import IG_APP_ID, IG_SESSION_ID, IG_DOC_ID, SCRAPER_DELAY_MIN, SCRAPER_DELAY_MAX
from database import get_all_tracked_reels, save_daily_stat

BASE_HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "x-ig-app-id": IG_APP_ID,
    "cookie": f"sessionid={IG_SESSION_ID}",
}

def get_reel_stats(shortcode: str) -> dict:
    """
    用 GraphQL 抓觀看數、按讚數、留言數
    """
    url = (
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
            url, headers=headers, impersonate="chrome120", timeout=15
        )
        if response.status_code == 200:
            node = response.json().get("data", {}).get("xdt_shortcode_media", {})
            if node:
                return {
                    "views":    node.get("video_view_count") or 0,
                    "plays":    node.get("video_play_count") or 0,
                    "likes":    node.get("edge_media_preview_like", {}).get("count") or 0,
                    "comments": node.get("edge_media_to_comment", {}).get("count") or 0,
                }
        print(f"    GraphQL 回傳異常：HTTP {response.status_code}")
        return {"views": 0, "plays": 0, "likes": 0, "comments": 0}
    except Exception as e:
        print(f"    抓互動數失敗：{e}")
        return {"views": 0, "plays": 0, "likes": 0, "comments": 0}

def should_update(first_seen_str: str, now: datetime) -> bool:
    """根據收錄時間決定這篇要不要更新"""
    first_seen = datetime.strptime(first_seen_str, "%Y-%m-%d %H:%M:%S")
    hours_old = (now - first_seen).total_seconds() / 3600

    if hours_old <= 6:
        return True
    elif hours_old <= 24:
        return now.hour % 2 == 0 and now.minute < 30
    elif hours_old <= 168:
        return now.hour == 2 and now.minute < 30
    else:
        return False

def run_daily_update():
    now = datetime.now()
    recorded_at = now.strftime("%Y-%m-%d %H:%M")
    reels = get_all_tracked_reels()

    if not reels:
        print("資料庫裡還沒有收錄任何 Reels，跳過更新")
        return

    print(f"開始更新，時間：{recorded_at}，共 {len(reels)} 篇待檢查")

    updated = 0
    skipped = 0

    for shortcode, url, first_seen in reels:
        if not should_update(first_seen, now):
            skipped += 1
            continue

        print(f"  更新：{shortcode}")
        stats = get_reel_stats(shortcode)
        save_daily_stat(
            shortcode=shortcode,
            recorded_at=recorded_at,
            likes=stats["likes"],
            comments=stats["comments"],
            views=stats["views"],
        )
        print(f"    觀看：{stats['views']}  按讚：{stats['likes']}  留言：{stats['comments']}")
        time.sleep(random.uniform(SCRAPER_DELAY_MIN, SCRAPER_DELAY_MAX))
        updated += 1

    print(f"更新完成：更新 {updated} 篇，跳過 {skipped} 篇")