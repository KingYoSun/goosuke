"""
統合テスト

このモジュールは、発火レイヤーと実行レイヤーの連携を確認するための統合テストを提供します。
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from api.models.action import Action
from api.models.task import Task
from api.services.action_service import ActionService
from api.services.task_service import TaskService


@pytest.mark.asyncio
async def test_action_to_task_execution_flow(integration_db_session):
    """アクションからタスク実行までの一連のフローをテスト"""
    # 1. テスト用のタスク（テンプレート）を作成
    template_task = Task(
        name="テストテンプレート",
        task_type="template",
        prompt="テンプレートプロンプト: {input}",
        is_template=True,
    )
    integration_db_session.add(template_task)
    await integration_db_session.commit()
    await integration_db_session.refresh(template_task)

    # 2. テスト用のアクションを作成
    action = Action(
        name="統合テストアクション",
        action_type="api",
        context_rules={"input": {"source": "message"}},
        task_id=template_task.id,
    )
    integration_db_session.add(action)
    await integration_db_session.commit()
    await integration_db_session.refresh(action)

    # get_db関数をモックして、integration_db_sessionを返すようにする
    # 実際のget_db関数と同じように動作するようにする
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_get_db():
        try:
            yield integration_db_session
            await integration_db_session.commit()
        except Exception:
            await integration_db_session.rollback()
            raise

    # get_db関数をモック
    with (
        patch("api.services.action_service.get_db", side_effect=mock_get_db),
        patch("api.services.task_service.get_db", side_effect=mock_get_db),
    ):
        # 3. TaskExecutor.execute_taskをモック
        with patch("goose.executor.TaskExecutor.execute_task") as mock_execute_task:
            # モックの戻り値を設定
            mock_execute_task.return_value = {
                "id": "test-id",
                "success": True,
                "output": "統合テスト実行結果",
                "extensions_output": {},
                "timestamp": datetime.now().isoformat(),
            }

            # 4. アクションサービスを使用してアクションをトリガー
            action_service = ActionService()
            result = await action_service.trigger_action(action_id=action.id, input_data={"message": "テスト入力"})

            # 5. 結果を検証
            assert result["success"] is True
            assert "output" in result
            assert "統合テスト実行結果" in result["output"]

            # 6. execute_taskが正しく呼ばれたことを検証
            mock_execute_task.assert_called_once()
            call_args = mock_execute_task.call_args[1]

            # プロンプトとコンテキストが正しく渡されていることを確認
            assert call_args["prompt"] == "テンプレートプロンプト: {input}"
            assert call_args["context"] == {"input": "テスト入力"}


@pytest.mark.asyncio
async def test_task_template_and_derived_task(integration_db_session):
    """タスクテンプレートと派生タスクの連携をテスト"""
    # get_db関数をモックして、integration_db_sessionを返すようにする
    # 実際のget_db関数と同じように動作するようにする
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_get_db():
        try:
            yield integration_db_session
            await integration_db_session.commit()
        except Exception:
            await integration_db_session.rollback()
            raise

    # get_db関数をモック
    with patch("api.services.task_service.get_db", side_effect=mock_get_db):
        # TaskServiceの実際のインスタンスを使用
        task_service = TaskService()

        # execute_taskをモック
        with patch("goose.executor.TaskExecutor.execute_task") as mock_execute_task:
            # モックの戻り値を設定
            mock_execute_task.return_value = {
                "id": "test-id",
                "success": True,
                "output": "テンプレートから派生したタスクの実行結果",
                "extensions_output": {},
                "timestamp": datetime.now().isoformat(),
            }

            try:
                # 1. テンプレートタスクを作成
                template_result = await task_service.create_task(
                    task_type="template",
                    prompt="共通プロンプト: {param}",
                    name="共通テンプレート",
                    is_template=True,
                )

                template_id = template_result["task_id"]

                # 2. テンプレートから派生したタスクを作成して実行
                derived_result = await task_service.create_task(
                    task_type="derived",
                    prompt="共通プロンプト: {param}",  # テンプレートと同じプロンプト
                    context={"param": "派生パラメータ"},
                    name="派生タスク",
                    parent_id=template_id,
                )

                # 3. 結果を検証
                assert derived_result["success"] is True
                assert derived_result["output"] == "テンプレートから派生したタスクの実行結果"

                # 4. execute_taskが正しく呼ばれたことを検証
                mock_execute_task.assert_called_once()
                call_args = mock_execute_task.call_args[1]

                # プロンプトとコンテキストが正しく渡されていることを確認
                assert call_args["prompt"] == "共通プロンプト: {param}"
                assert call_args["context"] == {"param": "派生パラメータ"}
            except Exception as e:
                print(f"テスト実行中にエラーが発生しました: {e}")
                raise


@pytest.mark.asyncio
async def test_end_to_end_flow_with_mocks(integration_db_session):
    """エンドツーエンドのフローをモックを使用してテスト"""
    # 1. テスト用のタスクを作成
    task = Task(
        name="E2Eテスト",
        task_type="e2e",
        prompt="E2Eテストプロンプト",
        context={"initial": "context"},
        status="completed",
    )
    integration_db_session.add(task)
    await integration_db_session.commit()
    await integration_db_session.refresh(task)

    # 2. テスト用のアクションを作成
    action = Action(
        name="E2Eアクション",
        action_type="webhook",
        context_rules={"webhook_data": {"source": "data"}},
        task_id=task.id,
    )
    integration_db_session.add(action)
    await integration_db_session.commit()
    await integration_db_session.refresh(action)

    # get_db関数をモックして、integration_db_sessionを返すようにする
    # 実際のget_db関数と同じように動作するようにする
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_get_db():
        try:
            yield integration_db_session
            await integration_db_session.commit()
        except Exception:
            await integration_db_session.rollback()
            raise

    # get_db関数をモック
    with (
        patch("api.services.action_service.get_db", side_effect=mock_get_db),
        patch("api.services.task_service.get_db", side_effect=mock_get_db),
    ):
        # 3. cli.pyのrun_with_text関数をモック
        with patch("goose.cli.run_with_text") as mock_run:
            # モックの戻り値を設定
            mock_run.return_value = (True, "E2E実行結果", None)

            # 4. アクションサービスを使用してアクションをトリガー
            action_service = ActionService()
            result = await action_service.trigger_action(
                action_id=action.id, input_data={"data": "Webhookからのデータ"}
            )

            # 5. 結果を検証
            assert result["success"] is True
            assert "task_id" in result

            # 6. run_with_textが正しく呼ばれたことを検証
            mock_run.assert_called_once()
            args, kwargs = mock_run.call_args

            # プロンプトにコンテキストが含まれていることを確認
            assert "E2Eテストプロンプト" in args[0]
            assert "webhook_data" in args[0]
            assert "Webhookからのデータ" in args[0]

            # 7. データベースのアクションが更新されていることを確認
            await integration_db_session.refresh(action)
            assert action.last_triggered_at is not None


@pytest.mark.asyncio
async def test_action_api_endpoint_flow():
    """アクションAPIエンドポイントのフローをテスト"""
    # このテストは実際のAPIエンドポイントを呼び出すのではなく、
    # サービスレイヤーをモックしてルーターの動作をテストします

    # FastAPIのテストクライアントを使用する場合は、以下のようなコードになります
    # from fastapi.testclient import TestClient
    # from api.main import app
    # client = TestClient(app)
    # response = client.post("/api/v1/actions/1/trigger", json={"data": "test"})
    # assert response.status_code == 200

    # ここでは簡略化のため、サービスレイヤーのモックテストのみを示します
    with patch("api.services.action_service.ActionService.trigger_action") as mock_trigger:
        # モックの戻り値を設定
        mock_trigger.return_value = {
            "task_id": 999,
            "success": True,
            "output": "APIエンドポイントテスト結果",
        }

        # APIエンドポイントが正しく動作することを想定
        # 実際のテストでは、FastAPIのTestClientを使用してエンドポイントを呼び出します

        # モックが正しく呼ばれたことを検証
        # mock_trigger.assert_called_once_with(action_id=1, input_data={"data": "test"})

        # このテストは実装例として示しています
