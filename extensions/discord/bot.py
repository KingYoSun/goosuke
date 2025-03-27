"""
Discord Botモジュール

このモジュールは、Discordとの連携機能を提供します。
Discord.pyを使用してBotを実装し、メッセージやリアクションのイベントを処理します。
"""

import logging
from typing import Any, Dict, Optional

import discord
from discord.ext import commands

from api.services.action_config_service import ActionConfigService
from api.services.discord_config_service import DiscordConfigService
from api.services.task_service import TaskService


class DiscordBotService:
    """Discord連携サービスクラス"""

    def __init__(self, token: str, goose_executor):
        """初期化

        Args:
            token (str): Discord Botトークン
            goose_executor: Goose実行ラッパーインスタンス
        """
        self.token = token
        self.goose_executor = goose_executor
        # 必要なインテントのみを有効化
        intents = discord.Intents.default()
        intents.message_content = True  # メッセージ内容の読み取りに必要
        intents.reactions = True  # リアクションの検出に必要
        self.bot = commands.Bot(command_prefix="!", intents=intents)
        self.setup_bot()
        self.logger = logging.getLogger("discord_service")

    def setup_bot(self):
        """Botコマンドとイベントの設定"""

        @self.bot.event
        async def on_ready():
            """Botが準備完了したときのイベントハンドラ"""
            self.logger.info(f"{self.bot.user} としてログインしました")

        @self.bot.event
        async def on_reaction_add(reaction, user):
            """リアクションが追加されたときのイベントハンドラ

            Args:
                reaction: 追加されたリアクション
                user: リアクションを追加したユーザー
            """
            # Bot自身のリアクションは無視
            if user.bot:
                return

            # リアクション情報を取得
            emoji = str(reaction.emoji)
            message = reaction.message

            # Discord設定サービスからリアクションに対応する設定を取得
            discord_config_service = DiscordConfigService()
            discord_config = await discord_config_service.get_discord_config_by_reaction(emoji)

            if discord_config:
                # 関連するアクションを取得
                action_config_service = ActionConfigService()
                action = await action_config_service.get_action_by_config("discord", discord_config["id"])
                if action:
                    await self._handle_discord_action(message, user, discord_config, action)
                else:
                    self.logger.info(f"リアクション {emoji} に対応するアクションが見つかりません")
            else:
                self.logger.info(f"リアクション {emoji} に対応するDiscord設定が見つかりません")

    async def _handle_discord_action(self, message, user, discord_config, action):
        """Discord設定に基づいてメッセージを処理

        Args:
            message: 対象メッセージ
            user: リクエストしたユーザー
            discord_config: Discord設定
            action: 関連するアクション
        """
        try:
            # 処理中のメッセージをユーザーに通知
            processing_msg = await message.channel.send(f"{user.mention} メッセージを処理しています...")

            # メッセージ収集戦略を決定
            messages = await self._collect_messages(message, discord_config["message_type"])

            # Gooseへのコンテキスト準備
            context = {
                "messages": [self._message_to_dict(msg) for msg in messages],
                "channel_name": message.channel.name,
                "channel_id": str(message.channel.id),  # チャンネルIDを追加
                "processing_message_id": str(processing_msg.id),  # 処理中メッセージIDを追加
                "timestamp": message.created_at.isoformat(),
                "requested_by": user.name,
                "discord_url": message.jump_url,
                "catch_type": discord_config["catch_type"],
                "catch_value": discord_config["catch_value"],
                "response_format": discord_config["response_format"],  # レスポンス形式を追加
                "user_mention": user.mention,  # ユーザーメンションを追加
            }

            # 関連するタスクテンプレートを取得
            task_service = TaskService()
            task = await task_service.get_task_template(action["task_template_id"])
            if not task:
                await processing_msg.edit(content=f"{user.mention} 関連するタスクテンプレートが見つかりません。")
                return

            # タスク実行を作成
            task_execution = await task_service.create_task_execution(
                task_template_id=action["task_template_id"], context=context
            )

            # Gooseにリクエスト
            result = await self.goose_executor.execute(task["prompt"], context=context)

            if not result["success"]:
                await processing_msg.edit(content=f"{user.mention} 処理中にエラーが発生しました。")
                self.logger.error(f"処理エラー: {result['output']}")
                return

            # 結果をTaskExecutionに保存するのみ（Discord送信はMCPを通じて行う）
            await task_service.update_task_execution(
                task_execution_id=task_execution["id"], status="completed", result=result
            )

            # 注意: ここでは直接Discordに送信しない
            # MCPを通じてGooseエージェントが送信する

        except Exception as e:
            self.logger.error(f"Discord処理エラー: {str(e)}")
            await message.channel.send(f"{user.mention} 処理中にエラーが発生しました。")

    async def _collect_messages(self, message, message_type):
        """メッセージ収集戦略に基づいてメッセージを収集

        Args:
            message: 基点となるメッセージ
            message_type: 収集戦略（"single", "thread", "range"）

        Returns:
            List: 収集されたメッセージのリスト
        """
        if message_type == "single":
            return [message]
        elif message_type == "thread":
            # スレッド内のメッセージを収集
            messages = []
            if hasattr(message, "thread") and message.thread:
                async for msg in message.thread.history(limit=100):
                    messages.append(msg)
                return messages
            else:
                return [message]
        elif message_type == "range":
            # 将来的に実装: 範囲指定のメッセージ収集
            return [message]
        else:
            return [message]

    async def _send_response(self, message, user, output, processing_msg, response_format):
        """レスポンス形式に基づいて結果を送信

        Args:
            message: 元のメッセージ
            user: リクエストしたユーザー
            output: 処理結果
            processing_msg: 処理中メッセージ
            response_format: レスポンス形式（"reply", "dm", "channel"）
        """
        response = f"{user.mention} 処理が完了しました。\n\n{output}\n\n"

        # Discordのメッセージ長制限を考慮
        if len(response) > 2000:
            chunks = self._split_message(response, 1900)  # マージンを残す

            if response_format == "reply":
                await processing_msg.edit(content=chunks[0])
                for chunk in chunks[1:]:
                    await message.channel.send(chunk)
            elif response_format == "dm":
                for chunk in chunks:
                    await user.send(chunk)
                await processing_msg.edit(content=f"{user.mention} DMに結果を送信しました。")
            elif response_format == "channel":
                for chunk in chunks:
                    await message.channel.send(chunk)
                await processing_msg.delete()
        else:
            if response_format == "reply":
                await processing_msg.edit(content=response)
            elif response_format == "dm":
                await user.send(response)
                await processing_msg.edit(content=f"{user.mention} DMに結果を送信しました。")
            elif response_format == "channel":
                await message.channel.send(response)
                await processing_msg.delete()

    def _message_to_dict(self, message):
        """メッセージをディクショナリに変換

        Args:
            message: メッセージ

        Returns:
            Dict: メッセージの辞書表現
        """
        return {
            "id": str(message.id),
            "author": message.author.name,
            "content": message.content,
            "timestamp": message.created_at.isoformat(),
            "reference_id": (str(message.reference.message_id) if message.reference else None),
        }

    def _split_message(self, message, chunk_size):
        """メッセージを指定サイズのチャンクに分割

        Args:
            message: メッセージ
            chunk_size: チャンクサイズ

        Returns:
            List[str]: 分割されたメッセージのリスト
        """
        return [message[i : i + chunk_size] for i in range(0, len(message), chunk_size)]

    async def send_message(
        self, channel_id: str, content: str, reference_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Discordチャンネルにメッセージを送信する

        Args:
            channel_id: チャンネルID
            content: メッセージ内容
            reference_message_id: 返信対象のメッセージID（オプション）

        Returns:
            Dict[str, Any]: 送信結果（message_id等）
        """
        try:
            # チャンネルを取得
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                self.logger.error(f"チャンネルが見つかりません: {channel_id}")
                return {"success": False, "error": f"チャンネルが見つかりません: {channel_id}"}

            # 返信対象のメッセージがある場合
            reference = None
            if reference_message_id:
                try:
                    reference_message = await channel.fetch_message(int(reference_message_id))
                    reference = reference_message.to_reference()
                except Exception as e:
                    self.logger.warning(f"参照メッセージの取得に失敗: {str(e)}")

            # メッセージ送信
            message = await channel.send(content=content, reference=reference)

            return {"success": True, "message_id": str(message.id), "channel_id": str(channel.id)}
        except Exception as e:
            self.logger.error(f"メッセージ送信エラー: {str(e)}")
            return {"success": False, "error": str(e)}

    async def edit_message(self, channel_id: str, message_id: str, content: str) -> Dict[str, Any]:
        """Discordメッセージを編集する

        Args:
            channel_id: チャンネルID
            message_id: メッセージID
            content: 新しいメッセージ内容

        Returns:
            Dict[str, Any]: 編集結果
        """
        try:
            # チャンネルを取得
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                self.logger.error(f"チャンネルが見つかりません: {channel_id}")
                return {"success": False, "error": f"チャンネルが見つかりません: {channel_id}"}

            # メッセージを取得
            try:
                message = await channel.fetch_message(int(message_id))
            except Exception as e:
                self.logger.error(f"メッセージが見つかりません: {message_id}, エラー: {str(e)}")
                return {"success": False, "error": f"メッセージが見つかりません: {message_id}"}

            # メッセージを編集
            await message.edit(content=content)

            return {"success": True, "message_id": message_id, "channel_id": channel_id}
        except Exception as e:
            self.logger.error(f"メッセージ編集エラー: {str(e)}")
            return {"success": False, "error": str(e)}

    async def delete_message(self, channel_id: str, message_id: str) -> Dict[str, Any]:
        """Discordメッセージを削除する

        Args:
            channel_id: チャンネルID
            message_id: メッセージID

        Returns:
            Dict[str, Any]: 削除結果
        """
        try:
            # チャンネルを取得
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                self.logger.error(f"チャンネルが見つかりません: {channel_id}")
                return {"success": False, "error": f"チャンネルが見つかりません: {channel_id}"}

            # メッセージを取得
            try:
                message = await channel.fetch_message(int(message_id))
            except Exception as e:
                self.logger.error(f"メッセージが見つかりません: {message_id}, エラー: {str(e)}")
                return {"success": False, "error": f"メッセージが見つかりません: {message_id}"}

            # メッセージを削除
            await message.delete()

            return {"success": True, "message_id": message_id, "channel_id": channel_id}
        except Exception as e:
            self.logger.error(f"メッセージ削除エラー: {str(e)}")
            return {"success": False, "error": str(e)}

    async def start(self):
        """Botを起動"""
        await self.bot.start(self.token)

    async def get_message(self, channel_id: str, message_id: str) -> Dict[str, Any]:
        """特定のDiscordメッセージを取得する

        Args:
            channel_id: チャンネルID
            message_id: メッセージID

        Returns:
            Dict[str, Any]: 取得結果（message等）
        """
        try:
            # チャンネルを取得
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                self.logger.error(f"チャンネルが見つかりません: {channel_id}")
                return {"success": False, "error": f"チャンネルが見つかりません: {channel_id}"}

            # メッセージを取得
            try:
                message = await channel.fetch_message(int(message_id))
                return {"success": True, "message": self._message_to_dict(message), "channel_id": str(channel.id)}
            except Exception as e:
                self.logger.error(f"メッセージが見つかりません: {message_id}, エラー: {str(e)}")
                return {"success": False, "error": f"メッセージが見つかりません: {message_id}"}
        except Exception as e:
            self.logger.error(f"メッセージ取得エラー: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_message_history(
        self, channel_id: str, reference_message_id: Optional[str] = None, limit: int = 10
    ) -> Dict[str, Any]:
        """チャンネルの履歴からメッセージを取得する

        Args:
            channel_id: チャンネルID
            reference_message_id: 基準となるメッセージID（指定した場合はそのメッセージより前のメッセージを取得）
            limit: 取得するメッセージの最大数

        Returns:
            Dict[str, Any]: 取得結果（messages等）
        """
        try:
            # チャンネルを取得
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                self.logger.error(f"チャンネルが見つかりません: {channel_id}")
                return {"success": False, "error": f"チャンネルが見つかりません: {channel_id}"}

            # 基準となるメッセージを取得（指定されている場合）
            before = None
            if reference_message_id:
                try:
                    before = await channel.fetch_message(int(reference_message_id))
                except Exception as e:
                    self.logger.warning(f"参照メッセージの取得に失敗: {str(e)}")
                    return {"success": False, "error": f"参照メッセージの取得に失敗: {str(e)}"}

            # メッセージ履歴を取得
            messages = []
            async for msg in channel.history(limit=limit, before=before):
                messages.append(self._message_to_dict(msg))

            return {"success": True, "messages": messages, "channel_id": str(channel.id), "count": len(messages)}
        except Exception as e:
            self.logger.error(f"メッセージ履歴取得エラー: {str(e)}")
            return {"success": False, "error": str(e)}

    async def search_messages(self, channel_id: str, query: str, limit: int = 25) -> Dict[str, Any]:
        """チャンネル内のメッセージを検索する

        Args:
            channel_id: チャンネルID
            query: 検索クエリ
            limit: 取得するメッセージの最大数

        Returns:
            Dict[str, Any]: 検索結果（messages等）
        """
        try:
            # チャンネルを取得
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                self.logger.error(f"チャンネルが見つかりません: {channel_id}")
                return {"success": False, "error": f"チャンネルが見つかりません: {channel_id}"}

            # メッセージを検索（discord.pyではネイティブの検索機能がないため、履歴を取得して検索）
            messages = []
            async for msg in channel.history(limit=100):  # より多くのメッセージから検索するために多めに取得
                if query.lower() in msg.content.lower():
                    messages.append(self._message_to_dict(msg))
                    if len(messages) >= limit:
                        break

            return {
                "success": True,
                "messages": messages,
                "channel_id": str(channel.id),
                "count": len(messages),
                "query": query,
            }
        except Exception as e:
            self.logger.error(f"メッセージ検索エラー: {str(e)}")
            return {"success": False, "error": str(e)}

    async def close(self):
        """Botを停止"""
        await self.bot.close()
