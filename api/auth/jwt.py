"""
JWT認証モジュール

このモジュールは、JWTトークンの生成と検証を行う機能を提供します。
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel

from ..config import settings


class TokenData(BaseModel):
    """トークンデータモデル"""

    username: Optional[str] = None
    user_id: Optional[int] = None
    is_admin: Optional[bool] = False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """アクセストークンを作成する関数
    Args:
        data (Dict[str, Any]): トークンに含めるデータ
        expires_delta (Optional[timedelta], optional): 有効期限。デフォルトはNone
    Returns:
        str: 生成されたJWTトークン
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """トークンをデコードする関数
    Args:
        token (str): JWTトークン
    Returns:
        TokenData: デコードされたトークンデータ
    Raises:
        HTTPException: トークンが無効な場合
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username = str(payload.get("sub")) if payload.get("sub") is not None else None
        user_id = int(payload.get("user_id")) if payload.get("user_id") is not None else None
        is_admin = bool(payload.get("is_admin", False))

        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return TokenData(username=username, user_id=user_id, is_admin=is_admin)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
