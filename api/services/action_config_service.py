"""
アクション設定関連サービスモジュール

このモジュールは、アクションと設定の関連付けを管理するサービスを提供します。
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import select

from ..database import _get_db_context
from ..models.action import Action
from ..models.action_config import ActionConfig


class ActionConfigService:
    """アクション設定関連サービスクラス"""

    async def create_action_config(
        self,
        action_id: int,
        config_type: str,
        config_id: int,
    ) -> Dict[str, Any]:
        """アクション設定関連を作成

        Args:
            action_id (int): アクションID
            config_type (str): 設定タイプ（"discord", "slack"など）
            config_id (int): 設定ID

        Returns:
            Dict[str, Any]: 作成されたアクション設定関連
        """
        async with _get_db_context() as db:
            action_config = ActionConfig(
                action_id=action_id,
                config_type=config_type,
                config_id=config_id,
            )
            db.add(action_config)
            await db.commit()
            await db.refresh(action_config)

            return self._action_config_to_dict(action_config)

    async def get_action_by_config(
        self,
        config_type: str,
        config_id: int,
    ) -> Optional[Dict[str, Any]]:
        """設定に関連するアクションを取得

        Args:
            config_type (str): 設定タイプ（"discord", "slack"など）
            config_id (int): 設定ID

        Returns:
            Optional[Dict[str, Any]]: 関連するアクション
        """
        async with _get_db_context() as db:
            query = (
                select(Action)
                .join(ActionConfig, Action.id == ActionConfig.action_id)
                .where(
                    ActionConfig.config_type == config_type,
                    ActionConfig.config_id == config_id,
                    Action.is_enabled,
                )
            )
            result = await db.execute(query)
            action = result.scalars().first()

            if not action:
                return None

            return {
                "id": action.id,
                "name": action.name,
                "action_type": action.action_type,
                "task_template_id": action.task_template_id,
                "is_enabled": action.is_enabled,
            }

    async def list_configs_by_action(
        self,
        action_id: int,
        config_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """アクションに関連する設定の一覧を取得

        Args:
            action_id (int): アクションID
            config_type (Optional[str], optional): 設定タイプ。デフォルトはNone

        Returns:
            List[Dict[str, Any]]: 関連する設定のリスト
        """
        async with _get_db_context() as db:
            query = select(ActionConfig).where(ActionConfig.action_id == action_id)

            if config_type:
                query = query.where(ActionConfig.config_type == config_type)

            result = await db.execute(query)
            action_configs = result.scalars().all()

            return [self._action_config_to_dict(config) for config in action_configs]

    def _action_config_to_dict(self, action_config: ActionConfig) -> Dict[str, Any]:
        """アクション設定関連をディクショナリに変換

        Args:
            action_config (ActionConfig): アクション設定関連

        Returns:
            Dict[str, Any]: アクション設定関連の辞書表現
        """
        return {
            "id": action_config.id,
            "action_id": action_config.action_id,
            "config_type": action_config.config_type,
            "config_id": action_config.config_id,
            "created_at": action_config.created_at.isoformat() if action_config.created_at else None,
            "updated_at": action_config.updated_at.isoformat() if action_config.updated_at else None,
        }
