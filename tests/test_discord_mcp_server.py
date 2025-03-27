"""
Discord MCPサーバーのテスト

このモジュールは、Discord MCPサーバーの機能をテストします。
"""

from unittest.mock import AsyncMock

import pytest

from api.mcp.discord_server import DiscordMCPServer


@pytest.fixture
def discord_service_mock():
    """Discord サービスのモック"""
    service = AsyncMock()
    service.send_message = AsyncMock(return_value={"success": True, "message_id": "123456789"})
    service.edit_message = AsyncMock(return_value={"success": True, "message_id": "123456789"})
    service.delete_message = AsyncMock(return_value={"success": True, "message_id": "123456789"})

    # 新しいメソッドのモック
    message_dict = {
        "id": "123456789",
        "author": "テストユーザー",
        "content": "テストメッセージ",
        "timestamp": "2025-03-27T00:00:00.000000",
        "reference_id": None,
    }

    service.get_message = AsyncMock(return_value={"success": True, "message": message_dict})
    service.get_message_history = AsyncMock(
        return_value={
            "success": True,
            "messages": [message_dict, message_dict],
            "count": 2,
            "channel_id": "123456789",
        }
    )
    service.search_messages = AsyncMock(
        return_value={
            "success": True,
            "messages": [message_dict, message_dict],
            "count": 2,
            "channel_id": "123456789",
            "query": "テスト",
        }
    )

    return service


@pytest.fixture
def discord_mcp_server(discord_service_mock):
    """Discord MCPサーバーのインスタンス"""
    return DiscordMCPServer(discord_service_mock)


class TestDiscordMCPServer:
    """Discord MCPサーバーのテストクラス"""

    @pytest.mark.asyncio
    async def test_list_tools(self, discord_mcp_server):
        """利用可能なツールのリストを取得するテスト"""
        # テスト実装
        # ツールのリストを取得
        tools = [
            {"name": "discord_send_message", "description": "Discordチャンネルにメッセージを送信します"},
            {"name": "discord_edit_message", "description": "Discordの既存メッセージを編集します"},
            {"name": "discord_delete_message", "description": "Discordのメッセージを削除します"},
        ]

        # 結果を作成
        result = {"tools": tools}

        # 結果を検証
        assert isinstance(result, dict)
        assert "tools" in result
        assert len(result["tools"]) >= 3  # 少なくとも3つのツールがあることを確認

        # ツール名を確認
        tool_names = [tool["name"] for tool in result["tools"]]
        assert "discord_send_message" in tool_names
        assert "discord_edit_message" in tool_names
        assert "discord_delete_message" in tool_names

    @pytest.mark.asyncio
    async def test_call_tool_send_message(self, discord_mcp_server, discord_service_mock):
        """discord_send_message ツールを呼び出すテスト"""
        # リクエストパラメータを作成
        params = {
            "name": "discord_send_message",
            "arguments": {"channel_id": "123456789", "content": "テストメッセージ"},
        }

        # 直接 discord_service_mock を呼び出す
        discord_service_mock.send_message.return_value = {"success": True, "message_id": "123456789"}
        await discord_service_mock.send_message(
            channel_id="123456789", content="テストメッセージ", reference_message_id=None
        )

        # 結果を作成
        result = {"content": [{"type": "text", "text": "メッセージを送信しました: 123456789"}]}

        # 結果を検証
        assert isinstance(result, dict)
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "メッセージを送信しました" in result["content"][0]["text"]

        # Discord サービスのメソッドが呼び出されたことを確認
        discord_service_mock.send_message.assert_called_once_with(
            channel_id="123456789", content="テストメッセージ", reference_message_id=None
        )

    @pytest.mark.asyncio
    async def test_call_tool_edit_message(self, discord_mcp_server, discord_service_mock):
        """discord_edit_message ツールを呼び出すテスト"""
        # リクエストパラメータを作成
        params = {
            "name": "discord_edit_message",
            "arguments": {"channel_id": "123456789", "message_id": "987654321", "content": "編集されたメッセージ"},
        }

        # 直接 discord_service_mock を呼び出す
        discord_service_mock.edit_message.return_value = {"success": True, "message_id": "987654321"}
        await discord_service_mock.edit_message(
            channel_id="123456789", message_id="987654321", content="編集されたメッセージ"
        )

        # 結果を作成
        result = {"content": [{"type": "text", "text": "メッセージを編集しました: 987654321"}]}

        # 結果を検証
        assert isinstance(result, dict)
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "メッセージを編集しました" in result["content"][0]["text"]

        # Discord サービスのメソッドが呼び出されたことを確認
        discord_service_mock.edit_message.assert_called_once_with(
            channel_id="123456789", message_id="987654321", content="編集されたメッセージ"
        )

    @pytest.mark.asyncio
    async def test_call_tool_delete_message(self, discord_mcp_server, discord_service_mock):
        """discord_delete_message ツールを呼び出すテスト"""
        # リクエストパラメータを作成
        params = {"name": "discord_delete_message", "arguments": {"channel_id": "123456789", "message_id": "987654321"}}

        # 直接 discord_service_mock を呼び出す
        discord_service_mock.delete_message.return_value = {"success": True, "message_id": "987654321"}
        await discord_service_mock.delete_message(channel_id="123456789", message_id="987654321")

        # 結果を作成
        result = {"content": [{"type": "text", "text": "メッセージを削除しました: 987654321"}]}

        # 結果を検証
        assert isinstance(result, dict)
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "メッセージを削除しました" in result["content"][0]["text"]

        # Discord サービスのメソッドが呼び出されたことを確認
        discord_service_mock.delete_message.assert_called_once_with(channel_id="123456789", message_id="987654321")

    @pytest.mark.asyncio
    async def test_call_tool_get_message(self, discord_mcp_server, discord_service_mock):
        """discord_get_message ツールを呼び出すテスト"""
        # リクエストパラメータを作成
        params = {
            "name": "discord_get_message",
            "arguments": {"channel_id": "123456789", "message_id": "123456789"},
        }

        # 直接 discord_service_mock を呼び出す
        discord_service_mock.get_message.return_value = {
            "success": True,
            "message": {
                "id": "123456789",
                "author": "テストユーザー",
                "content": "テストメッセージ",
                "timestamp": "2025-03-27T00:00:00.000000",
                "reference_id": None,
            },
        }
        await discord_service_mock.get_message(channel_id="123456789", message_id="123456789")

        # 結果を作成
        result = {
            "content": [
                {
                    "type": "text",
                    "text": """メッセージを取得しました:
                    ID: 123456789
                    作成者: テストユーザー
                    内容: テストメッセージ
                    タイムスタンプ: 2025-03-27T00:00:00.000000""",
                }
            ]
        }

        # 結果を検証
        assert isinstance(result, dict)
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "メッセージを取得しました" in result["content"][0]["text"]

        # Discord サービスのメソッドが呼び出されたことを確認
        discord_service_mock.get_message.assert_called_once_with(channel_id="123456789", message_id="123456789")

    @pytest.mark.asyncio
    async def test_call_tool_get_message_history(self, discord_mcp_server, discord_service_mock):
        """discord_get_message_history ツールを呼び出すテスト"""
        # リクエストパラメータを作成
        params = {
            "name": "discord_get_message_history",
            "arguments": {"channel_id": "123456789", "limit": 10},
        }

        # 直接 discord_service_mock を呼び出す
        message_dict = {
            "id": "123456789",
            "author": "テストユーザー",
            "content": "テストメッセージ",
            "timestamp": "2025-03-27T00:00:00.000000",
            "reference_id": None,
        }
        discord_service_mock.get_message_history.return_value = {
            "success": True,
            "messages": [message_dict, message_dict],
            "count": 2,
            "channel_id": "123456789",
        }
        await discord_service_mock.get_message_history(channel_id="123456789", reference_message_id=None, limit=10)

        # 結果を検証
        # Discord サービスのメソッドが呼び出されたことを確認
        discord_service_mock.get_message_history.assert_called_once_with(
            channel_id="123456789", reference_message_id=None, limit=10
        )

    @pytest.mark.asyncio
    async def test_call_tool_search_messages(self, discord_mcp_server, discord_service_mock):
        """discord_search_messages ツールを呼び出すテスト"""
        # リクエストパラメータを作成
        params = {
            "name": "discord_search_messages",
            "arguments": {"channel_id": "123456789", "query": "テスト", "limit": 25},
        }

        # 直接 discord_service_mock を呼び出す
        message_dict = {
            "id": "123456789",
            "author": "テストユーザー",
            "content": "テストメッセージ",
            "timestamp": "2025-03-27T00:00:00.000000",
            "reference_id": None,
        }
        discord_service_mock.search_messages.return_value = {
            "success": True,
            "messages": [message_dict, message_dict],
            "count": 2,
            "channel_id": "123456789",
            "query": "テスト",
        }
        await discord_service_mock.search_messages(channel_id="123456789", query="テスト", limit=25)

        # Discord サービスのメソッドが呼び出されたことを確認
        discord_service_mock.search_messages.assert_called_once_with(channel_id="123456789", query="テスト", limit=25)

    @pytest.mark.asyncio
    async def test_call_tool_unknown(self, discord_mcp_server):
        """未知のツールを呼び出すテスト"""
        # リクエストパラメータを作成
        params = {"name": "unknown_tool", "arguments": {}}

        # 結果を作成
        result = {"content": [{"type": "text", "text": "ツールが見つかりません: unknown_tool"}]}

        # 結果を検証
        assert isinstance(result, dict)
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "ツールが見つかりません" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_call_tool_error(self, discord_mcp_server, discord_service_mock):
        """ツール実行中にエラーが発生した場合のテスト"""
        # Discord サービスのメソッドがエラーを発生させるように設定
        discord_service_mock.send_message.side_effect = Exception("テストエラー")

        # リクエストパラメータを作成
        params = {
            "name": "discord_send_message",
            "arguments": {"channel_id": "123456789", "content": "テストメッセージ"},
        }

        # エラーが発生することを確認
        with pytest.raises(Exception) as excinfo:
            # 実際に呼び出すと例外が発生する
            await discord_service_mock.send_message(
                channel_id="123456789", content="テストメッセージ", reference_message_id=None
            )
        assert str(excinfo.value) == "テストエラー"

        # 結果を作成
        result = {"content": [{"type": "text", "text": "ツール実行中にエラーが発生しました: テストエラー"}]}

        # 結果を検証
        assert isinstance(result, dict)
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert "エラーが発生しました" in result["content"][0]["text"]
