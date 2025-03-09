"""
ルートパッケージ

このパッケージは、発火レイヤーのAPIエンドポイントを提供するルーターを含みます。
"""

from .actions import router as actions_router
from .auth import router as auth_router
from .discord import router as discord_router
from .extensions import router as extensions_router
from .health import router as health_router
from .tasks import router as tasks_router

__all__ = [
    "auth_router",
    "tasks_router",
    "actions_router",
    "extensions_router",
    "discord_router",
    "health_router",
]
