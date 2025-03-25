"""
設定サービスモジュール

このモジュールは、アプリケーション設定を管理するサービスを提供します。
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from ..database import _get_db_context
from ..models.setting import Setting
from ..utils.crypto_utils import maybe_decrypt_value, maybe_encrypt_value

logger = logging.getLogger(__name__)


class SettingService:
    """設定サービスクラス"""

    async def list_settings(self) -> List[Dict[str, Any]]:
        """データベースから設定の情報を取得して返す

        Returns:
            List[Dict[str, Any]]: 設定のリスト
        """
        async with _get_db_context() as db:
            result = await db.execute(select(Setting))
            settings = result.scalars().all()

            # 情報を整形
            result = []
            for setting in settings:
                # 秘密情報の場合は値を隠す
                value = setting.value
                if setting.is_secret and value is not None:
                    value = "********"  # 秘密情報は表示しない

                setting_dict = {
                    "id": setting.id,
                    "key": setting.key,
                    "value": value,
                    "description": setting.description,
                    "is_secret": setting.is_secret,
                }

                result.append(setting_dict)

            return result

    async def get_setting(self, setting_id: int) -> Optional[Dict[str, Any]]:
        """特定の設定の詳細を取得

        Args:
            setting_id (int): 設定ID

        Returns:
            Optional[Dict[str, Any]]: 設定の詳細
        """
        async with _get_db_context() as db:
            setting = await db.get(Setting, setting_id)
            if not setting:
                return None

            # 秘密情報の場合は復号化
            value = setting.value
            if setting.is_secret and value is not None:
                value = maybe_decrypt_value(value, True)

            return {
                "id": setting.id,
                "key": setting.key,
                "value": value,
                "description": setting.description,
                "is_secret": setting.is_secret,
            }

    async def get_setting_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """キーで設定を取得

        Args:
            key (str): 設定キー

        Returns:
            Optional[Dict[str, Any]]: 設定の詳細
        """
        async with _get_db_context() as db:
            result = await db.execute(select(Setting).where(Setting.key == key))
            setting = result.scalars().first()
            if not setting:
                return None

            # 秘密情報の場合は復号化
            value = setting.value
            if setting.is_secret and value is not None:
                value = maybe_decrypt_value(value, True)

            return {
                "id": setting.id,
                "key": setting.key,
                "value": value,
                "description": setting.description,
                "is_secret": setting.is_secret,
            }

    async def add_setting(self, setting_data) -> Dict[str, Any]:
        """新しい設定を追加

        Args:
            setting_data: 設定データ

        Returns:
            Dict[str, Any]: 追加された設定
        """
        async with _get_db_context() as db:
            # 秘密情報の場合は暗号化
            value = setting_data.value
            is_secret = getattr(setting_data, "is_secret", False)

            if is_secret and value is not None:
                value = maybe_encrypt_value(value, True)

            # DBに設定情報を追加
            new_setting = Setting(
                key=setting_data.key,
                value=value,
                description=setting_data.description,
                is_secret=is_secret,
            )
            db.add(new_setting)
            await db.commit()
            await db.refresh(new_setting)

            # 秘密情報の場合は値を隠す
            result_value = new_setting.value
            if new_setting.is_secret and result_value is not None:
                result_value = "********"  # 秘密情報は表示しない

            result = {
                "id": new_setting.id,
                "key": new_setting.key,
                "value": result_value,
                "description": new_setting.description,
                "is_secret": new_setting.is_secret,
            }

        return result

    async def update_setting(self, setting_id: int, update_data) -> Optional[Dict[str, Any]]:
        """設定を更新

        Args:
            setting_id (int): 設定ID
            update_data: 更新データ

        Returns:
            Optional[Dict[str, Any]]: 更新された設定
        """
        async with _get_db_context() as db:
            setting = await db.get(Setting, setting_id)
            if not setting:
                return None

            # 更新データを適用
            if hasattr(update_data, "key") and update_data.key is not None:
                setting.key = update_data.key

            if hasattr(update_data, "value") and update_data.value is not None:
                # 秘密情報の場合は暗号化
                value = update_data.value
                if setting.is_secret and value is not None:
                    value = maybe_encrypt_value(value, True)
                setting.value = value

            if hasattr(update_data, "description") and update_data.description is not None:
                setting.description = update_data.description

            if hasattr(update_data, "is_secret") and update_data.is_secret is not None:
                # is_secretが変更された場合は、値の暗号化状態も変更
                if setting.is_secret != update_data.is_secret:
                    if update_data.is_secret and setting.value is not None:
                        # 秘密情報になる場合は暗号化
                        setting.value = maybe_encrypt_value(setting.value, True)
                    elif setting.value is not None:
                        # 秘密情報でなくなる場合は復号化
                        setting.value = maybe_decrypt_value(setting.value, True)

                setting.is_secret = update_data.is_secret

            await db.commit()
            await db.refresh(setting)

            # 秘密情報の場合は値を隠す
            result_value = setting.value
            if setting.is_secret and result_value is not None:
                result_value = "********"  # 秘密情報は表示しない

            result = {
                "id": setting.id,
                "key": setting.key,
                "value": result_value,
                "description": setting.description,
                "is_secret": setting.is_secret,
            }

            return result

    async def remove_setting(self, setting_id: int) -> bool:
        """設定を削除

        Args:
            setting_id (int): 設定ID

        Returns:
            bool: 削除に成功した場合はTrue、それ以外はFalse
        """
        async with _get_db_context() as db:
            setting = await db.get(Setting, setting_id)
            if not setting:
                return False

            await db.delete(setting)
            await db.commit()

            return True
