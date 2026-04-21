FROM python:3.12-slim

WORKDIR /app

# 安裝系統套件
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案檔案
COPY . .

# 建立上傳目錄
RUN mkdir -p uploads static

# 開放 port
EXPOSE 8080

# 啟動指令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
