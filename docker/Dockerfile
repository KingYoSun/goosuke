FROM python:3.10-slim as base

WORKDIR /app

ARG GOOSE_PROVIDER
ARG GOOSE_MODEL

# 必要なパッケージのインストール
RUN apt-get update && apt-get install -y \
    curl \
    git \
    nodejs \
    npm \
    bzip2 \
    libdbus-1-3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Node.jsとnpmのバージョンを確認
RUN node -v && npm -v

# 依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Goose CLIのインストール - download_cli.shの内容に基づいて修正
ENV GOOSE_BIN_DIR="/usr/local/bin"
RUN curl -fsSL https://github.com/block/goose/releases/download/stable/download_cli.sh | CONFIGURE=false GOOSE_BIN_DIR=${GOOSE_BIN_DIR} bash && \
    # インストールされたバイナリに実行権限があることを確認
    chmod +x ${GOOSE_BIN_DIR}/goose && \
    # インストールが成功したか確認
    ${GOOSE_BIN_DIR}/goose --help || echo "Goose CLIのインストールに失敗しました"

# アプリケーションのコピー
COPY . .

# 実行ユーザーの設定
RUN useradd -m goosuke

# gooseユーザーに切り替え
USER goosuke

# PATH設定を明示的に行う
ENV PATH="/usr/local/bin:${PATH}"

# Goose CLIの設定
RUN mkdir -p /home/goosuke/.config/goose
RUN cat <<EOF > /home/goosuke/.config/goose/config.yaml
GOOSE_PROVIDER: ${GOOSE_PROVIDER}
GOOSE_MODEL: ${GOOSE_MODEL}
EOF

RUN cat <<EOF >> /home/goosuke/.config/goose/config.yaml
extensions:
  discord:
    enabled: true
    envs: {}
    name: discord
    timeout: 30
    type: sse
    uri: http://localhost:8000/mcp/discord/sse
EOF

# 最終確認 - gooseコマンドが利用可能か確認
RUN goose --help || echo "gooseコマンドが見つかりません。PATHを確認してください: $PATH"

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# コマンド
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]