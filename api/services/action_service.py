"""
アクションサービスモジュール

このモジュールは、システムへの入力点（APIリクエスト、Botメッセージ、Webhookなど）を管理するサービスを提供します。
アクションからコンテキストを抽出し、タスクの生成に必要な情報を提供します。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from ..database import _get_db_context
from ..models.action import Action
from ..models.task_template import TaskTemplate
from .task_service import TaskService


class ActionService:
    """アクションサービスクラス
    発火レイヤーの中核となるサービス
    """

    def __init__(self, task_service: Optional[TaskService] = None):
        """初期化

        Args:
            task_service (Optional[TaskService], optional): タスクサービスインスタンス。デフォルトはNone
        """
        self.task_service = task_service or TaskService()

    async def create_action(
        self,
        name: str,
        action_type: str,
        task_template_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """アクションを作成

        Args:
            name (str): アクション名
            action_type (str): アクションタイプ（'api', 'discord', 'slack', 'webhook'）
            task_template_id (Optional[int], optional): 関連するタスクテンプレートのID。デフォルトはNone

        Returns:
            Dict[str, Any]: 作成されたアクション
        """
        async with _get_db_context() as db:
            action = Action(
                name=name,
                action_type=action_type,
                task_template_id=task_template_id,
            )
            db.add(action)
            await db.commit()
            await db.refresh(action)

            return {
                "id": action.id,
                "name": action.name,
                "action_type": action.action_type,
                "task_template_id": action.task_template_id,
                "is_enabled": action.is_enabled,
                "created_at": (action.created_at.isoformat() if action.created_at else None),
            }

    async def get_action(self, action_id: int) -> Optional[Dict[str, Any]]:
        """アクションの詳細を取得

        Args:
            action_id (int): アクションID

        Returns:
            Optional[Dict[str, Any]]: アクションの詳細
        """
        async with _get_db_context() as db:
            action = await db.get(Action, action_id)
            if not action:
                return None

            return {
                "id": action.id,
                "name": action.name,
                "action_type": action.action_type,
                "task_template_id": action.task_template_id,
                "is_enabled": action.is_enabled,
                "created_at": (action.created_at.isoformat() if action.created_at else None),
                "updated_at": (action.updated_at.isoformat() if action.updated_at else None),
                "last_triggered_at": (action.last_triggered_at.isoformat() if action.last_triggered_at else None),
            }

    async def list_actions(
        self,
        action_type: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """アクションの一覧を取得

        Args:
            action_type (Optional[str], optional): アクションタイプ。デフォルトはNone
            is_enabled (Optional[bool], optional): 有効かどうか。デフォルトはNone
            limit (int, optional): 取得件数。デフォルトは10
            offset (int, optional): オフセット。デフォルトは0

        Returns:
            List[Dict[str, Any]]: アクションのリスト
        """
        async with _get_db_context() as db:
            query = select(Action)

            if action_type is not None:
                query = query.where(Action.action_type == action_type)

            if is_enabled is not None:
                query = query.where(Action.is_enabled == is_enabled)

            query = query.order_by(Action.created_at.desc()).limit(limit).offset(offset)

            result = await db.execute(query)
            actions = result.scalars().all()

            return [
                {
                    "id": action.id,
                    "name": action.name,
                    "action_type": action.action_type,
                    "task_template_id": action.task_template_id,
                    "is_enabled": action.is_enabled,
                    "created_at": (action.created_at.isoformat() if action.created_at else None),
                    "last_triggered_at": (action.last_triggered_at.isoformat() if action.last_triggered_at else None),
                }
                for action in actions
            ]

    async def trigger_action(self, action_id: int, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """アクションをトリガーしてタスクを実行

        Args:
            action_id (int): アクションID
            input_data (Dict[str, Any]): 入力データ

        Returns:
            Dict[str, Any]: 実行結果
        """
        async with _get_db_context() as db:
            action = await db.get(Action, action_id)
            if not action:
                return {"success": False, "error": "アクションが見つかりません"}

            if not action.is_enabled:
                return {"success": False, "error": "アクションは無効化されています"}

            # 関連するタスクテンプレートを取得
            task_template = None
            if action.task_template_id:
                task_template = await db.get(TaskTemplate, action.task_template_id)

            if not task_template:
                return {"success": False, "error": "関連するタスクテンプレートが見つかりません"}

            # 最終トリガー時刻を更新
            action.last_triggered_at = datetime.now()
            await db.commit()

            # タスクを実行
            result = await self.task_service.execute_task(
                template_id=task_template.id,
                context=input_data,  # 入力データをそのままコンテキストとして使用
                extensions=None,  # 必要に応じて設定
            )

            return result

    # _extract_context メソッドは不要になったため削除
