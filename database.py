# database.py
# 負責建立資料庫、建立資料表、以及所有存取資料的函數

import sqlite3
import os
from config import DB_PATH

def get_connection():
    """取得資料庫連線"""
    # 確保 data/ 資料夾存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    """
    初始化資料庫：建立三張資料表
    這個函數只需要執行一次，之後資料表就會一直存在
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 資料表一：influencers（你追蹤的網紅清單）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS influencers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,  -- IG 帳號名稱
            added_at    TEXT DEFAULT (datetime('now'))
        )
    """)

    # 資料表二：sponsored_reels（收錄的業配 Reels）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sponsored_reels (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT NOT NULL,        -- 哪個網紅
            shortcode       TEXT UNIQUE NOT NULL, -- Reels 的唯一識別碼
            url             TEXT NOT NULL,        -- 完整連結
            caption         TEXT,                 -- 文案內容
            post_time       TEXT,                 -- 發文時間
            video_duration  REAL,                 -- 影片長度（秒）
            ai_reason       TEXT,                 -- Gemini 判斷理由
            first_seen      TEXT DEFAULT (datetime('now')), -- 第一次發現的時間
            tagged_brands   TEXT                  -- 被 tag 的品牌帳號
        )
    """)

    # 資料表三：daily_stats（每日互動數快照）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_stats (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            shortcode   TEXT NOT NULL,   -- 對應哪篇 Reels
            date        TEXT NOT NULL,   -- 記錄日期 (YYYY-MM-DD)
            likes       INTEGER,         -- 按讚數
            comments    INTEGER,         -- 留言數
            views       INTEGER,         -- 觀看數
            UNIQUE(shortcode, date)      -- 同一篇同一天只記錄一次
        )
    """)

    conn.commit()
    conn.close()
    print("資料庫初始化完成")

def insert_influencers():
    """把 config.py 裡的網紅清單寫進資料庫"""
    from config import INFLUENCERS
    conn = get_connection()
    cursor = conn.cursor()
    for username in INFLUENCERS:
        # INSERT OR IGNORE：如果已經存在就跳過，不會重複新增
        cursor.execute("""
            INSERT OR IGNORE INTO influencers (username) VALUES (?)
        """, (username,))
    conn.commit()
    conn.close()
    print(f"網紅清單已更新，共 {len(INFLUENCERS)} 位")

def get_all_influencers():
    """取得所有要追蹤的網紅帳號"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM influencers")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def save_sponsored_reel(data: dict):
    """
    把一篇業配 Reels 存進資料庫
    如果已經存在（相同 shortcode）就跳過
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO sponsored_reels
            (username, shortcode, url, caption, post_time,
             video_duration, ai_reason, tagged_brands)
        VALUES
            (:username, :shortcode, :url, :caption, :post_time,
             :video_duration, :ai_reason, :tagged_brands)
    """, data)
    inserted = cursor.rowcount  # 1 表示新增成功，0 表示已存在跳過
    conn.commit()
    conn.close()
    return inserted

def save_daily_stat(shortcode: str, date: str, likes: int, comments: int, views: int):
    """儲存某篇 Reels 某天的互動數"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO daily_stats
            (shortcode, date, likes, comments, views)
        VALUES (?, ?, ?, ?, ?)
    """, (shortcode, date, likes, comments, views))
    conn.commit()
    conn.close()

def get_all_tracked_reels():
    """取得所有已收錄的業配 Reels（給 updater.py 用）"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT shortcode, url FROM sponsored_reels")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_stats_summary():
    """印出目前資料庫的收錄狀況"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM influencers")
    n_influencers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sponsored_reels")
    n_reels = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM daily_stats")
    n_stats = cursor.fetchone()[0]

    conn.close()
    print(f"目前追蹤網紅：{n_influencers} 位")
    print(f"已收錄業配 Reels：{n_reels} 篇")
    print(f"每日數據快照：{n_stats} 筆")