"""
アクションモデルのテスト

このモジュールは、アクションモデルの機能をテストします。
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.models.action import Action
from api.models.task import Task


@pytest.mark.asyncio
async def test_create_action(db_session: AsyncSession):
    """アクションの作成をテスト"""
    # テスト用のタスクを作成
    task = Task(
        task_type="test",
        prompt="テスト用プロンプト",
        context={"test": "data"},
        status="completed",
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # アクションを作成
    action = Action(
        name="テストアクション",
        action_type="api",
        config={"endpoint": "/test"},
        context_rules={"key": {"source": "data", "transform": "string"}},
        task_id=task.id,
        is_enabled=True,
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    # 作成されたアクションを検証
    assert action.id is not None
    assert action.name == "テストアクション"
    assert action.action_type == "api"
    assert action.config == {"endpoint": "/test"}
    assert action.context_rules == {"key": {"source": "data", "transform": "string"}}
    assert action.task_id == task.id
    assert action.is_enabled is True
    assert action.created_at is not None
    assert action.last_triggered_at is None


@pytest.mark.asyncio
async def test_action_task_relationship(db_session: AsyncSession):
    """アクションとタスクのリレーションシップをテスト"""
    # テスト用のタスクを作成
    task = Task(
        task_type="test",
        prompt="テスト用プロンプト",
        context={"test": "data"},
        status="completed",
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # アクションを作成
    action = Action(name="テストアクション", action_type="api", task_id=task.id)
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    # リレーションシップを検証
    assert action.task_id == task.id
    assert action.task.id == task.id
    assert action.task.task_type == "test"
    assert action.task.prompt == "テスト用プロンプト"

    # タスク側からのリレーションシップを検証 - 明示的にアクションを取得
    result = await db_session.execute(select(Action).where(Action.task_id == task.id))
    actions = result.scalars().all()
    assert len(actions) == 1
    assert actions[0].id == action.id
    assert actions[0].name == "テストアクション"


@pytest.mark.asyncio
async def test_action_disabled(db_session: AsyncSession):
    """アクションの無効化をテスト"""
    # アクションを作成
    action = Action(name="無効化テスト", action_type="webhook", is_enabled=True)
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    # 初期状態を検証
    assert action.is_enabled is True

    # アクションを無効化
    action.is_enabled = False
    await db_session.commit()
    await db_session.refresh(action)

    # 無効化されたことを検証
    assert action.is_enabled is False
