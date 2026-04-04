# main.py
import time
import random
from datetime import datetime

from config import SCRAPER_DELAY_MIN, SCRAPER_DELAY_MAX
from database import (
    init_db,
    insert_influencers,
    get_all_influencers,
    save_reel,
    get_stats_summary,
)
from scraper import scrape_influencer
from analyzer import analyze_reel
from updater import run_daily_update
from health_check import check_health

def run():
    start_time = datetime.now()
    print(f"========================================")
    print(f"開始執行：{start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"========================================")

    print("\n[Step 1] 初始化資料庫")
    init_db()
    insert_influencers()

    print("\n[Step 2] 健康檢查")
    api_ok = check_health()
    if not api_ok:
        print("IG API 異常，繼續嘗試...")

    print("\n[Step 3] 開始抓取網紅 Reels")
    influencers = get_all_influencers()
    print(f"共 {len(influencers)} 位網紅需要處理")

    total_found     = 0
    total_sponsored = 0
    total_saved     = 0

    for username in influencers:
        print(f"\n{'─' * 40}")
        reels = scrape_influencer(username)
        total_found += len(reels)

        for reel in reels:
            # 每篇都送去 AI 分析
            result = analyze_reel(reel)

            # 根據 AI 結果設定 sponsor_status
            sponsor_status = "sponsored" if result["is_sponsored"] else "none"
            if result["is_sponsored"]:
                total_sponsored += 1

            # 每篇都存進資料庫
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
                total_saved += 1
                label = "業配" if result["is_sponsored"] else "一般"
                print(f"  新收錄（{label}）：{result['shortcode']}")
            else:
                print(f"  已存在，跳過：{result['shortcode']}")

            time.sleep(random.uniform(SCRAPER_DELAY_MIN, SCRAPER_DELAY_MAX))

        time.sleep(random.uniform(5, 10))

    print(f"\n{'─' * 40}")
    print("\n[Step 4] 更新每日互動數")
    run_daily_update()

    end_time = datetime.now()
    duration = (end_time - start_time).seconds

    print(f"\n{'=' * 40}")
    print(f"執行完成：{end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"耗時：{duration} 秒")
    print(f"掃描影片總數：{total_found} 篇")
    print(f"判斷為業配：{total_sponsored} 篇")
    print(f"新收錄入庫：{total_saved} 篇")
    print(f"{'─' * 40}")
    print("\n目前資料庫狀況：")
    get_stats_summary()
    print(f"{'=' * 40}\n")

if __name__ == "__main__":
    run()