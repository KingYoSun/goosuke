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
- **YAML処理**: PyYAML

### データ検証
- **スキーマ検証**: Pydantic 2.0.0以上

### コンテナ化
- **コンテナ**: Docker
- **オーケストレーション**: Docker Compose
- **ベースイメージ**: python:3.10-slim

### テスト
- **テストフレームワーク**: pytest
- **コードカバレッジ**: pytest-cov
- **非同期テスト**: pytest-asyncio
- **テストデータベース**: SQLite（インメモリ）

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
│   ├── utils/          # ユーティリティ関数
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
├── memory-bank/        # メモリーバンク（プロジェクト文書）
│   ├── activeContext.md
│   ├── productContext.md
│   ├── progress.md
│   ├── projectbrief.md
│   ├── systemPatterns.md
│   └── techContext.md
├── clones/             # コンテキスト用リポジトリクローンフォルダ
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
- **トランザクション管理**: 非同期コンテキストマネージャを使用

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
- **リアクショントリガー**: 鉛筆リアクションによる要約機能

### コンテナ化
- **マルチステージビルド**: 軽量なイメージ
- **ヘルスチェック**: コンテナのヘルスチェック
- **環境変数**: 設定は環境変数で注入

### 拡張機能
- **タイプ**: builtin（組み込み）、stdio（標準入出力）、sse（Server-Sent Events）
- **設定同期**: GoosukeとGoose間で設定を同期
- **環境変数**: 拡張機能ごとに環境変数を設定可能
- **タイムアウト**: 拡張機能の実行タイムアウトを設定可能

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
pyyaml
```

## 開発ツール設定

### flake8 (.flake8)
```
[flake8]
max-line-length = 120
extend-ignore = E203, W503, F841
exclude = .git,__pycache__,build,dist,clones
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
   - 現在はAnthropicプロバイダーを使用（.envファイルで設定）
   - APIキー（ANTHROPIC_API_KEY）

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
GOOSE_PROVIDER=anthropic
GOOSE_MODEL=claude-3-7-sonnet-latest
ANTHROPIC_API_KEY=your-anthropic-api-key
```

## セキュリティ上の注意点

現在の実装では、`.env`ファイルに機密情報（Discord BotトークンやAnthropic APIキー）が平文で保存されています。これはセキュリティリスクとなるため、以下の対策を検討中です：

1. 環境変数の暗号化
2. シークレット管理サービスの利用
3. コンテナ実行時のみ環境変数を注入する方法
4. `.env`ファイルのアクセス制限強化

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
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GOOSE_PROVIDER=${GOOSE_PROVIDER}
      - GOOSE_MODEL=${GOOSE_MODEL}
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
- **モック最小化**: goose CLIとテスト用モックDB以外のモックは最小限に抑える
- **トランザクション活用**: テスト間の独立性を確保するためにトランザクションを活用
- **共通セットアップ**: テストコードの保守性を高めるために共通のセットアップコードを集約

### テストデータベース接続パターン
```python
@asynccontextmanager
async def test_get_db_context():
    async with TestAsyncSessionLocal() as session:
        async with session.begin():
            yield session
            # トランザクションは自動的にロールバックされる
```

### テスト用テーブル作成パターン
```python
# テーブルが存在することを確認
async def ensure_table_exists(session, table_name, create_table_sql):
    # テーブルの存在確認
    result = await session.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"))
    if result.scalar() is None:
        # テーブルが存在しない場合は作成
        await session.execute(text(create_table_sql))
        await session.commit()
```

### テスト用データベース初期化パターン
```python
# テスト用データベースを初期化する関数
async def init_test_db():
    # テーブルの作成
    async with test_engine.begin() as conn:
        # 既存のテーブルを削除
        await conn.run_sync(Base.metadata.drop_all)
        # テーブルを作成
        await conn.run_sync(Base.metadata.create_all)
        
        # 追加のテーブル作成（モデルに定義されていないテーブル）
        for table_name, create_table_sql in ADDITIONAL_TABLES.items():
            await ensure_table_exists(conn, table_name, create_table_sql)
```

### コードカバレッジ
テスト実行時にカバレッジレポートが生成されます。

### CI/CD
GitHub Actionsを使用して、プッシュやプルリクエスト時に自動的にテストとリントが実行されます。

## 拡張機能モデル

拡張機能モデルは以下のフィールドで構成されています：

```python
class Extension(Base):
    __tablename__ = "extensions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True, unique=True)
    description = Column(Text, nullable=True)
    version = Column(String, nullable=True)
    enabled = Column(Boolean, default=True)
    
    # Goose拡張機能の設定フィールド
    type = Column(String, nullable=True)  # builtin, stdio, sse
    cmd = Column(String, nullable=True)  # stdio タイプの場合のコマンド
    args = Column(JSON, nullable=True)  # stdio タイプの場合の引数
    timeout = Column(Integer, nullable=True)  # タイムアウト（秒）
    envs = Column(JSON, nullable=True)  # 環境変数
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 拡張機能タイプ
- **builtin**: Gooseに組み込まれた拡張機能
- **stdio**: 標準入出力を使用する外部プロセスとして実行される拡張機能
- **sse**: Server-Sent Events（SSE）を使用するHTTPベースの拡張機能

### Goose設定同期
GoosukeとGoose間の設定同期は、`api/utils/goose_config.py`モジュールを使用して行われます：

```python
def get_goose_config_path() -> Path:
    """Goose の設定ファイルのパスを取得する"""
    # ...

def read_goose_config() -> Dict[str, Any]:
    """Goose の設定ファイルを読み取る"""
    # ...

def read_goose_extensions() -> Dict[str, Any]:
    """Goose の設定ファイルから拡張機能の設定を読み取る"""
    # ...
```

これらの関数を使用して、`ExtensionService`クラスの`sync_from_goose`メソッドと`sync_to_goose`メソッドが実装されています。