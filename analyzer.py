# analyzer.py
# 負責用 Gemini AI 判斷一篇 Reels 是不是業配文

from google import genai
from config import GEMINI_API_KEY, SPONSORED_KEYWORDS

# 初始化 Gemini 客戶端
client = genai.Client(api_key=GEMINI_API_KEY)

def is_sponsored(caption: str, tagged_brands: str) -> tuple[bool, str]:
    """
    判斷一篇 Reels 是不是業配文

    輸入：
        caption       → 文案內容
        tagged_brands → 被 tag 的帳號（例如 @brandA @brandB）

    回傳：
        (True/False, "AI 的判斷理由")
    """

    # 如果文案和 tag 都是空的，直接跳過不問 Gemini
    if not caption.strip() and not tagged_brands.strip():
        return False, "文案為空，無法判斷"

    # 把關鍵字清單整理成文字給 Gemini 參考
    keywords_str = "、".join(SPONSORED_KEYWORDS)

    # 組合給 Gemini 的 Prompt
    prompt = f"""
你是一個專門分析台灣 Instagram 網紅業配文的助理。

請判斷以下這篇 Instagram Reels 的文案是否為業配文（商業合作/贊助內容）。

【文案內容】
{caption if caption else "（無文案）"}

【被 tag 的帳號】
{tagged_brands if tagged_brands else "（無 tag）"}

【判斷標準】
業配文通常包含以下特徵之一：
- 提到品牌名稱、產品名稱
- 有折扣碼、優惠碼、promo code
- 有 tag 品牌帳號（@品牌）
- 使用「合作」、「業配」、「贊助」、「gifted」、「sponsored」、「ad」等字
- 感謝某個品牌或公司
- 叫粉絲去連結購買或領取優惠

參考關鍵字：{keywords_str}

【請回答】
請只回答以下格式，不要多說其他話：

判斷：是業配 或 不是業配
理由：（一句話說明原因）
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        result_text = response.text.strip()

        # 解析 Gemini 的回答
        is_ad = "是業配" in result_text and "不是業配" not in result_text

        # 提取理由那一行
        reason = ""
        for line in result_text.split("\n"):
            if line.startswith("理由："):
                reason = line.replace("理由：", "").strip()
                break

        if not reason:
            reason = result_text

        return is_ad, reason

    except Exception as e:
        print(f"  Gemini 判斷時發生錯誤：{e}")
        return False, f"判斷失敗：{e}"


def analyze_reel(reel_data: dict) -> dict:
    """
    對一篇 Reels 執行業配判斷，並把結果填回 reel_data 裡

    輸入：scraper.py 回傳的 reel_data dict
    回傳：加上 is_sponsored 和 ai_reason 欄位的 dict
    """
    caption = reel_data.get("caption", "")
    tagged_brands = reel_data.get("tagged_brands", "")

    print(f"  Gemini 分析中：{reel_data['shortcode']}")

    is_ad, reason = is_sponsored(caption, tagged_brands)

    reel_data["ai_reason"] = reason
    reel_data["is_sponsored"] = is_ad

    status = "業配" if is_ad else "非業配"
    print(f"  判斷結果：{status} ── {reason}")

    return reel_data