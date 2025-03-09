"""
拡張機能サービスモジュール

このモジュールは、Goose拡張機能を管理するサービスを提供します。
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from goose.executor import TaskExecutor

from ..database import get_db
from ..models.extension import Extension


class ExtensionService:
    """拡張機能サービスクラス"""

    def __init__(self, goose_executor: Optional[TaskExecutor] = None):
        """初期化

        Args:
            goose_executor (Optional[TaskExecutor], optional): Goose実行ラッパーインスタンス。デフォルトはNone
        """
        self.goose_executor = goose_executor or TaskExecutor()

    async def list_extensions(self) -> List[Dict[str, Any]]:
        """データベースから拡張機能の情報を取得して返す

        Returns:
            List[Dict[str, Any]]: 拡張機能のリスト
        """
        async with get_db() as db:
            db_extensions = await self._get_db_extensions(db)

            # 情報を整形
            result = []
            for ext in db_extensions:
                ext_dict = {
                    "id": ext.id,
                    "name": ext.name,
                    "description": ext.description,
                    "enabled": ext.enabled,
                    "config": ext.config,
                }

                result.append(ext_dict)

            return result

    async def add_extension(self, extension_data) -> Dict[str, Any]:
        """新しい拡張機能を追加

        Args:
            extension_data: 拡張機能データ

        Returns:
            Dict[str, Any]: 追加された拡張機能
        """
        async with get_db() as db:
            # DBに拡張機能情報を追加
            new_extension = Extension(
                name=extension_data.name,
                description=extension_data.description,
                enabled=True,
                config=extension_data.config,
            )
            db.add(new_extension)
            await db.commit()
            await db.refresh(new_extension)

            # 拡張機能の実際のインストールはここで行うか、別の関数で実装
            # この例では手動でのインストールが必要であることを通知

            return {
                "id": new_extension.id,
                "name": new_extension.name,
                "description": new_extension.description,
                "enabled": new_extension.enabled,
                "config": new_extension.config,
            }

    async def get_extension(self, extension_id: int) -> Optional[Dict[str, Any]]:
        """特定の拡張機能の詳細を取得

        Args:
            extension_id (int): 拡張機能ID

        Returns:
            Optional[Dict[str, Any]]: 拡張機能の詳細
        """
        async with get_db() as db:
            extension = await db.get(Extension, extension_id)
            if not extension:
                return None

            return {
                "id": extension.id,
                "name": extension.name,
                "description": extension.description,
                "enabled": extension.enabled,
                "config": extension.config,
            }

    async def update_extension(self, extension_id: int, update_data) -> Optional[Dict[str, Any]]:
        """拡張機能の設定を更新

        Args:
            extension_id (int): 拡張機能ID
            update_data: 更新データ

        Returns:
            Optional[Dict[str, Any]]: 更新された拡張機能
        """
        async with get_db() as db:
            extension = await db.get(Extension, extension_id)
            if not extension:
                return None

            # 更新データを適用
            if hasattr(update_data, "enabled") and update_data.enabled is not None:
                extension.enabled = update_data.enabled

            if hasattr(update_data, "config") and update_data.config is not None:
                # 既存の設定と新しい設定をマージ
                extension.config = {**extension.config, **update_data.config}

            await db.commit()
            await db.refresh(extension)

            return {
                "id": extension.id,
                "name": extension.name,
                "description": extension.description,
                "enabled": extension.enabled,
                "config": extension.config,
            }

    async def remove_extension(self, extension_id: int) -> bool:
        """拡張機能を削除

        Args:
            extension_id (int): 拡張機能ID

        Returns:
            bool: 削除に成功した場合はTrue、それ以外はFalse
        """
        async with get_db() as db:
            extension = await db.get(Extension, extension_id)
            if not extension:
                return False

            await db.delete(extension)
            await db.commit()

            return True

    async def install_extension_from_url(self, name: str, url: str, description: str = "") -> Dict[str, Any]:
        """URLから拡張機能をインストール

        注意: 新しいGoose CLIコマンド体系では拡張機能のインストールコマンドが提供されていないため、
        このメソッドは手動でのインストールが必要であることを通知します。

        Args:
            name (str): 拡張機能名
            url (str): 拡張機能のURL
            description (str, optional): 説明。デフォルトは空文字

        Returns:
            Dict[str, Any]: インストール結果
        """
        # 新しいGoose CLIコマンド体系では拡張機能のインストールコマンドが提供されていないため、
        # 手動でのインストールが必要であることを通知
        message = "新しいGoose CLIコマンド体系では拡張機能のインストールコマンドが提供されていません。手動でのインストールが必要です。"

        # データベースに拡張機能情報を追加
        async with get_db() as db:
            # 既存の拡張機能を確認
            result = await db.execute(select(Extension).where(Extension.name == name))
            existing = result.scalars().first()

            if existing:
                # 既存の拡張機能を更新
                existing.description = description
                await db.commit()
                await db.refresh(existing)
                extension_id = existing.id
            else:
                # 新しい拡張機能を追加
                new_extension = Extension(name=name, description=description, enabled=True, config={})
                db.add(new_extension)
                await db.commit()
                await db.refresh(new_extension)
                extension_id = new_extension.id

        return {"success": True, "message": message, "extension_id": extension_id}

    async def _get_db_extensions(self, db: AsyncSession) -> List[Extension]:
        """データベースから全ての拡張機能を取得

        Args:
            db (AsyncSession): データベースセッション

        Returns:
            List[Extension]: 拡張機能のリスト
        """
        result = await db.execute(select(Extension))
        return list(result.scalars().all())
