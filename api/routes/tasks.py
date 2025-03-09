"""
タスクルートモジュール

このモジュールは、Gooseタスクに関連するAPIエンドポイントを提供します。
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..auth.dependencies import get_current_user, get_optional_user
from ..models.user import User
from ..services.extension_service import ExtensionService
from ..services.task_service import TaskService

router = APIRouter(prefix="/api/v1/tasks", tags=["タスク"])


@router.post("/", response_model=Dict[str, Any])
async def create_task(
    prompt: str,
    task_type: str = "general",
    context: Optional[Dict[str, Any]] = None,
    extension_ids: Optional[List[int]] = None,
    current_user: User = Depends(get_optional_user),
):
    """タスクを作成して実行するエンドポイント

    Args:
        prompt (str): プロンプト
        task_type (str, optional): タスクタイプ。デフォルトは"general"
        context (Optional[Dict[str, Any]], optional): コンテキスト。デフォルトはNone
        extension_ids (Optional[List[int]], optional): 使用する拡張機能のID。デフォルトはNone
        current_user (User, optional): 現在のユーザー。Depends(get_optional_user)から取得

    Returns:
        Dict[str, Any]: 実行結果
    """
    task_service = TaskService()
    extension_service = ExtensionService()

    # 拡張機能の取得
    extensions = []
    if extension_ids:
        for ext_id in extension_ids:
            ext = await extension_service.get_extension(ext_id)
            if ext and ext["enabled"]:
                extensions.append(ext["name"])

    # タスクの実行
    result = await task_service.create_task(
        task_type=task_type,
        prompt=prompt,
        context=context,
        user_id=current_user.id if current_user else None,
        extensions=extensions,
    )

    return result


@router.get("/{task_id}", response_model=Dict[str, Any])
async def get_task(task_id: int, current_user: User = Depends(get_current_user)):
    """タスクの詳細を取得するエンドポイント

    Args:
        task_id (int): タスクID
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        Dict[str, Any]: タスクの詳細

    Raises:
        HTTPException: タスクが見つからない場合
    """
    task_service = TaskService()
    task = await task_service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="タスクが見つかりません")

    # 管理者でない場合は、自分のタスクのみ取得可能
    if not current_user.is_admin and task["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このタスクにアクセスする権限がありません",
        )

    return task


@router.get("/", response_model=List[Dict[str, Any]])
async def list_tasks(
    user_id: Optional[int] = None,
    task_type: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
):
    """タスクの一覧を取得するエンドポイント

    Args:
        user_id (Optional[int], optional): ユーザーID。デフォルトはNone
        task_type (Optional[str], optional): タスクタイプ。デフォルトはNone
        limit (int, optional): 取得件数。デフォルトは10
        offset (int, optional): オフセット。デフォルトは0
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        List[Dict[str, Any]]: タスクのリスト
    """
    task_service = TaskService()

    # 管理者でない場合は、自分のタスクのみ取得可能
    if not current_user.is_admin:
        user_id = current_user.id

    tasks = await task_service.list_tasks(user_id=user_id, task_type=task_type, limit=limit, offset=offset)

    return tasks
