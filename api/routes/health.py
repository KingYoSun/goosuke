"""
ヘルスチェックルートモジュール

このモジュールは、アプリケーションのヘルスチェックに関連するAPIエンドポイントを提供します。
"""

import platform
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter

from ..config import settings
from ..database import get_db

router = APIRouter(prefix="/api/health", tags=["ヘルスチェック"])


@router.get("/", response_model=Dict[str, Any])
async def health_check():
    """ヘルスチェックエンドポイント

    アプリケーションの状態を確認するためのエンドポイント

    Returns:
        Dict[str, Any]: ヘルスチェック結果
    """
    # データベース接続を確認
    db_status = "ok"
    db_error = None

    try:
        async with get_db() as db:
            # テスト環境でも実際にクエリを実行する
            # ただし、モックされた場合はエラーを適切に処理する
            from sqlalchemy import text

            await db.execute(text("SELECT 1"))
    except Exception as e:
        # データベース接続エラーが発生した場合は常にエラーを返す
        db_status = "error"
        db_error = str(e)

    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "environment": settings.GOOSUKE_ENV,
        "system_info": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "hostname": platform.node(),
        },
        "database": {"status": db_status, "error": db_error},
    }


@router.get("/ping", response_model=Dict[str, str])
async def ping():
    """簡易ヘルスチェックエンドポイント

    Returns:
        Dict[str, str]: pingレスポンス
    """
    return {"ping": "pong"}
