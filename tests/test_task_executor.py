"""
タスク実行クラスのテスト

このモジュールは、実行レイヤーのTaskExecutorクラスの機能をテストします。
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from goose.executor import TaskExecutor


@pytest.mark.asyncio
async def test_execute_task():
    """execute_taskメソッドをテスト"""
    # cli.pyのrun_with_text関数をモック
    with patch("goose.cli.run_with_text") as mock_run:
        # モックの戻り値を設定
        mock_run.return_value = (True, "実行結果", None)

        # TaskExecutorのインスタンスを作成
        executor = TaskExecutor()

        # タスクを実行
        result = await executor.execute_task(
            prompt="テスト用プロンプト",
            context={"key": "value"},
            extensions=["test-extension"],
        )

        # 結果を検証
        assert result["success"] is True
        assert result["output"] == "実行結果"
        assert "id" in result
        assert "timestamp" in result
        assert result["context"] == {"key": "value"}

        # モックが正しく呼ばれたことを検証
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args

        # プロンプトにコンテキストが含まれていることを確認
        assert "contexts:" in args[0]  # 実装では "contexts:" を使用している
        assert "key" in args[0]
        assert "value" in args[0]
        assert "テスト用プロンプト" in args[0]


@pytest.mark.asyncio
async def test_execute_task_with_extensions_output():
    """拡張機能の出力を含むタスク実行をテスト"""
    # 拡張機能の出力を含むモックの戻り値
    mock_output = """実行結果

EXTENSION_OUTPUT:{"extension_name": "test-extension", "result": "success"}"""

    # cli.pyのrun_with_text関数をモック
    with patch("goose.cli.run_with_text") as mock_run:
        # モックの戻り値を設定
        mock_run.return_value = (True, mock_output, None)

        # TaskExecutorのインスタンスを作成
        executor = TaskExecutor()

        # タスクを実行
        result = await executor.execute_task(prompt="テスト用プロンプト")

        # 結果を検証
        assert result["success"] is True
        assert result["output"] == "実行結果"
        assert result["extensions_output"] == {
            "extension_name": "test-extension",
            "result": "success",
        }


@pytest.mark.asyncio
async def test_execute_task_failure():
    """タスク実行の失敗をテスト"""
    # cli.pyのrun_with_text関数をモック
    with patch("goose.cli.run_with_text") as mock_run:
        # モックの戻り値を設定（失敗）
        mock_run.return_value = (False, "", "エラーメッセージ")

        # TaskExecutorのインスタンスを作成
        executor = TaskExecutor()

        # タスクを実行
        result = await executor.execute_task(prompt="テスト用プロンプト")

        # 結果を検証
        assert result["success"] is False
        assert result["output"] == "エラーメッセージ"
        assert "id" in result
        assert "timestamp" in result


@pytest.mark.asyncio
async def test_execute_task_with_session_name():
    """セッション名を指定したタスク実行をテスト"""
    # cli.pyのrun_with_text関数をモック
    with patch("goose.cli.run_with_text") as mock_run:
        # モックの戻り値を設定
        mock_run.return_value = (True, "セッション実行結果", None)

        # TaskExecutorのインスタンスを作成
        executor = TaskExecutor()

        # タスクを実行（セッション名を指定）
        result = await executor.execute_task(prompt="テスト用プロンプト", session_name="test-session")

        # 結果を検証
        assert result["success"] is True
        assert result["output"] == "セッション実行結果"

        # モックが正しく呼ばれたことを検証
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args

        # セッション名が渡されていることを確認
        assert args[1] == "test-session"


@pytest.mark.asyncio
async def test_backward_compatibility():
    """後方互換性のためのexecuteメソッドをテスト"""
    # execute_taskメソッドをモック
    with patch.object(TaskExecutor, "execute_task") as mock_execute_task:
        # モックの戻り値を設定
        mock_execute_task.return_value = {
            "id": "test-id",
            "success": True,
            "output": "互換性テスト結果",
            "timestamp": datetime.now().isoformat(),
        }

        # TaskExecutorのインスタンスを作成
        executor = TaskExecutor()

        # 古いexecuteメソッドを呼び出し
        result = await executor.execute(
            prompt="古いプロンプト",
            extensions=["old-extension"],
            context={"old": "context"},
        )

        # 結果を検証
        assert result["success"] is True
        assert result["output"] == "互換性テスト結果"

        # execute_taskが正しく呼ばれたことを検証
        mock_execute_task.assert_called_once_with(
            prompt="古いプロンプト",
            context={"old": "context"},
            extensions=["old-extension"],
        )
