# notifier.py
import smtplib
import urllib.request
import urllib.parse
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import GMAIL_USER, GMAIL_APP_PASSWORD, NOTIFY_EMAIL
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def send_telegram(message: str):
    """發送 Telegram 訊息"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("  Telegram 設定不完整，跳過")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        }).encode()
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=10)
        print("  Telegram 通知已發送")
    except Exception as e:
        print(f"  Telegram 發送失敗：{e}")

def send_email(subject: str, body: str):
    """發送 email 通知"""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD or not NOTIFY_EMAIL:
        print("  通知設定不完整，跳過發信")
        return
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = NOTIFY_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
            print(f"  Email 已發送到 {NOTIFY_EMAIL}")
    except Exception as e:
        print(f"  Email 發送失敗：{e}")

def notify_session_expired():
    """sessionid 過期時通知"""
    msg = (
        "⚠️ <b>IG Reels Tracker 警告</b>\n\n"
        "sessionid 已過期或被封鎖（HTTP 400/401）\n\n"
        "請照以下步驟更新：\n"
        "1. Chrome 登入 IG 小帳號\n"
        "2. F12 → Application → Cookies\n"
        "3. 複製 sessionid\n"
        "4. 更新 GitHub Secrets 的 IG_SESSION_ID"
    )
    send_telegram(msg)
    send_email(
        subject="⚠️ IG Reels Tracker：sessionid 已過期",
        body=msg.replace("<b>", "").replace("</b>", "")
    )

def notify_scan_result(duration: int, total_new: int, n_influencers: int, n_reels: int, n_sponsored: int, n_stats: int):
    """每次 scan 完成後發送結果"""
    msg = (
        f"✅ <b>Scan 完成</b>\n\n"
        f"⏱ 耗時：{duration} 秒\n"
        f"🆕 新收錄：{total_new} 篇\n\n"
        f"📊 <b>資料庫狀況</b>\n"
        f"追蹤網紅：{n_influencers} 位\n"
        f"收錄 Reels 總數：{n_reels} 篇\n"
        f"其中業配：{n_sponsored} 篇\n"
        f"互動數快照：{n_stats} 筆"
    )
    send_telegram(msg)