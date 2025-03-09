"""
タスクサービスモジュール

このモジュールは、発火レイヤーで生成されたタスクの実行と管理を行うサービスを提供します。
コンテキストとプロンプトをセットにしたタスクを作成し、実行レイヤーに渡します。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from goose.executor import TaskExecutor

from ..database import get_db
from ..models.task import Task


class TaskService:
    """タスクサービスクラス
    発火レイヤーと実行レイヤーの橋渡しを行うサービス
    """

    def __init__(self, task_executor: Optional[TaskExecutor] = None):
        """初期化

        Args:
            task_executor (Optional[TaskExecutor], optional): タスク実行インスタンス。デフォルトはNone
        """
        self.task_executor = task_executor or TaskExecutor()

    async def create_task(
        self,
        task_type: str,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        extensions: Optional[List[str]] = None,
        name: Optional[str] = None,
        is_template: bool = False,
        parent_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """タスクを作成して実行

        Args:
            task_type (str): タスクタイプ
            prompt (str): ユーザーが望む動作を記述したプロンプト
            context (Optional[Dict[str, Any]], optional): アクションから得られたコンテキスト。デフォルトはNone
            user_id (Optional[int], optional): ユーザーID。デフォルトはNone
            extensions (Optional[List[str]], optional): 使用する拡張機能のリスト。デフォルトはNone
            name (Optional[str], optional): タスク名（再利用のため）。デフォルトはNone
            is_template (bool, optional): テンプレートとして使用可能か。デフォルトはFalse
            parent_id (Optional[int], optional): 親タスク（テンプレート）のID。デフォルトはNone

        Returns:
            Dict[str, Any]: 実行結果
        """
        # データベースにタスクを記録
        async with get_db() as db:
            task = Task(
                user_id=user_id,
                name=name,
                task_type=task_type,
                prompt=prompt,
                context=context,
                status="processing",
                is_template=is_template,
                parent_id=parent_id,
            )
            db.add(task)
            await db.commit()
            await db.refresh(task)

            # テンプレートの場合は実行しない
            if is_template:
                return {
                    "task_id": task.id,
                    "success": True,
                    "message": "テンプレートとして保存されました",
                }

            try:
                # 実行レイヤーでタスクを実行
                result = await self.task_executor.execute_task(prompt=prompt, context=context, extensions=extensions)

                # タスクを更新
                task.result = result["output"]
                task.extensions_output = result.get("extensions_output", {})
                task.status = "completed" if result["success"] else "failed"
                task.error = None if result["success"] else result["output"]
                task.completed_at = datetime.now()

                await db.commit()
                await db.refresh(task)

                return {
                    "task_id": task.id,
                    "success": result["success"],
                    "output": result["output"],
                    "extensions_output": result.get("extensions_output", {}),
                }

            except Exception as e:
                # エラー発生時
                task.status = "failed"
                task.error = str(e)
                task.completed_at = datetime.now()

                await db.commit()

                return {
                    "task_id": task.id,
                    "success": False,
                    "output": str(e),
                    "extensions_output": {},
                }

    async def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """タスクの詳細を取得

        Args:
            task_id (int): タスクID

        Returns:
            Optional[Dict[str, Any]]: タスクの詳細
        """
        async with get_db() as db:
            task = await db.get(Task, task_id)
            if not task:
                return None

            return {
                "id": task.id,
                "user_id": task.user_id,
                "name": task.name,
                "task_type": task.task_type,
                "prompt": task.prompt,
                "context": task.context,
                "result": task.result,
                "extensions_output": task.extensions_output,
                "status": task.status,
                "error": task.error,
                "is_template": task.is_template,
                "parent_id": task.parent_id,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "completed_at": (task.completed_at.isoformat() if task.completed_at else None),
            }

    async def list_tasks(
        self,
        user_id: Optional[int] = None,
        task_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """タスクの一覧を取得

        Args:
            user_id (Optional[int], optional): ユーザーID。デフォルトはNone
            task_type (Optional[str], optional): タスクタイプ。デフォルトはNone
            limit (int, optional): 取得件数。デフォルトは10
            offset (int, optional): オフセット。デフォルトは0

        Returns:
            List[Dict[str, Any]]: タスクのリスト
        """
        async with get_db() as db:
            query = select(Task)

            if user_id is not None:
                query = query.where(Task.user_id == user_id)

            if task_type is not None:
                query = query.where(Task.task_type == task_type)

            query = query.order_by(Task.created_at.desc()).limit(limit).offset(offset)

            result = await db.execute(query)
            tasks = result.scalars().all()

            return [
                {
                    "id": task.id,
                    "user_id": task.user_id,
                    "name": task.name,
                    "task_type": task.task_type,
                    "status": task.status,
                    "is_template": task.is_template,
                    "parent_id": task.parent_id,
                    "created_at": (task.created_at.isoformat() if task.created_at else None),
                    "completed_at": (task.completed_at.isoformat() if task.completed_at else None),
                }
                for task in tasks
            ]
