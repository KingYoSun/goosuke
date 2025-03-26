"""
アクション設定関連サービスのテスト

このモジュールは、アクション設定関連サービスの機能をテストします。
"""

import pytest

from api.models.action import Action
from api.models.action_config import ActionConfig
from api.models.task_template import TaskTemplate
from api.services.action_config_service import ActionConfigService


@pytest.mark.asyncio
async def test_create_action_config(db_session):
    """アクション設定関連作成機能をテスト"""
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

    # アクション設定関連サービスのインスタンスを作成
    action_config_service = ActionConfigService()

    # アクション設定関連を作成
    result = await action_config_service.create_action_config(
        action_id=action.id,
        config_type="discord",
        config_id=1,
    )

    # 結果を検証
    assert result["id"] is not None
    assert result["action_id"] == action.id
    assert result["config_type"] == "discord"
    assert result["config_id"] == 1
    assert "created_at" in result


@pytest.mark.asyncio
async def test_get_action_by_config(db_session):
    """設定によるアクション取得機能をテスト"""
    # テスト用のタスクテンプレートを作成
    task_template = TaskTemplate(
        name="取得テスト用テンプレート",
        task_type="test",
        prompt="テスト用プロンプト",
    )
    db_session.add(task_template)
    await db_session.commit()
    await db_session.refresh(task_template)

    # テスト用のアクションを作成
    action = Action(
        name="取得テスト用アクション",
        action_type="webhook",
        task_template_id=task_template.id,
        is_enabled=True,
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    # テスト用のアクション設定関連を作成
    action_config = ActionConfig(
        action_id=action.id,
        config_type="discord",
        config_id=123,
    )
    db_session.add(action_config)
    await db_session.commit()
    await db_session.refresh(action_config)

    # アクション設定関連サービスのインスタンスを作成
    action_config_service = ActionConfigService()

    # 設定によるアクション取得
    result = await action_config_service.get_action_by_config(
        config_type="discord",
        config_id=123,
    )

    # 結果を検証
    assert result is not None
    assert result["id"] == action.id
    assert result["name"] == "取得テスト用アクション"
    assert result["action_type"] == "webhook"
    assert result["task_template_id"] == task_template.id
    assert result["is_enabled"] is True

    # 存在しない設定でテスト
    result = await action_config_service.get_action_by_config(
        config_type="discord",
        config_id=999,
    )

    # 結果を検証
    assert result is None


@pytest.mark.asyncio
async def test_get_action_by_config_disabled(db_session):
    """無効化されたアクションが取得されないことをテスト"""
    # テスト用のタスクテンプレートを作成
    task_template = TaskTemplate(
        name="無効化テスト用テンプレート",
        task_type="test",
        prompt="テスト用プロンプト",
    )
    db_session.add(task_template)
    await db_session.commit()
    await db_session.refresh(task_template)

    # テスト用のアクションを作成（無効化）
    action = Action(
        name="無効化テスト用アクション",
        action_type="webhook",
        task_template_id=task_template.id,
        is_enabled=False,  # 無効化
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    # テスト用のアクション設定関連を作成
    action_config = ActionConfig(
        action_id=action.id,
        config_type="discord",
        config_id=456,
    )
    db_session.add(action_config)
    await db_session.commit()
    await db_session.refresh(action_config)

    # アクション設定関連サービスのインスタンスを作成
    action_config_service = ActionConfigService()

    # 設定による無効化アクション取得
    result = await action_config_service.get_action_by_config(
        config_type="discord",
        config_id=456,
    )

    # 結果を検証（無効化されたアクションは取得されない）
    assert result is None


@pytest.mark.asyncio
async def test_list_configs_by_action(db_session):
    """アクションによる設定一覧取得機能をテスト"""
    # テスト用のタスクテンプレートを作成
    task_template = TaskTemplate(
        name="一覧テスト用テンプレート",
        task_type="test",
        prompt="テスト用プロンプト",
    )
    db_session.add(task_template)
    await db_session.commit()
    await db_session.refresh(task_template)

    # テスト用のアクションを作成
    action = Action(
        name="一覧テスト用アクション",
        action_type="api",
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
            config_type="discord",
            config_id=2,
        ),
        ActionConfig(
            action_id=action.id,
            config_type="slack",
            config_id=3,
        ),
    ]

    for config in action_configs:
        db_session.add(config)
    await db_session.commit()

    # アクション設定関連サービスのインスタンスを作成
    action_config_service = ActionConfigService()

    # すべての設定を取得
    all_results = await action_config_service.list_configs_by_action(action.id)
    assert len(all_results) == 3

    # タイプでフィルタリング
    discord_results = await action_config_service.list_configs_by_action(action.id, config_type="discord")
    assert len(discord_results) == 2
    for result in discord_results:
        assert result["config_type"] == "discord"

    # slackタイプの設定を取得
    slack_results = await action_config_service.list_configs_by_action(action.id, config_type="slack")
    assert len(slack_results) == 1
    assert slack_results[0]["config_type"] == "slack"
    assert slack_results[0]["config_id"] == 3
