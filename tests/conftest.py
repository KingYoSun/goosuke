"""
テスト設定モジュール

このモジュールは、pytestのフィクスチャを提供します。
"""

import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.password import get_password_hash
from api.database import Base, _get_db_context
from api.database import engine as test_engine
from api.database import get_db
from api.main import app

# すべてのモデルを明示的にインポート
from api.models import User

# プロジェクトルートディレクトリを取得
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
# alembic.iniのパス
ALEMBIC_INI_PATH = PROJECT_ROOT / "alembic.ini"

# テスト用DBパス
db_file_path = os.path.abspath("/app/db/test_database.db")


async def run_migrations():
    """テスト用データベースにマイグレーションを実行する"""
    print("Running migrations...")
    async with _get_db_context() as db:
        # Alembic設定オブジェクトの作成
        alembic_cfg = Config(str(ALEMBIC_INI_PATH))
        # テスト用データベースURLを設定
        alembic_cfg.set_main_option("sqlalchemy.url", db.bind_url)

        try:
            # マイグレーションを実行（headまでアップグレード）
            command.upgrade(alembic_cfg, "head")
            print("✅ マイグレーションが完了しました")
        except Exception as e:
            print(f"❌ マイグレーション実行中にエラーが発生しました: {e}")
            raise


async def clear_tables(session: AsyncSession):
    """テーブルをクリアする関数"""
    print("🧹 Clearing tables for test...")

    # テーブルが存在するか確認
    try:
        # 既存のテーブルを取得
        result = await session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        )
        # SQLAlchemyのバージョンによっては、fetchall()が同期関数の場合がある
        rows = result.fetchall()
        existing_tables = [row[0] for row in rows]

        if not existing_tables:
            print("ℹ️ No tables to clear")
            return

        # 外部キー制約を一時的に無効化
        await session.execute(text("PRAGMA foreign_keys = OFF"))

        try:
            # alembic_versionテーブルは除外
            tables_to_clear = [t for t in existing_tables if t != "alembic_version"]

            for table in tables_to_clear:
                try:
                    await session.execute(text(f"DELETE FROM {table}"))
                    print(f"  ✓ Cleared table: {table}")
                except Exception as e:
                    print(f"  ✗ Error clearing table {table}: {e}")

            await session.commit()
            print("✅ Tables cleared successfully")
        except Exception as e:
            await session.rollback()
            print(f"❌ Failed to clear tables: {e}")
            raise e
        finally:
            # 外部キー制約を再び有効化
            await session.execute(text("PRAGMA foreign_keys = ON"))
    except Exception as e:
        print(f"❌ Error checking tables: {e}")


@pytest.fixture(scope="session")
def event_loop():
    """セッションスコープのイベントループを提供するフィクスチャ"""
    print("Creating event loop for session")
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    print("Closing event loop")
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def mocking_test_db():
    await initialize_test_db()

    yield

    # テスト終了後にデータベースを削除
    print("🧹 Cleaning up test database...")
    await test_engine.dispose()
    # ファイルベースのDBファイルを削除
    if os.path.exists(db_file_path):
        os.remove(db_file_path)
        print(f"✅ Removed database file: {db_file_path}")


async def initialize_test_db():
    """テスト実行前に一度だけデータベースを初期化する"""
    print("📦 Setting up test database...")

    # 既存のDBファイルがあれば削除して確実にクリーンな状態から開始
    if os.path.exists(db_file_path):
        os.remove(db_file_path)
        print(f"🧹 Removed existing database file: {db_file_path}")

    try:
        # データベーススキーマを作成
        async with test_engine.begin() as conn:
            # モデル定義の確認
            print(f"📋 Registered models: {Base.metadata.tables.keys()}")

            # SQLAlchemyのモデル定義に基づいてテーブルを作成
            # テスト環境ではマイグレーションを実行せず、SQLAlchemyのcreate_allだけを使用
            # これにより、SQLiteの制限（特に制約の変更に関する制限）を回避
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Database schema created")

            # テーブルが正しく作成されたことを確認
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            rows = result.fetchall()
            tables = [row[0] for row in rows]
            print(f"📋 Created tables: {tables}")

            # 必要なテーブルが存在することを確認
            required_tables = [
                "settings",
                "extensions",
                "users",
                "task_templates",
                "actions",
                "task_executions",
                "action_config",
                "config_discord",
            ]
            missing_tables = [table for table in required_tables if table not in tables]
            if missing_tables:
                print(f"⚠️ Missing tables: {missing_tables}")
                print("⚠️ This may cause tests to fail!")

        # データベースが正しく設定されたことを確認
        async with test_engine.begin() as conn:
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            # SQLAlchemyのバージョンによっては、fetchall()が同期関数の場合がある
            rows = result.fetchall()
            tables = [row[0] for row in rows]
            print(f"📋 Tables after initialization: {tables}")

    except Exception as e:
        print(f"❌ データベース初期化中にエラーが発生しました: {e}")
        import traceback

        print(traceback.format_exc())
        raise


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """テスト用データベースセッションのフィクスチャ

    各テスト関数で独立したデータベースセッションを提供します。
    """
    print("🔄 Creating new database session for test session...")

    # セッションの作成
    async with _get_db_context() as session:
        # 各テスト関数の実行前にテーブルをクリア
        try:
            await clear_tables(session)
            await session.commit()
        except Exception as e:
            print(f"テーブルクリア中にエラーが発生しました: {e}")
            await session.rollback()
            raise

        # セッションを提供
        try:
            yield session
        finally:
            await session.close()


@pytest_asyncio.fixture
async def integration_db_session() -> AsyncGenerator[AsyncSession, None]:
    """統合テスト用データベースセッションのフィクスチャ"""
    print("🔄 Setting up database for integration test...")

    # セッションの作成
    async with _get_db_context() as session:
        # テーブルが作成されたことを確認
        async with test_engine.begin() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: sync_conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                ).fetchall()
            )
            print(f"テーブル一覧: {[table[0] for table in tables]}")

        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """テスト用クライアントのフィクスチャ"""
    print("🔄 Setting up test client...")

    # get_dbの依存関係をオーバーライド
    async def override_get_db():
        print("  ✓ Using test database session")
        yield db_session

    # 既存のオーバーライドをクリア
    app.dependency_overrides.clear()
    # 新しいオーバーライドを設定
    app.dependency_overrides[get_db] = override_get_db
    print("  ✓ Dependency override set for get_db")

    # テスト用クライアントの作成
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", follow_redirects=True) as client:
        print("✅ Test client created")
        yield client
        print("✅ Test client closed")

    # 依存関係のオーバーライドをクリア
    app.dependency_overrides.clear()
    print("✅ Dependency overrides cleared")


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """テスト用ユーザーのフィクスチャ"""
    print("🔄 Creating test user...")

    # テスト用ユーザーの作成
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password"),
        is_active=True,
        is_admin=False,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    print(f"✅ Test user created: {user.username}")
    return user


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """テスト用管理者ユーザーのフィクスチャ"""
    print("🔄 Creating test admin user...")

    # テスト用管理者ユーザーの作成
    admin = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword"),
        is_active=True,
        is_admin=True,
    )

    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    print(f"✅ Test admin user created: {admin.username}")
    return admin


# 共通のモック関数やユーティリティ
class MockGooseCLI:
    """Goose CLIのモック"""

    def __init__(self, return_value=None):
        self.return_value = return_value or {"result": "success"}
        self.calls = []

    async def execute(self, *args, **kwargs):
        """Goose CLIの実行をモック"""
        self.calls.append((args, kwargs))
        return self.return_value
