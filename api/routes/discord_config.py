"""
Discord設定ルートモジュール

このモジュールは、Discord設定に関連するAPIエンドポイントを提供します。
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..auth.dependencies import get_current_user
from ..models.user import User
from ..services.action_config_service import ActionConfigService
from ..services.discord_config_service import DiscordConfigService

router = APIRouter(prefix="/api/v1/discord-configs", tags=["Discord設定"])


@router.post("/", response_model=Dict[str, Any])
async def create_discord_config(
    name: str,
    catch_type: str,
    catch_value: str,
    message_type: str = "single",
    response_format: str = "reply",
    current_user: User = Depends(get_current_user),
):
    """Discord設定を作成するエンドポイント

    Args:
        name (str): 設定名
        catch_type (str): 取得タイプ（'reaction', 'text', 'textWithMention'）
        catch_value (str): 取得対象（絵文字、キーワードなど）
        message_type (str, optional): メッセージ収集戦略。デフォルトは"single"
        response_format (str, optional): レスポンス形式。デフォルトは"reply"
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        Dict[str, Any]: 作成されたDiscord設定
    """
    # 管理者のみDiscord設定を作成可能
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Discord設定を作成する権限がありません",
        )

    discord_config_service = DiscordConfigService()
    result = await discord_config_service.create_discord_config(
        name=name,
        catch_type=catch_type,
        catch_value=catch_value,
        message_type=message_type,
        response_format=response_format,
    )

    return result


@router.post("/{config_id}/link-action", response_model=Dict[str, Any])
async def link_action_to_discord_config(
    config_id: int,
    action_id: int,
    current_user: User = Depends(get_current_user),
):
    """Discord設定とアクションを関連付けるエンドポイント

    Args:
        config_id (int): Discord設定ID
        action_id (int): アクションID
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        Dict[str, Any]: 作成されたアクション設定関連
    """
    # 管理者のみDiscord設定とアクションを関連付け可能
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Discord設定とアクションを関連付ける権限がありません",
        )

    # Discord設定の存在確認
    discord_config_service = DiscordConfigService()
    discord_config = await discord_config_service.get_discord_config(config_id)
    if not discord_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discord設定が見つかりません",
        )

    # アクション設定関連の作成
    action_config_service = ActionConfigService()
    result = await action_config_service.create_action_config(
        action_id=action_id,
        config_type="discord",
        config_id=config_id,
    )

    return result


@router.get("/{config_id}", response_model=Dict[str, Any])
async def get_discord_config(config_id: int, current_user: User = Depends(get_current_user)):
    """Discord設定の詳細を取得するエンドポイント

    Args:
        config_id (int): Discord設定ID
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        Dict[str, Any]: Discord設定の詳細
    """
    discord_config_service = DiscordConfigService()
    discord_config = await discord_config_service.get_discord_config(config_id)

    if not discord_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discord設定が見つかりません",
        )

    return discord_config


@router.get("/", response_model=List[Dict[str, Any]])
async def list_discord_configs(
    catch_type: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
):
    """Discord設定の一覧を取得するエンドポイント

    Args:
        catch_type (Optional[str], optional): 取得タイプ。デフォルトはNone
        limit (int, optional): 取得件数。デフォルトは10
        offset (int, optional): オフセット。デフォルトは0
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        List[Dict[str, Any]]: Discord設定のリスト
    """
    discord_config_service = DiscordConfigService()
    discord_configs = await discord_config_service.list_discord_configs(
        catch_type=catch_type,
        limit=limit,
        offset=offset,
    )

    return discord_configs


@router.put("/{config_id}", response_model=Dict[str, Any])
async def update_discord_config(
    config_id: int,
    name: Optional[str] = None,
    catch_type: Optional[str] = None,
    catch_value: Optional[str] = None,
    message_type: Optional[str] = None,
    response_format: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Discord設定を更新するエンドポイント

    Args:
        config_id (int): Discord設定ID
        name (Optional[str], optional): 設定名。デフォルトはNone
        catch_type (Optional[str], optional): 取得タイプ。デフォルトはNone
        catch_value (Optional[str], optional): 取得対象。デフォルトはNone
        message_type (Optional[str], optional): メッセージ収集戦略。デフォルトはNone
        response_format (Optional[str], optional): レスポンス形式。デフォルトはNone
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        Dict[str, Any]: 更新されたDiscord設定
    """
    # 管理者のみDiscord設定を更新可能
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Discord設定を更新する権限がありません",
        )

    discord_config_service = DiscordConfigService()
    updated_config = await discord_config_service.update_discord_config(
        config_id=config_id,
        name=name,
        catch_type=catch_type,
        catch_value=catch_value,
        message_type=message_type,
        response_format=response_format,
    )

    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discord設定が見つかりません",
        )

    return updated_config


@router.delete("/{config_id}", response_model=Dict[str, Any])
async def delete_discord_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
):
    """Discord設定を削除するエンドポイント

    Args:
        config_id (int): Discord設定ID
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        Dict[str, Any]: 削除結果
    """
    # 管理者のみDiscord設定を削除可能
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Discord設定を削除する権限がありません",
        )

    discord_config_service = DiscordConfigService()
    success = await discord_config_service.delete_discord_config(config_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discord設定が見つかりません",
        )

    return {"success": True, "message": "Discord設定を削除しました"}
