"""
アクションモデルのテスト

このモジュールは、アクションモデルの機能をテストします。
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.models.action import Action
from api.models.task_template import TaskTemplate


@pytest.mark.asyncio
async def test_create_action(db_session: AsyncSession):
    """アクションの作成をテスト"""
    # テスト用のタスクテンプレートを作成
    task_template = TaskTemplate(
        name="テストテンプレート",
        task_type="test",
        prompt="テスト用プロンプト",
    )
    db_session.add(task_template)
    await db_session.commit()
    await db_session.refresh(task_template)

    # アクションを作成
    action = Action(
        name="テストアクション",
        action_type="api",
        task_template_id=task_template.id,
        is_enabled=True,
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    # 作成されたアクションを検証
    assert action.id is not None
    assert action.name == "テストアクション"
    assert action.action_type == "api"
    assert action.task_template_id == task_template.id
    assert action.is_enabled is True
    assert action.created_at is not None
    assert action.last_triggered_at is None


@pytest.mark.asyncio
async def test_action_task_template_relationship(db_session: AsyncSession):
    """アクションとタスクテンプレートのリレーションシップをテスト"""
    # テスト用のタスクテンプレートを作成
    task_template = TaskTemplate(
        name="関係テスト用テンプレート",
        task_type="test",
        prompt="テスト用プロンプト",
    )
    db_session.add(task_template)
    await db_session.commit()
    await db_session.refresh(task_template)

    # アクションを作成
    action = Action(name="テストアクション", action_type="api", task_template_id=task_template.id)
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    # リレーションシップを検証
    assert action.task_template_id == task_template.id
    assert action.task_template.id == task_template.id
    assert action.task_template.task_type == "test"
    assert action.task_template.prompt == "テスト用プロンプト"

    # タスクテンプレート側からのリレーションシップを検証 - 明示的にアクションを取得
    result = await db_session.execute(select(Action).where(Action.task_template_id == task_template.id))
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
