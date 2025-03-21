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


# タスクテンプレート関連のエンドポイント
@router.post("/templates/", response_model=Dict[str, Any])
async def create_task_template(
    name: str,
    prompt: str,
    task_type: str = "general",
    description: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """タスクテンプレートを作成するエンドポイント

    Args:
        name (str): テンプレート名
        prompt (str): プロンプト
        task_type (str, optional): タスクタイプ。デフォルトは"general"
        description (Optional[str], optional): テンプレートの説明。デフォルトはNone
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        Dict[str, Any]: 作成されたタスクテンプレート
    """
    task_service = TaskService()

    # タスクテンプレートの作成
    result = await task_service.create_task_template(
        task_type=task_type,
        prompt=prompt,
        name=name,
        user_id=current_user.id,
        description=description,
    )

    return result


@router.get("/templates/{template_id}", response_model=Dict[str, Any])
async def get_task_template(template_id: int, current_user: User = Depends(get_current_user)):
    """タスクテンプレートの詳細を取得するエンドポイント

    Args:
        template_id (int): タスクテンプレートID
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        Dict[str, Any]: タスクテンプレートの詳細

    Raises:
        HTTPException: タスクテンプレートが見つからない場合
    """
    task_service = TaskService()
    template = await task_service.get_task_template(template_id)

    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="タスクテンプレートが見つかりません")

    # 管理者でない場合は、自分のタスクテンプレートのみ取得可能
    if not current_user.is_admin and template["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このタスクテンプレートにアクセスする権限がありません",
        )

    return template


@router.get("/templates/", response_model=List[Dict[str, Any]])
async def list_task_templates(
    user_id: Optional[int] = None,
    task_type: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
):
    """タスクテンプレートの一覧を取得するエンドポイント

    Args:
        user_id (Optional[int], optional): ユーザーID。デフォルトはNone
        task_type (Optional[str], optional): タスクタイプ。デフォルトはNone
        limit (int, optional): 取得件数。デフォルトは10
        offset (int, optional): オフセット。デフォルトは0
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        List[Dict[str, Any]]: タスクテンプレートのリスト
    """
    task_service = TaskService()

    # 管理者でない場合は、自分のタスクテンプレートのみ取得可能
    if not current_user.is_admin:
        user_id = current_user.id

    templates = await task_service.list_task_templates(user_id=user_id, task_type=task_type, limit=limit, offset=offset)

    return templates


# タスク実行関連のエンドポイント
@router.post("/executions/", response_model=Dict[str, Any])
async def execute_task(
    template_id: int,
    context: Optional[Dict[str, Any]] = None,
    extension_ids: Optional[List[int]] = None,
    current_user: User = Depends(get_optional_user),
):
    """タスクを実行するエンドポイント

    Args:
        template_id (int): タスクテンプレートID
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
    result = await task_service.execute_task(
        template_id=template_id,
        context=context,
        user_id=current_user.id if current_user else None,
        extensions=extensions,
    )

    return result


@router.get("/executions/{execution_id}", response_model=Dict[str, Any])
async def get_task_execution(execution_id: int, current_user: User = Depends(get_current_user)):
    """タスク実行ログの詳細を取得するエンドポイント

    Args:
        execution_id (int): タスク実行ログID
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        Dict[str, Any]: タスク実行ログの詳細

    Raises:
        HTTPException: タスク実行ログが見つからない場合
    """
    task_service = TaskService()
    execution = await task_service.get_task_execution(execution_id)

    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="タスク実行ログが見つかりません")

    # 管理者でない場合は、自分のタスク実行ログのみ取得可能
    if not current_user.is_admin and execution["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このタスク実行ログにアクセスする権限がありません",
        )

    return execution


@router.get("/executions/", response_model=List[Dict[str, Any]])
async def list_task_executions(
    template_id: Optional[int] = None,
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
):
    """タスク実行ログの一覧を取得するエンドポイント

    Args:
        template_id (Optional[int], optional): タスクテンプレートID。デフォルトはNone
        user_id (Optional[int], optional): ユーザーID。デフォルトはNone
        status (Optional[str], optional): ステータス。デフォルトはNone
        limit (int, optional): 取得件数。デフォルトは10
        offset (int, optional): オフセット。デフォルトは0
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        List[Dict[str, Any]]: タスク実行ログのリスト
    """
    task_service = TaskService()

    # 管理者でない場合は、自分のタスク実行ログのみ取得可能
    if not current_user.is_admin:
        user_id = current_user.id

    executions = await task_service.list_task_executions(
        template_id=template_id, user_id=user_id, status=status, limit=limit, offset=offset
    )

    return executions
