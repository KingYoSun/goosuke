"""
Discord連携ルートのテストモジュール

このモジュールは、Discord連携に関連するAPIエンドポイントのテストを提供します。
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_start_discord_bot(client: AsyncClient, test_admin):
    """Discord Bot起動エンドポイントのテスト"""
    # DiscordBotManagerのモック
    with patch("api.routes.discord.DiscordBotManager") as mock_service_class:
        # モックの設定
        mock_service = AsyncMock()
        mock_service.start_bot.return_value = {
            "success": True,
            "message": "Discord Botを起動しています",
        }
        mock_service_class.return_value = mock_service

        # 管理者としてログイン
        login_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "adminpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]

        # Bot起動リクエスト
        response = await client.post("/api/v1/discord/bot/start", headers={"Authorization": f"Bearer {token}"})

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "起動しています" in data["message"]

        # start_botが正しく呼ばれたことを検証
        mock_service.start_bot.assert_called_once()


@pytest.mark.asyncio
async def test_start_discord_bot_unauthorized(client: AsyncClient, test_user):
    """非管理者によるDiscord Bot起動エンドポイントのテスト"""
    # 通常ユーザーとしてログイン
    login_response = await client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login_response.json()["access_token"]

    # Bot起動リクエスト
    response = await client.post("/api/v1/discord/bot/start", headers={"Authorization": f"Bearer {token}"})

    # 検証
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_stop_discord_bot(client: AsyncClient, test_admin):
    """Discord Bot停止エンドポイントのテスト"""
    # DiscordBotManagerのモック
    with patch("api.routes.discord.DiscordBotManager") as mock_service_class:
        # モックの設定
        mock_service = AsyncMock()
        mock_service.stop_bot.return_value = {
            "success": True,
            "message": "Discord Botを停止しました",
        }
        mock_service_class.return_value = mock_service

        # 管理者としてログイン
        login_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "adminpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]

        # Bot停止リクエスト
        response = await client.post("/api/v1/discord/bot/stop", headers={"Authorization": f"Bearer {token}"})

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "停止しました" in data["message"]

        # stop_botが正しく呼ばれたことを検証
        mock_service.stop_bot.assert_called_once()


@pytest.mark.asyncio
async def test_get_discord_bot_status(client: AsyncClient, test_user):
    """Discord Botステータス取得エンドポイントのテスト"""
    # DiscordBotManagerのモック
    with patch("api.routes.discord.DiscordBotManager") as mock_service_class:
        # モックの設定
        mock_service = AsyncMock()
        mock_service.get_status.return_value = {
            "is_running": True,
            "bot_user": "TestBot#1234",
        }
        mock_service_class.return_value = mock_service

        # 通常ユーザーとしてログイン
        login_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "testuser", "password": "password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]

        # ステータス取得リクエスト
        response = await client.get("/api/v1/discord/bot/status", headers={"Authorization": f"Bearer {token}"})

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["is_running"] is True
        assert data["bot_user"] == "TestBot#1234"

        # get_statusが正しく呼ばれたことを検証
        mock_service.get_status.assert_called_once()
