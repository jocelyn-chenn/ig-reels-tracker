# IG Reels Tracker
自動追蹤 Instagram 網紅的業配 Reels，用 AI 判斷是否為業配文，並每天記錄互動數據。

---

## 目錄

- [這個專案在做什麼](#這個專案在做什麼)
- [系統架構與運作邏輯](#系統架構與運作邏輯)
- [每個檔案的用途](#每個檔案的用途)
- [資料庫結構](#資料庫結構)
- [快速開始](#快速開始)
- [設定 GitHub Actions 自動排程](#設定-github-actions-自動排程)
- [常見問題](#常見問題)
- [注意事項](#注意事項)

---

## 這個專案在做什麼

這是一個**全自動的 IG 業配監測系統**，主要功能：

1. **每 30 分鐘**自動掃描指定網紅的 IG 主頁，偵測有沒有發新的 Reels
2. 發現新 Reels 後，把文案丟給 **Gemini AI** 判斷是不是業配文（商業合作/贊助內容）
3. 判斷為業配的 Reels 自動收錄進 **SQLite 資料庫**
4. 每天持續回去抓已收錄 Reels 的**按讚數、留言數、觀看數**，形成成長曲線
5. 整個系統跑在 **GitHub Actions** 上，電腦關著也照樣運行

適合用來追蹤 KOL 的業配頻率、品牌合作狀況、以及業配貼文的互動表現。

---

## 系統架構與運作邏輯

```
GitHub Actions 排程觸發（每30分鐘）
        │
        ▼
   main.py 主程式
        │
        ├─── [Step 1] 初始化資料庫
        │         database.py → 建立三張資料表（如果不存在）
        │         從 config.py 載入 KOL 清單 → 寫入 influencers 表
        │
        ├─── [Step 2] 健康檢查
        │         health_check.py → 測試 IG REST API 是否正常
        │                        → 測試 GraphQL doc_id 是否還有效
        │
        ├─── [Step 3] 對每位 KOL 執行抓取 + AI 分析
        │         scraper.py → 掃主頁，取得最新 Reels 清單（REST API，穩定）
        │                   → 抓單篇詳細資料（GraphQL API，需 doc_id）
        │         analyzer.py → 把文案 + tagged 帳號丟給 Gemini
        │                    → Gemini 回傳「是業配 / 不是業配」+ 理由
        │         database.py → 業配的 Reels 存進 sponsored_reels 表
        │
        └─── [Step 4] 更新每日互動數
                  updater.py → 對所有已收錄的 Reels 重新抓按讚/留言/觀看數
                  database.py → 存進 daily_stats 表（每天一筆快照）
```

### 為什麼用兩種 API？

| API 類型 | 用途 | 穩定性 |
|----------|------|--------|
| REST API (`web_profile_info`) | 掃主頁、取得 Reels 清單 | 穩定，不需要 doc_id |
| GraphQL API | 抓單篇詳細數據（按讚數、文案等）| 需要 doc_id，約 2-4 週更新一次 |

這樣設計是為了降低風險：就算 doc_id 過期，至少還能掃到有沒有新 Reels，只是詳細數據暫時抓不到。

### 為什麼用 curl_cffi？

IG 有很強的反爬蟲機制，會檢查你的請求「看起來像不像真實瀏覽器」。`curl_cffi` 可以模擬真實 Chrome 瀏覽器的 TLS 指紋，大幅降低被封鎖的機率。

---

## 每個檔案的用途

```
ig-reels-tracker/
│
├── .github/
│   └── workflows/
│       └── daily_run.yml    ← GitHub Actions 排程設定（每30分鐘執行）
│
├── data/
│   └── tracker.db           ← SQLite 資料庫（自動產生，存所有資料）
│
├── config.py                ← 設定中心：KOL 清單、API Keys、爬蟲參數
├── scraper.py               ← 負責從 IG 抓資料（用 curl_cffi 模擬瀏覽器）
├── analyzer.py              ← 負責用 Gemini AI 判斷是否為業配文
├── database.py              ← 負責所有資料庫讀寫操作
├── updater.py               ← 負責每日回抓已收錄 Reels 的互動數
├── health_check.py          ← 每次執行前先測試 API 是否正常
├── main.py                  ← 主程式，把以上全部串起來
│
├── KOL_sheet.csv            ← 你要追蹤的 KOL 名單（自行替換）
├── requirements.txt         ← Python 套件清單
├── .env                     ← 你的 API Keys（不能上傳 GitHub！）
└── .env.example             ← .env 的格式範本（可以上傳）
```

### `config.py`
整個專案的控制台。修改這裡就能調整所有行為，不需要動其他程式碼。
- 從 `KOL_sheet.csv` 讀取要追蹤的帳號
- 設定爬蟲延遲時間（太短容易被封，預設 3-7 秒）
- 存放 IG 的 `doc_id`（過期時只需改這裡）

### `scraper.py`
分兩個函數：
- `get_recent_reels(username)` — 用 REST API 掃主頁，取得最新影片清單
- `get_reel_detail(shortcode)` — 用 GraphQL 抓單篇詳細資料（文案、時間、tagged 帳號）

### `analyzer.py`
把文案和 tagged 帳號傳給 Gemini，用繁體中文的業配判斷邏輯分析。
回傳 `(True/False, "判斷理由")` 的格式。

### `database.py`
所有資料庫操作都集中在這裡，包括建表、寫入、查詢。
其他模組需要存/讀資料時，統一透過這個檔案，不直接操作資料庫。

### `updater.py`
每次執行時，對資料庫裡所有已收錄的業配 Reels 重新抓一次互動數，
形成時間序列資料，可以看每篇業配貼文的成長曲線。

### `health_check.py`
每次執行的最開始先跑健康檢查：
- 如果 REST API 異常 → 可能 IP 被封，印出警告
- 如果 GraphQL 異常 → `doc_id` 可能過期，印出提醒並告訴你怎麼更新

---

## 資料庫結構

資料庫有三張表：

### `influencers`（追蹤的 KOL 清單）
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INTEGER | 自動編號 |
| username | TEXT | IG 帳號名稱 |
| added_at | TEXT | 加入追蹤的時間 |

### `sponsored_reels`（收錄的業配 Reels）
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INTEGER | 自動編號 |
| username | TEXT | 哪個網紅發的 |
| shortcode | TEXT | Reels 的唯一識別碼 |
| url | TEXT | 完整連結 |
| caption | TEXT | 文案內容 |
| post_time | TEXT | 發文時間 |
| video_duration | REAL | 影片長度（秒） |
| ai_reason | TEXT | Gemini 的判斷理由 |
| tagged_brands | TEXT | 被 tag 的品牌帳號 |
| first_seen | TEXT | 第一次被收錄的時間 |

### `daily_stats`（每日互動數快照）
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INTEGER | 自動編號 |
| shortcode | TEXT | 對應哪篇 Reels |
| date | TEXT | 記錄日期（YYYY-MM-DD）|
| likes | INTEGER | 當天的按讚數 |
| comments | INTEGER | 當天的留言數 |
| views | INTEGER | 當天的觀看數 |

---

## 快速開始

### 前置需求
- Python 3.10 以上
- Git
- GitHub 帳號
- Gemini API Key（免費，申請網址：[aistudio.google.com](https://aistudio.google.com)）

### 安裝步驟

**1. Clone 這個 repo**
```bash
git clone https://github.com/你的帳號/ig-reels-tracker.git
cd ig-reels-tracker
```

**2. 建立虛擬環境並安裝套件**
```bash
python3 -m venv venv
source venv/bin/activate      # Windows 用：venv\Scripts\activate
pip install -r requirements.txt
```

**3. 建立 `.env` 檔案**
```bash
cp .env.example .env
```
用任何文字編輯器打開 `.env`，填入你的 Gemini API Key：
```
GEMINI_API_KEY=你的_api_key_貼這裡
```

**4. 準備你的 KOL 名單**

把你的 KOL 清單存成 `KOL_sheet.csv`，格式如下：
```csv
KOL ID,LINK,FANS,TYPE
黃大謙,https://www.instagram.com/da_chien_huang/,514254,美妝時尚
```
> `LINK` 欄位填 IG 個人頁面的完整網址，程式會自動擷取 username。

**5. 測試執行**
```bash
python3 main.py
```

---

## 設定 GitHub Actions 自動排程

### Step 1：把 Gemini API Key 存進 GitHub Secrets

1. 進入你的 GitHub repo 頁面
2. 點上方 `Settings` → 左側 `Secrets and variables` → `Actions`
3. 點 `New repository secret`
4. Name 填 `GEMINI_API_KEY`，Secret 填你的 API Key
5. 點 `Add secret`

### Step 2：推上 GitHub

```bash
git add .
git commit -m "Initial setup"
git push
```

### Step 3：手動觸發測試

1. 進入 GitHub repo → 點 `Actions`
2. 左側點 `Daily IG Reels Tracker`
3. 右側點 `Run workflow` → `Run workflow`

看到綠色勾勾就代表成功！之後每天 08:00-23:00 每 30 分鐘會自動執行。

---

## 常見問題

### doc_id 過期怎麼辦？

`doc_id` 是 IG GraphQL 的內部查詢 ID，大約每 2-4 週會更新一次。過期時 `health_check.py` 會印出警告。

更新方法（約 5 分鐘）：
1. 用 Chrome 登入 IG，按 `F12` 開 DevTools
2. 切到 `Network` 分頁，過濾 `graphql`
3. 點開任意一篇 Reels
4. 在 Network 裡找到含有 `doc_id` 的請求，複製新的數字
5. 貼到 `config.py` 的 `IG_DOC_ID` 並推上 GitHub

### 為什麼有些 Reels 抓不到詳細資料？

可能原因：
- 該 Reels 設定為限定受眾或私人帳號
- `doc_id` 已過期（看 health_check 的輸出）
- 該次請求被 IG 限流（等下次自動執行就好）

### 怎麼查看已收錄的業配資料？

可以用任何 SQLite 工具打開 `data/tracker.db`，例如：
- [DB Browser for SQLite](https://sqlitebrowser.org/)（免費桌面軟體）
- VSCode 安裝 `SQLite Viewer` 插件

或是直接用 Python 查詢：
```python
import sqlite3
conn = sqlite3.connect("data/tracker.db")
cursor = conn.cursor()
cursor.execute("SELECT username, url, post_time, ai_reason FROM sponsored_reels ORDER BY first_seen DESC")
for row in cursor.fetchall():
    print(row)
conn.close()
```

### 怎麼新增或移除追蹤的 KOL？

直接修改 `KOL_sheet.csv`，加入或刪除對應的列，推上 GitHub 後下次執行就會生效。不需要動任何程式碼。

---

## 注意事項

- **`.env` 絕對不能上傳 GitHub**，裡面有你的 API Key，已透過 `.gitignore` 擋住
- 這個專案使用 IG 的內部 API，非官方支援，使用時請遵守 IG 使用條款
- 爬蟲延遲設定請不要調太短（建議最低 1 秒），避免對 IG 伺服器造成過大負擔或被封鎖
- Gemini API 有免費使用額度限制，如果 KOL 數量很多，留意有沒有超額

---

## 技術棧

| 工具 | 用途 |
|------|------|
| Python 3.10+ | 主要程式語言 |
| curl_cffi | 模擬真實瀏覽器發送請求，繞過 IG 反爬蟲 |
| google-genai | 呼叫 Gemini AI 判斷業配文 |
| SQLite | 輕量資料庫，存放所有追蹤資料 |
| pandas | 讀取 KOL 名單 CSV |
| python-dotenv | 從 .env 檔案讀取 API Key |
| GitHub Actions | 雲端自動排程，電腦關著也能跑 |