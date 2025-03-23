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
- **非同期テスト**: pytest-asyncio
- **テストデータベース**: SQLite（インメモリ）

### コード品質
- **リンター**: flake8
- **型チェック**: mypy
- **フォーマッター**: black, isort

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
```

## ディレクトリ構造

```
goosuke/
├── api/                # 発火レイヤー（FastAPI アプリケーション）
│   ├── auth/           # 認証関連
│   ├── models/         # データベースモデル
│   ├── routes/         # APIルート
│   ├── services/       # ビジネスロジック
│   └── utils/          # ユーティリティ関数
├── goose/              # 実行レイヤー（Goose CLI とカスタマイズ）
│   └── extensions/     # 拡張機能
├── extensions/         # 拡張機能
│   └── discord/        # Discord 連携
├── db/                 # データベース関連
│   └── migrations/     # マイグレーションスクリプト
├── docker/             # Docker関連
├── docs/               # ドキュメント
├── tests/              # テスト
├── memory-bank/        # メモリーバンク（プロジェクト文書）
└── clones/             # コンテキスト用リポジトリクローンフォルダ
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

### 拡張機能
- **タイプ**: builtin（組み込み）、stdio（標準入出力）、sse（Server-Sent Events）
- **設定同期**: GoosukeとGoose間で設定を同期
- **環境変数**: 拡張機能ごとに環境変数を設定可能
- **タイムアウト**: 拡張機能の実行タイムアウトを設定可能

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

## テスト戦略

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