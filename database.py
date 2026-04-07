# database.py
import sqlite3
import os
from config import DB_PATH

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS influencers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            added_at    TEXT DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sponsored_reels (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT NOT NULL,
            shortcode       TEXT UNIQUE NOT NULL,
            url             TEXT NOT NULL,
            caption         TEXT,
            post_time       TEXT,
            video_duration  REAL,
            ai_reason       TEXT,
            sponsor_status  TEXT DEFAULT 'none',
            first_seen      TEXT DEFAULT (datetime('now')),
            tagged_brands   TEXT
        )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_stats (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        shortcode    TEXT NOT NULL,
        recorded_at  TEXT NOT NULL,
        likes        INTEGER DEFAULT 0,
        comments     INTEGER DEFAULT 0,
        views        INTEGER DEFAULT 0,
        plays        INTEGER DEFAULT 0,
        UNIQUE(shortcode, recorded_at)
    )
""")

    conn.commit()
    conn.close()
    print("資料庫初始化完成")

def insert_influencers():
    from config import INFLUENCERS
    conn = get_connection()
    cursor = conn.cursor()
    for username in INFLUENCERS:
        cursor.execute("""
            INSERT OR IGNORE INTO influencers (username) VALUES (?)
        """, (username,))
    conn.commit()
    conn.close()
    print(f"網紅清單已更新，共 {len(INFLUENCERS)} 位")

def get_all_influencers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM influencers")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def save_reel(data: dict):
    """
    存入一篇 Reels（無論是不是業配都存）
    sponsor_status: 'sponsored' 或 'none'
    如果已存在（相同 shortcode）就跳過
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO sponsored_reels
            (username, shortcode, url, caption, post_time,
             video_duration, ai_reason, sponsor_status, tagged_brands)
        VALUES
            (:username, :shortcode, :url, :caption, :post_time,
             :video_duration, :ai_reason, :sponsor_status, :tagged_brands)
    """, data)
    inserted = cursor.rowcount
    conn.commit()
    conn.close()
    return inserted

def save_daily_stat(shortcode: str, recorded_at: str, likes: int, comments: int, views: int, plays: int = 0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO daily_stats
            (shortcode, recorded_at, likes, comments, views, plays)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (shortcode, recorded_at, likes, comments, views, plays))
    conn.commit()
    conn.close()

def get_all_tracked_reels():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT shortcode, url, first_seen FROM sponsored_reels")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_stats_summary():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM influencers")
    n_influencers = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM sponsored_reels")
    n_reels = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM sponsored_reels WHERE sponsor_status='sponsored'")
    n_sponsored = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM daily_stats")
    n_stats = cursor.fetchone()[0]
    conn.close()
    print(f"追蹤網紅：{n_influencers} 位")
    print(f"收錄 Reels 總數：{n_reels} 篇（其中業配：{n_sponsored} 篇）")
    print(f"每日數據快照：{n_stats} 筆")