"""
Discord連携サービスモジュール

このモジュールは、Discord連携機能を提供するサービスを実装します。
"""

import logging
from typing import Optional

from fastapi import BackgroundTasks

from extensions.discord import DiscordService
from goose.executor import TaskExecutor

from ..config import settings
from .task_service import TaskService


class DiscordBotService:
    """Discord Bot連携サービスクラス"""

    _instance = None
    _bot = None
    _is_running = False
    _initialized = False

    def __new__(cls, *args, **kwargs):
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super(DiscordBotService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, goose_executor: Optional[TaskExecutor] = None):
        """初期化

        Args:
            goose_executor (Optional[TaskExecutor], optional): Goose実行ラッパーインスタンス。デフォルトはNone
        """
        # シングルトンの初期化は一度だけ
        if self._initialized:
            return

        self.logger = logging.getLogger("discord_bot_service")
        self.goose_executor = goose_executor or TaskExecutor()
        self.task_service = TaskService(self.goose_executor)
        self._initialized = True

    async def start_bot(self, background_tasks: BackgroundTasks):
        """Botを起動

        Args:
            background_tasks (BackgroundTasks): バックグラウンドタスク
        """
        if not settings.DISCORD_BOT_TOKEN:
            self.logger.error("Discord Botトークンが設定されていません")
            return {
                "success": False,
                "message": "Discord Botトークンが設定されていません",
            }

        if self._is_running:
            return {"success": True, "message": "Discord Botは既に実行中です"}

        # バックグラウンドでBotを起動
        background_tasks.add_task(self._run_bot)

        return {"success": True, "message": "Discord Botを起動しています"}

    async def stop_bot(self):
        """Botを停止"""
        if not self._is_running or not self._bot:
            return {"success": False, "message": "Discord Botは実行されていません"}

        try:
            await self._bot.close()
            self._is_running = False
            self._bot = None

            return {"success": True, "message": "Discord Botを停止しました"}
        except Exception as e:
            self.logger.error(f"Discord Bot停止エラー: {str(e)}")
            return {"success": False, "message": f"Discord Bot停止エラー: {str(e)}"}

    async def get_status(self):
        """Botのステータスを取得"""
        return {
            "is_running": self._is_running,
            "bot_user": str(self._bot.user) if self._bot and self._bot.user else None,
        }

    async def _run_bot(self):
        """Botを実行（バックグラウンドタスク）"""
        try:
            self._bot = DiscordService(settings.DISCORD_BOT_TOKEN, self.goose_executor)
            self._is_running = True

            self.logger.info("Discord Botを起動しています...")
            await self._bot.start()
        except Exception as e:
            self.logger.error(f"Discord Bot実行エラー: {str(e)}")
            self._is_running = False
            self._bot = None
        finally:
            self._is_running = False
            self._bot = None
            self.logger.info("Discord Botが停止しました")
