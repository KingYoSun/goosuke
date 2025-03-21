"""
Discord設定サービスモジュール

このモジュールは、Discord固有の設定を管理するサービスを提供します。
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import select

from ..database import _get_db_context
from ..models.config_discord import ConfigDiscord


class DiscordConfigService:
    """Discord設定サービスクラス"""

    async def create_discord_config(
        self,
        name: str,
        catch_type: str,
        catch_value: str,
        message_type: str = "single",
        response_format: str = "reply",
    ) -> Dict[str, Any]:
        """Discord設定を作成

        Args:
            name (str): 設定名
            catch_type (str): 取得タイプ（'reaction', 'text', 'textWithMention'）
            catch_value (str): 取得対象（絵文字、キーワードなど）
            message_type (str, optional): メッセージ収集戦略。デフォルトは"single"
            response_format (str, optional): レスポンス形式。デフォルトは"reply"

        Returns:
            Dict[str, Any]: 作成されたDiscord設定
        """
        async with _get_db_context() as db:
            discord_config = ConfigDiscord(
                name=name,
                catch_type=catch_type,
                catch_value=catch_value,
                message_type=message_type,
                response_format=response_format,
            )
            db.add(discord_config)
            await db.commit()
            await db.refresh(discord_config)

            return self._discord_config_to_dict(discord_config)

    async def get_discord_config(self, config_id: int) -> Optional[Dict[str, Any]]:
        """Discord設定の詳細を取得

        Args:
            config_id (int): 設定ID

        Returns:
            Optional[Dict[str, Any]]: Discord設定の詳細
        """
        async with _get_db_context() as db:
            discord_config = await db.get(ConfigDiscord, config_id)
            if not discord_config:
                return None

            return self._discord_config_to_dict(discord_config)

    async def get_discord_config_by_reaction(self, reaction_value: str) -> Optional[Dict[str, Any]]:
        """リアクション値に基づいてDiscord設定を取得

        Args:
            reaction_value (str): リアクション値（絵文字）

        Returns:
            Optional[Dict[str, Any]]: マッチするDiscord設定
        """
        async with _get_db_context() as db:
            query = select(ConfigDiscord).where(
                ConfigDiscord.catch_type == "reaction", ConfigDiscord.catch_value == reaction_value
            )
            result = await db.execute(query)
            discord_config = result.scalars().first()

            if not discord_config:
                return None

            return self._discord_config_to_dict(discord_config)

    async def list_discord_configs(
        self,
        catch_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Discord設定の一覧を取得

        Args:
            catch_type (Optional[str], optional): 取得タイプ。デフォルトはNone
            limit (int, optional): 取得件数。デフォルトは10
            offset (int, optional): オフセット。デフォルトは0

        Returns:
            List[Dict[str, Any]]: Discord設定のリスト
        """
        async with _get_db_context() as db:
            query = select(ConfigDiscord)

            if catch_type:
                query = query.where(ConfigDiscord.catch_type == catch_type)

            query = query.order_by(ConfigDiscord.created_at.desc()).limit(limit).offset(offset)

            result = await db.execute(query)
            discord_configs = result.scalars().all()

            return [self._discord_config_to_dict(config) for config in discord_configs]

    async def update_discord_config(
        self,
        config_id: int,
        name: Optional[str] = None,
        catch_type: Optional[str] = None,
        catch_value: Optional[str] = None,
        message_type: Optional[str] = None,
        response_format: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Discord設定を更新

        Args:
            config_id (int): 設定ID
            name (Optional[str], optional): 設定名。デフォルトはNone
            catch_type (Optional[str], optional): 取得タイプ。デフォルトはNone
            catch_value (Optional[str], optional): 取得対象。デフォルトはNone
            message_type (Optional[str], optional): メッセージ収集戦略。デフォルトはNone
            response_format (Optional[str], optional): レスポンス形式。デフォルトはNone

        Returns:
            Optional[Dict[str, Any]]: 更新されたDiscord設定（存在しない場合はNone）
        """
        async with _get_db_context() as db:
            discord_config = await db.get(ConfigDiscord, config_id)
            if not discord_config:
                return None

            # 指定されたフィールドのみ更新
            if name is not None:
                discord_config.name = name
            if catch_type is not None:
                discord_config.catch_type = catch_type
            if catch_value is not None:
                discord_config.catch_value = catch_value
            if message_type is not None:
                discord_config.message_type = message_type
            if response_format is not None:
                discord_config.response_format = response_format

            await db.commit()
            await db.refresh(discord_config)

            return self._discord_config_to_dict(discord_config)

    async def delete_discord_config(self, config_id: int) -> bool:
        """Discord設定を削除

        Args:
            config_id (int): 設定ID

        Returns:
            bool: 削除に成功した場合はTrue、設定が存在しない場合はFalse
        """
        async with _get_db_context() as db:
            discord_config = await db.get(ConfigDiscord, config_id)
            if not discord_config:
                return False

            await db.delete(discord_config)
            await db.commit()

            return True

    def _discord_config_to_dict(self, discord_config: ConfigDiscord) -> Dict[str, Any]:
        """Discord設定をディクショナリに変換

        Args:
            discord_config (ConfigDiscord): Discord設定

        Returns:
            Dict[str, Any]: Discord設定の辞書表現
        """
        return {
            "id": discord_config.id,
            "name": discord_config.name,
            "catch_type": discord_config.catch_type,
            "catch_value": discord_config.catch_value,
            "message_type": discord_config.message_type,
            "response_format": discord_config.response_format,
            "created_at": discord_config.created_at.isoformat() if discord_config.created_at else None,
            "updated_at": discord_config.updated_at.isoformat() if discord_config.updated_at else None,
        }
