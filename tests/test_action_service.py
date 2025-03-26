"""
アクションサービスのテスト

このモジュールは、アクションサービスの機能をテストします。
"""

from unittest.mock import AsyncMock

import pytest

from api.models.action import Action
from api.models.task_template import TaskTemplate
from api.services.action_service import ActionService


@pytest.mark.asyncio
async def test_create_action(db_session):
    """アクション作成機能をテスト"""
    # テスト用のタスクテンプレートを作成
    task_template = TaskTemplate(
        name="テストテンプレート",
        task_type="test",
        prompt="テスト用プロンプト",
    )
    db_session.add(task_template)
    await db_session.commit()
    await db_session.refresh(task_template)

    # アクションサービスのインスタンスを作成
    action_service = ActionService()

    # アクションを作成
    result = await action_service.create_action(
        name="テストアクション",
        action_type="api",
        task_template_id=task_template.id,
    )

    # 結果を検証
    assert result["id"] is not None
    assert result["name"] == "テストアクション"
    assert result["action_type"] == "api"
    assert result["task_template_id"] == task_template.id
    assert result["is_enabled"] is True
    assert "created_at" in result


@pytest.mark.asyncio
async def test_get_action(db_session):
    """アクション取得機能をテスト"""
    # テスト用のアクションを作成
    action = Action(
        name="取得テスト",
        action_type="webhook",
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    # アクションサービスのインスタンスを作成
    action_service = ActionService()

    # アクションを取得
    result = await action_service.get_action(action.id)

    # 結果を検証
    assert result["id"] == action.id
    assert result["name"] == "取得テスト"
    assert result["action_type"] == "webhook"
    assert result["is_enabled"] is True
    assert "created_at" in result


@pytest.mark.asyncio
async def test_list_actions(db_session):
    """アクション一覧取得機能をテスト"""
    # テスト用のアクションを複数作成
    actions = []
    for i in range(3):
        action = Action(
            name=f"一覧テスト{i+1}",
            action_type="api" if i % 2 == 0 else "webhook",
            is_enabled=i != 1,  # 2番目のアクションは無効化
        )
        db_session.add(action)
        actions.append(action)

    await db_session.commit()

    # アクションサービスのインスタンスを作成
    action_service = ActionService()

    # すべてのアクションを取得
    all_results = await action_service.list_actions()
    assert len(all_results) >= 3  # 他のテストで作成されたアクションも含まれる可能性がある

    # タイプでフィルタリング
    api_results = await action_service.list_actions(action_type="api")
    assert len(api_results) >= 2  # 少なくとも2つのAPIアクションがある
    for result in api_results:
        assert result["action_type"] == "api"

    # 有効/無効でフィルタリング
    enabled_results = await action_service.list_actions(is_enabled=True)
    disabled_results = await action_service.list_actions(is_enabled=False)

    # 少なくとも2つの有効なアクションと1つの無効なアクションがある
    assert len(enabled_results) >= 2
    assert len(disabled_results) >= 1


@pytest.mark.asyncio
async def test_trigger_action(db_session):
    """アクショントリガー機能をテスト"""
    # テスト用のタスクテンプレートを作成
    task_template = TaskTemplate(
        name="トリガーテスト用テンプレート",
        task_type="test",
        prompt="テスト用プロンプト",
    )
    db_session.add(task_template)
    await db_session.commit()
    await db_session.refresh(task_template)

    # テスト用のアクションを作成
    action = Action(
        name="トリガーテスト",
        action_type="api",
        task_template_id=task_template.id,
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    # TaskServiceのモックを作成
    mock_task_service = AsyncMock()
    mock_task_service.execute_task.return_value = {
        "execution_id": 999,
        "template_id": task_template.id,
        "success": True,
        "output": "テスト結果",
    }

    # アクションサービスのインスタンスを作成（モックを注入）
    action_service = ActionService(task_service=mock_task_service)

    # アクションをトリガー
    result = await action_service.trigger_action(action_id=action.id, input_data={"data": "テスト入力"})

    # 結果を検証
    assert result["execution_id"] == 999
    assert result["template_id"] == task_template.id
    assert result["success"] is True
    assert result["output"] == "テスト結果"

    # TaskServiceのexecute_taskが正しく呼ばれたことを検証
    mock_task_service.execute_task.assert_called_once()
    call_args = mock_task_service.execute_task.call_args[1]
    assert call_args["template_id"] == task_template.id
    assert call_args["context"] == {"data": "テスト入力"}  # 入力データがそのままコンテキストとして使用される

    # アクションの最終トリガー時刻が更新されたことを検証
    await db_session.refresh(action)
    assert action.last_triggered_at is not None
