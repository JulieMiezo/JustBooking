# JustBooking 客戶建置申請系統

## 專案結構

```
justbooking-onboarding/
├── main.py           # FastAPI 入口
├── database.py       # MySQL 連線
├── config.py         # 環境變數設定
├── models.py         # 資料庫 Schema
├── schemas.py        # API 資料驗證
├── routers/
│   ├── auth.py       # 登入 / JWT
│   ├── clients.py    # 客戶申請 API
│   ├── admin.py      # 後台管理 API
│   └── upload.py     # 檔案上傳 API
├── static/
│   ├── client.html   # 客戶端頁面
│   └── admin.html    # 後台管理頁面
├── requirements.txt
├── Dockerfile
└── .env.example
```

## 本機開發

```bash
# 1. 安裝套件
pip install -r requirements.txt

# 2. 複製環境變數
cp .env.example .env
# 編輯 .env 填入 MySQL 連線資訊

# 3. 啟動
uvicorn main:app --reload --port 8000
```

瀏覽器開啟：
- 客戶端：http://localhost:8000
- 後台：http://localhost:8000/admin
- API 文件：http://localhost:8000/docs

## Zeabur 部署步驟

1. 將這個資料夾推上 GitHub
2. 登入 Zeabur → 新增專案 → 連接 GitHub repo
3. Zeabur 會自動偵測 Dockerfile 並部署
4. 在 Zeabur 的「環境變數」填入 .env.example 的所有設定
5. 把 static/client.html 和 static/admin.html 放進 static/ 資料夾

## API 說明

| 方法   | 路徑                                   | 說明             |
|--------|----------------------------------------|-----------------|
| POST   | /api/auth/login                        | 管理員登入       |
| GET    | /api/clients/query/{tax_id}            | 查詢申請進度     |
| POST   | /api/clients/step1                     | 金流申請         |
| POST   | /api/clients/step2/{tax_id}            | 文件上傳完成     |
| POST   | /api/clients/step3/{tax_id}            | 發票方案         |
| POST   | /api/clients/step4/{tax_id}            | 加值服務         |
| POST   | /api/clients/step5/{tax_id}            | 確認送出         |
| POST   | /api/upload/{tax_id}/{doc_type}        | 上傳文件         |
| GET    | /api/admin/applications                | 客戶列表（需登入）|
| GET    | /api/admin/applications/{id}           | 客戶詳情（需登入）|
| PATCH  | /api/admin/applications/{id}/status    | 更新狀態（需登入）|
| GET    | /api/admin/stats                       | 統計數字（需登入）|

## 資料庫 Schema

首次啟動時 FastAPI 會自動建立資料表（CREATE TABLE IF NOT EXISTS）。
