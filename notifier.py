# notifier.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import GMAIL_USER, GMAIL_APP_PASSWORD, NOTIFY_EMAIL

def send_alert(subject: str, body: str):
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
            print(f"  通知信已發送到 {NOTIFY_EMAIL}")

    except Exception as e:
        print(f"  發送通知失敗：{e}")

def notify_session_expired():
    send_alert(
        subject="⚠️ IG Reels Tracker：sessionid 已過期",
        body="""你好，

IG Reels Tracker 偵測到 sessionid 已過期或被封鎖（HTTP 400/401）。

請照以下步驟更新：
1. 用 Chrome 登入你的 IG 小帳號
2. 按 F12 → Application → Cookies → https://www.instagram.com
3. 找到 sessionid，複製新的值
4. 去 GitHub repo → Settings → Secrets → 更新 IG_SESSION_ID

更新完成後系統會自動恢復正常。

IG Reels Tracker
"""
    )