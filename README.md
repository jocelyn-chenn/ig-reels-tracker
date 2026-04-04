# IG KOL 業配 Reels 自動追蹤系統

這是一個全自動的 Instagram 監測工具，會每小時掃描指定 KOL 的 IG 帳號，用 AI 判斷有沒有發業配 Reels，並且持續追蹤每篇 Reels 的觀看數、按讚數、留言數變化。

> 電腦不用開著，GitHub 會幫你自動跑。

---

## 這個系統在做什麼

```
每小時整點（scan）
  → 掃 126 位 KOL 的 IG 主頁
  → 偵測有沒有 30 分鐘內的新 Reels
  → 丟給 Gemini AI 判斷是不是業配文
  → 全部存進資料庫（業配標 sponsored，一般標 none）

每小時半點（update）
  → 對資料庫裡所有 Reels 重新抓一次數據
  → 記錄當下的觀看數、按讚數、留言數
  → 形成時間序列，可以畫趨勢圖
```

---

## 資料夾結構

```
ig-reels-tracker/
│
├── .github/
│   └── workflows/
│       ├── scan.yml       ← 每小時整點自動掃新 Reels
│       └── update.yml     ← 每小時半點自動更新互動數
│
├── data/
│   └── tracker.db         ← SQLite 資料庫（自動產生）
│
├── scan.py                ← 掃新貼文的入口
├── update.py              ← 更新互動數的入口
├── scraper.py             ← 負責從 IG 抓資料
├── analyzer.py            ← 負責用 Gemini AI 判斷業配
├── database.py            ← 負責所有資料庫讀寫
├── updater.py             ← 負責抓互動數的邏輯
├── health_check.py        ← 每次執行前先確認 API 正常
├── config.py              ← 所有設定集中在這裡
│
├── KOL_sheet.csv          ← KOL 名單（自行替換）
├── requirements.txt       ← Python 套件清單
├── .env                   ← 你的 API Keys（不能上傳！）
└── .env.example           ← .env 的格式範本
```

---

## 資料庫長什麼樣子

資料庫有三張表：

### `sponsored_reels`（每篇 Reels 一筆）

| 欄位 | 說明 |
|------|------|
| username | 哪個 KOL |
| shortcode | Reels 的唯一 ID |
| url | 完整連結 |
| caption | 文案內容 |
| post_time | 發文時間 |
| sponsor_status | `sponsored`（業配）或 `none`（一般） |
| ai_reason | Gemini 的判斷理由 |
| tagged_brands | 被 tag 的品牌帳號 |
| first_seen | 第一次被收錄的時間 |

### `daily_stats`（每篇 Reels 每小時一筆）

| 欄位 | 說明 |
|------|------|
| shortcode | 對應哪篇 Reels |
| recorded_at | 記錄時間（精確到分鐘） |
| views | 觀看數 |
| plays | 播放數 |
| likes | 按讚數 |
| comments | 留言數 |

### `influencers`（追蹤的 KOL 清單）

| 欄位 | 說明 |
|------|------|
| username | IG 帳號名稱 |
| added_at | 加入追蹤的時間 |

---

## 如何 Clone 並在自己的電腦跑

### 前置需求

在開始之前，你需要準備好三樣東西：

**1. Gemini API Key（免費）**
- 去 [aistudio.google.com](https://aistudio.google.com) 登入 Google 帳號
- 點左側「Get API Key」→「Create API Key」
- 複製那串 Key 備用

**2. IG 小帳號的 sessionid**

> ⚠️ 強烈建議申請一個專用小帳號，不要用你的主帳號，否則可能被 IG 偵測到自動化行為。

- 用 Chrome 登入你的 IG 小帳號
- 按 `F12` 開 DevTools → 切到 `Application` 分頁
- 左側找 `Cookies` → `https://www.instagram.com`
- 找到 `sessionid` 這個 cookie，複製它的值

**3. Python 3.10 以上**
- 在終端機輸入 `python3 --version` 確認版本

---

### Step 1：Clone repo 到你的電腦

打開終端機，切到你想放專案的地方（例如桌面）：

```bash
cd ~/Desktop
git clone https://github.com/jocelyn-chenn/ig-reels-tracker.git
cd ig-reels-tracker
```

### Step 2：建立虛擬環境

```bash
python3 -m venv venv
source venv/bin/activate
```

成功後，終端機最前面會出現 `(venv)` 字樣。

> 每次重新開終端機都要記得執行 `source venv/bin/activate`

### Step 3：安裝套件

```bash
pip install -r requirements.txt
```

### Step 4：建立 `.env` 檔案

```bash
cp .env.example .env
```

用任何編輯器打開 `.env`，填入你的 Key：

```
GEMINI_API_KEY=你的_gemini_api_key
IG_SESSION_ID=你的_ig_sessionid
```

### Step 5：準備你的 KOL 名單

把你的 KOL 清單存成 `KOL_sheet.csv`，格式如下：

```csv
KOL ID,LINK,FANS,TYPE
黃大謙,https://www.instagram.com/da_chien_huang/,514254,美妝時尚
```

程式會自動從 `KOL ID` 欄讀取 IG 帳號名稱。

### Step 6：測試執行

```bash
python3 scan.py
```

看到「Scan 完成」就代表成功！

---

## 如何設定 GitHub Actions 自動跑

這樣你的電腦就不用一直開著了。

### Step 1：建立自己的 repo

在 GitHub 上建一個新的 private repo，把所有程式碼放進去。

### Step 2：加入 GitHub Secrets

去你的 repo → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

加入兩個 Secret：

| Name | Secret |
|------|--------|
| `GEMINI_API_KEY` | 你的 Gemini API Key |
| `IG_SESSION_ID` | 你的 IG sessionid |

### Step 3：開啟 Actions 寫入權限

repo → `Settings` → `Actions` → `General` → 拉到最下面 → `Workflow permissions` → 選 `Read and write permissions` → `Save`

### Step 4：手動觸發測試

repo → `Actions` → 左側選 `Scan New Reels` → 右側 `Run workflow` → `Run workflow`

看到綠色勾勾就成功了！之後每小時整點會自動跑 scan，半點會自動跑 update。

---

## 怎麼查看收集到的資料

安裝 [DB Browser for SQLite](https://sqlitebrowser.org/)（免費），直接打開 `data/tracker.db` 就可以用表格方式瀏覽所有資料。

或是用 Python 查詢：

```python
import sqlite3
conn = sqlite3.connect("data/tracker.db")
cursor = conn.cursor()

# 查所有業配 Reels
cursor.execute("""
    SELECT username, post_time, url, ai_reason
    FROM sponsored_reels
    WHERE sponsor_status = 'sponsored'
    ORDER BY post_time DESC
""")
for row in cursor.fetchall():
    print(row)

conn.close()
```

---

## 常見問題

**sessionid 過期怎麼辦？**
重新從 Chrome 複製新的 sessionid，更新 `.env` 和 GitHub Secrets 裡的 `IG_SESSION_ID` 就好。大概幾週到幾個月會過期一次。

**Gemini 判斷錯了怎麼辦？**
去 `analyzer.py` 裡調整 prompt，增加更多業配的判斷標準，或是針對特定品牌加入關鍵字。

**要新增或移除 KOL 怎麼辦？**
直接修改 `KOL_sheet.csv`，加入或刪除對應的列，推上 GitHub 後下次執行就會生效。

**為什麼一定要用小帳號跑？**
IG 會偵測自動化行為，用主帳號跑爬蟲有被停權的風險。用專用小帳號就算被封也不影響你的主帳號。

---

## 技術說明

| 工具 | 用途 |
|------|------|
| `curl_cffi` | 模擬真實 Chrome 瀏覽器發送請求，繞過 IG 反爬蟲偵測 |
| `google-genai` | 呼叫 Gemini 2.5 Flash 判斷業配文 |
| `SQLite` | 輕量資料庫，存放所有追蹤資料 |
| `pandas` | 讀取 KOL 名單 CSV |
| `python-dotenv` | 從 `.env` 讀取 API Key |
| `GitHub Actions` | 雲端自動排程，每小時自動執行 |

---

## 注意事項

- `.env` 絕對不能上傳 GitHub，裡面有你的 API Key 和 sessionid
- 這個工具使用 IG 的內部 API，非官方支援，請自行評估使用風險
- 建議使用專用小帳號，不要用主帳號的 sessionid