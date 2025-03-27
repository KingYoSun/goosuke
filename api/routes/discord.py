"""
Discord連携ルートモジュール

このモジュールは、Discord連携に関連するAPIエンドポイントを提供します。
"""

from typing import Any, Dict

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
)

from ..auth.dependencies import get_current_active_admin, get_current_user
from ..models.user import User
from ..services.discord_service import DiscordBotManager

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
    discord_service = DiscordBotManager()
    return await discord_service.start_bot(background_tasks)


@router.post("/bot/stop", response_model=Dict[str, Any])
async def stop_discord_bot(current_user: User = Depends(get_current_active_admin)):
    """Discord Botを停止するエンドポイント

    Args:
        current_user (User, optional): 現在の管理者ユーザー。Depends(get_current_active_admin)から取得

    Returns:
        Dict[str, Any]: 停止結果
    """
    discord_service = DiscordBotManager()
    return await discord_service.stop_bot()


@router.get("/bot/status", response_model=Dict[str, Any])
async def get_discord_bot_status(current_user: User = Depends(get_current_user)):
    """Discord Botのステータスを取得するエンドポイント

    Args:
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        Dict[str, Any]: ステータス情報
    """
    discord_service = DiscordBotManager()
    return await discord_service.get_status()
