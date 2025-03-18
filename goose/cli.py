"""
Goose CLIコマンド実行ユーティリティ

このモジュールは、Goose CLIコマンドを直接実行するためのユーティリティ関数を提供します。
"""

import asyncio
import re
from typing import List, Optional, Tuple


def strip_ansi_codes(text: str) -> str:
    """ANSIエスケープコードを除去する

    Args:
        text (str): ANSIコードを含む可能性のあるテキスト

    Returns:
        str: ANSIコードが除去されたテキスト
    """
    # 一般的なANSIエスケープコードを除去
    ansi_escape1 = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    # エスケープ文字が省略された形式のANSIコードも除去
    ansi_escape2 = re.compile(r"\[(?:[0-9]{1,3}(?:;[0-9]{1,3})*)?[m]")

    # 両方の正規表現を適用
    text = ansi_escape1.sub("", text)
    text = ansi_escape2.sub("", text)
    return text


def strip_loggin_rows(text: str) -> str:
    # "starting session"から"working directory"までの行を削除
    # 複数行にマッチする正規表現パターン
    pattern = r"^.*starting session.*\n.*logging to.*\n.*working directory.*\n"
    # セッション情報を削除
    return re.sub(pattern, "", text, flags=re.MULTILINE)


async def run_command(command: List[str]) -> Tuple[bool, str, Optional[str]]:
    """Goose CLIコマンドを実行する

    Args:
        command (List[str]): 実行するコマンドとその引数のリスト

    Returns:
        Tuple[bool, str, Optional[str]]: 成功したかどうか、標準出力、標準エラー出力（エラー時のみ）
    """
    try:
        process = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            return False, "", stderr.decode()

        # stdoutをデコードし、ANSIコードを除去
        cleaned_output = strip_ansi_codes(stdout.decode())
        cleaned_output = strip_loggin_rows(cleaned_output)
        return True, cleaned_output, None
    except Exception as e:
        return False, "", str(e)


async def help_command() -> Tuple[bool, str, Optional[str]]:
    """helpコマンドを実行する

    Returns:
        Tuple[bool, str, Optional[str]]: 成功したかどうか、ヘルプ出力、エラー（エラー時のみ）
    """
    return await run_command(["goose", "--help"])


# configureコマンドは対話的な実行が必要なため、APIからの実行には対応していません。
# ユーザーはターミナルで直接 `goose configure` コマンドを実行する必要があります。
# 詳細はREADME.mdを参照してください。


async def session(
    name: str,
    resume: bool = False,
    with_extension: Optional[str] = None,
    with_builtin: Optional[str] = None,
) -> Tuple[bool, str, Optional[str]]:
    """sessionコマンドを実行する

    Args:
        name (str): セッション名
        resume (bool, optional): 以前のセッションを再開するかどうか。デフォルトはFalse
        with_extension (Optional[str], optional): 使用する拡張機能。デフォルトはNone
        with_builtin (Optional[str], optional): 使用するビルトイン拡張機能のID。デフォルトはNone

    Returns:
        Tuple[bool, str, Optional[str]]: 成功したかどうか、出力、エラー（エラー時のみ）
    """
    cmd = ["goose", "session", "--name", name]

    if resume:
        cmd.append("--resume")

    if with_extension:
        cmd.extend(["--with-extension", with_extension])

    if with_builtin:
        cmd.extend(["--with-builtin", with_builtin])

    return await run_command(cmd)


async def info(verbose: bool = False) -> Tuple[bool, str, Optional[str]]:
    """infoコマンドを実行する

    Args:
        verbose (bool, optional): 詳細情報を表示するかどうか。デフォルトはFalse

    Returns:
        Tuple[bool, str, Optional[str]]: 成功したかどうか、情報出力、エラー（エラー時のみ）
    """
    cmd = ["goose", "info"]

    if verbose:
        cmd.append("--verbose")

    return await run_command(cmd)


async def version() -> Tuple[bool, str, Optional[str]]:
    """versionコマンドを実行する

    Returns:
        Tuple[bool, str, Optional[str]]: 成功したかどうか、バージョン情報、エラー（エラー時のみ）
    """
    return await run_command(["goose", "version"])


async def update(canary: bool = False, reconfigure: bool = False) -> Tuple[bool, str, Optional[str]]:
    """updateコマンドを実行する

    Args:
        canary (bool, optional): カナリーバージョンに更新するかどうか。デフォルトはFalse
        reconfigure (bool, optional): 設定をリセットするかどうか。デフォルトはFalse

    Returns:
        Tuple[bool, str, Optional[str]]: 成功したかどうか、更新結果、エラー（エラー時のみ）
    """
    cmd = ["goose", "update"]

    if canary:
        cmd.append("--canary")

    if reconfigure:
        cmd.append("--reconfigure")

    return await run_command(cmd)


async def mcp(name: str) -> Tuple[bool, str, Optional[str]]:
    """mcpコマンドを実行する

    Args:
        name (str): MCPサーバー名

    Returns:
        Tuple[bool, str, Optional[str]]: 成功したかどうか、出力、エラー（エラー時のみ）
    """
    return await run_command(["goose", "mcp", name])


async def run_with_text(text: str, name: Optional[str] = None, resume: bool = False) -> Tuple[bool, str, Optional[str]]:
    """runコマンドをテキスト入力で実行する

    Args:
        text (str): 入力テキスト
        name (Optional[str], optional): セッション名。デフォルトはNone
        resume (bool, optional): 以前の実行から再開するかどうか。デフォルトはFalse

    Returns:
        Tuple[bool, str, Optional[str]]: 成功したかどうか、出力、エラー（エラー時のみ）
    """
    cmd = ["goose", "run", "--text", text]

    if name:
        cmd.extend(["--name", name])

    if resume:
        cmd.append("--resume")

    return await run_command(cmd)


async def run_with_file(
    file_path: str, name: Optional[str] = None, resume: bool = False
) -> Tuple[bool, str, Optional[str]]:
    """runコマンドを指示ファイルで実行する

    Args:
        file_path (str): 指示ファイルのパス
        name (Optional[str], optional): セッション名。デフォルトはNone
        resume (bool, optional): 以前の実行から再開するかどうか。デフォルトはFalse

    Returns:
        Tuple[bool, str, Optional[str]]: 成功したかどうか、出力、エラー（エラー時のみ）
    """
    cmd = ["goose", "run", "--instructions", file_path]

    if name:
        cmd.extend(["--name", name])

    if resume:
        cmd.append("--resume")

    return await run_command(cmd)


async def agents() -> Tuple[bool, List[str], Optional[str]]:
    """agentsコマンドを実行する

    Returns:
        Tuple[bool, List[str], Optional[str]]: 成功したかどうか、エージェントのリスト、エラー（エラー時のみ）
    """
    success, output, error = await run_command(["goose", "agents"])

    if not success:
        return False, [], error

    # 出力を行ごとに分割してリストに変換
    agents_list = [line.strip() for line in output.strip().split("\n") if line.strip()]

    return True, agents_list, None
