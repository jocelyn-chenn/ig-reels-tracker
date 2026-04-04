# config.py
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 從 CSV 讀取 KOL 名單
# ============================================================
def load_influencers_from_csv(csv_path="KOL_sheet.csv") -> list[str]:
    try:
        df = pd.read_csv(csv_path)
        usernames = []
        for val in df["LINK"].dropna():
            val = str(val).strip()

            if "instagram.com" in val:
                # 移除網址參數（? 後面的部分）
                val = val.split("?")[0]
                # 移除結尾斜線
                val = val.rstrip("/")
                # 取路徑各段
                parts = val.split("/")
                # 過濾掉空字串
                parts = [p for p in parts if p]

                # 跳過格式是 /reels/shortcode/ 的連結（這是單篇貼文，不是帳號）
                if "reels" in parts:
                    idx = parts.index("reels")
                    # reels 前面那個才是帳號（如果有的話）
                    if idx > 0 and parts[idx-1] not in ("www.instagram.com", "instagram.com"):
                        username = parts[idx-1]
                    else:
                        # 純 /reels/shortcode 格式，跳過
                        continue
                else:
                    # 一般帳號連結，取最後一段
                    username = parts[-1]
            else:
                username = val.strip()

            # 基本驗證：跳過明顯不是帳號的字串
            if not username or "?" in username or "=" in username or len(username) > 30:
                continue

            usernames.append(username)

        # 去除重複，但保留順序
        seen = set()
        unique = []
        for u in usernames:
            if u not in seen:
                seen.add(u)
                unique.append(u)

        print(f"從 CSV 載入 {len(unique)} 位 KOL")
        return unique

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