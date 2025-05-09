"""
Discord連携サービスのテストモジュール

このモジュールは、Discord連携サービスのテストを提供します。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import BackgroundTasks

from api.services.discord_service import DiscordBotManager
from goose.executor import TaskExecutor


@pytest.mark.asyncio
async def test_discord_bot_service_singleton():
    """DiscordBotManagerのシングルトンパターンをテスト"""
    # 2つのインスタンスが同じオブジェクトを参照することを確認
    service1 = DiscordBotManager()
    service2 = DiscordBotManager()

    assert service1 is service2


@pytest.mark.asyncio
async def test_discord_bot_service_init():
    """DiscordBotManagerの初期化をテスト"""
    # TaskExecutorのモック
    mock_executor = AsyncMock(spec=TaskExecutor)

    # 既存のインスタンスをリセット
    DiscordBotManager._instance = None

    # 新しいインスタンスを作成
    service = DiscordBotManager()

    # 初期化の検証
    assert service._initialized is True
    assert service._is_running is False
    assert service._bot is None


@pytest.mark.asyncio
async def test_start_bot_no_token():
    """トークンなしでのBot起動をテスト"""
    # 設定のモック
    with patch("api.services.discord_service.settings") as mock_settings:
        mock_settings.DISCORD_BOT_TOKEN = None

        # 既存のインスタンスをリセット
        DiscordBotManager._instance = None

        # サービスのインスタンスを作成
        service = DiscordBotManager()

        # バックグラウンドタスクのモック
        background_tasks = MagicMock(spec=BackgroundTasks)

        # Bot起動を試行
        result = await service.start_bot(background_tasks)

        # 検証
        assert result["success"] is False
        assert "トークンが設定されていません" in result["message"]
        background_tasks.add_task.assert_not_called()


@pytest.mark.asyncio
async def test_start_bot_already_running():
    """既に実行中のBotの起動をテスト"""
    # 設定のモック
    with patch("api.services.discord_service.settings") as mock_settings:
        mock_settings.DISCORD_BOT_TOKEN = "test_token"

        # 既存のインスタンスをリセット
        DiscordBotManager._instance = None

        # サービスのインスタンスを作成
        service = DiscordBotManager()
        service._is_running = True

        # バックグラウンドタスクのモック
        background_tasks = MagicMock(spec=BackgroundTasks)

        # Bot起動を試行
        result = await service.start_bot(background_tasks)

        # 検証
        assert result["success"] is True
        assert "既に実行中" in result["message"]
        background_tasks.add_task.assert_not_called()


@pytest.mark.asyncio
async def test_start_bot_success():
    """Botの起動成功をテスト"""
    # 設定のモック
    with patch("api.services.discord_service.settings") as mock_settings:
        mock_settings.DISCORD_BOT_TOKEN = "test_token"

        # 既存のインスタンスをリセット
        DiscordBotManager._instance = None

        # サービスのインスタンスを作成
        service = DiscordBotManager()
        service._is_running = False

        # バックグラウンドタスクのモック
        background_tasks = MagicMock(spec=BackgroundTasks)

        # Bot起動を試行
        result = await service.start_bot(background_tasks)

        # 検証
        assert result["success"] is True
        assert "起動しています" in result["message"]
        background_tasks.add_task.assert_called_once()
        args, kwargs = background_tasks.add_task.call_args
        assert args[0] == service._run_bot
        # トークンが渡されていることを確認（具体的な値は検証しない）
        assert len(args) > 1


@pytest.mark.asyncio
async def test_stop_bot_not_running():
    """実行されていないBotの停止をテスト"""
    # 既存のインスタンスをリセット
    DiscordBotManager._instance = None

    # サービスのインスタンスを作成
    service = DiscordBotManager()
    service._is_running = False
    service._bot = None

    # Bot停止を試行
    result = await service.stop_bot()

    # 検証
    assert result["success"] is False
    assert "実行されていません" in result["message"]


@pytest.mark.asyncio
async def test_stop_bot_success():
    """Botの停止成功をテスト"""
    # 既存のインスタンスをリセット
    DiscordBotManager._instance = None

    # サービスのインスタンスを作成
    service = DiscordBotManager()
    service._is_running = True

    # _botをモック
    mock_bot = MagicMock()
    mock_bot.close = AsyncMock()
    service._bot = mock_bot

    # Bot停止を試行
    result = await service.stop_bot()

    # 検証
    assert result["success"] is True
    assert "停止しました" in result["message"]
    mock_bot.close.assert_called_once()
    assert service._is_running is False
    assert service._bot is None


@pytest.mark.asyncio
async def test_stop_bot_error():
    """Bot停止時のエラーをテスト"""
    # 既存のインスタンスをリセット
    DiscordBotManager._instance = None

    # サービスのインスタンスを作成
    service = DiscordBotManager()
    service._is_running = True
    service._bot = MagicMock()
    service._bot.close = AsyncMock(side_effect=Exception("停止エラー"))

    # Bot停止を試行
    result = await service.stop_bot()

    # 検証
    assert result["success"] is False
    assert "エラー" in result["message"]


@pytest.mark.asyncio
async def test_get_status():
    """Botのステータス取得をテスト"""
    # 既存のインスタンスをリセット
    DiscordBotManager._instance = None

    # サービスのインスタンスを作成
    service = DiscordBotManager()
    service._is_running = True
    service._bot = MagicMock()
    service._bot.user = "TestBot"

    # ステータス取得
    result = await service.get_status()

    # 検証
    assert result["is_running"] is True
    assert result["bot_user"] == "TestBot"


@pytest.mark.asyncio
async def test_run_bot_success():
    """Bot実行の成功をテスト"""
    # DiscordServiceのモック
    with patch("api.services.discord_service.DiscordBot") as mock_discord_bot_class:
        # モックの設定
        mock_discord_bot = MagicMock()
        mock_discord_bot.start = AsyncMock()
        mock_discord_bot_class.return_value = mock_discord_bot

        # 既存のインスタンスをリセット
        DiscordBotManager._instance = None

        # サービスのインスタンスを作成
        service = DiscordBotManager()

        # _is_runningとservice._botの初期状態を確認
        assert service._is_running is False
        assert service._bot is None

        # Bot実行前にモックを設定
        with patch.object(service, "_bot", mock_discord_bot):
            # Bot実行
            await service._run_bot("test_token")

            # 検証
            mock_discord_bot_class.assert_called_once_with("test_token", service.goose_executor)
            mock_discord_bot.start.assert_called_once()

        # 終了後の状態を検証
        assert service._is_running is False
        assert service._bot is None


@pytest.mark.asyncio
async def test_run_bot_error():
    """Bot実行時のエラーをテスト"""
    # DiscordBotのモック
    with patch("api.services.discord_service.DiscordBot") as mock_discord_bot_class:
        # モックの設定
        mock_discord_bot = MagicMock()
        mock_discord_bot.start = AsyncMock(side_effect=Exception("起動エラー"))
        mock_discord_bot_class.return_value = mock_discord_bot

        # 既存のインスタンスをリセット
        DiscordBotManager._instance = None

        # サービスのインスタンスを作成
        service = DiscordBotManager()

        # _is_runningとservice._botの初期状態を確認
        assert service._is_running is False
        assert service._bot is None

        # Bot実行前にモックを設定
        with patch.object(service, "_bot", mock_discord_bot):
            # Bot実行
            await service._run_bot("test_token")

            # 検証
            mock_discord_bot_class.assert_called_once_with("test_token", service.goose_executor)
            mock_discord_bot.start.assert_called_once()

        # 終了後の状態を検証
        assert service._is_running is False
        assert service._bot is None
