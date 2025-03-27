"""
MCPルーターのテスト

このモジュールは、MCPルーターの機能をテストします。
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.mcp.discord_server import DiscordMCPServer
from api.routes.mcp import router as mcp_router


@pytest.fixture
def discord_service_mock():
    """Discord サービスのモック"""
    service = AsyncMock()
    service.send_message = AsyncMock(return_value={"success": True, "message_id": "123456789"})
    service.edit_message = AsyncMock(return_value={"success": True, "message_id": "123456789"})
    service.delete_message = AsyncMock(return_value={"success": True, "message_id": "123456789"})
    return service


@pytest.fixture
def discord_mcp_server_mock(discord_service_mock):
    """Discord MCPサーバーのモック"""
    from starlette.responses import JSONResponse, StreamingResponse

    # StreamingResponseのモック
    async def mock_generator():
        yield b"SSE response"

    server = MagicMock(spec=DiscordMCPServer)
    server.handle_sse = AsyncMock(return_value=StreamingResponse(mock_generator(), media_type="text/event-stream"))
    server.handle_messages = AsyncMock(
        return_value=JSONResponse({"status": "success", "message": "Message sent to SSE server"})
    )
    return server


@pytest.fixture
def app(discord_mcp_server_mock):
    """テスト用アプリケーション"""
    app = FastAPI()

    # get_discord_mcp_server 依存関数をモックに置き換え
    async def get_discord_mcp_server_override():
        return discord_mcp_server_mock

    # 依存関数をオーバーライド
    from api.routes.mcp import get_discord_mcp_server

    app.dependency_overrides[get_discord_mcp_server] = get_discord_mcp_server_override

    # ルーターを追加（mcpルーターは既に/mcp/discordプレフィックスを持っているため、追加のプレフィックスは不要）
    app.include_router(mcp_router)

    return app


@pytest.fixture
def client(app):
    """テストクライアント"""
    return TestClient(app)


class TestMCPRoutes:
    """MCPルーターのテストクラス"""

    def test_discord_sse_endpoint(self, client, discord_mcp_server_mock):
        """Discord SSEエンドポイントのテスト"""
        # テストクライアントでリクエスト
        response = client.get("/mcp/discord/sse")

        # レスポンスを検証
        assert response.status_code == 200
        # StreamingResponseの場合、content-typeを検証
        assert response.headers["content-type"].startswith("text/event-stream")
        # 実際のコンテンツはストリームから読み取るため、ここでは検証しない

        # Discord MCPサーバーのメソッドが呼び出されたことを確認
        discord_mcp_server_mock.handle_sse.assert_called_once()

    def test_discord_messages_endpoint(self, client, discord_mcp_server_mock):
        """Discord メッセージエンドポイントのテスト"""
        # テストクライアントでリクエスト
        response = client.post("/mcp/discord/messages", json={"test": "data"})

        # レスポンスを検証
        assert response.status_code == 200
        # JSONResponseの場合、JSONとして解析して検証
        assert response.json() == {"status": "success", "message": "Message sent to SSE server"}

        # Discord MCPサーバーのメソッドが呼び出されたことを確認
        discord_mcp_server_mock.handle_messages.assert_called_once()
