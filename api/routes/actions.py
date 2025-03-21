"""
アクションルートモジュール

このモジュールは、アクションに関連するAPIエンドポイントを提供します。
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..auth.dependencies import get_current_user, get_optional_user
from ..models.user import User
from ..services.action_service import ActionService

router = APIRouter(prefix="/api/v1/actions", tags=["アクション"])


@router.post("/", response_model=Dict[str, Any])
async def create_action(
    name: str,
    action_type: str,
    task_template_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
):
    """アクションを作成するエンドポイント

    Args:
        name (str): アクション名
        action_type (str): アクションタイプ（'api', 'discord', 'slack', 'webhook'）
        task_template_id (Optional[int], optional): 関連するタスクテンプレートのID。デフォルトはNone
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        Dict[str, Any]: 作成されたアクション
    """
    # 管理者のみアクションを作成可能
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アクションを作成する権限がありません",
        )

    action_service = ActionService()
    result = await action_service.create_action(
        name=name,
        action_type=action_type,
        task_template_id=task_template_id,
    )

    return result


@router.get("/{action_id}", response_model=Dict[str, Any])
async def get_action(action_id: int, current_user: User = Depends(get_current_user)):
    """アクションの詳細を取得するエンドポイント

    Args:
        action_id (int): アクションID
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        Dict[str, Any]: アクションの詳細

    Raises:
        HTTPException: アクションが見つからない場合
    """
    action_service = ActionService()
    action = await action_service.get_action(action_id)

    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="アクションが見つかりません")

    # 管理者のみアクションの詳細を取得可能
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このアクションにアクセスする権限がありません",
        )

    return action


@router.get("/", response_model=List[Dict[str, Any]])
async def list_actions(
    action_type: Optional[str] = None,
    is_enabled: Optional[bool] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
):
    """アクションの一覧を取得するエンドポイント

    Args:
        action_type (Optional[str], optional): アクションタイプ。デフォルトはNone
        is_enabled (Optional[bool], optional): 有効かどうか。デフォルトはNone
        limit (int, optional): 取得件数。デフォルトは10
        offset (int, optional): オフセット。デフォルトは0
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        List[Dict[str, Any]]: アクションのリスト
    """
    # 管理者のみアクションの一覧を取得可能
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アクションの一覧を取得する権限がありません",
        )

    action_service = ActionService()
    actions = await action_service.list_actions(
        action_type=action_type, is_enabled=is_enabled, limit=limit, offset=offset
    )

    return actions


@router.post("/{action_id}/trigger", response_model=Dict[str, Any])
async def trigger_action(
    action_id: int,
    input_data: Dict[str, Any],
    current_user: User = Depends(get_optional_user),
):
    """アクションをトリガーするエンドポイント

    Args:
        action_id (int): アクションID
        input_data (Dict[str, Any]): 入力データ
        current_user (User, optional): 現在のユーザー。Depends(get_optional_user)から取得

    Returns:
        Dict[str, Any]: 実行結果
    """
    action_service = ActionService()
    result = await action_service.trigger_action(action_id=action_id, input_data=input_data)

    return result


@router.put("/{action_id}/enable", response_model=Dict[str, Any])
async def enable_action(action_id: int, current_user: User = Depends(get_current_user)):
    """アクションを有効化するエンドポイント

    Args:
        action_id (int): アクションID
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        Dict[str, Any]: 更新されたアクション
    """
    # 管理者のみアクションを有効化可能
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アクションを有効化する権限がありません",
        )

    # 実装は省略（ActionServiceに対応するメソッドを追加する必要があります）
    return {"message": "アクションを有効化しました"}


@router.put("/{action_id}/disable", response_model=Dict[str, Any])
async def disable_action(action_id: int, current_user: User = Depends(get_current_user)):
    """アクションを無効化するエンドポイント

    Args:
        action_id (int): アクションID
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        Dict[str, Any]: 更新されたアクション
    """
    # 管理者のみアクションを無効化可能
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アクションを無効化する権限がありません",
        )

    # 実装は省略（ActionServiceに対応するメソッドを追加する必要があります）
    return {"message": "アクションを無効化しました"}
