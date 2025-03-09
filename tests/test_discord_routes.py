"""
Discord連携ルートのテストモジュール

このモジュールは、Discord連携に関連するAPIエンドポイントのテストを提供します。
"""

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_start_discord_bot(client: AsyncClient, test_admin):
    """Discord Bot起動エンドポイントのテスト"""
    # DiscordBotServiceのモック
    with patch("api.routes.discord.DiscordBotService") as mock_service_class:
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
    # DiscordBotServiceのモック
    with patch("api.routes.discord.DiscordBotService") as mock_service_class:
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
    # DiscordBotServiceのモック
    with patch("api.routes.discord.DiscordBotService") as mock_service_class:
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


@pytest.mark.asyncio
async def test_handle_discord_webhook_no_secret(client: AsyncClient):
    """シークレットなしのDiscord Webhookエンドポイントのテスト"""
    # 設定のモック
    with (
        patch("api.routes.discord.settings") as mock_settings,
        patch("api.routes.discord.DiscordWebhookService") as mock_service_class,
    ):
        # モックの設定
        mock_settings.DISCORD_WEBHOOK_SECRET = None

        mock_service = AsyncMock()
        mock_service.handle_webhook.return_value = {
            "success": True,
            "message": "Webhookを処理しました",
        }
        mock_service_class.return_value = mock_service

        # Webhookデータ
        webhook_data = {"type": "message", "content": "テストメッセージ"}

        # Webhookリクエスト
        response = await client.post("/api/v1/discord/webhooks", json=webhook_data)

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "処理しました" in data["message"]

        # handle_webhookが正しく呼ばれたことを検証
        mock_service.handle_webhook.assert_called_once_with(webhook_data)


@pytest.mark.asyncio
async def test_handle_discord_webhook_with_secret(client: AsyncClient):
    """シークレット付きのDiscord Webhookエンドポイントのテスト"""
    # 設定のモック
    with (
        patch("api.routes.discord.settings") as mock_settings,
        patch("api.routes.discord.DiscordWebhookService") as mock_service_class,
    ):
        # モックの設定
        mock_settings.DISCORD_WEBHOOK_SECRET = "test_secret"

        mock_service = AsyncMock()
        mock_service.handle_webhook.return_value = {
            "success": True,
            "message": "Webhookを処理しました",
        }
        mock_service_class.return_value = mock_service

        # Webhookデータ
        webhook_data = {"type": "message", "content": "テストメッセージ"}

        # リクエストボディ
        body = json.dumps(webhook_data).encode()

        # 署名を計算
        signature = hmac.new("test_secret".encode(), body, hashlib.sha256).hexdigest()

        # Webhookリクエスト
        response = await client.post(
            "/api/v1/discord/webhooks",
            content=body,
            headers={"Content-Type": "application/json", "X-Signature": signature},
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "処理しました" in data["message"]

        # handle_webhookが正しく呼ばれたことを検証
        mock_service.handle_webhook.assert_called_once()


@pytest.mark.asyncio
async def test_handle_discord_webhook_missing_signature(client: AsyncClient):
    """署名なしのDiscord Webhookエンドポイントのテスト（シークレット必須の場合）"""
    # 設定のモック
    with patch("api.routes.discord.settings") as mock_settings:
        # モックの設定
        mock_settings.DISCORD_WEBHOOK_SECRET = "test_secret"

        # Webhookデータ
        webhook_data = {"type": "message", "content": "テストメッセージ"}

        # Webhookリクエスト（署名なし）
        response = await client.post("/api/v1/discord/webhooks", json=webhook_data)

        # 検証
        assert response.status_code == 401
        data = response.json()
        assert "署名が必要です" in data["detail"]


@pytest.mark.asyncio
async def test_handle_discord_webhook_invalid_signature(client: AsyncClient):
    """無効な署名のDiscord Webhookエンドポイントのテスト"""
    # 設定のモック
    with patch("api.routes.discord.settings") as mock_settings:
        # モックの設定
        mock_settings.DISCORD_WEBHOOK_SECRET = "test_secret"

        # Webhookデータ
        webhook_data = {"type": "message", "content": "テストメッセージ"}

        # Webhookリクエスト（無効な署名）
        response = await client.post(
            "/api/v1/discord/webhooks",
            json=webhook_data,
            headers={"X-Signature": "invalid_signature"},
        )

        # 検証
        assert response.status_code == 401
        data = response.json()
        assert "署名が無効です" in data["detail"]


@pytest.mark.asyncio
async def test_handle_discord_webhook_invalid_json(client: AsyncClient):
    """無効なJSONのDiscord Webhookエンドポイントのテスト"""
    # 設定のモック
    with patch("api.routes.discord.settings") as mock_settings:
        # モックの設定
        mock_settings.DISCORD_WEBHOOK_SECRET = None

        # 無効なJSONデータ
        invalid_json = "{invalid json"

        # Webhookリクエスト
        response = await client.post(
            "/api/v1/discord/webhooks",
            content=invalid_json,
            headers={"Content-Type": "application/json"},
        )

        # 検証
        assert response.status_code == 400
        data = response.json()
        assert "無効なJSONデータです" in data["detail"]
