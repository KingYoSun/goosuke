"""
タスク実行モデルのテスト

このモジュールは、タスク実行モデルの基本機能をテストします。
"""

from datetime import datetime

import pytest

from api.models.task_execution import TaskExecution
from api.models.task_template import TaskTemplate
from api.services.task_service import TaskService


@pytest.fixture
async def task_template(db_session):
    """テスト用タスクテンプレート"""
    task_template = TaskTemplate(
        name="テストテンプレート", task_type="test", prompt="テストプロンプト", description="テスト用タスクテンプレート"
    )
    db_session.add(task_template)
    await db_session.commit()
    await db_session.refresh(task_template)
    return task_template


@pytest.fixture
async def task_execution(db_session, task_template):
    """テスト用タスク実行"""
    # フィクスチャからタスクテンプレートを取得
    template = await task_template

    task_execution = TaskExecution(
        template_id=template.id,
        context={"test": "data"},
        status="completed",
        result="テスト結果",
        created_at=datetime.now(),
        completed_at=datetime.now(),
    )
    db_session.add(task_execution)
    await db_session.commit()
    await db_session.refresh(task_execution)
    return task_execution


class TestTaskExecution:
    """タスク実行モデルのテストクラス"""

    @pytest.mark.asyncio
    async def test_create_task_execution(self, db_session, task_template):
        """タスク実行を作成するテスト"""
        # フィクスチャからタスクテンプレートを取得
        template = await task_template

        # タスク実行を作成
        task_execution = TaskExecution(
            template_id=template.id,
            context={"test": "data"},
            status="pending",
        )
        db_session.add(task_execution)
        await db_session.commit()
        await db_session.refresh(task_execution)

        # 作成されたタスク実行を検証
        assert task_execution.id is not None
        assert task_execution.template_id == template.id
        assert task_execution.context == {"test": "data"}
        assert task_execution.status == "pending"

    @pytest.mark.asyncio
    async def test_update_task_execution(self, db_session, task_execution):
        """タスク実行を更新するテスト"""
        # フィクスチャからタスク実行を取得
        execution = await task_execution

        # タスク実行を更新
        execution.status = "failed"
        execution.result = "更新されたテスト結果"
        execution.error = "テストエラー"
        await db_session.commit()
        await db_session.refresh(execution)

        # 更新されたタスク実行を検証
        assert execution.status == "failed"
        assert execution.result == "更新されたテスト結果"
        assert execution.error == "テストエラー"

    @pytest.mark.asyncio
    async def test_task_service_create_task_execution(self, db_session, task_template):
        """TaskServiceのcreate_task_execution関数のテスト"""
        # フィクスチャからタスクテンプレートを取得
        template = await task_template

        # TaskServiceのインスタンスを作成
        task_service = TaskService()

        # タスク実行を作成
        task_execution = await task_service.create_task_execution(
            task_template_id=template.id, context={"test": "data"}
        )

        # 作成されたタスク実行を検証
        assert task_execution["id"] is not None
        assert task_execution["template_id"] == template.id
        assert task_execution["context"] == {"test": "data"}
        assert task_execution["status"] == "pending"

    @pytest.mark.asyncio
    async def test_task_service_update_task_execution(self, db_session, task_execution):
        """TaskServiceのupdate_task_execution関数のテスト"""
        # フィクスチャからタスク実行を取得
        execution = await task_execution

        # TaskServiceのインスタンスを作成
        task_service = TaskService()

        # タスク実行を更新
        updated_task = await task_service.update_task_execution(
            task_execution_id=execution.id,
            status="failed",
            result={"output": "更新されたテスト結果"},
            error="テストエラー",
        )

        # 更新されたタスク実行を検証
        assert updated_task["id"] == execution.id
        assert updated_task["status"] == "failed"
        assert updated_task["result"] == "更新されたテスト結果"
        assert updated_task["error"] == "テストエラー"
