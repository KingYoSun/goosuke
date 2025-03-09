"""
認証依存関係モジュール

このモジュールは、FastAPIのエンドポイントで使用する認証依存関係を提供します。
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_db
from ..models.user import User
from .jwt import decode_token

# OAuth2のトークン取得エンドポイント
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    """現在のユーザーを取得する依存関係
    Args:
        token (str, optional): JWTトークン。Depends(oauth2_scheme)から取得
        db (AsyncSession, optional): データベースセッション。Depends(get_db)から取得
    Returns:
        User: 現在のユーザーオブジェクト
    Raises:
        HTTPException: ユーザーが見つからない場合
    """
    token_data = decode_token(token)

    # ユーザーをデータベースから取得
    result = await db.execute(select(User).where(User.username == token_data.username))
    user = result.scalars().first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """現在の管理者ユーザーを取得する依存関係
    Args:
        current_user (User, optional): 現在のユーザー。Depends(get_current_user)から取得
    Returns:
        User: 現在の管理者ユーザーオブジェクト
    Raises:
        HTTPException: ユーザーが管理者でない場合
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return current_user


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """オプションのユーザーを取得する依存関係
    トークンが提供されない場合はNoneを返します。
    Args:
        token (Optional[str], optional): JWTトークン。Depends(oauth2_scheme)から取得
        db (AsyncSession, optional): データベースセッション。Depends(get_db)から取得
    Returns:
        Optional[User]: ユーザーオブジェクトまたはNone
    """
    if token is None:
        return None

    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None
