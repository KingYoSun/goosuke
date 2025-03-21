"""
統合テスト

このモジュールは、発火レイヤーと実行レイヤーの連携を確認するための統合テストを提供します。
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from api.models.action import Action
from api.models.task_template import TaskTemplate
from api.services.action_service import ActionService
from api.services.task_service import TaskService


@pytest.mark.asyncio
async def test_action_to_task_execution_flow(integration_db_session):
    """アクションからタスク実行までの一連のフローをテスト"""
    # 1. テスト用のタスクテンプレートを作成
    task_template = TaskTemplate(
        name="テストテンプレート",
        task_type="template",
        prompt="テンプレートプロンプト: {input}",
    )
    integration_db_session.add(task_template)
    await integration_db_session.commit()
    await integration_db_session.refresh(task_template)

    # 2. テスト用のアクションを作成
    action = Action(
        name="統合テストアクション",
        action_type="api",
        task_template_id=task_template.id,
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
        patch("api.services.action_service._get_db_context", side_effect=mock_get_db),
        patch("api.services.task_service._get_db_context", side_effect=mock_get_db),
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
            assert call_args["context"] == {"message": "テスト入力"}


@pytest.mark.asyncio
async def test_task_template_and_execution(integration_db_session):
    """タスクテンプレートと実行の連携をテスト"""
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
    with patch("api.services.task_service._get_db_context", side_effect=mock_get_db):
        # TaskServiceの実際のインスタンスを使用
        task_service = TaskService()

        # execute_taskをモック
        with patch("goose.executor.TaskExecutor.execute_task") as mock_execute_task:
            # モックの戻り値を設定
            mock_execute_task.return_value = {
                "id": "test-id",
                "success": True,
                "output": "テンプレートから実行したタスクの結果",
                "extensions_output": {},
                "timestamp": datetime.now().isoformat(),
            }

            try:
                # 1. タスクテンプレートを作成
                template_result = await task_service.create_task_template(
                    task_type="template",
                    prompt="共通プロンプト: {param}",
                    name="共通テンプレート",
                    description="テスト用テンプレート",
                )

                template_id = template_result["template_id"]

                # 2. テンプレートからタスクを実行
                execution_result = await task_service.execute_task(
                    template_id=template_id,
                    context={"param": "実行パラメータ"},
                )

                # 3. 結果を検証
                assert execution_result["success"] is True
                assert execution_result["output"] == "テンプレートから実行したタスクの結果"

                # 4. execute_taskが正しく呼ばれたことを検証
                mock_execute_task.assert_called_once()
                call_args = mock_execute_task.call_args[1]

                # プロンプトとコンテキストが正しく渡されていることを確認
                assert call_args["prompt"] == "共通プロンプト: {param}"
                assert call_args["context"] == {"param": "実行パラメータ"}
            except Exception as e:
                print(f"テスト実行中にエラーが発生しました: {e}")
                raise


@pytest.mark.asyncio
async def test_end_to_end_flow_with_mocks(integration_db_session):
    """エンドツーエンドのフローをモックを使用してテスト"""
    # 1. テスト用のタスクテンプレートを作成
    task_template = TaskTemplate(
        name="E2Eテスト",
        task_type="e2e",
        prompt="E2Eテストプロンプト",
    )
    integration_db_session.add(task_template)
    await integration_db_session.commit()
    await integration_db_session.refresh(task_template)

    # 2. テスト用のアクションを作成
    action = Action(
        name="E2Eアクション",
        action_type="webhook",
        task_template_id=task_template.id,
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
        patch("api.services.action_service._get_db_context", side_effect=mock_get_db),
        patch("api.services.task_service._get_db_context", side_effect=mock_get_db),
    ):
        # 3. TaskExecutor.execute_taskをモック
        with patch("goose.executor.TaskExecutor.execute_task") as mock_execute_task:
            # モックの戻り値を設定
            mock_execute_task.return_value = {
                "id": "test-id",
                "success": True,
                "output": "E2E実行結果",
                "extensions_output": {},
                "timestamp": datetime.now().isoformat(),
            }

            # 4. アクションサービスを使用してアクションをトリガー
            action_service = ActionService()
            result = await action_service.trigger_action(
                action_id=action.id, input_data={"data": "Webhookからのデータ"}
            )

            # 5. 結果を検証
            assert result["success"] is True
            assert "template_id" in result

            # 6. execute_taskが正しく呼ばれたことを検証
            mock_execute_task.assert_called_once()
            call_args = mock_execute_task.call_args[1]

            # プロンプトとコンテキストが正しく渡されていることを確認
            assert call_args["prompt"] == "E2Eテストプロンプト"
            assert call_args["context"] == {"data": "Webhookからのデータ"}

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
            "execution_id": 999,
            "template_id": 1,
            "success": True,
            "output": "APIエンドポイントテスト結果",
        }

        # APIエンドポイントが正しく動作することを想定
        # 実際のテストでは、FastAPIのTestClientを使用してエンドポイントを呼び出します

        # モックが正しく呼ばれたことを検証
        # mock_trigger.assert_called_once_with(action_id=1, input_data={"data": "test"})

        # このテストは実装例として示しています
