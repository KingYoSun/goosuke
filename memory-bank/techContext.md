# Goosuke 技術コンテキスト

## 技術スタック

Goosuke は以下の技術スタックを使用しています：

### 言語・フレームワーク
- **言語**: Python 3.10
- **APIフレームワーク**: FastAPI 0.100.0以上
- **ASGI サーバー**: Uvicorn 0.22.0以上

### データベース
- **主要DB**: SQLite（小規模用）
- **ORM**: SQLAlchemy 2.0.0以上
- **マイグレーション**: Alembic

### 認証・セキュリティ
- **認証**: JWT（JSON Web Token）
- **JWT実装**: python-jose 3.3.0以上
- **パスワードハッシュ**: passlib 1.7.4以上
- **フォーム処理**: python-multipart 0.0.6以上

### 外部連携
- **HTTP クライアント**: aiohttp 3.8.5以上
- **Discord API**: discord.py 2.3.0以上

### 設定管理
- **環境変数**: python-dotenv 1.0.0以上

### データ検証
- **スキーマ検証**: Pydantic 2.0.0以上

### コンテナ化
- **コンテナ**: Docker
- **オーケストレーション**: Docker Compose
- **ベースイメージ**: python:3.10-slim

### テスト
- **テストフレームワーク**: pytest
- **コードカバレッジ**: pytest-cov

### コード品質
- **リンター**: flake8
- **型チェック**: mypy
- **フォーマッター**: black, isort
- **未使用インポート削除**: autoflake

## 開発環境

### ローカル開発環境
```bash
# 依存関係のインストール
pip install -r requirements.txt

# 開発サーバーの起動
uvicorn api.main:app --reload
```

### Docker開発環境
```bash
# Dockerコンテナのビルドと起動
docker-compose up -d

# ログの確認
docker-compose logs -f
```

### テスト環境
```bash
# テストの実行
docker-compose -f docker-compose.test.yml run --rm test

# リントの実行
docker-compose -f docker-compose.test.yml run --rm lint

# フォーマットの実行
docker-compose -f docker-compose.test.yml run --rm format
```

## ディレクトリ構造

```
goosuke/
├── api/                # 発火レイヤー（FastAPI アプリケーション）
│   ├── __init__.py
│   ├── config.py       # 設定
│   ├── database.py     # データベース接続
│   ├── main.py         # アプリケーションのエントリーポイント
│   ├── auth/           # 認証関連
│   ├── models/         # データベースモデル
│   ├── routes/         # APIルート
│   ├── services/       # ビジネスロジック
│   └── docs/           # APIドキュメント
├── goose/              # 実行レイヤー（Goose CLI とカスタマイズ）
│   ├── __init__.py
│   ├── cli.py          # Goose CLI ラッパー
│   ├── executor.py     # タスク実行
│   └── extensions/     # 拡張機能
├── extensions/         # 拡張機能
│   ├── __init__.py
│   └── discord/        # Discord 連携
├── db/                 # データベース関連
│   └── migrations/     # マイグレーションスクリプト
├── docker/             # Docker関連
│   ├── Dockerfile      # メインDockerfile
│   └── Dockerfile.base # ベースDockerfile
├── docs/               # ドキュメント
│   ├── database_migrations.md
│   ├── design_doc.md
│   ├── testing.md
│   └── user_guide.md
├── tests/              # テスト
│   ├── __init__.py
│   ├── conftest.py     # テスト設定
│   └── test_*.py       # テストファイル
├── .env.example        # 環境変数の例
├── .flake8             # flake8設定
├── .gitignore          # Gitの除外ファイル
├── alembic.ini         # Alembic設定
├── docker-compose.yml  # Docker Compose設定
├── docker-compose.test.yml # テスト用Docker Compose設定
├── mypy.ini            # mypy設定
├── pyproject.toml      # Python プロジェクト設定
└── requirements.txt    # 依存関係
```

## 技術的制約

### データベース
- **SQLite**: 小規模用途向け
- **非同期接続**: aiosqliteを使用
- **マイグレーション**: 起動時に自動実行

### 認証
- **JWT**: シンプルなJWTベースの認証
- **トークン有効期限**: デフォルト24時間
- **リフレッシュトークン**: サポート

### API
- **OpenAPI**: Swagger UIとReDocでドキュメント自動生成
- **バージョニング**: URLパスでバージョン管理（/api/v1/）
- **レート制限**: シンプルなレート制限実装

### Discord連携
- **Bot権限**: メッセージの読み取り、送信、リアクションの追加
- **イベント**: メッセージ、リアクション、コマンド

### コンテナ化
- **マルチステージビルド**: 軽量なイメージ
- **ヘルスチェック**: コンテナのヘルスチェック
- **環境変数**: 設定は環境変数で注入

## 依存関係

```
fastapi>=0.100.0
uvicorn>=0.22.0
python-jose>=3.3.0
python-multipart>=0.0.6
sqlalchemy>=2.0.0
pydantic>=2.0.0
aiohttp>=3.8.5
discord.py>=2.3.0
python-dotenv>=1.0.0
passlib>=1.7.4
```

## 開発ツール設定

### flake8 (.flake8)
```
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist
per-file-ignores = __init__.py:F401
```

### mypy (mypy.ini)
```
[mypy]
python_version = 3.10
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True

[mypy.plugins.sqlalchemy.ext.declarative.mapped_classes]
class_name_is_required = True

[mypy.plugins.sqlalchemy.ext.declarative.registry]
strict_optional = True
```

### black & isort (pyproject.toml)
```
[tool.black]
line-length = 88
target-version = ['py310']

[tool.isort]
profile = "black"
line_length = 88
```

## Goose CLI 設定

Goose CLIは以下の設定が必要です：

1. LLM Providerの設定
   - OpenAI、Anthropic、Mistral AIなどのプロバイダー
   - APIキー

2. 拡張機能の設定
   - MCPベースの拡張機能
   - カスタム拡張機能

```bash
# Goose CLIの設定
goose configure
```

## 環境変数

主要な環境変数：

```
# アプリケーション設定
APP_NAME=goosuke
ENVIRONMENT=development
LOG_LEVEL=info

# データベース設定
DATABASE_URL=sqlite:///db/sqlite.db

# 認証設定
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Discord設定
DISCORD_BOT_TOKEN=your-discord-bot-token
DISCORD_GUILD_ID=your-discord-guild-id

# Goose設定
GOOSE_PATH=/usr/local/bin/goose
```

## デプロイメント

### Docker Compose
```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./db:/app/db
    environment:
      - DATABASE_URL=sqlite:///db/sqlite.db
      - SECRET_KEY=${SECRET_KEY}
      - DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### ヘルスチェック
APIは `/api/v1/health` エンドポイントを提供し、システムの状態を確認できます。

## コード品質とテスト

### テスト戦略
- **単体テスト**: モデル、サービス、ユーティリティのテスト
- **統合テスト**: 発火レイヤーと実行レイヤーの連携テスト
- **APIテスト**: エンドポイント、認証、ヘルスチェックのテスト

### コードカバレッジ
テスト実行時にカバレッジレポートが生成されます。

### CI/CD
GitHub Actionsを使用して、プッシュやプルリクエスト時に自動的にテストとリントが実行されます。