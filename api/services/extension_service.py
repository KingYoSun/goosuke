"""
拡張機能サービスモジュール

このモジュールは、Goose拡張機能を管理するサービスを提供します。
"""

import logging
import os
from typing import Any, Dict, List, Optional

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from goose.executor import TaskExecutor

from ..database import _get_db_context
from ..models.extension import Extension
from ..utils.goose_config import get_goose_config_path, read_goose_config, read_goose_extensions

logger = logging.getLogger(__name__)


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
        async with _get_db_context() as db:
            db_extensions = await self._get_db_extensions(db)

            # 情報を整形
            result = []
            for ext in db_extensions:
                ext_dict = {
                    "id": ext.id,
                    "name": ext.name,
                    "description": ext.description,
                    "enabled": ext.enabled,
                    "type": ext.type,
                    "cmd": ext.cmd,
                    "args": ext.args,
                    "timeout": ext.timeout,
                    "envs": ext.envs,
                    "secrets": ext.secrets,
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
        async with _get_db_context() as db:
            # DBに拡張機能情報を追加
            new_extension = Extension(
                name=extension_data.name,
                description=extension_data.description,
                enabled=extension_data.enabled,
                type=extension_data.type,
                cmd=extension_data.cmd,
                args=extension_data.args,
                timeout=extension_data.timeout,
                envs=extension_data.envs,
                secrets=extension_data.secrets,
            )
            db.add(new_extension)
            await db.commit()
            await db.refresh(new_extension)

            # 拡張機能の実際のインストールはここで行うか、別の関数で実装
            # この例では手動でのインストールが必要であることを通知

            result = {
                "id": new_extension.id,
                "name": new_extension.name,
                "description": new_extension.description,
                "enabled": new_extension.enabled,
                "type": new_extension.type,
                "cmd": new_extension.cmd,
                "args": new_extension.args,
                "timeout": new_extension.timeout,
                "envs": new_extension.envs,
                "secrets": new_extension.secrets,
            }

            # Goose の設定ファイルに同期
            try:
                await self.sync_to_goose()
                logger.info(f"拡張機能の追加後に Goose の設定ファイルに同期しました: {new_extension.name}")
            except Exception as e:
                logger.error(f"拡張機能の追加後の同期中にエラーが発生しました: {e}")

        return result

    async def get_extension(self, extension_id: int) -> Optional[Dict[str, Any]]:
        """特定の拡張機能の詳細を取得

        Args:
            extension_id (int): 拡張機能ID

        Returns:
            Optional[Dict[str, Any]]: 拡張機能の詳細
        """
        async with _get_db_context() as db:
            extension = await db.get(Extension, extension_id)
            if not extension:
                return None

            return {
                "id": extension.id,
                "name": extension.name,
                "description": extension.description,
                "enabled": extension.enabled,
                "type": extension.type,
                "cmd": extension.cmd,
                "args": extension.args,
                "timeout": extension.timeout,
                "envs": extension.envs,
                "secrets": extension.secrets,
            }

    async def update_extension(self, extension_id: int, update_data) -> Optional[Dict[str, Any]]:
        """拡張機能の設定を更新

        Args:
            extension_id (int): 拡張機能ID
            update_data: 更新データ

        Returns:
            Optional[Dict[str, Any]]: 更新された拡張機能
        """
        async with _get_db_context() as db:
            extension = await db.get(Extension, extension_id)
            if not extension:
                return None

            # 更新データを適用
            if hasattr(update_data, "enabled") and update_data.enabled is not None:
                extension.enabled = update_data.enabled

            if hasattr(update_data, "type") and update_data.type is not None:
                extension.type = update_data.type

            if hasattr(update_data, "cmd") and update_data.cmd is not None:
                extension.cmd = update_data.cmd

            if hasattr(update_data, "args") and update_data.args is not None:
                extension.args = update_data.args

            if hasattr(update_data, "timeout") and update_data.timeout is not None:
                extension.timeout = update_data.timeout

            if hasattr(update_data, "envs") and update_data.envs is not None:
                extension.envs = update_data.envs

            if hasattr(update_data, "secrets") and update_data.secrets is not None:
                extension.secrets = update_data.secrets

            await db.commit()
            await db.refresh(extension)

            result = {
                "id": extension.id,
                "name": extension.name,
                "description": extension.description,
                "enabled": extension.enabled,
                "type": extension.type,
                "cmd": extension.cmd,
                "args": extension.args,
                "timeout": extension.timeout,
                "envs": extension.envs,
                "secrets": extension.secrets,
            }

            # Goose の設定ファイルに同期
            try:
                await self.sync_to_goose()
                logger.info(f"拡張機能の更新後に Goose の設定ファイルに同期しました: {extension.name}")
            except Exception as e:
                logger.error(f"拡張機能の更新後の同期中にエラーが発生しました: {e}")

            return result

    async def remove_extension(self, extension_id: int) -> bool:
        """拡張機能を削除

        Args:
            extension_id (int): 拡張機能ID

        Returns:
            bool: 削除に成功した場合はTrue、それ以外はFalse
        """
        async with _get_db_context() as db:
            extension = await db.get(Extension, extension_id)
            if not extension:
                return False

            extension_name = extension.name
            await db.delete(extension)
            await db.commit()

            # Goose の設定ファイルに同期
            try:
                await self.sync_to_goose()
                logger.info(f"拡張機能の削除後に Goose の設定ファイルに同期しました: {extension_name}")
            except Exception as e:
                logger.error(f"拡張機能の削除後の同期中にエラーが発生しました: {e}")

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

        async with _get_db_context() as db:
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
                # URLから拡張機能をインストールする場合は、stdio タイプとして扱う
                new_extension = Extension(
                    name=name,
                    description=description,
                    enabled=True,
                    type="stdio",
                    cmd="npx",
                    args=["-y", url],
                    timeout=300,
                    envs={},
                    secrets=[],
                )
                db.add(new_extension)
                await db.commit()
                await db.refresh(new_extension)
                extension_id = new_extension.id

            # Goose の設定ファイルに同期
            try:
                await self.sync_to_goose()
                logger.info(f"拡張機能のインストール後に Goose の設定ファイルに同期しました: {name}")
            except Exception as e:
                logger.error(f"拡張機能のインストール後の同期中にエラーが発生しました: {e}")

            return {"success": True, "message": message, "extension_id": extension_id}

    async def _get_db_extensions(self, db: AsyncSession) -> List[Extension]:
        """データベースから全ての拡張機能を取得

        Args:
            db (AsyncSession): データベースセッション

        Returns:
            List[Extension]: 拡張機能のリスト
        """
        # テーブル作成処理はconftest.pyで行われるため、ここでは行わない
        # 拡張機能を取得
        try:
            result = await db.execute(select(Extension))
            extensions = list(result.scalars().all())
            logger.info(f"拡張機能を{len(extensions)}件取得しました")
            return extensions
        except Exception as e:
            logger.error(f"拡張機能取得中にエラーが発生しました: {e}")
            # エラーが発生した場合は空のリストを返す
            return []

    async def sync_to_goose(self) -> Dict[str, Any]:
        """Goosuke のデータベースの拡張機能を Goose の設定ファイルに同期する

        Goosuke のデータベースから拡張機能の情報を取得し、
        Goose の設定ファイルに反映します。

        Returns:
            Dict[str, Any]: 同期結果
        """
        logger.info("Goosuke の拡張機能を Goose の設定ファイルに同期しています...")

        try:
            # Goose の設定ファイルを読み取る
            config_path = get_goose_config_path()
            config = read_goose_config()

            # extensions キーがなければ初期化
            if "extensions" not in config:
                config["extensions"] = {}

            async with _get_db_context() as db:
                # データベースから全ての拡張機能を取得
                db_extensions = await self._get_db_extensions(db)

                # データベースの拡張機能を設定ファイルに反映
                for ext in db_extensions:
                    key = ext.name.lower().replace(" ", "")

                    # 拡張機能エントリを作成
                    # 各フィールドを直接 extensions.{key} の下に配置
                    extension_config = {
                        "enabled": ext.enabled,
                        "type": ext.type,
                    }

                    # 必須でないフィールドは None でない場合のみ追加
                    if ext.cmd is not None:
                        extension_config["cmd"] = ext.cmd

                    if ext.args is not None:
                        extension_config["args"] = ext.args

                    if ext.timeout is not None:
                        extension_config["timeout"] = ext.timeout

                    if ext.envs is not None:
                        extension_config["envs"] = ext.envs.copy() if isinstance(ext.envs, dict) else {}
                    else:
                        extension_config["envs"] = {}

                    # 秘密情報の設定
                    try:
                        if ext.secrets is not None and isinstance(ext.secrets, list):
                            # 秘密情報のキーリストから値を取得
                            # 循環インポートを避けるため、必要な時だけインポート
                            from ..services.setting_service import SettingService

                            setting_service = SettingService()

                            for secret_key in ext.secrets:
                                # 設定値を取得
                                setting = await setting_service.get_setting_by_key(secret_key)
                                if setting and setting["value"] is not None:
                                    # 値を拡張機能の環境変数に追加
                                    extension_config["envs"][secret_key] = setting["value"]
                                    logger.info(f"拡張機能 {ext.name} に秘密情報 {secret_key} を設定しました")
                    except Exception as e:
                        logger.error(f"拡張機能 {ext.name} の秘密情報処理中にエラーが発生しました: {e}")

                    # 名前も追加
                    extension_config["name"] = ext.name

                    config["extensions"][key] = extension_config

            # 設定ファイルを保存
            os.makedirs(config_path.parent, exist_ok=True)
            with open(config_path, "w") as f:
                yaml.dump(config, f)

            logger.info(
                f"Goosuke の拡張機能を Goose の設定ファイルに同期しました。{len(db_extensions)}件の拡張機能を同期しました。"
            )
            return {
                "success": True,
                "message": f"Goosuke の拡張機能を Goose の設定ファイルに同期しました。{len(db_extensions)}件の拡張機能を同期しました。",
                "synced_count": len(db_extensions),
            }
        except Exception as e:
            logger.error(f"Goose の設定ファイルへの同期中にエラーが発生しました: {e}")
            return {
                "success": False,
                "message": f"Goose の設定ファイルへの同期中にエラーが発生しました: {str(e)}",
                "synced_count": 0,
            }

    async def sync_from_goose(self) -> Dict[str, Any]:
        """Goose の拡張機能設定を Goosuke のデータベースに同期する

        Goose の設定ファイルから拡張機能の設定を読み取り、
        Goosuke のデータベースに反映します。

        Returns:
            Dict[str, Any]: 同期結果
        """
        logger.info("Goose の拡張機能設定を同期しています...")

        try:
            # Goose の拡張機能設定を読み取る
            goose_extensions = read_goose_extensions()
            if not goose_extensions:
                logger.info("Goose の拡張機能設定が見つかりませんでした。空の設定として処理します。")
                return {
                    "success": True,
                    "message": "Goose の拡張機能設定が見つかりませんでした。空の設定として処理します。",
                    "synced_count": 0,
                }

            synced_count = 0

            async with _get_db_context() as db:
                # データベースから既存の拡張機能を取得
                db_extensions = await self._get_db_extensions(db)
                db_extensions_dict = {ext.name: ext for ext in db_extensions}

                # Goose の拡張機能を Goosuke のデータベースに反映
                for key, entry in goose_extensions.items():
                    if not entry.get("enabled", False):
                        continue

                    # 設定は直接 entry に含まれている（config キーの下ではない）
                    # enabled フラグは別途取得
                    enabled = entry.get("enabled", False)

                    # 各フィールドを直接取得
                    extension_type = entry.get("type")
                    name = entry.get("name", "")

                    if not name:
                        logger.warning(f"拡張機能名が見つかりません: {key}")
                        continue

                    if name in db_extensions_dict:
                        # 既存の拡張機能を更新
                        ext = db_extensions_dict[name]
                        ext.enabled = enabled
                        ext.type = extension_type

                        # 他のフィールドも更新
                        if "cmd" in entry:
                            ext.cmd = entry.get("cmd")
                        if "args" in entry:
                            ext.args = entry.get("args")
                        if "timeout" in entry:
                            ext.timeout = entry.get("timeout")
                        if "envs" in entry:
                            ext.envs = entry.get("envs")

                        logger.info(f"拡張機能を更新しました: {name}")
                    else:
                        # 新しい拡張機能を追加
                        description = ""
                        if extension_type == "builtin":
                            description = f"Goose built-in extension: {name}"
                        elif extension_type == "stdio":
                            description = f"Goose stdio extension: {name}"
                        elif extension_type == "sse":
                            description = f"Goose SSE extension: {name}"
                        else:
                            description = f"Goose extension: {name}"

                        new_extension = Extension(
                            name=name,
                            description=description,
                            enabled=enabled,
                            type=extension_type,
                            cmd=entry.get("cmd"),
                            args=entry.get("args"),
                            timeout=entry.get("timeout"),
                            envs=entry.get("envs"),
                        )
                        db.add(new_extension)
                        logger.info(f"新しい拡張機能を追加しました: {name}")

                    synced_count += 1

                # データベースの変更を保存
                await db.commit()

            logger.info(f"Goose の拡張機能設定の同期が完了しました。{synced_count}件の拡張機能を同期しました。")
            return {
                "success": True,
                "message": f"Goose の拡張機能設定を同期しました。{synced_count}件の拡張機能を同期しました。",
                "synced_count": synced_count,
            }
        except Exception as e:
            logger.error(f"拡張機能の同期中にエラーが発生しました: {e}")
            return {"success": False, "message": f"拡張機能の同期中にエラーが発生しました: {str(e)}", "synced_count": 0}
