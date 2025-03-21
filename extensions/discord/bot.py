"""
Discord Botモジュール

このモジュールは、Discordとの連携機能を提供します。
Discord.pyを使用してBotを実装し、メッセージやリアクションのイベントを処理します。
"""

import logging

import discord
from discord.ext import commands

from api.services.action_config_service import ActionConfigService
from api.services.discord_config_service import DiscordConfigService
from api.services.task_service import TaskService


class DiscordService:
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
                "timestamp": message.created_at.isoformat(),
                "requested_by": user.name,
                "discord_url": message.jump_url,
                "catch_type": discord_config["catch_type"],
                "catch_value": discord_config["catch_value"],
            }

            # 関連するタスクテンプレートを取得
            task_service = TaskService()
            task = await task_service.get_task_template(action["task_template_id"])
            if not task:
                await processing_msg.edit(content=f"{user.mention} 関連するタスクテンプレートが見つかりません。")
                return

            # Gooseにリクエスト
            result = await self.goose_executor.execute(task["prompt"], context=context)

            if not result["success"]:
                await processing_msg.edit(content=f"{user.mention} 処理中にエラーが発生しました。")
                self.logger.error(f"処理エラー: {result['output']}")
                return

            # 結果をDiscordに表示
            output = result["output"]

            # レスポンス形式に基づいて結果を送信
            await self._send_response(message, user, output, processing_msg, discord_config["response_format"])

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

    async def start(self):
        """Botを起動"""
        await self.bot.start(self.token)

    async def close(self):
        """Botを停止"""
        await self.bot.close()
