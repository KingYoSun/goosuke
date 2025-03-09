"""
アクションサービスモジュール

このモジュールは、システムへの入力点（APIリクエスト、Botメッセージ、Webhookなど）を管理するサービスを提供します。
アクションからコンテキストを抽出し、タスクの生成に必要な情報を提供します。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from ..database import get_db
from ..models.action import Action
from ..models.task import Task
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
        config: Optional[Dict[str, Any]] = None,
        context_rules: Optional[Dict[str, Any]] = None,
        task_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """アクションを作成

        Args:
            name (str): アクション名
            action_type (str): アクションタイプ（'api', 'discord', 'slack', 'webhook'）
            config (Optional[Dict[str, Any]], optional): アクション固有の設定。デフォルトはNone
            context_rules (Optional[Dict[str, Any]], optional): コンテキスト抽出のためのルール。デフォルトはNone
            task_id (Optional[int], optional): 関連するタスクのID。デフォルトはNone

        Returns:
            Dict[str, Any]: 作成されたアクション
        """
        async with get_db() as db:
            action = Action(
                name=name,
                action_type=action_type,
                config=config,
                context_rules=context_rules,
                task_id=task_id,
            )
            db.add(action)
            await db.commit()
            await db.refresh(action)

            return {
                "id": action.id,
                "name": action.name,
                "action_type": action.action_type,
                "config": action.config,
                "context_rules": action.context_rules,
                "task_id": action.task_id,
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
        async with get_db() as db:
            action = await db.get(Action, action_id)
            if not action:
                return None

            return {
                "id": action.id,
                "name": action.name,
                "action_type": action.action_type,
                "config": action.config,
                "context_rules": action.context_rules,
                "task_id": action.task_id,
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
        async with get_db() as db:
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
                    "task_id": action.task_id,
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
        async with get_db() as db:
            action = await db.get(Action, action_id)
            if not action:
                return {"success": False, "error": "アクションが見つかりません"}

            if not action.is_enabled:
                return {"success": False, "error": "アクションは無効化されています"}

            # コンテキスト抽出
            context = self._extract_context(input_data, action.context_rules)

            # 関連するタスクを取得
            task = None
            if action.task_id:
                task = await db.get(Task, action.task_id)

            if not task:
                return {"success": False, "error": "関連するタスクが見つかりません"}

            # 最終トリガー時刻を更新
            action.last_triggered_at = datetime.now()
            await db.commit()

            # タスクを実行
            result = await self.task_service.create_task(
                task_type=task.task_type,
                prompt=task.prompt,
                context=context,
                extensions=None,  # 必要に応じて設定
                name=f"{action.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                parent_id=task.id,
            )

            return result

    def _extract_context(self, input_data: Dict[str, Any], context_rules: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """入力データからコンテキストを抽出

        Args:
            input_data (Dict[str, Any]): 入力データ
            context_rules (Optional[Dict[str, Any]]): コンテキスト抽出ルール

        Returns:
            Dict[str, Any]: 抽出されたコンテキスト
        """
        # ルールがない場合は入力データをそのまま返す
        if not context_rules:
            return input_data

        # ルールに基づいてコンテキストを抽出
        context = {}
        for key, rule in context_rules.items():
            if "source" in rule:
                # ネストされたフィールドを処理（例: metadata.channel）
                source_path = rule["source"].split(".")
                source_value = input_data
                try:
                    for path_part in source_path:
                        if path_part in source_value:
                            source_value = source_value[path_part]
                        else:
                            source_value = None
                            break
                except (TypeError, KeyError):
                    source_value = None

                # 変換処理（必要に応じて）
                if source_value is not None:
                    if "transform" in rule and rule["transform"] == "string":
                        source_value = str(source_value)
                    elif "transform" in rule and rule["transform"] == "int":
                        try:
                            source_value = int(source_value)
                        except (ValueError, TypeError):
                            source_value = 0

                    context[key] = source_value
                elif "default" in rule:
                    context[key] = rule["default"]
            elif "default" in rule:
                context[key] = rule["default"]

        return context
