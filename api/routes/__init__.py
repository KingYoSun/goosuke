"""
ルートパッケージ

このパッケージは、発火レイヤーのAPIエンドポイントを提供するルーターを含みます。
"""

from .actions import router as actions_router
from .auth import router as auth_router
from .discord import router as discord_router
from .discord_config import router as discord_config_router
from .extensions import router as extensions_router
from .health import router as health_router
from .mcp import router as mcp_router
from .settings import router as settings_router
from .tasks import router as tasks_router

__all__ = [
    "auth_router",
    "tasks_router",
    "actions_router",
    "extensions_router",
    "discord_router",
    "discord_config_router",
    "health_router",
    "settings_router",
    "mcp_router",  # MCPルーターをエクスポート
]
