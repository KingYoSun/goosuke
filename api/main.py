"""
発火レイヤーメインモジュール

このモジュールは、発火レイヤーのエントリーポイントを提供します。
アクションを受け取り、コンテキストとプロンプトをセットにしたタスクを生成します。
"""

import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db

# ロガーの設定
logging.basicConfig(
    level=logging.INFO if settings.GOOSUKE_ENV == "production" else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("goosuke")

try:
    from .routes import (
        actions_router,
        auth_router,
        discord_config_router,
        discord_router,
        extensions_router,
        health_router,
        tasks_router,
        settings_router
    )
except Exception as e:
    logger.error(f"routerのインポート中にエラーが発生しました: {e}")

# FastAPIアプリケーションの作成
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/api/docs" if settings.GOOSUKE_ENV != "production" else None,
    redoc_url="/api/redoc" if settings.GOOSUKE_ENV != "production" else None,
)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限すること
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの登録
app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(actions_router)  # 新しいアクションルーター
app.include_router(extensions_router)
app.include_router(discord_router)
app.include_router(discord_config_router)  # Discord設定ルーター
app.include_router(settings_router)  # 設定ルーター
app.include_router(health_router)


@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時のイベントハンドラ"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} in {settings.GOOSUKE_ENV} mode")

    # データベースの初期化
    # 開発環境でのみ自動初期化を実行（本番環境ではAlembicマイグレーションを使用）
    if settings.GOOSUKE_ENV == "development":
        logger.info("Initializing database in development mode...")
        await init_db()
        logger.info("Database initialized")
    else:
        logger.info("Skipping automatic database initialization in non-development mode")

    # Goose の拡張機能設定を同期
    try:
        from .services.extension_service import ExtensionService

        extension_service = ExtensionService()
        result = await extension_service.sync_from_goose()
        if result["success"]:
            logger.info(f"GooseからGoosukeへの拡張機能の同期が完了しました: {result['synced_count']}件")
        else:
            logger.warning(f"GooseからGoosukeへの拡張機能の同期に失敗しました: {result['message']}")

        result = await extension_service.sync_to_goose()
        if result["success"]:
            logger.info(f"GoosukeからGooseへの拡張機能の同期が完了しました: {result['synced_count']}件")
        else:
            logger.warning(f"GoosukeからGooseへの拡張機能の同期に失敗しました: {result['message']}")
    except Exception as e:
        logger.error(f"拡張機能の同期中にエラーが発生しました: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時のイベントハンドラ"""
    logger.info(f"Shutting down {settings.APP_NAME}")


@app.get("/")
async def root():
    """ルートエンドポイント

    Returns:
        dict: アプリケーション情報
    """
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "docs_url": "/api/docs" if settings.GOOSUKE_ENV != "production" else None,
    }


if __name__ == "__main__":
    # 直接実行された場合はUvicornでサーバーを起動
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=True)
