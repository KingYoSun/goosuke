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
        intents = discord.Intents.all()
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

            # 関連メッセージの収集
            related_messages = await self._collect_related_messages(message)
            if not related_messages:
                await processing_msg.edit(content="関連するメッセージが見つかりませんでした。")
                return

            # 会話スレッドの構築
            conversation_thread = self._build_conversation_thread(related_messages)
            conversation_text = self._format_conversation(conversation_thread)

            # Gooseへのコンテキスト準備
            context = {
                "messages": [self._message_to_dict(msg) for msg in related_messages],
                "channel_name": message.channel.name,
                "timestamp": message.created_at.isoformat(),
                "requested_by": user.name,
                "discord_url": message.jump_url,
                "conversation_text": conversation_text,
            }

            # Gooseに要約リクエスト
            prompt = "以下の会話を簡潔に要約してください。重要なポイントを箇条書きでまとめ、その後に要約文を作成してください。"

            result = await self.goose_executor.execute(prompt, context=context)

            if not result["success"]:
                await processing_msg.edit(content=f"{user.mention} 要約の生成中にエラーが発生しました。")
                self.logger.error(f"要約エラー: {result['output']}")
                return

            # 結果をDiscordに表示
            summary = result["output"]

            # フォーマットして返信
            response = f"{user.mention} 会話の要約が完了しました。\n\n"
            response += "## 要約\n"
            response += f"{summary}\n\n"

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

    async def _collect_related_messages(self, trigger_message) -> List[discord.Message]:
        """関連メッセージの収集

        Args:
            trigger_message: トリガーとなったメッセージ

        Returns:
            List[discord.Message]: 関連メッセージのリスト
        """
        related_messages: Set[discord.Message] = set()
        mentioned_messages: Set[discord.Message] = set()

        # 1. トリガーメッセージ自体を追加
        related_messages.add(trigger_message)

        # 2. 直近20件のメッセージを取得
        async for msg in trigger_message.channel.history(limit=20, before=trigger_message):
            related_messages.add(msg)

        # 3. メンション先の処理
        await self._process_mentions(trigger_message, related_messages, mentioned_messages)

        # 4. 他のメッセージのメンション先も処理
        for msg in list(related_messages):
            await self._process_mentions(msg, related_messages, mentioned_messages)

        # 集合をリストに変換し時間順に並べる
        all_messages = list(related_messages.union(mentioned_messages))
        return sorted(all_messages, key=lambda m: m.created_at)

    async def _process_mentions(self, message, related_messages: Set, mentioned_messages: Set):
        """メッセージ内のメンションを処理

        Args:
            message: 処理するメッセージ
            related_messages: 関連メッセージの集合
            mentioned_messages: メンションされたメッセージの集合
        """
        # メッセージ参照があれば取得
        if message.reference and message.reference.message_id:
            try:
                referenced_msg = await message.channel.fetch_message(message.reference.message_id)
                mentioned_messages.add(referenced_msg)

                # さらにそのメッセージの参照も確認（再帰的）
                if referenced_msg.reference and referenced_msg.reference.message_id:
                    await self._process_mentions(referenced_msg, related_messages, mentioned_messages)
            except Exception as e:
                self.logger.warning(f"メッセージ参照の取得エラー: {str(e)}")

    def _build_conversation_thread(self, messages):
        """関連メッセージから会話スレッドを構築

        Args:
            messages: メッセージのリスト

        Returns:
            List: 会話スレッドのリスト
        """
        # 返信関係に基づいて会話スレッドを構築するロジック
        thread_map = {}
        root_messages = []

        for msg in messages:
            if not msg.reference or not msg.reference.message_id:
                # 参照がないメッセージはルートとして扱う
                root_messages.append(msg)
                thread_map[msg.id] = []
            else:
                # 参照があるメッセージは、参照先の子として追加
                parent_id = msg.reference.message_id
                if parent_id in thread_map:
                    thread_map[parent_id].append(msg)
                else:
                    # 親がまだ登録されていない場合、新たに登録
                    thread_map[parent_id] = [msg]

        # スレッド構造を構築
        conversation_threads = []
        for root in root_messages:
            thread = self._build_thread_recursive(root, thread_map)
            conversation_threads.append(thread)

        return conversation_threads

    def _build_thread_recursive(self, message, thread_map):
        """再帰的にスレッドを構築

        Args:
            message: メッセージ
            thread_map: スレッドマップ

        Returns:
            Dict: スレッド構造
        """
        thread = {"message": message, "replies": []}

        # このメッセージへの返信を取得
        if message.id in thread_map:
            for reply in thread_map[message.id]:
                # 返信ごとに再帰的に処理
                reply_thread = self._build_thread_recursive(reply, thread_map)
                thread["replies"].append(reply_thread)

        return thread

    def _format_conversation(self, conversation_threads):
        """会話スレッドをテキスト形式に整形

        Args:
            conversation_threads: 会話スレッドのリスト

        Returns:
            str: 整形されたテキスト
        """
        formatted_text = []

        for thread in conversation_threads:
            formatted_text.append(self._format_thread_recursive(thread, 0))

        return "\n\n".join(formatted_text)

    def _format_thread_recursive(self, thread, indent_level):
        """再帰的にスレッドをテキスト形式に整形

        Args:
            thread: スレッド構造
            indent_level: インデントレベル

        Returns:
            str: 整形されたテキスト
        """
        message = thread["message"]
        indent = "  " * indent_level

        # メッセージ本文を整形
        formatted = f"{indent}**{message.author.name}** ({message.created_at.strftime('%H:%M:%S')}):\n"
        formatted += f"{indent}{message.content}\n"

        # 返信を再帰的に処理
        for reply in thread["replies"]:
            formatted += self._format_thread_recursive(reply, indent_level + 1)

        return formatted

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
