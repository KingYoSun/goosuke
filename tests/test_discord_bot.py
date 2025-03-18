"""
Discord Bot機能のテストモジュール

このモジュールは、Discord Bot機能のテストを提供します。
Discord.pyのクライアントとイベントハンドラをモックして、機能をテストします。
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from extensions.discord.bot import DiscordService
from goose.executor import TaskExecutor


class MockMessage:
    """モックメッセージクラス"""

    def __init__(
        self,
        content="テストメッセージ",
        author=None,
        channel=None,
        id=12345,
        created_at=None,
        reference=None,
        jump_url="https://discord.com/test",
    ):
        self.content = content
        self.author = author or MockUser()
        self.channel = channel or MockChannel()
        self.id = id
        self.created_at = created_at or datetime.now()
        self.reference = reference
        self.jump_url = jump_url


class MockUser:
    """モックユーザークラス"""

    def __init__(self, name="testuser", id=67890, bot=False, mention="<@67890>"):
        self.name = name
        self.id = id
        self.bot = bot
        self.mention = mention


class MockAsyncIterator:
    """非同期イテレータのモック"""

    def __init__(self, items):
        self.items = items

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return self.items.pop(0)
        except IndexError:
            raise StopAsyncIteration


class MockChannel:
    """モックチャンネルクラス"""

    def __init__(self, name="testchannel", id=54321):
        self.name = name
        self.id = id
        self.history = AsyncMock()
        self.send = AsyncMock()
        self.fetch_message = AsyncMock()
        # historyメソッドが返すモックを設定
        self.history.return_value = MockAsyncIterator([])

    async def send(self, content=None, **kwargs):
        """メッセージ送信のモック"""
        mock_msg = MockMessage(content=content)
        mock_msg.edit = AsyncMock()
        return mock_msg


class MockReaction:
    """モックリアクションクラス"""

    def __init__(self, emoji="✏️", message=None):
        self.emoji = emoji
        self.message = message or MockMessage()


class MockReference:
    """モックメッセージ参照クラス"""

    def __init__(self, message_id=None):
        self.message_id = message_id


@pytest.mark.asyncio
async def test_discord_service_init():
    """DiscordServiceの初期化をテスト"""
    # TaskExecutorのモック
    mock_executor = AsyncMock(spec=TaskExecutor)

    # discord.Intentsとcommands.Botをモック
    with (
        patch("discord.Intents.all") as mock_intents,
        patch("discord.ext.commands.Bot") as mock_bot_class,
    ):

        # モックの設定
        mock_intents.return_value = MagicMock()
        mock_bot = MagicMock()
        mock_bot_class.return_value = mock_bot

        # DiscordServiceのインスタンスを作成
        service = DiscordService("test_token", mock_executor)

        # 初期化の検証
        assert service.token == "test_token"
        assert service.goose_executor == mock_executor
        assert service.bot == mock_bot
        mock_bot_class.assert_called_once()


@pytest.mark.asyncio
async def test_on_ready_handler():
    """on_readyイベントハンドラをテスト"""

    # TaskExecutorのモック
    mock_executor = AsyncMock(spec=TaskExecutor)

    # DiscordServiceのインスタンスを作成
    with (
        patch("discord.Intents.all"),
        patch("discord.ext.commands.Bot") as mock_bot_class,
    ):

        # モックの設定
        mock_bot = MagicMock()
        mock_bot_class.return_value = mock_bot
        mock_bot.user = "TestBot"

        # モックの設定
        # eventデコレータが関数を受け取って同じ関数を返すようにする
        event_handlers = {}

        def mock_event_decorator(func):
            # デコレータが呼ばれたときに関数名をキーとして保存
            event_handlers[func.__name__] = func
            return func

        mock_bot.event = mock_event_decorator

        # DiscordServiceのインスタンスを作成
        service = DiscordService("test_token", mock_executor)

        # on_readyハンドラを取得
        on_ready_handler = event_handlers.get("on_ready")

        assert on_ready_handler is not None
        # イベントハンドラを実行
        await on_ready_handler()
        # ログ出力の検証は難しいため、エラーが発生しないことを確認


@pytest.mark.asyncio
async def test_on_reaction_add_handler_bot_reaction():
    """Botからのリアクションを無視するテスト"""
    # TaskExecutorのモック
    mock_executor = AsyncMock(spec=TaskExecutor)

    # DiscordServiceのインスタンスを作成
    with (
        patch("discord.Intents.all"),
        patch("discord.ext.commands.Bot") as mock_bot_class,
    ):

        # モックの設定
        mock_bot = MagicMock()
        mock_bot_class.return_value = mock_bot

        # DiscordServiceのインスタンスを作成
        service = DiscordService("test_token", mock_executor)

        # _handle_pencil_reactionをモック
        service._handle_pencil_reaction = AsyncMock()

        # on_reaction_addイベントハンドラを取得
        on_reaction_add_handler = None
        for call in mock_bot.event.call_args_list:
            if len(call.args) > 0 and call.args[0].__name__ == "on_reaction_add":
                on_reaction_add_handler = call.args[0]
                break

        assert on_reaction_add_handler is not None

        # Botからのリアクションをテスト
        bot_user = MockUser(bot=True)
        reaction = MockReaction()

        # イベントハンドラを実行
        await on_reaction_add_handler(reaction, bot_user)

        # _handle_pencil_reactionが呼ばれないことを検証
        service._handle_pencil_reaction.assert_not_called()


@pytest.mark.asyncio
async def test_on_reaction_add_handler_pencil_reaction():
    """鉛筆リアクションの処理をテスト"""
    # TaskExecutorのモック
    mock_executor = AsyncMock(spec=TaskExecutor)

    # DiscordServiceのインスタンスを作成
    with (
        patch("discord.Intents.all"),
        patch("discord.ext.commands.Bot") as mock_bot_class,
    ):

        # モックの設定
        mock_bot = MagicMock()
        mock_bot_class.return_value = mock_bot

        # DiscordServiceのインスタンスを作成
        service = DiscordService("test_token", mock_executor)

        # _handle_pencil_reactionをモック
        service._handle_pencil_reaction = AsyncMock()

        # on_reaction_addイベントハンドラを取得
        on_reaction_add_handler = None
        for call in mock_bot.event.call_args_list:
            if len(call.args) > 0 and call.args[0].__name__ == "on_reaction_add":
                on_reaction_add_handler = call.args[0]
                break

        assert on_reaction_add_handler is not None

        # 通常ユーザーからの鉛筆リアクションをテスト
        user = MockUser()
        message = MockMessage()
        reaction = MockReaction(emoji="✏️", message=message)

        # イベントハンドラを実行
        await on_reaction_add_handler(reaction, user)

        # _handle_pencil_reactionが呼ばれることを検証
        service._handle_pencil_reaction.assert_called_once_with(message, user)


@pytest.mark.asyncio
async def test_on_reaction_add_handler_non_pencil_reaction():
    """鉛筆以外のリアクションの処理をテスト"""
    # TaskExecutorのモック
    mock_executor = AsyncMock(spec=TaskExecutor)

    # DiscordServiceのインスタンスを作成
    with (
        patch("discord.Intents.all"),
        patch("discord.ext.commands.Bot") as mock_bot_class,
    ):

        # モックの設定
        mock_bot = MagicMock()
        mock_bot_class.return_value = mock_bot

        # DiscordServiceのインスタンスを作成
        service = DiscordService("test_token", mock_executor)

        # _handle_pencil_reactionをモック
        service._handle_pencil_reaction = AsyncMock()

        # on_reaction_addイベントハンドラを取得
        on_reaction_add_handler = None
        for call in mock_bot.event.call_args_list:
            if len(call.args) > 0 and call.args[0].__name__ == "on_reaction_add":
                on_reaction_add_handler = call.args[0]
                break

        assert on_reaction_add_handler is not None

        # 通常ユーザーからの他のリアクションをテスト
        user = MockUser()
        reaction = MockReaction(emoji="👍")

        # イベントハンドラを実行
        await on_reaction_add_handler(reaction, user)

        # _handle_pencil_reactionが呼ばれないことを検証
        service._handle_pencil_reaction.assert_not_called()


@pytest.mark.asyncio
async def test_handle_pencil_reaction_success():
    """鉛筆リアクション処理の成功をテスト"""
    # TaskExecutorのモック
    mock_executor = AsyncMock(spec=TaskExecutor)
    mock_executor.execute.return_value = {"success": True, "output": "テスト要約結果"}

    # DiscordServiceのインスタンスを作成
    with patch("discord.Intents.all"), patch("discord.ext.commands.Bot"):

        # DiscordServiceのインスタンスを作成
        service = DiscordService("test_token", mock_executor)

        # _collect_related_messagesと_build_conversation_threadをモック
        service._collect_related_messages = AsyncMock()
        service._build_conversation_thread = MagicMock()
        service._format_conversation = MagicMock()

        # モックの戻り値を設定
        mock_messages = [
            MockMessage(content="テストメッセージ1"),
            MockMessage(content="テストメッセージ2"),
        ]
        service._collect_related_messages.return_value = mock_messages
        service._build_conversation_thread.return_value = [{"message": msg, "replies": []} for msg in mock_messages]
        service._format_conversation.return_value = "整形された会話"

        # テスト用のメッセージとユーザー
        channel = MockChannel()
        message = MockMessage(channel=channel)
        user = MockUser()

        # 処理を実行
        await service._handle_pencil_reaction(message, user)

        # 検証
        channel.send.assert_called_once()
        processing_msg = await channel.send()
        processing_msg.edit.assert_called()

        # Goose実行が正しく呼ばれたことを検証
        mock_executor.execute.assert_called_once()
        call_args = mock_executor.execute.call_args
        assert "要約" in call_args.args[0]
        # 実装ではconversation_textではなくmessagesキーを使用している
        assert "messages" in call_args.kwargs.get("context", {})


@pytest.mark.asyncio
async def test_handle_pencil_reaction_goose_error():
    """Goose実行エラーのテスト"""
    # TaskExecutorのモック
    mock_executor = AsyncMock(spec=TaskExecutor)
    mock_executor.execute.return_value = {
        "success": False,
        "output": "エラーメッセージ",
    }

    # DiscordServiceのインスタンスを作成
    with patch("discord.Intents.all"), patch("discord.ext.commands.Bot"):

        # DiscordServiceのインスタンスを作成
        service = DiscordService("test_token", mock_executor)

        # _collect_related_messagesと_build_conversation_threadをモック
        service._collect_related_messages = AsyncMock()
        service._build_conversation_thread = MagicMock()
        service._format_conversation = MagicMock()

        # モックの戻り値を設定
        mock_messages = [MockMessage(content="テストメッセージ")]
        service._collect_related_messages.return_value = mock_messages
        service._build_conversation_thread.return_value = [{"message": mock_messages[0], "replies": []}]
        service._format_conversation.return_value = "整形された会話"

        # テスト用のメッセージとユーザー
        channel = MockChannel()
        message = MockMessage(channel=channel)
        user = MockUser()

        # 処理を実行
        await service._handle_pencil_reaction(message, user)

        # 検証
        channel.send.assert_called_once()
        processing_msg = await channel.send()
        processing_msg.edit.assert_called_once()

        # エラーメッセージが表示されることを検証
        edit_args = processing_msg.edit.call_args[1]
        assert "エラーが発生しました" in edit_args["content"]


@pytest.mark.asyncio
async def test_start_and_close():
    """Botの起動と停止をテスト"""
    # TaskExecutorのモック
    mock_executor = AsyncMock(spec=TaskExecutor)

    # DiscordServiceのインスタンスを作成
    with (
        patch("discord.Intents.all"),
        patch("discord.ext.commands.Bot") as mock_bot_class,
    ):

        # モックの設定
        mock_bot = MagicMock()
        mock_bot.start = AsyncMock()
        mock_bot.close = AsyncMock()
        mock_bot_class.return_value = mock_bot

        # DiscordServiceのインスタンスを作成
        service = DiscordService("test_token", mock_executor)

        # 起動テスト
        await service.start()
        mock_bot.start.assert_called_once_with("test_token")

        # 停止テスト
        await service.close()
        mock_bot.close.assert_called_once()


def test_message_to_dict():
    """メッセージの辞書変換をテスト"""
    # TaskExecutorのモック
    mock_executor = AsyncMock(spec=TaskExecutor)

    # DiscordServiceのインスタンスを作成
    with patch("discord.Intents.all"), patch("discord.ext.commands.Bot"):

        # DiscordServiceのインスタンスを作成
        service = DiscordService("test_token", mock_executor)

        # テスト用のメッセージ
        reference = MockReference(message_id=777)
        author = MockUser(name="テストユーザー")
        created_at = datetime.now()
        message = MockMessage(
            id=123,
            content="テスト内容",
            author=author,
            created_at=created_at,
            reference=reference,
        )

        # 変換を実行
        result = service._message_to_dict(message)

        # 検証
        assert result["id"] == "123"
        assert result["author"] == "テストユーザー"
        assert result["content"] == "テスト内容"
        assert result["timestamp"] == created_at.isoformat()
        assert result["reference_id"] == "777"


def test_split_message():
    """メッセージ分割をテスト"""
    # TaskExecutorのモック
    mock_executor = AsyncMock(spec=TaskExecutor)

    # DiscordServiceのインスタンスを作成
    with patch("discord.Intents.all"), patch("discord.ext.commands.Bot"):

        # DiscordServiceのインスタンスを作成
        service = DiscordService("test_token", mock_executor)

        # テスト用の長いメッセージ
        long_message = "a" * 100 + "b" * 100 + "c" * 100

        # 分割を実行（チャンクサイズ100）
        result = service._split_message(long_message, 100)

        # 検証
        assert len(result) == 3
        assert result[0] == "a" * 100
        assert result[1] == "b" * 100
        assert result[2] == "c" * 100
