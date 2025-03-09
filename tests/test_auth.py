"""
認証機能のテストモジュール

このモジュールは、認証機能のテストを提供します。
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import User

pytestmark = pytest.mark.asyncio


async def test_login(client: AsyncClient, test_user: User):
    """ログインのテスト"""
    # ログインリクエスト
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    # レスポンスの検証
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["username"] == "testuser"


async def test_login_invalid_credentials(client: AsyncClient, test_user: User):
    """無効な認証情報でのログインのテスト"""
    # 無効なパスワードでログインリクエスト
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    # レスポンスの検証
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


async def test_register_user(client: AsyncClient, db_session: AsyncSession):
    """ユーザー登録のテスト"""
    # ユーザー登録リクエスト
    response = await client.post(
        "/api/v1/auth/register",
        params={
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpassword",
        },
    )

    # レスポンスの検証
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert "id" in data

    # データベースの検証
    result = await db_session.execute(text("SELECT COUNT(*) FROM users WHERE username = 'newuser'"))
    count = result.scalar()
    assert count == 1


async def test_register_duplicate_username(client: AsyncClient, test_user: User):
    """重複ユーザー名での登録のテスト"""
    # 既存のユーザー名で登録リクエスト
    response = await client.post(
        "/api/v1/auth/register",
        params={
            "username": "testuser",
            "email": "another@example.com",
            "password": "password",
        },
    )

    # レスポンスの検証
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
