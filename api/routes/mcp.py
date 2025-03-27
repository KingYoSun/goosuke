"""
MCP ルーターモジュール

このモジュールは、MCPサーバーのエンドポイントを提供します。
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Request
from starlette.responses import Response

from api.mcp.discord_server import DiscordMCPServer
from api.services.discord_service import DiscordBotManager

router = APIRouter(prefix="/mcp/discord", tags=["DiscordMCP"])
logger = logging.getLogger("mcp_router")

# シングルトンインスタンス
_discord_mcp_server: Optional[DiscordMCPServer] = None


def get_discord_mcp_server(discord_service: DiscordBotManager = Depends()) -> DiscordMCPServer:
    """Discord MCPサーバーのシングルトンインスタンスを取得

    Args:
        discord_service: Discord サービスインスタンス

    Returns:
        Discord MCPサーバーインスタンス
    """
    global _discord_mcp_server
    if _discord_mcp_server is None:
        logger.info("Discord MCPサーバーを初期化しています")
        _discord_mcp_server = DiscordMCPServer(discord_service)
    return _discord_mcp_server


@router.get("/sse")
async def discord_sse_endpoint(
    request: Request, server: DiscordMCPServer = Depends(get_discord_mcp_server)
) -> Response:
    """Discord MCP SSEエンドポイント

    Args:
        request: リクエスト
        server: Discord MCPサーバーインスタンス

    Returns:
        SSEレスポンス
    """
    logger.info("Discord MCP SSE接続を受け付けました")
    return await server.handle_sse(request)


@router.post("/messages")
async def discord_messages_endpoint(
    request: Request, server: DiscordMCPServer = Depends(get_discord_mcp_server)
) -> Response:
    """Discord MCP メッセージエンドポイント

    Args:
        request: リクエスト
        server: Discord MCPサーバーインスタンス

    Returns:
        メッセージレスポンス
    """
    logger.info("Discord MCP メッセージリクエストを受け付けました")
    return await server.handle_messages(request)
