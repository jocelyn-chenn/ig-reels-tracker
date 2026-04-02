# updater.py
# 負責每天回抓已收錄業配 Reels 的最新互動數
# 把每天的數據存成快照，這樣之後可以看成長曲線

import time
from datetime import date
from curl_cffi import requests
from config import IG_APP_ID, IG_DOC_ID, SCRAPER_DELAY_MIN, SCRAPER_DELAY_MAX
from database import get_all_tracked_reels, save_daily_stat
import random

BASE_HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "x-ig-app-id": IG_APP_ID,
    "accept-language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
}

def get_reel_stats(shortcode: str) -> dict | None:
    """
    抓取單篇 Reels 目前的互動數
    回傳：{"likes": 123, "comments": 45, "views": 6789}
    """
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

        likes    = node.get("edge_media_preview_like", {}).get("count", 0)
        comments = node.get("edge_media_to_comment", {}).get("count", 0)
        views    = node.get("video_view_count", 0)

        return {"likes": likes, "comments": comments, "views": views}

    except Exception as e:
        print(f"    抓取互動數時發生錯誤：{e}")
        return None


def run_daily_update():
    """
    對所有已收錄的業配 Reels 執行每日互動數更新
    這個函數每天被 GitHub Actions 呼叫一次
    """
    today = str(date.today())   # 格式：2024-04-02
    reels = get_all_tracked_reels()

    if not reels:
        print("資料庫裡還沒有收錄任何 Reels，跳過更新")
        return

    print(f"開始每日更新，今天日期：{today}")
    print(f"共需更新 {len(reels)} 篇 Reels")

    success = 0
    failed  = 0

    for shortcode, url in reels:
        print(f"  更新：{shortcode}")
        stats = get_reel_stats(shortcode)

        if stats:
            save_daily_stat(
                shortcode = shortcode,
                date      = today,
                likes     = stats["likes"],
                comments  = stats["comments"],
                views     = stats["views"],
            )
            print(f"    按讚：{stats['likes']}  留言：{stats['comments']}  觀看：{stats['views']}")
            success += 1
        else:
            failed += 1

        # 隨機延遲，避免被封
        delay = random.uniform(SCRAPER_DELAY_MIN, SCRAPER_DELAY_MAX)
        time.sleep(delay)

    print(f"\n每日更新完成：成功 {success} 篇，失敗 {failed} 篇")