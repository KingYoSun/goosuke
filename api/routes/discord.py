"""
Discord連携ルートモジュール

このモジュールは、Discord連携に関連するAPIエンドポイントを提供します。
"""

import hashlib
import hmac
import json
from typing import Any, Dict, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Request,
    status,
)

from ..auth.dependencies import get_current_active_admin, get_current_user
from ..config import settings
from ..models.user import User
from ..services.discord_service import DiscordBotService, DiscordWebhookService

router = APIRouter(prefix="/api/v1/discord", tags=["Discord連携"])


@router.post("/bot/start", response_model=Dict[str, Any])
async def start_discord_bot(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_admin),
):
    """Discord Botを起動するエンドポイント

    Args:
        background_tasks (BackgroundTasks): バックグラウンドタスク
        current_user (User, optional): 現在の管理者ユーザー。Depends(get_current_active_admin)から取得

    Returns:
        Dict[str, Any]: 起動結果
    """
    discord_service = DiscordBotService()
    return await discord_service.start_bot(background_tasks)


@router.post("/bot/stop", response_model=Dict[str, Any])
async def stop_discord_bot(current_user: User = Depends(get_current_active_admin)):
    """Discord Botを停止するエンドポイント

    Args:
        current_user (User, optional): 現在の管理者ユーザー。Depends(get_current_active_admin)から取得

    Returns:
        Dict[str, Any]: 停止結果
    """
    discord_service = DiscordBotService()
    return await discord_service.stop_bot()


@router.get("/bot/status", response_model=Dict[str, Any])
async def get_discord_bot_status(current_user: User = Depends(get_current_user)):
    """Discord Botのステータスを取得するエンドポイント

    Args:
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        Dict[str, Any]: ステータス情報
    """
    discord_service = DiscordBotService()
    return await discord_service.get_status()


@router.post("/webhooks", response_model=Dict[str, Any])
async def handle_discord_webhook(request: Request, x_signature: Optional[str] = Header(None)):
    """Discord Webhookを処理するエンドポイント

    Args:
        request (Request): リクエスト
        x_signature (Optional[str], optional): 署名。デフォルトはNone

    Returns:
        Dict[str, Any]: 処理結果

    Raises:
        HTTPException: 署名が無効な場合
    """
    # Webhookのシークレットが設定されている場合は署名を検証
    if settings.DISCORD_WEBHOOK_SECRET:
        if not x_signature:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="署名が必要です")

        # リクエストボディを取得
        body = await request.body()

        # 署名を検証
        expected_signature = hmac.new(settings.DISCORD_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_signature, x_signature):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="署名が無効です")

    # リクエストボディをJSONとしてパース
    try:
        data = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無効なJSONデータです")

    # Webhookを処理
    discord_service = DiscordWebhookService()
    return await discord_service.handle_webhook(data)
