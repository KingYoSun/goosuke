"""
Discord Botモジュール

このモジュールは、Discordとの連携機能を提供します。
Discord.pyを使用してBotを実装し、メッセージやリアクションのイベントを処理します。
"""

import logging
from typing import List, Set

import discord
from discord.ext import commands


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

            # 鉛筆リアクションを検出
            if str(reaction.emoji) == "✏️":
                message = reaction.message
                await self._handle_pencil_reaction(message, user)

    async def _handle_pencil_reaction(self, message, user):
        """鉛筆リアクションが付いた投稿の処理

        Args:
            message: リアクションが付いたメッセージ
            user: リアクションを追加したユーザー
        """
        try:
            # 処理中のメッセージをユーザーに通知
            processing_msg = await message.channel.send(f"{user.mention} 会話を分析しています...")

            # 単一のメッセージのみを使用
            # Gooseへのコンテキスト準備
            context = {
                "messages": [self._message_to_dict(message)],
                "channel_name": message.channel.name,
                "timestamp": message.created_at.isoformat(),
                "requested_by": user.name,
                "discord_url": message.jump_url,
            }

            # Gooseに要約リクエスト
            prompt = "メッセージを簡潔に要約してください。重要なポイントを箇条書きでまとめ、その後に要約文を作成してください。\n要約文にANSIコードを付与しないでください。"

            result = await self.goose_executor.execute(prompt, context=context)

            if not result["success"]:
                await processing_msg.edit(content=f"{user.mention} 要約の生成中にエラーが発生しました。")
                self.logger.error(f"要約エラー: {result['output']}")
                return

            # 結果をDiscordに表示（ANSIコードはすでにcli.pyで除去済み）
            summary = result["output"]

            # フォーマットして返信
            response = f"{user.mention} 会話の要約が完了しました。\n\n"

            response += summary + "\n\n"

            # Discordのメッセージ長制限を考慮
            if len(response) > 2000:
                # 長すぎる場合は分割して送信
                chunks = self._split_message(response, 1900)  # マージンを残す
                await processing_msg.edit(content=chunks[0])
                for chunk in chunks[1:]:
                    await message.channel.send(chunk)
            else:
                await processing_msg.edit(content=response)

        except Exception as e:
            self.logger.error(f"リアクション処理エラー: {str(e)}")
            await message.channel.send(f"{user.mention} 処理中にエラーが発生しました。")

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
