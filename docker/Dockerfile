FROM python:3.10-slim as base

WORKDIR /app

# 必要なパッケージのインストール
RUN apt-get update && apt-get install -y \
    curl \
    git \
    bzip2 \
    && rm -rf /var/lib/apt/lists/*

# 依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Goose CLIのインストール
RUN curl -fsSL https://github.com/block/goose/releases/download/stable/download_cli.sh | CONFIGURE=false bash

# アプリケーションのコピー
COPY . .

# 実行ユーザーの設定
RUN useradd -m goosuke
USER goosuke

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# コマンド
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]