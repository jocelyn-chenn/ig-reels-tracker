# scan.py
# 只負責掃新貼文、AI 判斷、存資料庫
from datetime import datetime
from database import init_db, insert_influencers, get_all_influencers, save_reel, get_stats_summary
from scraper import scrape_influencer
from analyzer import analyze_reel
from health_check import check_health
import time, random
from config import SCRAPER_DELAY_MIN, SCRAPER_DELAY_MAX

def run():
    start = datetime.now()
    print(f"=== Scan 開始：{start.strftime('%Y-%m-%d %H:%M:%S')} ===")

    init_db()
    insert_influencers()

    if not check_health():
        print("健康檢查失敗，中止執行")
        return

    influencers = get_all_influencers()
    print(f"共 {len(influencers)} 位 KOL")

    total_new = 0

    for username in influencers:
        reels = scrape_influencer(username)
        for reel in reels:
            result = analyze_reel(reel)
            sponsor_status = "sponsored" if result["is_sponsored"] else "none"
            inserted = save_reel({
                "username":       result["username"],
                "shortcode":      result["shortcode"],
                "url":            result["url"],
                "caption":        result["caption"],
                "post_time":      result["post_time"],
                "video_duration": result["video_duration"],
                "ai_reason":      result["ai_reason"],
                "sponsor_status": sponsor_status,
                "tagged_brands":  result["tagged_brands"],
            })
            if inserted:
                total_new += 1
                label = "業配" if result["is_sponsored"] else "一般"
                print(f"  新收錄（{label}）：{result['shortcode']}")
            time.sleep(random.uniform(SCRAPER_DELAY_MIN, SCRAPER_DELAY_MAX))
        time.sleep(random.uniform(5, 10))

    end = datetime.now()
    print(f"=== Scan 完成：耗時 {(end-start).seconds} 秒，新收錄 {total_new} 篇 ===")
    get_stats_summary()

if __name__ == "__main__":
    run()