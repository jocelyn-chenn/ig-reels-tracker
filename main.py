# main.py
# 整個專案的主程式，每天被 GitHub Actions 自動執行
# 流程：掃主頁 → 抓詳細資料 → AI 判斷 → 存資料庫 → 更新互動數

import time
import random
from datetime import datetime

from config import SCRAPER_DELAY_MIN, SCRAPER_DELAY_MAX
from database import (
    init_db,
    insert_influencers,
    get_all_influencers,
    save_sponsored_reel,
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

    # Step 1：初始化資料庫（第一次執行時建立資料表）
    print("\n[Step 1] 初始化資料庫")
    init_db()
    insert_influencers()

    # Step 2：健康檢查（確認 IG API 是否正常）
    print("\n[Step 2] 健康檢查")
    api_ok = check_health()
    if not api_ok:
        print("IG API 異常，今天的抓取可能會失敗，繼續嘗試...")

    # Step 3：對每個網紅執行抓取 + AI 分析
    print("\n[Step 3] 開始抓取網紅 Reels")
    influencers = get_all_influencers()
    print(f"共 {len(influencers)} 位網紅需要處理")

    total_found     = 0   # 總共找到幾篇影片
    total_sponsored = 0   # 判斷是業配的有幾篇
    total_saved     = 0   # 新收錄進資料庫的有幾篇

    for username in influencers:
        print(f"\n{'─' * 40}")

        # 抓這個網紅的所有最新 Reels
        reels = scrape_influencer(username)
        total_found += len(reels)

        for reel in reels:
            # 用 Gemini 判斷是不是業配
            result = analyze_reel(reel)

            if result["is_sponsored"]:
                total_sponsored += 1

                # 存進資料庫
                inserted = save_sponsored_reel({
                    "username":       result["username"],
                    "shortcode":      result["shortcode"],
                    "url":            result["url"],
                    "caption":        result["caption"],
                    "post_time":      result["post_time"],
                    "video_duration": result["video_duration"],
                    "ai_reason":      result["ai_reason"],
                    "tagged_brands":  result["tagged_brands"],
                })

                if inserted:
                    total_saved += 1
                    print(f"  已收錄：{result['url']}")
                else:
                    print(f"  已存在，跳過：{result['shortcode']}")

            # 每篇之間稍微等一下
            time.sleep(random.uniform(SCRAPER_DELAY_MIN, SCRAPER_DELAY_MAX))

        # 每個網紅之間多等一點
        time.sleep(random.uniform(5, 10))

    # Step 4：更新已收錄 Reels 的每日互動數
    print(f"\n{'─' * 40}")
    print("\n[Step 4] 更新每日互動數")
    run_daily_update()

    # Step 5：印出今天的執行摘要
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