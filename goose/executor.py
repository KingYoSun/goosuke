"""
実行レイヤーモジュール

このモジュールは、タスクを実行するための機能を提供します。
コンテキストとプロンプトをセットにしたタスクを受け取り、Goose CLIを使用して実行します。
cli.pyモジュールを利用してGoose CLIを呼び出し、結果を処理します。
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from goose import cli


class TaskExecutor:
    """タスク実行クラス
    発火レイヤーから受け取ったタスクを実行するクラス
    """

    @staticmethod
    async def run(prompt: str, session_name: Optional[str] = None, resume: bool = False) -> Dict[str, Any]:
        """Goose CLIのrunコマンドを実行し結果を返す

        注: 新しい実装では execute_task メソッドの使用を推奨します

        Args:
            prompt (str): 実行するプロンプト
            session_name (Optional[str], optional): セッション名。デフォルトはNone
            resume (bool, optional): 以前の実行から再開するかどうか。デフォルトはFalse

        Returns:
            Dict[str, Any]: 実行結果
        """
        task_id = str(uuid4())

        # cli.pyのrun_with_text関数を使用
        success, output, error = await cli.run_with_text(prompt, session_name, resume)

        if not success:
            return {
                "id": task_id,
                "success": False,
                "output": error,
                "timestamp": datetime.now().isoformat(),
            }

        # 拡張機能の出力を処理（JSON形式を検出）
        extensions_output = {}
        try:
            # JSONブロックを検出（拡張機能の出力）
            if "EXTENSION_OUTPUT:" in output:
                parts = output.split("EXTENSION_OUTPUT:")
                main_output = parts[0].strip()
                json_data = parts[1].strip()
                extensions_output = json.loads(json_data)
                output = main_output
        except Exception:
            pass  # JSON解析エラーは無視

        return {
            "id": task_id,
            "success": True,
            "output": output,
            "extensions_output": extensions_output,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    async def run_with_file(
        instruction_file: str, session_name: Optional[str] = None, resume: bool = False
    ) -> Dict[str, Any]:
        """指示ファイルを使用してGoose CLIのrunコマンドを実行

        Args:
            instruction_file (str): 指示ファイルのパス
            session_name (Optional[str], optional): セッション名。デフォルトはNone
            resume (bool, optional): 以前の実行から再開するかどうか。デフォルトはFalse

        Returns:
            Dict[str, Any]: 実行結果
        """
        task_id = str(uuid4())

        # cli.pyのrun_with_file関数を使用
        success, output, error = await cli.run_with_file(instruction_file, session_name, resume)

        if not success:
            return {
                "id": task_id,
                "success": False,
                "output": error,
                "timestamp": datetime.now().isoformat(),
            }

        return {
            "id": task_id,
            "success": True,
            "output": output,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    async def session(
        name: str,
        resume: bool = False,
        with_extension: Optional[str] = None,
        with_builtin: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Goose CLIのsessionコマンドを実行

        Args:
            name (str): セッション名
            resume (bool, optional): 以前のセッションを再開するかどうか。デフォルトはFalse
            with_extension (Optional[str], optional): 使用する拡張機能。デフォルトはNone
            with_builtin (Optional[str], optional): 使用するビルトイン拡張機能のID。デフォルトはNone

        Returns:
            Dict[str, Any]: 実行結果
        """
        # cli.pyのsession関数を使用
        success, output, error = await cli.session(name, resume, with_extension, with_builtin)

        if not success:
            return {
                "success": False,
                "output": error,
                "timestamp": datetime.now().isoformat(),
            }

        return {
            "success": True,
            "output": output,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    async def configure() -> Dict[str, Any]:
        """Goose CLIのconfigureコマンドを実行

        Note:
            configureコマンドは対話的な実行が必要なため、APIからの実行には対応していません。
            ユーザーはターミナルで直接 `goose configure` コマンドを実行する必要があります。

        Returns:
            Dict[str, Any]: 実行結果
        """
        return {
            "success": False,
            "output": "configureコマンドは対話的な実行が必要なため、APIからの実行には対応していません。ターミナルで直接 `goose configure` コマンドを実行してください。",
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    async def info(verbose: bool = False) -> Dict[str, Any]:
        """Goose CLIのinfoコマンドを実行

        Args:
            verbose (bool, optional): 詳細情報を表示するかどうか。デフォルトはFalse

        Returns:
            Dict[str, Any]: 実行結果
        """
        # cli.pyのinfo関数を使用
        success, output, error = await cli.info(verbose)

        if not success:
            return {
                "success": False,
                "output": error,
                "timestamp": datetime.now().isoformat(),
            }

        return {
            "success": True,
            "output": output,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    async def version() -> Dict[str, Any]:
        """Goose CLIのversionコマンドを実行

        Returns:
            Dict[str, Any]: 実行結果
        """
        # cli.pyのversion関数を使用
        success, output, error = await cli.version()

        if not success:
            return {
                "success": False,
                "output": error,
                "timestamp": datetime.now().isoformat(),
            }

        return {
            "success": True,
            "version": output.strip(),
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    async def update(canary: bool = False, reconfigure: bool = False) -> Dict[str, Any]:
        """Goose CLIのupdateコマンドを実行

        Args:
            canary (bool, optional): カナリーバージョンに更新するかどうか。デフォルトはFalse
            reconfigure (bool, optional): 設定をリセットするかどうか。デフォルトはFalse

        Returns:
            Dict[str, Any]: 実行結果
        """
        # cli.pyのupdate関数を使用
        success, output, error = await cli.update(canary, reconfigure)

        if not success:
            return {
                "success": False,
                "output": error,
                "timestamp": datetime.now().isoformat(),
            }

        return {
            "success": True,
            "output": output,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    async def mcp(name: str) -> Dict[str, Any]:
        """Goose CLIのmcpコマンドを実行

        Args:
            name (str): MCPサーバー名

        Returns:
            Dict[str, Any]: 実行結果
        """
        # cli.pyのmcp関数を使用
        success, output, error = await cli.mcp(name)

        if not success:
            return {
                "success": False,
                "output": error,
                "timestamp": datetime.now().isoformat(),
            }

        return {
            "success": True,
            "output": output,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    async def agents() -> Dict[str, Any]:
        """Goose CLIのagentsコマンドを実行

        Returns:
            Dict[str, Any]: 実行結果（利用可能なエージェント実装のリスト）
        """
        # cli.pyのagents関数を使用
        success, agents_list, error = await cli.agents()

        if not success:
            return {
                "success": False,
                "output": error,
                "timestamp": datetime.now().isoformat(),
            }

        return {
            "success": True,
            "agents": agents_list,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    async def execute_task(
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        extensions: Optional[List[str]] = None,
        session_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """タスクを実行する

        Args:
            prompt (str): ユーザーが望む動作を記述したプロンプト
            context (Optional[Dict[str, Any]], optional): アクションから得られたコンテキスト。デフォルトはNone
            extensions (Optional[List[str]], optional): 使用する拡張機能のリスト。デフォルトはNone
            session_name (Optional[str], optional): セッション名。デフォルトはNone

        Returns:
            Dict[str, Any]: 実行結果
        """
        task_id = str(uuid4())

        # コンテキスト情報をプロンプトに追加
        enhanced_prompt = prompt
        if context:
            context_str = json.dumps(context, ensure_ascii=False, indent=2)
            enhanced_prompt = f"contexts:\n{context_str}\n\nprompts:\n{prompt}"

        # cli.pyのrun_with_text関数を使用
        success, output, error = await cli.run_with_text(enhanced_prompt, session_name)

        if not success:
            return {
                "id": task_id,
                "success": False,
                "output": error,
                "context": context,
                "timestamp": datetime.now().isoformat(),
            }

        # 拡張機能の出力を処理（JSON形式を検出）
        extensions_output = {}
        try:
            # JSONブロックを検出（拡張機能の出力）
            if "EXTENSION_OUTPUT:" in output:
                parts = output.split("EXTENSION_OUTPUT:")
                main_output = parts[0].strip()
                json_data = parts[1].strip()
                extensions_output = json.loads(json_data)
                output = main_output
        except Exception:
            pass  # JSON解析エラーは無視

        return {
            "id": task_id,
            "success": True,
            "output": output,
            "context": context,
            "extensions_output": extensions_output,
            "timestamp": datetime.now().isoformat(),
        }

    # 後方互換性のためのメソッド
    @staticmethod
    async def execute(
        prompt: str,
        extensions: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """後方互換性のためのメソッド。execute_taskメソッドにリダイレクト

        Args:
            prompt (str): 実行するプロンプト
            extensions (Optional[List[str]], optional): 使用する拡張機能のリスト。デフォルトはNone
            context (Optional[Dict[str, Any]], optional): コンテキスト情報。デフォルトはNone

        Returns:
            Dict[str, Any]: 実行結果
        """
        return await TaskExecutor.execute_task(prompt=prompt, context=context, extensions=extensions)
