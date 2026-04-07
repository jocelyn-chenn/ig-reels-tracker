# config.py
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

IG_SESSION_ID = os.getenv("IG_SESSION_ID")

# 每次掃主頁只看最新幾篇（3篇就夠抓到新發的）
REELS_PER_SCAN = 3

# ============================================================
# 從 CSV 讀取 KOL 名單
# ============================================================
def load_influencers_from_csv(csv_path="KOL_sheet.csv") -> list[str]:
    try:
        df = pd.read_csv(csv_path)
        # 直接取 ID 欄，裡面就是 IG username
        usernames = df["ID"].dropna().tolist()
        # 去除重複
        usernames = list(dict.fromkeys(usernames))
        print(f"從 CSV 載入 {len(usernames)} 位 KOL")
        return usernames
    except Exception as e:
        print(f"讀取 CSV 失敗：{e}")
        return []

INFLUENCERS = load_influencers_from_csv()

# ============================================================
# API Keys
# ============================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ============================================================
# 爬蟲設定
# ============================================================
SCRAPER_DELAY_MIN = 3
SCRAPER_DELAY_MAX = 7

IG_DOC_ID = "8845758582119845"
IG_APP_ID  = "936619743392459"

# ============================================================
# 業配關鍵字（給 Gemini 參考用）
# ============================================================
SPONSORED_KEYWORDS = [
    "合作", "業配", "贊助", "sponsored", "collaboration",
    "gifted", "ad", "廣告", "折扣碼", "優惠碼",
    "discount code", "promo code", "感謝品牌",
]

# ============================================================
# 資料庫設定
# ============================================================
DB_PATH = "data/tracker.db"

import random

PROXIES = [
    ("31.59.20.176", "6754", "ngbhahmk", "p8vgbsa6ljjn"),
    ("23.95.150.145", "6114", "ngbhahmk", "p8vgbsa6ljjn"),
    ("198.23.239.134", "6540", "ngbhahmk", "p8vgbsa6ljjn"),
    ("45.38.107.97", "6014", "ngbhahmk", "p8vgbsa6ljjn"),
    ("107.172.163.27", "6543", "ngbhahmk", "p8vgbsa6ljjn"),
    ("198.105.121.200", "6462", "ngbhahmk", "p8vgbsa6ljjn"),
    ("216.10.27.159", "6837", "ngbhahmk", "p8vgbsa6ljjn"),
    ("142.111.67.146", "5611", "ngbhahmk", "p8vgbsa6ljjn"),
    ("191.96.254.138", "6185", "ngbhahmk", "p8vgbsa6ljjn"),
    ("31.58.9.4", "6077", "ngbhahmk", "p8vgbsa6ljjn"),
]

def get_random_proxy() -> dict:
    host, port, user, passwd = random.choice(PROXIES)
    proxy_url = f"http://{user}:{passwd}@{host}:{port}"
    return {"http": proxy_url, "https": proxy_url}