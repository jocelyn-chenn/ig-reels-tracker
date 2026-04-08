# export_json.py
# 把資料庫內容匯出成 JSON 給 GitHub Pages 用

import sqlite3
import json
import os
from database import get_connection

def export():
    conn = get_connection()
    cursor = conn.cursor()

    # 匯出 sponsored_reels
    cursor.execute("""
        SELECT username, shortcode, url, post_time, 
               sponsor_status, ai_reason, tagged_brands, first_seen
        FROM sponsored_reels
        ORDER BY first_seen DESC
    """)
    cols = [d[0] for d in cursor.description]
    reels = [dict(zip(cols, row)) for row in cursor.fetchall()]

    # 匯出 daily_stats（每篇最新一筆）
    cursor.execute("""
        SELECT d.shortcode, s.username, d.recorded_at, 
               d.views, d.plays, d.likes, d.comments
        FROM daily_stats d
        JOIN sponsored_reels s ON d.shortcode = s.shortcode
        ORDER BY d.recorded_at DESC
    """)
    cols = [d[0] for d in cursor.description]
    stats = [dict(zip(cols, row)) for row in cursor.fetchall()]

    # 統計摘要
    cursor.execute("SELECT COUNT(*) FROM influencers")
    n_influencers = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM sponsored_reels")
    n_reels = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM sponsored_reels WHERE sponsor_status='sponsored'")
    n_sponsored = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM daily_stats")
    n_stats = cursor.fetchone()[0]

    conn.close()

    from datetime import datetime, timezone, timedelta
    tw_tz = timezone(timedelta(hours=8))
    now = datetime.now(tw_tz).strftime("%Y-%m-%d %H:%M")

    data = {
        "updated_at": now,
        "summary": {
            "n_influencers": n_influencers,
            "n_reels": n_reels,
            "n_sponsored": n_sponsored,
            "n_stats": n_stats,
        },
        "reels": reels,
        "stats": stats,
    }

    os.makedirs("docs", exist_ok=True)
    with open("docs/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 匯出完成：docs/data.json")

if __name__ == "__main__":
    export()