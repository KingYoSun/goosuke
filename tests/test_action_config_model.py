"""
アクション設定関連モデルのテスト

このモジュールは、アクション設定関連モデルの機能をテストします。
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.models.action import Action
from api.models.action_config import ActionConfig
from api.models.task_template import TaskTemplate


@pytest.mark.asyncio
async def test_create_action_config(db_session: AsyncSession):
    """アクション設定関連の作成をテスト"""
    # テスト用のタスクテンプレートを作成
    task_template = TaskTemplate(
        name="テストテンプレート",
        task_type="test",
        prompt="テスト用プロンプト",
    )
    db_session.add(task_template)
    await db_session.commit()
    await db_session.refresh(task_template)

    # テスト用のアクションを作成
    action = Action(
        name="テストアクション",
        action_type="api",
        task_template_id=task_template.id,
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    # アクション設定関連を作成
    action_config = ActionConfig(
        action_id=action.id,
        config_type="discord",
        config_id=1,  # 仮のDiscord設定ID
    )
    db_session.add(action_config)
    await db_session.commit()
    await db_session.refresh(action_config)

    # 作成されたアクション設定関連を検証
    assert action_config.id is not None
    assert action_config.action_id == action.id
    assert action_config.config_type == "discord"
    assert action_config.config_id == 1
    assert action_config.created_at is not None


@pytest.mark.asyncio
async def test_action_config_relationship(db_session: AsyncSession):
    """アクション設定関連のリレーションシップをテスト"""
    # テスト用のタスクテンプレートを作成
    task_template = TaskTemplate(
        name="関係テスト用テンプレート",
        task_type="test",
        prompt="テスト用プロンプト",
    )
    db_session.add(task_template)
    await db_session.commit()
    await db_session.refresh(task_template)

    # テスト用のアクションを作成
    action = Action(
        name="関係テスト用アクション",
        action_type="webhook",
        task_template_id=task_template.id,
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    # 複数のアクション設定関連を作成
    action_configs = [
        ActionConfig(
            action_id=action.id,
            config_type="discord",
            config_id=1,
        ),
        ActionConfig(
            action_id=action.id,
            config_type="slack",
            config_id=2,
        ),
    ]

    for config in action_configs:
        db_session.add(config)
    await db_session.commit()

    # リレーションシップを検証
    # 各設定のIDを保存
    config_ids = []
    for config in action_configs:
        await db_session.refresh(config)
        config_ids.append(config.id)
        assert config.action_id == action.id

    # アクション側からのリレーションシップを検証
    # 明示的にクエリを実行して取得
    query = select(Action).where(Action.id == action.id)
    result = await db_session.execute(query)
    action_from_db = result.scalars().first()

    # 関連するアクション設定を取得
    query = select(ActionConfig).where(ActionConfig.action_id == action.id)
    result = await db_session.execute(query)
    configs_from_db = result.scalars().all()

    assert len(configs_from_db) == 2
    config_types = [config.config_type for config in configs_from_db]
    assert "discord" in config_types
    assert "slack" in config_types


@pytest.mark.asyncio
async def test_query_action_by_config(db_session: AsyncSession):
    """設定タイプとIDによるアクションの検索をテスト"""
    # テスト用のタスクテンプレートを作成
    task_template = TaskTemplate(
        name="検索テスト用テンプレート",
        task_type="test",
        prompt="テスト用プロンプト",
    )
    db_session.add(task_template)
    await db_session.commit()
    await db_session.refresh(task_template)

    # テスト用のアクションを作成
    action = Action(
        name="検索テスト用アクション",
        action_type="api",
        task_template_id=task_template.id,
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    # アクション設定関連を作成
    action_config = ActionConfig(
        action_id=action.id,
        config_type="discord",
        config_id=99,  # 特定のDiscord設定ID
    )
    db_session.add(action_config)
    await db_session.commit()

    # 設定タイプとIDでアクションを検索
    query = (
        select(Action)
        .join(ActionConfig, Action.id == ActionConfig.action_id)
        .where(ActionConfig.config_type == "discord", ActionConfig.config_id == 99)
    )
    result = await db_session.execute(query)
    found_action = result.scalars().first()

    # 検索結果を検証
    assert found_action is not None
    assert found_action.id == action.id
    assert found_action.name == "検索テスト用アクション"
