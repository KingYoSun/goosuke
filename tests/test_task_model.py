"""
タスクモデルのテスト

このモジュールは、タスクテンプレートとタスク実行モデルの機能をテストします。
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.models.task_execution import TaskExecution
from api.models.task_template import TaskTemplate


@pytest.mark.asyncio
async def test_create_task_template(db_session: AsyncSession):
    """タスクテンプレートの作成をテスト"""
    # タスクテンプレートを作成
    task_template = TaskTemplate(
        name="テストテンプレート",
        task_type="test",
        prompt="テスト用プロンプト",
        description="テスト用説明",
    )
    db_session.add(task_template)
    await db_session.commit()
    await db_session.refresh(task_template)

    # 作成されたタスクテンプレートを検証
    assert task_template.id is not None
    assert task_template.name == "テストテンプレート"
    assert task_template.task_type == "test"
    assert task_template.prompt == "テスト用プロンプト"
    assert task_template.description == "テスト用説明"
    assert task_template.created_at is not None


@pytest.mark.asyncio
async def test_create_task_execution(db_session: AsyncSession):
    """タスク実行の作成をテスト"""
    # タスクテンプレートを作成
    task_template = TaskTemplate(
        name="実行テスト用テンプレート",
        task_type="test",
        prompt="テスト用プロンプト",
    )
    db_session.add(task_template)
    await db_session.commit()
    await db_session.refresh(task_template)

    # タスク実行を作成
    task_execution = TaskExecution(
        template_id=task_template.id,
        context={"test": "data"},
        status="completed",
        result="テスト実行結果",
    )
    db_session.add(task_execution)
    await db_session.commit()
    await db_session.refresh(task_execution)

    # 作成されたタスク実行を検証
    assert task_execution.id is not None
    assert task_execution.template_id == task_template.id
    assert task_execution.context == {"test": "data"}
    assert task_execution.status == "completed"
    assert task_execution.result == "テスト実行結果"
    assert task_execution.created_at is not None


@pytest.mark.asyncio
async def test_template_execution_relationship(db_session: AsyncSession):
    """テンプレートと実行の関係をテスト"""
    # テンプレートを作成
    template = TaskTemplate(
        name="関係テスト用テンプレート",
        task_type="template",
        prompt="テンプレートプロンプト",
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    # 複数の実行を作成
    executions = []
    for i in range(3):
        execution = TaskExecution(
            template_id=template.id,
            context={"instance": i + 1},
            status="completed",
            result=f"実行結果{i+1}",
        )
        db_session.add(execution)
        executions.append(execution)

    await db_session.commit()

    # 実行を検証
    for i, execution in enumerate(executions):
        await db_session.refresh(execution)
        assert execution.template_id == template.id
        assert execution.context == {"instance": i + 1}
        assert execution.result == f"実行結果{i+1}"

    # テンプレートからの実行を検証
    result = await db_session.execute(select(TaskExecution).where(TaskExecution.template_id == template.id))
    executions_db = result.scalars().all()
    assert len(executions_db) == 3

    # 実行の順序を検証（IDの昇順になるはず）
    execution_ids = [execution.id for execution in executions_db]
    assert execution_ids == sorted(execution_ids)

    # リレーションシップを検証 - 明示的にクエリを実行
    query = select(TaskTemplate).where(TaskTemplate.id == template.id)
    result = await db_session.execute(query)
    template_from_db = result.scalars().first()

    # 関連する実行を取得
    query = select(TaskExecution).where(TaskExecution.template_id == template.id)
    result = await db_session.execute(query)
    executions_from_db = result.scalars().all()

    assert len(executions_from_db) == 3
    for execution in executions_from_db:
        assert execution.template_id == template.id
