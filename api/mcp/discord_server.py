"""
Discord MCP サーバーモジュール

このモジュールは、Discord連携のためのMCPサーバーを提供します。
SSEトランスポートを使用して、GooseエージェントからのリクエストをDiscord Botに転送します。
"""

import logging
from typing import Any, Dict, List

import mcp.types as types
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.responses import Response

from api.services.discord_service import DiscordBotManager


class DiscordMCPServer:
    """Discord MCP サーバークラス"""

    def __init__(self, discord_service: DiscordBotManager):
        """初期化

        Args:
            discord_service: Discord サービスインスタンス
        """
        self.discord_service = discord_service
        self.app = Server("discord-mcp-server")  # type: ignore
        self.sse = SseServerTransport("/mcp/discord/messages")
        self.logger = logging.getLogger("discord_mcp_server")

        # ツール定義
        @self.app.list_tools()
        async def list_tools() -> List[types.Tool]:
            """利用可能なツールのリストを返す"""
            return [
                types.Tool(
                    name="discord_send_message",
                    description="Discordチャンネルにメッセージを送信します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "channel_id": {"type": "string", "description": "送信先のDiscordチャンネルID"},
                            "content": {"type": "string", "description": "送信するメッセージ内容"},
                            "reference_message_id": {
                                "type": "string",
                                "description": "返信対象のメッセージID（オプション）",
                                "nullable": True,
                            },
                        },
                        "required": ["channel_id", "content"],
                    },
                ),
                types.Tool(
                    name="discord_edit_message",
                    description="Discordの既存メッセージを編集します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "channel_id": {"type": "string", "description": "メッセージのあるDiscordチャンネルID"},
                            "message_id": {"type": "string", "description": "編集対象のメッセージID"},
                            "content": {"type": "string", "description": "新しいメッセージ内容"},
                        },
                        "required": ["channel_id", "message_id", "content"],
                    },
                ),
                types.Tool(
                    name="discord_delete_message",
                    description="Discordのメッセージを削除します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "channel_id": {"type": "string", "description": "メッセージのあるDiscordチャンネルID"},
                            "message_id": {"type": "string", "description": "削除対象のメッセージID"},
                        },
                        "required": ["channel_id", "message_id"],
                    },
                ),
                types.Tool(
                    name="discord_get_message",
                    description="特定のDiscordメッセージを取得します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "channel_id": {"type": "string", "description": "メッセージのあるDiscordチャンネルID"},
                            "message_id": {"type": "string", "description": "取得対象のメッセージID"},
                        },
                        "required": ["channel_id", "message_id"],
                    },
                ),
                types.Tool(
                    name="discord_get_message_history",
                    description="Discordチャンネルの履歴からメッセージを取得します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "channel_id": {"type": "string", "description": "メッセージのあるDiscordチャンネルID"},
                            "reference_message_id": {
                                "type": "string",
                                "description": "基準となるメッセージID（指定した場合はそのメッセージより前のメッセージを取得）",
                                "nullable": True,
                            },
                            "limit": {
                                "type": "integer",
                                "description": "取得するメッセージの最大数",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 100,
                            },
                        },
                        "required": ["channel_id"],
                    },
                ),
                types.Tool(
                    name="discord_search_messages",
                    description="Discordチャンネル内のメッセージを検索します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "channel_id": {"type": "string", "description": "検索対象のDiscordチャンネルID"},
                            "query": {"type": "string", "description": "検索クエリ"},
                            "limit": {
                                "type": "integer",
                                "description": "取得するメッセージの最大数",
                                "default": 25,
                                "minimum": 1,
                                "maximum": 100,
                            },
                        },
                        "required": ["channel_id", "query"],
                    },
                ),
            ]

        # ツール呼び出し処理
        @self.app.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """ツールを呼び出す

            Args:
                name: ツール名
                arguments: ツールの引数

            Returns:
                ツールの実行結果
            """
            self.logger.info(f"ツール呼び出し: {name}, 引数: {arguments}")

            try:
                if name == "discord_send_message":
                    channel_id = arguments["channel_id"]
                    content = arguments["content"]
                    reference_message_id = arguments.get("reference_message_id")

                    # Discord Botを使用してメッセージを送信
                    result = await self.discord_service.send_message(
                        channel_id=channel_id, content=content, reference_message_id=reference_message_id
                    )

                    if result.get("success", False):
                        return [
                            types.TextContent(type="text", text=f"メッセージを送信しました: {result['message_id']}")
                        ]
                    else:
                        return [
                            types.TextContent(
                                type="text", text=f"メッセージ送信エラー: {result.get('error', '不明なエラー')}"
                            )
                        ]

                elif name == "discord_edit_message":
                    channel_id = arguments["channel_id"]
                    message_id = arguments["message_id"]
                    content = arguments["content"]

                    # Discord Botを使用してメッセージを編集
                    result = await self.discord_service.edit_message(
                        channel_id=channel_id, message_id=message_id, content=content
                    )

                    if result.get("success", False):
                        return [types.TextContent(type="text", text=f"メッセージを編集しました: {message_id}")]
                    else:
                        return [
                            types.TextContent(
                                type="text", text=f"メッセージ編集エラー: {result.get('error', '不明なエラー')}"
                            )
                        ]

                elif name == "discord_delete_message":
                    channel_id = arguments["channel_id"]
                    message_id = arguments["message_id"]

                    # Discord Botを使用してメッセージを削除
                    result = await self.discord_service.delete_message(channel_id=channel_id, message_id=message_id)

                    if result.get("success", False):
                        return [types.TextContent(type="text", text=f"メッセージを削除しました: {message_id}")]
                    else:
                        return [
                            types.TextContent(
                                type="text", text=f"メッセージ削除エラー: {result.get('error', '不明なエラー')}"
                            )
                        ]

                elif name == "discord_get_message":
                    channel_id = arguments["channel_id"]
                    message_id = arguments["message_id"]

                    # Discord Botを使用してメッセージを取得
                    result = await self.discord_service.get_message(channel_id=channel_id, message_id=message_id)

                    if result.get("success", False):
                        message = result["message"]
                        return [
                            types.TextContent(
                                type="text",
                                text=f"メッセージを取得しました:\n"
                                f"ID: {message['id']}\n"
                                f"作成者: {message['author']}\n"
                                f"内容: {message['content']}\n"
                                f"タイムスタンプ: {message['timestamp']}",
                            )
                        ]
                    else:
                        return [
                            types.TextContent(
                                type="text", text=f"メッセージ取得エラー: {result.get('error', '不明なエラー')}"
                            )
                        ]

                elif name == "discord_get_message_history":
                    channel_id = arguments["channel_id"]
                    reference_message_id = arguments.get("reference_message_id")
                    limit = arguments.get("limit", 10)

                    # Discord Botを使用してメッセージ履歴を取得
                    result = await self.discord_service.get_message_history(
                        channel_id=channel_id, reference_message_id=reference_message_id, limit=limit
                    )

                    if result.get("success", False):
                        messages = result["messages"]
                        message_texts = []
                        for msg in messages:
                            message_texts.append(
                                f"ID: {msg['id']}\n"
                                f"作成者: {msg['author']}\n"
                                f"内容: {msg['content']}\n"
                                f"タイムスタンプ: {msg['timestamp']}\n"
                            )

                        return [
                            types.TextContent(
                                type="text",
                                text=f"{len(messages)}件のメッセージを取得しました:\n\n"
                                + "\n---\n".join(message_texts),
                            )
                        ]
                    else:
                        return [
                            types.TextContent(
                                type="text", text=f"メッセージ履歴取得エラー: {result.get('error', '不明なエラー')}"
                            )
                        ]

                elif name == "discord_search_messages":
                    channel_id = arguments["channel_id"]
                    query = arguments["query"]
                    limit = arguments.get("limit", 25)

                    # Discord Botを使用してメッセージを検索
                    result = await self.discord_service.search_messages(channel_id=channel_id, query=query, limit=limit)

                    if result.get("success", False):
                        messages = result["messages"]
                        message_texts = []
                        for msg in messages:
                            message_texts.append(
                                f"ID: {msg['id']}\n"
                                f"作成者: {msg['author']}\n"
                                f"内容: {msg['content']}\n"
                                f"タイムスタンプ: {msg['timestamp']}\n"
                            )

                        return [
                            types.TextContent(
                                type="text",
                                text=f"検索クエリ「{query}」に一致する{len(messages)}件のメッセージを取得しました:\n\n"
                                + "\n---\n".join(message_texts),
                            )
                        ]
                    else:
                        return [
                            types.TextContent(
                                type="text", text=f"メッセージ検索エラー: {result.get('error', '不明なエラー')}"
                            )
                        ]

                else:
                    self.logger.error(f"未知のツール: {name}")
                    return [types.TextContent(type="text", text=f"ツールが見つかりません: {name}")]

            except Exception as e:
                self.logger.error(f"ツール実行エラー: {str(e)}")
                return [types.TextContent(type="text", text=f"ツール実行中にエラーが発生しました: {str(e)}")]

    async def handle_sse(self, request: Request) -> Response:
        """SSE接続ハンドラ

        Args:
            request: リクエスト

        Returns:
            レスポンス
        """

        self.logger.info("Discord MCP SSE接続をhandlingします")

        from starlette.responses import StreamingResponse

        async def event_generator():
            # SSEストリームを生成するジェネレーター
            # カスタムsend関数を作成 - 非同期関数として実装
            async def custom_send(message):
                # 非同期ジェネレータではなく、通常の非同期関数として実装
                # メッセージを適切に処理して返す
                if message["type"] == "http.response.body":
                    content = message.get("body", b"")
                    if content:
                        return content
                return message  # デフォルトではメッセージをそのまま返す

            # SSE接続を確立
            async with self.sse.connect_sse(request.scope, request.receive, custom_send) as streams:
                await self.app.run(streams[0], streams[1], self.app.create_initialization_options())

            # ストリーミングレスポンスのために少なくとも1つの値を生成する必要がある
            yield b""

        # 非同期ジェネレータを返す
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    async def handle_messages(self, request: Request) -> Response:
        """メッセージハンドラ

        Args:
            request: リクエスト

        Returns:
            レスポンス
        """

        from starlette.responses import JSONResponse

        # リクエストボディを取得
        body = await request.json()

        # SSEサーバーにメッセージを送信
        # リクエストをASGIメッセージに変換して処理
        # FIXME SSEがすぐDisconnectedになってしまう
        try:
            # カスタムsend関数を作成
            response_data = {"status": "success", "message": "Message sent to SSE server"}
            response_sent = False

            async def custom_send(message):
                nonlocal response_sent
                if message["type"] == "http.response.start":
                    # レスポンスヘッダーを記録するだけで何もしない
                    pass
                elif message["type"] == "http.response.body" and not response_sent:
                    # 最初のボディメッセージを受け取ったらレスポンスを送信済みとマーク
                    response_sent = True

            # SSEサーバーにメッセージを転送
            await self.sse.handle_post_message(request.scope, request.receive, custom_send)
            return JSONResponse(response_data)
        except Exception as e:
            self.logger.error(f"メッセージ処理エラー: {str(e)}")
            return JSONResponse({"status": "error", "message": f"Failed to process message: {str(e)}"}, status_code=500)
