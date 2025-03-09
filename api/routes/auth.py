"""
認証ルートモジュール

このモジュールは、ユーザー認証に関連するAPIエンドポイントを提供します。
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import create_access_token
from ..database import get_db
from ..services.user_service import UserService

router = APIRouter(prefix="/api/v1/auth", tags=["認証"])


@router.post("/token", response_model=Dict[str, Any])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """アクセストークンを取得するエンドポイント

    Args:
        form_data (OAuth2PasswordRequestForm, optional): OAuth2フォームデータ
        db (AsyncSession, optional): データベースセッション

    Returns:
        Dict[str, Any]: アクセストークン情報

    Raises:
        HTTPException: 認証に失敗した場合
    """
    user_service = UserService()

    async with db as session:
        user = await user_service.authenticate_user(form_data.username, form_data.password, session)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="ユーザー名またはパスワードが正しくありません",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # JWTトークンを生成
        token_data = {"sub": user.username, "user_id": user.id, "is_admin": user.is_admin}
        access_token = create_access_token(token_data)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username,
            "is_admin": user.is_admin,
        }


@router.post("/register", response_model=Dict[str, Any])
async def register_user(username: str, email: str, password: str, db: AsyncSession = Depends(get_db)):
    """新規ユーザー登録エンドポイント

    Args:
        username (str): ユーザー名
        email (str): メールアドレス
        password (str): パスワード
        db (AsyncSession, optional): データベースセッション

    Returns:
        Dict[str, Any]: 登録されたユーザー情報

    Raises:
        HTTPException: ユーザー登録に失敗した場合
    """
    user_service = UserService()

    # 最初のユーザーは管理者として登録
    is_admin = False

    # ユーザー数を確認
    async with db as session:
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        if count == 0:
            is_admin = True

        # ユーザーを作成
        user = await user_service.create_user(
            username=username, email=email, password=password, is_admin=is_admin, db=session
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ユーザー名またはメールアドレスが既に使用されています",
        )

    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "is_admin": user["is_admin"],
        "message": "ユーザーが正常に登録されました",
    }
