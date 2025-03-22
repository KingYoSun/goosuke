"""
拡張機能ルートのテストモジュール

このモジュールは、拡張機能に関連するAPIエンドポイントのテストを提供します。
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_extensions(client: AsyncClient, test_user):
    """拡張機能一覧取得エンドポイントのテスト"""
    # ExtensionServiceのモック
    with patch("api.routes.extensions.ExtensionService") as mock_service_class:
        # モックの設定
        mock_service = AsyncMock()
        mock_service.list_extensions.return_value = [
            {
                "id": 1,
                "name": "拡張機能1",
                "description": "テスト拡張機能1",
                "enabled": True,
                "type": "stdio",
                "cmd": "python",
                "args": ["-m", "extension1"],
                "timeout": 300,
                "envs": {"ENV1": "value1"},
            },
            {
                "id": 2,
                "name": "拡張機能2",
                "description": "テスト拡張機能2",
                "enabled": False,
                "type": "builtin",
                "cmd": None,
                "args": None,
                "timeout": None,
                "envs": None,
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

        # 拡張機能一覧取得リクエスト
        response = await client.get(
            "/api/v1/extensions/",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[0]["name"] == "拡張機能1"
        assert data[0]["type"] == "stdio"
        assert data[1]["id"] == 2
        assert data[1]["name"] == "拡張機能2"
        assert data[1]["type"] == "builtin"

        # list_extensionsが正しく呼ばれたことを検証
        mock_service.list_extensions.assert_called_once()


@pytest.mark.asyncio
async def test_add_extension(client: AsyncClient, test_admin):
    """拡張機能追加エンドポイントのテスト"""
    # ExtensionServiceのモック
    with patch("api.routes.extensions.ExtensionService") as mock_service_class:
        # モックの設定
        mock_service = AsyncMock()
        mock_service.add_extension.return_value = {
            "id": 1,
            "name": "新規拡張機能",
            "description": "新しく追加された拡張機能",
            "enabled": True,
            "type": "stdio",
            "cmd": "node",
            "args": ["index.js"],
            "timeout": 600,
            "envs": {"NODE_ENV": "development"},
        }
        mock_service_class.return_value = mock_service

        # 管理者としてログイン
        login_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "adminpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]

        # 拡張機能追加リクエスト
        response = await client.post(
            "/api/v1/extensions/",
            json={
                "name": "新規拡張機能",
                "description": "新しく追加された拡張機能",
                "type": "stdio",
                "enabled": True,
                "cmd": "node",
                "args": ["index.js"],
                "timeout": 600,
                "envs": {"NODE_ENV": "development"},
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # 検証
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "新規拡張機能"
        assert data["description"] == "新しく追加された拡張機能"
        assert data["enabled"] is True
        assert data["type"] == "stdio"
        assert data["cmd"] == "node"
        assert data["args"] == ["index.js"]
        assert data["timeout"] == 600
        assert data["envs"] == {"NODE_ENV": "development"}

        # add_extensionが正しく呼ばれたことを検証
        mock_service.add_extension.assert_called_once()


@pytest.mark.asyncio
async def test_add_extension_unauthorized(client: AsyncClient, test_user):
    """非管理者による拡張機能追加エンドポイントのテスト"""
    # 通常ユーザーとしてログイン
    login_response = await client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login_response.json()["access_token"]

    # 拡張機能追加リクエスト
    response = await client.post(
        "/api/v1/extensions/",
        json={
            "name": "新規拡張機能",
            "description": "新しく追加された拡張機能",
            "type": "stdio",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # 検証
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_extension(client: AsyncClient, test_user):
    """特定の拡張機能取得エンドポイントのテスト"""
    # ExtensionServiceのモック
    with patch("api.routes.extensions.ExtensionService") as mock_service_class:
        # モックの設定
        mock_service = AsyncMock()
        mock_service.get_extension.return_value = {
            "id": 1,
            "name": "テスト拡張機能",
            "description": "テスト用の拡張機能",
            "enabled": True,
            "type": "stdio",
            "cmd": "python",
            "args": ["-m", "test_extension"],
            "timeout": 300,
            "envs": {"TEST_ENV": "test_value"},
        }
        mock_service_class.return_value = mock_service

        # ユーザーとしてログイン
        login_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "testuser", "password": "password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]

        # 拡張機能取得リクエスト
        response = await client.get(
            "/api/v1/extensions/1",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "テスト拡張機能"
        assert data["description"] == "テスト用の拡張機能"
        assert data["enabled"] is True
        assert data["type"] == "stdio"
        assert data["cmd"] == "python"
        assert data["args"] == ["-m", "test_extension"]
        assert data["timeout"] == 300
        assert data["envs"] == {"TEST_ENV": "test_value"}

        # get_extensionが正しく呼ばれたことを検証
        mock_service.get_extension.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_extension_not_found(client: AsyncClient, test_user):
    """存在しない拡張機能取得エンドポイントのテスト"""
    # ExtensionServiceのモック
    with patch("api.routes.extensions.ExtensionService") as mock_service_class:
        # モックの設定
        mock_service = AsyncMock()
        mock_service.get_extension.return_value = None
        mock_service_class.return_value = mock_service

        # ユーザーとしてログイン
        login_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "testuser", "password": "password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]

        # 存在しない拡張機能取得リクエスト
        response = await client.get(
            "/api/v1/extensions/999",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 検証
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "見つかりません" in data["detail"]

        # get_extensionが正しく呼ばれたことを検証
        mock_service.get_extension.assert_called_once_with(999)


@pytest.mark.asyncio
async def test_update_extension(client: AsyncClient, test_admin):
    """拡張機能更新エンドポイントのテスト"""
    # ExtensionServiceのモック
    with patch("api.routes.extensions.ExtensionService") as mock_service_class:
        # モックの設定
        mock_service = AsyncMock()
        mock_service.update_extension.return_value = {
            "id": 1,
            "name": "更新後の拡張機能",
            "description": "更新後の説明",
            "enabled": False,
            "type": "builtin",
            "cmd": "node",
            "args": ["index.js"],
            "timeout": 600,
            "envs": {"NODE_ENV": "production"},
        }
        mock_service_class.return_value = mock_service

        # 管理者としてログイン
        login_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "adminpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]

        # 拡張機能更新リクエスト
        response = await client.patch(
            "/api/v1/extensions/1",
            json={
                "id": 1,
                "name": "更新後の拡張機能",
                "description": "更新後の説明",
                "enabled": False,
                "type": "builtin",
                "cmd": "node",
                "args": ["index.js"],
                "timeout": 600,
                "envs": {"NODE_ENV": "production"},
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "更新後の拡張機能"
        assert data["description"] == "更新後の説明"
        assert data["enabled"] is False
        assert data["type"] == "builtin"
        assert data["cmd"] == "node"
        assert data["args"] == ["index.js"]
        assert data["timeout"] == 600
        assert data["envs"] == {"NODE_ENV": "production"}

        # update_extensionが正しく呼ばれたことを検証
        mock_service.update_extension.assert_called_once()


@pytest.mark.asyncio
async def test_update_extension_not_found(client: AsyncClient, test_admin):
    """存在しない拡張機能更新エンドポイントのテスト"""
    # ExtensionServiceのモック
    with patch("api.routes.extensions.ExtensionService") as mock_service_class:
        # モックの設定
        mock_service = AsyncMock()
        mock_service.update_extension.return_value = None
        mock_service_class.return_value = mock_service

        # 管理者としてログイン
        login_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "adminpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]

        # 存在しない拡張機能更新リクエスト
        response = await client.patch(
            "/api/v1/extensions/999",
            json={
                "id": 999,
                "enabled": False,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # 検証
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "見つかりません" in data["detail"]

        # update_extensionが正しく呼ばれたことを検証
        mock_service.update_extension.assert_called_once()


@pytest.mark.asyncio
async def test_update_extension_unauthorized(client: AsyncClient, test_user):
    """非管理者による拡張機能更新エンドポイントのテスト"""
    # 通常ユーザーとしてログイン
    login_response = await client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login_response.json()["access_token"]

    # 拡張機能更新リクエスト
    response = await client.patch(
        "/api/v1/extensions/1",
        json={
            "id": 1,
            "enabled": False,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # 検証
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_remove_extension(client: AsyncClient, test_admin):
    """拡張機能削除エンドポイントのテスト"""
    # ExtensionServiceのモック
    with patch("api.routes.extensions.ExtensionService") as mock_service_class:
        # モックの設定
        mock_service = AsyncMock()
        mock_service.remove_extension.return_value = True
        mock_service_class.return_value = mock_service

        # 管理者としてログイン
        login_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "adminpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]

        # 拡張機能削除リクエスト
        response = await client.delete(
            "/api/v1/extensions/1",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 検証
        assert response.status_code == 204

        # remove_extensionが正しく呼ばれたことを検証
        mock_service.remove_extension.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_remove_extension_not_found(client: AsyncClient, test_admin):
    """存在しない拡張機能削除エンドポイントのテスト"""
    # ExtensionServiceのモック
    with patch("api.routes.extensions.ExtensionService") as mock_service_class:
        # モックの設定
        mock_service = AsyncMock()
        mock_service.remove_extension.return_value = False
        mock_service_class.return_value = mock_service

        # 管理者としてログイン
        login_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "adminpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]

        # 存在しない拡張機能削除リクエスト
        response = await client.delete(
            "/api/v1/extensions/999",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 検証
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "見つかりません" in data["detail"]

        # remove_extensionが正しく呼ばれたことを検証
        mock_service.remove_extension.assert_called_once_with(999)


@pytest.mark.asyncio
async def test_remove_extension_unauthorized(client: AsyncClient, test_user):
    """非管理者による拡張機能削除エンドポイントのテスト"""
    # 通常ユーザーとしてログイン
    login_response = await client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login_response.json()["access_token"]

    # 拡張機能削除リクエスト
    response = await client.delete(
        "/api/v1/extensions/1",
        headers={"Authorization": f"Bearer {token}"},
    )

    # 検証
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_install_extension(client: AsyncClient, test_admin):
    """拡張機能インストールエンドポイントのテスト"""
    # ExtensionServiceのモック
    with patch("api.routes.extensions.ExtensionService") as mock_service_class:
        # モックの設定
        mock_service = AsyncMock()
        mock_service.install_extension_from_url.return_value = {
            "success": True,
            "message": "新しいGoose CLIコマンド体系では拡張機能のインストールコマンドが提供されていません。手動でのインストールが必要です。",
            "extension_id": 1,
        }
        mock_service_class.return_value = mock_service

        # 管理者としてログイン
        login_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "adminpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]

        # 拡張機能インストールリクエスト
        response = await client.post(
            "/api/v1/extensions/install",
            json={
                "name": "テスト拡張機能",
                "url": "https://example.com/extension",
                "description": "テスト用の拡張機能",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # 検証
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        assert "extension_id" in data
        assert data["extension_id"] == 1

        # install_extension_from_urlが正しく呼ばれたことを検証
        mock_service.install_extension_from_url.assert_called_once_with(
            "テスト拡張機能", "https://example.com/extension", "テスト用の拡張機能"
        )


@pytest.mark.asyncio
async def test_install_extension_failure(client: AsyncClient, test_admin):
    """拡張機能インストール失敗のテスト"""
    # ExtensionServiceのモック
    with patch("api.routes.extensions.ExtensionService") as mock_service_class:
        # モックの設定
        mock_service = AsyncMock()
        mock_service.install_extension_from_url.return_value = {
            "success": False,
            "message": "インストールに失敗しました",
        }
        mock_service_class.return_value = mock_service

        # 管理者としてログイン
        login_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "adminpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]

        # 拡張機能インストールリクエスト
        response = await client.post(
            "/api/v1/extensions/install",
            json={
                "name": "テスト拡張機能",
                "url": "https://example.com/invalid-extension",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # 検証
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "インストールに失敗しました"

        # install_extension_from_urlが正しく呼ばれたことを検証
        mock_service.install_extension_from_url.assert_called_once_with(
            "テスト拡張機能", "https://example.com/invalid-extension", ""
        )


@pytest.mark.asyncio
async def test_install_extension_unauthorized(client: AsyncClient, test_user):
    """非管理者による拡張機能インストールエンドポイントのテスト"""
    # 通常ユーザーとしてログイン
    login_response = await client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login_response.json()["access_token"]

    # 拡張機能インストールリクエスト
    response = await client.post(
        "/api/v1/extensions/install",
        json={
            "name": "テスト拡張機能",
            "url": "https://example.com/extension",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # 検証
    assert response.status_code == 403
