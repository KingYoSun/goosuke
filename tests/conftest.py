"""
テスト設定モジュール

このモジュールは、pytestのフィクスチャを提供します。
"""

import asyncio
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.auth.password import get_password_hash
from api.database import Base, get_db
from api.main import app
from api.models import User

# テスト用のデータベースURL
# 共有モードでインメモリデータベースを使用
TEST_DATABASE_URL = "sqlite+aiosqlite:///file:memdb?mode=memory&cache=shared&uri=true"

# グローバルなエンジンとセッションファクトリを作成
# これにより、テスト間でデータベース接続を共有できる

# テスト用の非同期エンジンの作成
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)

# テスト用の非同期セッションの作成
TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# プロジェクトルートディレクトリを取得
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
# alembic.iniのパス
ALEMBIC_INI_PATH = PROJECT_ROOT / "alembic.ini"


def run_migrations():
    """テスト用データベースにマイグレーションを実行する"""
    # Alembic設定オブジェクトの作成
    alembic_cfg = Config(str(ALEMBIC_INI_PATH))

    # テスト用データベースURLを設定
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)

    # マイグレーションを実行（headまでアップグレード）
    command.upgrade(alembic_cfg, "head")

    print("テスト用データベースのマイグレーションが完了しました。")


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """イベントループのフィクスチャ"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# テスト用のデータベースを初期化する関数
async def init_test_db():
    """テスト用データベースを初期化する"""
    # テーブルの作成
    async with test_engine.begin() as conn:
        # 既存のテーブルを削除
        await conn.run_sync(Base.metadata.drop_all)
        # テーブルを作成
        await conn.run_sync(Base.metadata.create_all)

    # 初期化が完了したことをログに出力
    print("テスト用データベースの初期化が完了しました。")


# テスト実行前に一度だけデータベースを初期化
@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """テスト実行前に一度だけデータベースを初期化する"""
    # マイグレーションを実行してテーブルを作成
    run_migrations()

    # 初期化
    await init_test_db()
    yield
    # テスト終了後にテーブルを削除する必要はない（インメモリDBなので）


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """テスト用データベースセッションのフィクスチャ"""
    # テーブルを確実に作成
    async with test_engine.begin() as conn:
        # テーブルを作成（既存のテーブルは削除しない）
        await conn.run_sync(Base.metadata.create_all)

    # セッションの作成
    async with TestAsyncSessionLocal() as session:
        # 各テスト関数の実行前にセッションをクリア
        try:
            await session.execute(text("DELETE FROM action_config"))
            await session.execute(text("DELETE FROM config_discord"))
            await session.execute(text("DELETE FROM actions"))
            await session.execute(text("DELETE FROM task_executions"))
            await session.execute(text("DELETE FROM task_templates"))
            await session.execute(text("DELETE FROM users"))
            await session.execute(text("DELETE FROM settings"))
            await session.execute(text("DELETE FROM extensions"))
            await session.commit()
        except Exception as e:
            print(f"テーブルクリア中にエラーが発生しました: {e}")
            await session.rollback()
            # エラーが発生した場合は、テーブルを作成
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        yield session


@pytest_asyncio.fixture(scope="function")
async def integration_db_session() -> AsyncGenerator[AsyncSession, None]:
    """統合テスト用データベースセッションのフィクスチャ"""
    # テーブルを確実に作成
    async with test_engine.begin() as conn:
        # 既存のテーブルを削除
        await conn.run_sync(Base.metadata.drop_all)
        # テーブルを作成
        await conn.run_sync(Base.metadata.create_all)

    # セッションの作成
    async with TestAsyncSessionLocal() as session:
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

    # get_dbの依存関係をオーバーライド
    async def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db

    # テスト用クライアントの作成
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    # 依存関係のオーバーライドをクリア
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """テスト用ユーザーのフィクスチャ"""
    # 既存のユーザーを削除
    await db_session.execute(text("DELETE FROM users WHERE username = 'testuser'"))
    await db_session.commit()

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

    return user


@pytest_asyncio.fixture(scope="function")
async def test_admin(db_session: AsyncSession) -> User:
    """テスト用管理者ユーザーのフィクスチャ"""
    # 既存の管理者ユーザーを削除
    await db_session.execute(text("DELETE FROM users WHERE username = 'admin'"))
    await db_session.commit()

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

    return admin
