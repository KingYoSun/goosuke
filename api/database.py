"""
データベース接続モジュール

このモジュールは、SQLAlchemyを使用してデータベース接続を管理します。
非同期セッションの作成と管理を行います。
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from .config import settings

# SQLiteのURLをasync対応形式に変換
if settings.DATABASE_URL.startswith("sqlite:///"):
    db_url = settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
else:
    db_url = settings.DATABASE_URL

# 非同期エンジンの作成
engine: AsyncEngine = create_async_engine(db_url, echo=settings.GOOSUKE_ENV == "development", future=True)

# 非同期セッションの作成
async_session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# モデルのベースクラス
Base = declarative_base()


@asynccontextmanager
async def _get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """非同期データベースセッションを取得するコンテキストマネージャ
    Yields:
        AsyncSession: 非同期SQLAlchemyセッション
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """非同期データベースセッションを取得する依存関係
    Yields:
        AsyncSession: 非同期SQLAlchemyセッション
    """
    async with _get_db_context() as session:
        yield session


async def init_db() -> None:
    """データベースの初期化を行う関数
    アプリケーション起動時にデータベーススキーマを作成します。
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
