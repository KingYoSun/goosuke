"""
Alembic環境設定モジュール

このモジュールは、Alembicマイグレーションの環境設定を行います。
SQLAlchemyの非同期接続に対応しています。
"""

import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# プロジェクトルートをPythonパスに追加
# Dockerコンテナ内では/appがプロジェクトルート
if os.path.exists("/app"):
    sys.path.insert(0, "/app")
else:
    # ローカル環境用
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 環境変数からデータベースURLを取得
from api.config import settings

# モデルのメタデータをインポート
from api.database import Base

# Alembic設定オブジェクト
config = context.config

# Pythonロギングの設定
fileConfig(config.config_file_name)

# 全てのモデルをインポートして、メタデータに登録されるようにする

# マイグレーション対象のメタデータ
target_metadata = Base.metadata

# SQLAlchemyのURLを環境変数から設定
# SQLiteのURLをasync対応形式に変換
if settings.DATABASE_URL.startswith("sqlite:///"):
    db_url = settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
else:
    db_url = settings.DATABASE_URL

# alembic.iniのSQLAlchemy URL設定を上書き
config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    """オフラインモードでマイグレーションを実行

    このモードでは、実際のデータベース接続を確立せずにマイグレーションを実行します。
    SQLスクリプトが出力されます。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """マイグレーションを実行する内部関数

    Args:
        connection: SQLAlchemy接続オブジェクト
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """非同期モードでマイグレーションを実行"""
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """オンラインモードでマイグレーションを実行

    このモードでは、実際のデータベース接続を確立してマイグレーションを実行します。
    テスト環境では同期的なSQLiteデータベースを使用します。
    """
    # テスト環境かどうかを判断
    is_test_env = os.environ.get("GOOSUKE_ENV") == "test"

    if is_test_env:
        # テスト環境では同期的なSQLiteデータベースを使用
        url = config.get_main_option("sqlalchemy.url")
        # sqlite+aiosqlite:// を sqlite:// に変換
        if url.startswith("sqlite+aiosqlite:///"):
            url = url.replace("sqlite+aiosqlite:///", "sqlite:///")

        # 同期的な接続を使用
        from sqlalchemy import create_engine

        connectable = create_engine(url)

        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                compare_server_default=True,
            )

            with context.begin_transaction():
                context.run_migrations()
    else:
        # 本番環境では非同期接続を使用
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
