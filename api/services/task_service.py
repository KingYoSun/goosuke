"""
タスクサービスモジュール

このモジュールは、発火レイヤーで生成されたタスクの実行と管理を行うサービスを提供します。
タスクテンプレートの管理と、タスク実行の記録を行います。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from goose.executor import TaskExecutor

from ..database import _get_db_context
from ..models.task_execution import TaskExecution
from ..models.task_template import TaskTemplate


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

    async def create_task_template(
        self,
        task_type: str,
        prompt: str,
        name: str,
        user_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """タスクテンプレートを作成

        Args:
            task_type (str): タスクタイプ
            prompt (str): ユーザーが望む動作を記述したプロンプト
            name (str): テンプレート名
            user_id (Optional[int], optional): ユーザーID。デフォルトはNone
            description (Optional[str], optional): テンプレートの説明。デフォルトはNone

        Returns:
            Dict[str, Any]: 作成されたタスクテンプレート
        """
        # データベースにタスクテンプレートを記録
        async with _get_db_context() as db:
            task_template = TaskTemplate(
                user_id=user_id,
                name=name,
                task_type=task_type,
                prompt=prompt,
                description=description,
            )
            db.add(task_template)
            await db.commit()
            await db.refresh(task_template)

            return {
                "template_id": task_template.id,
                "name": task_template.name,
                "task_type": task_template.task_type,
                "prompt": task_template.prompt,
                "description": task_template.description,
                "user_id": task_template.user_id,
                "created_at": task_template.created_at.isoformat() if task_template.created_at else None,
            }

    async def create_task_execution(
        self,
        task_template_id: int,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """タスク実行を作成する

        Args:
            task_template_id (int): タスクテンプレートID
            context (Optional[Dict[str, Any]], optional): コンテキスト。デフォルトはNone
            user_id (Optional[int], optional): ユーザーID。デフォルトはNone

        Returns:
            Dict[str, Any]: 作成されたタスク実行
        """
        async with _get_db_context() as db:
            task_execution = TaskExecution(
                template_id=task_template_id,
                user_id=user_id,
                context=context,
                status="pending",
            )
            db.add(task_execution)
            await db.commit()
            await db.refresh(task_execution)

            return {
                "id": task_execution.id,
                "template_id": task_execution.template_id,
                "user_id": task_execution.user_id,
                "context": task_execution.context,
                "status": task_execution.status,
                "created_at": task_execution.created_at.isoformat() if task_execution.created_at else None,
            }

    async def update_task_execution(
        self,
        task_execution_id: int,
        status: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """タスク実行を更新する

        Args:
            task_execution_id (int): タスク実行ID
            status (Optional[str], optional): ステータス。デフォルトはNone
            result (Optional[Dict[str, Any]], optional): 実行結果。デフォルトはNone
            error (Optional[str], optional): エラーメッセージ。デフォルトはNone

        Returns:
            Dict[str, Any]: 更新されたタスク実行
        """
        async with _get_db_context() as db:
            task_execution = await db.get(TaskExecution, task_execution_id)
            if not task_execution:
                raise ValueError(f"タスク実行が見つかりません: {task_execution_id}")

            if status:
                task_execution.status = status

            if result:
                task_execution.result = result.get("output", "")
                task_execution.extensions_output = result.get("extensions_output", {})

            if error:
                task_execution.error = error

            if status == "completed" or status == "failed":
                task_execution.completed_at = datetime.now()

            await db.commit()
            await db.refresh(task_execution)

            return {
                "id": task_execution.id,
                "template_id": task_execution.template_id,
                "user_id": task_execution.user_id,
                "status": task_execution.status,
                "result": task_execution.result,
                "error": task_execution.error,
                "completed_at": task_execution.completed_at.isoformat() if task_execution.completed_at else None,
            }

    async def execute_task(
        self,
        template_id: int,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        extensions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """タスクを実行

        Args:
            template_id (int): タスクテンプレートID
            context (Optional[Dict[str, Any]], optional): アクションから得られたコンテキスト。デフォルトはNone
            user_id (Optional[int], optional): ユーザーID。デフォルトはNone
            extensions (Optional[List[str]], optional): 使用する拡張機能のリスト。デフォルトはNone

        Returns:
            Dict[str, Any]: 実行結果
        """
        # タスクテンプレートを取得
        async with _get_db_context() as db:
            task_template = await db.get(TaskTemplate, template_id)
            if not task_template:
                return {
                    "success": False,
                    "output": f"テンプレートID {template_id} が見つかりません",
                }

            # タスク実行ログを作成
            task_execution = TaskExecution(
                template_id=template_id,
                user_id=user_id,
                context=context,
                status="processing",
            )
            db.add(task_execution)
            await db.commit()
            await db.refresh(task_execution)

            try:
                # 実行レイヤーでタスクを実行
                result = await self.task_executor.execute_task(
                    prompt=task_template.prompt, context=context, extensions=extensions
                )

                # タスク実行ログを更新
                task_execution.result = result["output"]
                task_execution.extensions_output = result.get("extensions_output", {})
                task_execution.status = "completed" if result["success"] else "failed"
                task_execution.error = None if result["success"] else result["output"]
                task_execution.completed_at = datetime.now()

                await db.commit()
                await db.refresh(task_execution)

                return {
                    "execution_id": task_execution.id,
                    "template_id": task_template.id,
                    "success": result["success"],
                    "output": result["output"],
                    "extensions_output": result.get("extensions_output", {}),
                }

            except Exception as e:
                # エラー発生時
                task_execution.status = "failed"
                task_execution.error = str(e)
                task_execution.completed_at = datetime.now()

                await db.commit()

                return {
                    "execution_id": task_execution.id,
                    "template_id": task_template.id,
                    "success": False,
                    "output": str(e),
                    "extensions_output": {},
                }

    async def get_task_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """タスクテンプレートの詳細を取得

        Args:
            template_id (int): タスクテンプレートID

        Returns:
            Optional[Dict[str, Any]]: タスクテンプレートの詳細
        """
        async with _get_db_context() as db:
            task_template = await db.get(TaskTemplate, template_id)
            if not task_template:
                return None

            return {
                "id": task_template.id,
                "user_id": task_template.user_id,
                "name": task_template.name,
                "task_type": task_template.task_type,
                "prompt": task_template.prompt,
                "description": task_template.description,
                "created_at": task_template.created_at.isoformat() if task_template.created_at else None,
                "updated_at": task_template.updated_at.isoformat() if task_template.updated_at else None,
            }

    async def get_task_execution(self, execution_id: int) -> Optional[Dict[str, Any]]:
        """タスク実行ログの詳細を取得

        Args:
            execution_id (int): タスク実行ログID

        Returns:
            Optional[Dict[str, Any]]: タスク実行ログの詳細
        """
        async with _get_db_context() as db:
            task_execution = await db.get(TaskExecution, execution_id)
            if not task_execution:
                return None

            return {
                "id": task_execution.id,
                "template_id": task_execution.template_id,
                "user_id": task_execution.user_id,
                "context": task_execution.context,
                "result": task_execution.result,
                "extensions_output": task_execution.extensions_output,
                "status": task_execution.status,
                "error": task_execution.error,
                "created_at": task_execution.created_at.isoformat() if task_execution.created_at else None,
                "updated_at": task_execution.updated_at.isoformat() if task_execution.updated_at else None,
                "completed_at": task_execution.completed_at.isoformat() if task_execution.completed_at else None,
            }

    async def list_task_templates(
        self,
        user_id: Optional[int] = None,
        task_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """タスクテンプレートの一覧を取得

        Args:
            user_id (Optional[int], optional): ユーザーID。デフォルトはNone
            task_type (Optional[str], optional): タスクタイプ。デフォルトはNone
            limit (int, optional): 取得件数。デフォルトは10
            offset (int, optional): オフセット。デフォルトは0

        Returns:
            List[Dict[str, Any]]: タスクテンプレートのリスト
        """
        async with _get_db_context() as db:
            query = select(TaskTemplate)

            if user_id is not None:
                query = query.where(TaskTemplate.user_id == user_id)

            if task_type is not None:
                query = query.where(TaskTemplate.task_type == task_type)

            query = query.order_by(TaskTemplate.created_at.desc()).limit(limit).offset(offset)

            result = await db.execute(query)
            templates = result.scalars().all()

            return [
                {
                    "id": template.id,
                    "user_id": template.user_id,
                    "name": template.name,
                    "task_type": template.task_type,
                    "description": template.description,
                    "created_at": template.created_at.isoformat() if template.created_at else None,
                    "updated_at": template.updated_at.isoformat() if template.updated_at else None,
                }
                for template in templates
            ]

    async def list_task_executions(
        self,
        template_id: Optional[int] = None,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """タスク実行ログの一覧を取得

        Args:
            template_id (Optional[int], optional): タスクテンプレートID。デフォルトはNone
            user_id (Optional[int], optional): ユーザーID。デフォルトはNone
            status (Optional[str], optional): ステータス。デフォルトはNone
            limit (int, optional): 取得件数。デフォルトは10
            offset (int, optional): オフセット。デフォルトは0

        Returns:
            List[Dict[str, Any]]: タスク実行ログのリスト
        """
        async with _get_db_context() as db:
            query = select(TaskExecution)

            if template_id is not None:
                query = query.where(TaskExecution.template_id == template_id)

            if user_id is not None:
                query = query.where(TaskExecution.user_id == user_id)

            if status is not None:
                query = query.where(TaskExecution.status == status)

            query = query.order_by(TaskExecution.created_at.desc()).limit(limit).offset(offset)

            result = await db.execute(query)
            executions = result.scalars().all()

            return [
                {
                    "id": execution.id,
                    "template_id": execution.template_id,
                    "user_id": execution.user_id,
                    "status": execution.status,
                    "created_at": execution.created_at.isoformat() if execution.created_at else None,
                    "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                }
                for execution in executions
            ]
