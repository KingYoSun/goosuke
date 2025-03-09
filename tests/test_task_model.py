"""
タスクモデルのテスト

このモジュールは、拡張されたタスクモデルの機能をテストします。
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.models.task import Task


@pytest.mark.asyncio
async def test_create_task_with_new_fields(db_session: AsyncSession):
    """新しいフィールドを持つタスクの作成をテスト"""
    # タスクを作成
    task = Task(
        name="テストタスク",
        task_type="test",
        prompt="テスト用プロンプト",
        context={"test": "data"},
        status="completed",
        is_template=True,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # 作成されたタスクを検証
    assert task.id is not None
    assert task.name == "テストタスク"
    assert task.task_type == "test"
    assert task.prompt == "テスト用プロンプト"
    assert task.context == {"test": "data"}
    assert task.status == "completed"
    assert task.is_template is True
    assert task.parent_id is None
    assert task.created_at is not None


@pytest.mark.asyncio
async def test_task_parent_child_relationship(db_session: AsyncSession):
    """タスクの親子関係をテスト"""
    # 親タスク（テンプレート）を作成
    parent_task = Task(
        name="親タスク",
        task_type="template",
        prompt="テンプレートプロンプト",
        context={"template": "data"},
        status="completed",
        is_template=True,
    )
    db_session.add(parent_task)
    await db_session.commit()
    await db_session.refresh(parent_task)

    # 子タスクを作成
    child_task = Task(
        name="子タスク",
        task_type="derived",
        prompt="派生プロンプト",
        context={"derived": "data"},
        status="completed",
        is_template=False,
        parent_id=parent_task.id,
    )
    db_session.add(child_task)
    await db_session.commit()
    await db_session.refresh(child_task)

    # 親子関係を検証
    assert child_task.parent_id == parent_task.id
    assert child_task.parent.id == parent_task.id
    assert child_task.parent.name == "親タスク"

    # 親タスク側からの関係を検証 - 明示的に親タスクを取得
    result = await db_session.execute(select(Task).where(Task.id == parent_task.id))
    db_parent = result.scalars().first()

    # 子タスクを直接取得して検証
    result_child = await db_session.execute(select(Task).where(Task.parent_id == parent_task.id))
    derived_tasks = result_child.scalars().all()
    assert len(derived_tasks) == 1
    assert derived_tasks[0].id == child_task.id
    assert derived_tasks[0].name == "子タスク"


@pytest.mark.asyncio
async def test_multiple_derived_tasks(db_session: AsyncSession):
    """複数の派生タスクをテスト"""
    # 親タスク（テンプレート）を作成
    template = Task(
        name="テンプレート",
        task_type="template",
        prompt="共通プロンプト",
        is_template=True,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    # 複数の派生タスクを作成
    derived_tasks = []
    for i in range(3):
        task = Task(
            name=f"派生タスク{i+1}",
            task_type="derived",
            prompt="派生プロンプト",
            context={"instance": i + 1},
            parent_id=template.id,
        )
        db_session.add(task)
        derived_tasks.append(task)

    await db_session.commit()

    # 派生タスクを検証
    for i, task in enumerate(derived_tasks):
        await db_session.refresh(task)
        assert task.parent_id == template.id
        assert task.name == f"派生タスク{i+1}"
        assert task.context == {"instance": i + 1}

    # テンプレートからの派生タスクを検証 - 明示的に派生タスクを取得
    result = await db_session.execute(select(Task).where(Task.parent_id == template.id))
    derived_tasks_db = result.scalars().all()
    assert len(derived_tasks_db) == 3

    # 派生タスクの順序を検証（IDの昇順になるはず）
    derived_ids = [task.id for task in derived_tasks_db]
    assert derived_ids == sorted(derived_ids)
