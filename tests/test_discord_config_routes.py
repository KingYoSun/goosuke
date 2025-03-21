"""
Discord設定ルートのテストモジュール

このモジュールは、Discord設定に関連するAPIエンドポイントのテストを提供します。
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_discord_config(client: AsyncClient, test_admin):
    """Discord設定作成エンドポイントのテスト"""
    # DiscordConfigServiceのモック
    with patch("api.routes.discord_config.DiscordConfigService") as mock_service_class:
        # モックの設定
        mock_service = AsyncMock()
        mock_service.create_discord_config.return_value = {
            "id": 1,
            "name": "テスト設定",
            "catch_type": "reaction",
            "catch_value": "✅",
            "message_type": "single",
            "response_format": "reply",
            "created_at": "2025-03-21T10:00:00+09:00",
        }
        mock_service_class.return_value = mock_service

        # 管理者としてログイン
        login_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "adminpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]

        # Discord設定作成リクエスト
        response = await client.post(
            "/api/v1/discord-configs/",
            params={
                "name": "テスト設定",
                "catch_type": "reaction",
                "catch_value": "✅",
                "message_type": "single",
                "response_format": "reply",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "テスト設定"
        assert data["catch_type"] == "reaction"
        assert data["catch_value"] == "✅"
        assert data["message_type"] == "single"
        assert data["response_format"] == "reply"

        # create_discord_configが正しく呼ばれたことを検証
        mock_service.create_discord_config.assert_called_once_with(
            name="テスト設定",
            catch_type="reaction",
            catch_value="✅",
            message_type="single",
            response_format="reply",
        )


@pytest.mark.asyncio
async def test_create_discord_config_unauthorized(client: AsyncClient, test_user):
    """非管理者によるDiscord設定作成エンドポイントのテスト"""
    # 通常ユーザーとしてログイン
    login_response = await client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login_response.json()["access_token"]

    # Discord設定作成リクエスト
    response = await client.post(
        "/api/v1/discord-configs/",
        params={
            "name": "テスト設定",
            "catch_type": "reaction",
            "catch_value": "✅",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # 検証
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_link_action_to_discord_config(client: AsyncClient, test_admin):
    """Discord設定とアクションの関連付けエンドポイントのテスト"""
    # DiscordConfigServiceとActionConfigServiceのモック
    with (
        patch("api.routes.discord_config.DiscordConfigService") as mock_discord_service_class,
        patch("api.routes.discord_config.ActionConfigService") as mock_action_config_service_class,
    ):
        # モックの設定
        mock_discord_service = AsyncMock()
        mock_discord_service.get_discord_config.return_value = {
            "id": 1,
            "name": "テスト設定",
            "catch_type": "reaction",
            "catch_value": "✅",
        }
        mock_discord_service_class.return_value = mock_discord_service

        mock_action_config_service = AsyncMock()
        mock_action_config_service.create_action_config.return_value = {
            "id": 1,
            "action_id": 2,
            "config_type": "discord",
            "config_id": 1,
            "created_at": "2025-03-21T10:00:00+09:00",
        }
        mock_action_config_service_class.return_value = mock_action_config_service

        # 管理者としてログイン
        login_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "adminpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]

        # 関連付けリクエスト
        response = await client.post(
            "/api/v1/discord-configs/1/link-action",
            params={"action_id": 2},
            headers={"Authorization": f"Bearer {token}"},
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["action_id"] == 2
        assert data["config_type"] == "discord"
        assert data["config_id"] == 1

        # get_discord_configが正しく呼ばれたことを検証
        mock_discord_service.get_discord_config.assert_called_once_with(1)

        # create_action_configが正しく呼ばれたことを検証
        mock_action_config_service.create_action_config.assert_called_once_with(
            action_id=2,
            config_type="discord",
            config_id=1,
        )


@pytest.mark.asyncio
async def test_get_discord_config(client: AsyncClient, test_user):
    """Discord設定取得エンドポイントのテスト"""
    # DiscordConfigServiceのモック
    with patch("api.routes.discord_config.DiscordConfigService") as mock_service_class:
        # モックの設定
        mock_service = AsyncMock()
        mock_service.get_discord_config.return_value = {
            "id": 1,
            "name": "テスト設定",
            "catch_type": "reaction",
            "catch_value": "✅",
            "message_type": "single",
            "response_format": "reply",
            "created_at": "2025-03-21T10:00:00+09:00",
        }
        mock_service_class.return_value = mock_service

        # ユーザーとしてログイン
        login_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "testuser", "password": "password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]

        # Discord設定取得リクエスト
        response = await client.get(
            "/api/v1/discord-configs/1",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "テスト設定"
        assert data["catch_type"] == "reaction"
        assert data["catch_value"] == "✅"

        # get_discord_configが正しく呼ばれたことを検証
        mock_service.get_discord_config.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_discord_config_not_found(client: AsyncClient, test_user):
    """存在しないDiscord設定取得エンドポイントのテスト"""
    # DiscordConfigServiceのモック
    with patch("api.routes.discord_config.DiscordConfigService") as mock_service_class:
        # モックの設定
        mock_service = AsyncMock()
        mock_service.get_discord_config.return_value = None
        mock_service_class.return_value = mock_service

        # ユーザーとしてログイン
        login_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "testuser", "password": "password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]

        # 存在しないDiscord設定取得リクエスト
        response = await client.get(
            "/api/v1/discord-configs/999",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 検証
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "見つかりません" in data["detail"]


@pytest.mark.asyncio
async def test_list_discord_configs(client: AsyncClient, test_user):
    """Discord設定一覧取得エンドポイントのテスト"""
    # DiscordConfigServiceのモック
    with patch("api.routes.discord_config.DiscordConfigService") as mock_service_class:
        # モックの設定
        mock_service = AsyncMock()
        mock_service.list_discord_configs.return_value = [
            {
                "id": 1,
                "name": "設定1",
                "catch_type": "reaction",
                "catch_value": "✅",
                "created_at": "2025-03-21T10:00:00+09:00",
            },
            {
                "id": 2,
                "name": "設定2",
                "catch_type": "text",
                "catch_value": "!test",
                "created_at": "2025-03-21T11:00:00+09:00",
            },
        ]
        mock_service_class.return_value = mock_service

        # ユーザーとしてログイン
        login_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "testuser", "password": "password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]

        # Discord設定一覧取得リクエスト
        response = await client.get(
            "/api/v1/discord-configs/",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[0]["name"] == "設定1"
        assert data[1]["id"] == 2
        assert data[1]["name"] == "設定2"

        # list_discord_configsが正しく呼ばれたことを検証
        mock_service.list_discord_configs.assert_called_once_with(
            catch_type=None,
            limit=10,
            offset=0,
        )


@pytest.mark.asyncio
async def test_update_discord_config(client: AsyncClient, test_admin):
    """Discord設定更新エンドポイントのテスト"""
    # DiscordConfigServiceのモック
    with patch("api.routes.discord_config.DiscordConfigService") as mock_service_class:
        # モックの設定
        mock_service = AsyncMock()
        mock_service.update_discord_config.return_value = {
            "id": 1,
            "name": "更新後の設定",
            "catch_type": "text",
            "catch_value": "!updated",
            "message_type": "thread",
            "response_format": "channel",
            "updated_at": "2025-03-21T12:00:00+09:00",
        }
        mock_service_class.return_value = mock_service

        # 管理者としてログイン
        login_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "adminpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]

        # Discord設定更新リクエスト
        response = await client.put(
            "/api/v1/discord-configs/1",
            params={
                "name": "更新後の設定",
                "catch_type": "text",
                "catch_value": "!updated",
                "message_type": "thread",
                "response_format": "channel",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "更新後の設定"
        assert data["catch_type"] == "text"
        assert data["catch_value"] == "!updated"
        assert data["message_type"] == "thread"
        assert data["response_format"] == "channel"

        # update_discord_configが正しく呼ばれたことを検証
        mock_service.update_discord_config.assert_called_once_with(
            config_id=1,
            name="更新後の設定",
            catch_type="text",
            catch_value="!updated",
            message_type="thread",
            response_format="channel",
        )


@pytest.mark.asyncio
async def test_delete_discord_config(client: AsyncClient, test_admin):
    """Discord設定削除エンドポイントのテスト"""
    # DiscordConfigServiceのモック
    with patch("api.routes.discord_config.DiscordConfigService") as mock_service_class:
        # モックの設定
        mock_service = AsyncMock()
        mock_service.delete_discord_config.return_value = True
        mock_service_class.return_value = mock_service

        # 管理者としてログイン
        login_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "adminpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]

        # Discord設定削除リクエスト
        response = await client.delete(
            "/api/v1/discord-configs/1",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "削除しました" in data["message"]

        # delete_discord_configが正しく呼ばれたことを検証
        mock_service.delete_discord_config.assert_called_once_with(1)
