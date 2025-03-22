"""
拡張機能ルートモジュール

このモジュールは、Goose拡張機能に関連するAPIエンドポイントを提供します。
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel

from ..auth.dependencies import get_current_active_admin, get_current_user
from ..models.user import User
from ..services.extension_service import ExtensionService

router = APIRouter(prefix="/api/v1/extensions", tags=["拡張機能"])


class ExtensionBase(BaseModel):
    """拡張機能基本モデル"""

    name: str
    description: str


class ExtensionCreate(ExtensionBase):
    """拡張機能作成モデル"""

    type: str  # builtin, stdio, sse
    enabled: bool = True
    # stdio タイプの場合のフィールド
    cmd: Optional[str] = None
    args: Optional[List[str]] = None
    timeout: Optional[int] = None
    envs: Optional[Dict[str, str]] = None


class ExtensionResponse(ExtensionBase):
    """拡張機能レスポンスモデル"""

    id: int
    enabled: bool
    type: str
    version: Optional[str] = None
    # stdio タイプの場合のフィールド
    cmd: Optional[str] = None
    args: Optional[List[str]] = None
    timeout: Optional[int] = None
    envs: Optional[Dict[str, str]] = None


class ExtensionUpdate(BaseModel):
    """拡張機能更新モデル"""

    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    type: Optional[str] = None
    cmd: Optional[str] = None
    args: Optional[List[str]] = None
    timeout: Optional[int] = None
    envs: Optional[Dict[str, str]] = None


@router.get("/", response_model=List[ExtensionResponse])
async def list_extensions(current_user: User = Depends(get_current_user)):
    """利用可能な拡張機能の一覧を取得するエンドポイント

    Args:
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        List[ExtensionResponse]: 拡張機能のリスト
    """
    extension_service = ExtensionService()
    return await extension_service.list_extensions()


@router.post("/", response_model=ExtensionResponse, status_code=status.HTTP_201_CREATED)
async def add_extension(extension: ExtensionCreate, current_user: User = Depends(get_current_active_admin)):
    """新しい拡張機能を追加するエンドポイント

    Args:
        extension (ExtensionCreate): 拡張機能データ
        current_user (User, optional): 現在の管理者ユーザー。Depends(get_current_active_admin)から取得

    Returns:
        ExtensionResponse: 追加された拡張機能
    """
    extension_service = ExtensionService()
    return await extension_service.add_extension(extension)


@router.get("/{extension_id}", response_model=ExtensionResponse)
async def get_extension(extension_id: int, current_user: User = Depends(get_current_user)):
    """特定の拡張機能の詳細を取得するエンドポイント

    Args:
        extension_id (int): 拡張機能ID
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得

    Returns:
        ExtensionResponse: 拡張機能の詳細

    Raises:
        HTTPException: 拡張機能が見つからない場合
    """
    extension_service = ExtensionService()
    extension = await extension_service.get_extension(extension_id)

    if not extension:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="拡張機能が見つかりません")

    return extension


@router.patch("/{extension_id}", response_model=ExtensionResponse)
async def update_extension(
    extension_id: int,
    extension_update: ExtensionUpdate,
    current_user: User = Depends(get_current_active_admin),
):
    """拡張機能の有効/無効や設定を更新するエンドポイント

    Args:
        extension_id (int): 拡張機能ID
        extension_update (ExtensionUpdate): 更新データ
        current_user (User, optional): 現在の管理者ユーザー。Depends(get_current_active_admin)から取得

    Returns:
        ExtensionResponse: 更新された拡張機能

    Raises:
        HTTPException: 拡張機能が見つからない場合
    """
    extension_service = ExtensionService()
    extension = await extension_service.update_extension(extension_id, extension_update)

    if not extension:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="拡張機能が見つかりません")

    return extension


@router.delete("/{extension_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_extension(extension_id: int, current_user: User = Depends(get_current_active_admin)):
    """拡張機能を削除するエンドポイント

    Args:
        extension_id (int): 拡張機能ID
        current_user (User, optional): 現在の管理者ユーザー。Depends(get_current_active_admin)から取得

    Raises:
        HTTPException: 拡張機能が見つからない場合
    """
    extension_service = ExtensionService()
    success = await extension_service.remove_extension(extension_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="拡張機能が見つかりません")

    return None


@router.post("/install", response_model=Dict[str, Any])
async def install_extension(
    name: str = Body(...),
    url: str = Body(...),
    description: str = Body(""),
    current_user: User = Depends(get_current_active_admin),
):
    """URLから拡張機能をインストールするエンドポイント

    Args:
        name (str): 拡張機能名
        url (str): 拡張機能のURL
        description (str, optional): 説明。デフォルトは空文字
        current_user (User, optional): 現在の管理者ユーザー。Depends(get_current_active_admin)から取得

    Returns:
        Dict[str, Any]: インストール結果
    """
    extension_service = ExtensionService()
    result = await extension_service.install_extension_from_url(name, url, description)

    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])

    return result
