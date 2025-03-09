"""
アクションサービスのテスト

このモジュールは、アクションサービスの機能をテストします。
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import pytest

from api.models.action import Action
from api.models.task import Task
from api.services.action_service import ActionService


@pytest.mark.asyncio
async def test_create_action(db_session):
    """アクション作成機能をテスト"""
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

    # get_db関数をオーバーライドして、テスト用のdb_sessionを返すようにする
    @asynccontextmanager
    async def override_get_db():
        yield db_session

    # アクションサービスのインスタンスを作成
    action_service = ActionService()

    # get_db関数をパッチして、テスト用のdb_sessionを使用する
    with patch("api.services.action_service.get_db", override_get_db):
        # アクションを作成
        result = await action_service.create_action(
            name="テストアクション",
            action_type="api",
            config={"endpoint": "/test"},
            context_rules={"key": {"source": "data"}},
            task_id=task.id,
        )

    # 結果を検証
    assert result["id"] is not None
    assert result["name"] == "テストアクション"
    assert result["action_type"] == "api"
    assert result["config"] == {"endpoint": "/test"}
    assert result["context_rules"] == {"key": {"source": "data"}}
    assert result["task_id"] == task.id
    assert result["is_enabled"] is True
    assert "created_at" in result


@pytest.mark.asyncio
async def test_get_action(db_session):
    """アクション取得機能をテスト"""
    # テスト用のアクションを作成
    action = Action(
        name="取得テスト",
        action_type="webhook",
        config={"url": "https://example.com/webhook"},
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    # get_db関数をオーバーライドして、テスト用のdb_sessionを返すようにする
    @asynccontextmanager
    async def override_get_db():
        yield db_session

    # アクションサービスのインスタンスを作成
    action_service = ActionService()

    # get_db関数をパッチして、テスト用のdb_sessionを使用する
    with patch("api.services.action_service.get_db", override_get_db):
        # アクションを取得
        result = await action_service.get_action(action.id)

    # 結果を検証
    assert result["id"] == action.id
    assert result["name"] == "取得テスト"
    assert result["action_type"] == "webhook"
    assert result["config"] == {"url": "https://example.com/webhook"}
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

    # get_db関数をオーバーライドして、テスト用のdb_sessionを返すようにする
    @asynccontextmanager
    async def override_get_db():
        yield db_session

    # アクションサービスのインスタンスを作成
    action_service = ActionService()

    # get_db関数をパッチして、テスト用のdb_sessionを使用する
    with patch("api.services.action_service.get_db", override_get_db):
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
async def test_extract_context():
    """コンテキスト抽出機能をテスト"""
    # アクションサービスのインスタンスを作成
    action_service = ActionService()

    # テスト用の入力データ
    input_data = {
        "user": "testuser",
        "message": "Hello, world!",
        "timestamp": 1646092800,
        "metadata": {"channel": "general", "is_bot": False},
    }

    # テスト1: ルールなし
    context1 = action_service._extract_context(input_data, None)
    assert context1 == input_data  # 入力データがそのまま返される

    # テスト2: 基本的なルール
    rules2 = {
        "username": {"source": "user"},
        "text": {"source": "message"},
        "channel": {"source": "metadata.channel"},
    }
    context2 = action_service._extract_context(input_data, rules2)
    assert context2 == {
        "username": "testuser",
        "text": "Hello, world!",
        "channel": "general",  # ネストされたフィールドもサポート
    }

    # テスト3: 変換ルール
    rules3 = {
        "username": {"source": "user", "transform": "string"},
        "timestamp": {"source": "timestamp", "transform": "int"},
        "missing": {"source": "nonexistent", "default": "default value"},
    }
    context3 = action_service._extract_context(input_data, rules3)
    assert context3 == {
        "username": "testuser",
        "timestamp": 1646092800,
        "missing": "default value",
    }


@pytest.mark.asyncio
async def test_trigger_action(db_session):
    """アクショントリガー機能をテスト"""
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

    # テスト用のアクションを作成
    action = Action(
        name="トリガーテスト",
        action_type="api",
        context_rules={"key": {"source": "data"}},
        task_id=task.id,
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    # get_db関数をオーバーライドして、テスト用のdb_sessionを返すようにする
    @asynccontextmanager
    async def override_get_db():
        yield db_session

    # TaskServiceのモックを作成
    mock_task_service = AsyncMock()
    mock_task_service.create_task.return_value = {
        "task_id": 999,
        "success": True,
        "output": "テスト結果",
    }

    # アクションサービスのインスタンスを作成（モックを注入）
    action_service = ActionService(task_service=mock_task_service)

    # get_db関数をパッチして、テスト用のdb_sessionを使用する
    with patch("api.services.action_service.get_db", override_get_db):
        # アクションをトリガー
        result = await action_service.trigger_action(action_id=action.id, input_data={"data": "テスト入力"})

    # 結果を検証
    assert result["task_id"] == 999
    assert result["success"] is True
    assert result["output"] == "テスト結果"

    # TaskServiceのcreate_taskが正しく呼ばれたことを検証
    mock_task_service.create_task.assert_called_once()
    call_args = mock_task_service.create_task.call_args[1]
    assert call_args["task_type"] == "test"
    assert call_args["prompt"] == "テスト用プロンプト"
    assert call_args["context"] == {"key": "テスト入力"}  # コンテキストルールが適用されている
    assert call_args["parent_id"] == task.id

    # アクションの最終トリガー時刻が更新されたことを検証
    await db_session.refresh(action)
    assert action.last_triggered_at is not None
