# update.py
# 只負責更新資料庫中所有 Reels 的最新互動數
from datetime import datetime, timezone, timedelta
from database import init_db, get_all_tracked_reels, save_daily_stat
from updater import get_reel_stats
import time, random
from config import SCRAPER_DELAY_MIN, SCRAPER_DELAY_MAX


# 改成台灣時間 UTC+8
tw_tz = timezone(timedelta(hours=8))
now = datetime.now(tw_tz)
recorded_at = now.strftime("%Y-%m-%d %H:%M")

def run():
    start = datetime.now()
    recorded_at = start.strftime("%Y-%m-%d %H:%M")
    print(f"=== Update 開始：{recorded_at} ===")

    init_db()
    reels = get_all_tracked_reels()

    if not reels:
        print("資料庫還沒有 Reels，跳過")
        return

    print(f"共 {len(reels)} 篇需要更新")

    for shortcode, url, first_seen in reels:
        print(f"  更新：{shortcode}")
        stats = get_reel_stats(shortcode)
        save_daily_stat(
            shortcode=shortcode,
            recorded_at=recorded_at,
            likes=stats["likes"],
            comments=stats["comments"],
            views=stats["views"],
            plays=stats["plays"],
        )
        print(f"    觀看：{stats['views']}  按讚：{stats['likes']}  留言：{stats['comments']}")
        time.sleep(random.uniform(SCRAPER_DELAY_MIN, SCRAPER_DELAY_MAX))

    end = datetime.now()
    print(f"=== Update 完成：耗時 {(end-start).seconds} 秒 ===")

if __name__ == "__main__":
    run()

from export_json import export
export()