"""
設定ルーターモジュール

このモジュールは、設定に関するAPIエンドポイントを提供します。
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..auth.dependencies import get_current_user
from ..services.setting_service import SettingService

# ルーターの作成
router = APIRouter(
    prefix="/api/settings",
    tags=["settings"],
    responses={404: {"description": "Not found"}},
)


# リクエスト・レスポンスモデル
class SettingBase(BaseModel):
    """設定ベースモデル"""

    key: str = Field(..., description="設定キー")
    value: Any = Field(None, description="設定値")
    description: Optional[str] = Field(None, description="説明")
    is_secret: bool = Field(False, description="秘密情報かどうか")


class SettingCreate(SettingBase):
    """設定作成モデル"""


class SettingUpdate(BaseModel):
    """設定更新モデル"""

    key: Optional[str] = Field(None, description="設定キー")
    value: Optional[Any] = Field(None, description="設定値")
    description: Optional[str] = Field(None, description="説明")
    is_secret: Optional[bool] = Field(None, description="秘密情報かどうか")


class SettingResponse(SettingBase):
    """設定レスポンスモデル"""

    id: int = Field(..., description="設定ID")

    class Config:
        """設定"""

        from_attributes = True


# エンドポイント
@router.get("/", response_model=List[SettingResponse])
async def list_settings(current_user: Dict[str, Any] = Depends(get_current_user)):
    """設定一覧を取得

    Args:
        current_user (Dict[str, Any], optional): 現在のユーザー

    Returns:
        List[SettingResponse]: 設定一覧
    """
    setting_service = SettingService()
    return await setting_service.list_settings()


@router.get("/{setting_id}", response_model=SettingResponse)
async def get_setting(setting_id: int, current_user: Dict[str, Any] = Depends(get_current_user)):
    """設定詳細を取得

    Args:
        setting_id (int): 設定ID
        current_user (Dict[str, Any], optional): 現在のユーザー

    Returns:
        SettingResponse: 設定詳細
    """
    setting_service = SettingService()
    setting = await setting_service.get_setting(setting_id)
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="設定が見つかりません")
    return setting


@router.post("/", response_model=SettingResponse, status_code=status.HTTP_201_CREATED)
async def create_setting(setting: SettingCreate, current_user: Dict[str, Any] = Depends(get_current_user)):
    """設定を作成

    Args:
        setting (SettingCreate): 設定データ
        current_user (Dict[str, Any], optional): 現在のユーザー

    Returns:
        SettingResponse: 作成された設定
    """
    setting_service = SettingService()
    return await setting_service.add_setting(setting)


@router.put("/{setting_id}", response_model=SettingResponse)
async def update_setting(
    setting_id: int,
    setting: SettingUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """設定を更新

    Args:
        setting_id (int): 設定ID
        setting (SettingUpdate): 更新データ
        current_user (Dict[str, Any], optional): 現在のユーザー

    Returns:
        SettingResponse: 更新された設定
    """
    setting_service = SettingService()
    updated_setting = await setting_service.update_setting(setting_id, setting)
    if not updated_setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="設定が見つかりません")
    return updated_setting


@router.delete("/{setting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setting(setting_id: int, current_user: Dict[str, Any] = Depends(get_current_user)):
    """設定を削除

    Args:
        setting_id (int): 設定ID
        current_user (Dict[str, Any], optional): 現在のユーザー
    """
    setting_service = SettingService()
    result = await setting_service.remove_setting(setting_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="設定が見つかりません")
