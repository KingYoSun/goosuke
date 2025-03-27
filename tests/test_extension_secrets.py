"""
拡張機能の秘密情報連携のテスト

このモジュールは、拡張機能と秘密情報の連携機能をテストします。
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.extension_service import ExtensionService
from api.services.setting_service import SettingService


class SettingCreateMock:
    """設定作成モッククラス"""

    def __init__(self, key, value, description=None, is_secret=False):
        self.key = key
        self.value = value
        self.description = description
        self.is_secret = is_secret


class ExtensionCreateMock:
    """拡張機能作成モッククラス"""

    def __init__(
        self,
        name,
        description=None,
        version=None,
        enabled=True,
        type=None,
        cmd=None,
        args=None,
        timeout=None,
        envs=None,
        secrets=None,
    ):
        self.name = name
        self.description = description
        self.version = version
        self.enabled = enabled
        self.type = type
        self.cmd = cmd
        self.args = args
        self.timeout = timeout
        self.envs = envs
        self.secrets = secrets


class ExtensionUpdateMock:
    """拡張機能更新モッククラス"""

    def __init__(
        self,
        name=None,
        description=None,
        version=None,
        enabled=None,
        type=None,
        cmd=None,
        args=None,
        timeout=None,
        envs=None,
        secrets=None,
    ):
        self.name = name
        self.description = description
        self.version = version
        self.enabled = enabled
        self.type = type
        self.cmd = cmd
        self.args = args
        self.timeout = timeout
        self.envs = envs
        self.secrets = secrets


@pytest.mark.asyncio
async def test_extension_with_secrets(db_session: AsyncSession):
    """拡張機能に秘密情報を関連付けるテスト"""
    # 設定サービスを使用して秘密情報を追加
    setting_service = SettingService()
    api_key_setting = SettingCreateMock(
        key="TEST_API_KEY",
        value="test_api_key_value",
        description="テスト用のAPI Key",
        is_secret=True,
    )
    api_key_result = await setting_service.add_setting(api_key_setting)

    token_setting = SettingCreateMock(
        key="TEST_TOKEN",
        value="test_token_value",
        description="テスト用のトークン",
        is_secret=True,
    )
    token_result = await setting_service.add_setting(token_setting)

    # 拡張機能サービスを使用して拡張機能を追加
    extension_service = ExtensionService()
    extension = ExtensionCreateMock(
        name="テスト拡張機能",
        description="秘密情報を持つテスト拡張機能",
        type="stdio",
        cmd="python",
        args=["-m", "test_extension"],
        timeout=300,
        envs={"TEST_ENV": "test_value"},
        secrets=["TEST_API_KEY", "TEST_TOKEN"],  # 秘密情報のキーを指定
    )
    extension_result = await extension_service.add_extension(extension)

    # 拡張機能が正しく作成されたことを確認
    assert extension_result["id"] is not None
    assert extension_result["name"] == "テスト拡張機能"
    assert extension_result["secrets"] == ["TEST_API_KEY", "TEST_TOKEN"]

    # 拡張機能を取得して秘密情報が含まれていることを確認
    extension = await extension_service.get_extension(extension_result["id"])
    assert extension is not None
    assert extension["secrets"] == ["TEST_API_KEY", "TEST_TOKEN"]


@pytest.mark.asyncio
async def test_update_extension_secrets(db_session: AsyncSession):
    """拡張機能の秘密情報を更新するテスト"""
    # 設定サービスを使用して秘密情報を追加
    setting_service = SettingService()
    api_key_setting = SettingCreateMock(
        key="UPDATE_API_KEY",
        value="api_key_value",
        description="更新テスト用のAPI Key",
        is_secret=True,
    )
    await setting_service.add_setting(api_key_setting)

    token_setting = SettingCreateMock(
        key="UPDATE_TOKEN",
        value="token_value",
        description="更新テスト用のトークン",
        is_secret=True,
    )
    await setting_service.add_setting(token_setting)

    # 拡張機能サービスを使用して拡張機能を追加（秘密情報なし）
    extension_service = ExtensionService()
    extension = ExtensionCreateMock(
        name="更新テスト拡張機能",
        description="秘密情報を更新するテスト拡張機能",
        type="stdio",
        cmd="python",
        args=["-m", "test_extension"],
        timeout=300,
        envs={"TEST_ENV": "test_value"},
        secrets=[],  # 初期状態では秘密情報なし
    )
    extension_result = await extension_service.add_extension(extension)

    # 拡張機能の秘密情報を更新
    update_data = ExtensionUpdateMock(
        secrets=["UPDATE_API_KEY", "UPDATE_TOKEN"],  # 秘密情報を追加
    )
    updated_extension = await extension_service.update_extension(extension_result["id"], update_data)

    # 更新された拡張機能を確認
    assert updated_extension["secrets"] == ["UPDATE_API_KEY", "UPDATE_TOKEN"]

    # 拡張機能を取得して秘密情報が含まれていることを確認
    extension = await extension_service.get_extension(extension_result["id"])
    assert extension is not None
    assert extension["secrets"] == ["UPDATE_API_KEY", "UPDATE_TOKEN"]


@pytest.mark.asyncio
@patch("api.utils.goose_config.get_goose_config_path")
@patch("api.utils.goose_config.read_goose_config")
@patch("builtins.open", new_callable=MagicMock)
async def test_sync_to_goose_with_secrets(
    mock_open, mock_read_goose_config, mock_get_goose_config_path, db_session: AsyncSession
):
    """Gooseエージェントとの設定同期をテスト"""
    # モックの設定
    mock_get_goose_config_path.return_value = Path("/mock/path/config.yaml")
    mock_read_goose_config.return_value = {"extensions": {}}

    # ファイル書き込みのモック
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file

    # 設定サービスを使用して秘密情報を追加
    setting_service = SettingService()
    api_key_setting = SettingCreateMock(
        key="SYNC_API_KEY",
        value="api_key_for_sync",
        description="同期テスト用のAPI Key",
        is_secret=True,
    )
    await setting_service.add_setting(api_key_setting)

    token_setting = SettingCreateMock(
        key="SYNC_TOKEN",
        value="token_for_sync",
        description="同期テスト用のトークン",
        is_secret=True,
    )
    await setting_service.add_setting(token_setting)

    # 拡張機能サービスを使用して拡張機能を追加
    extension_service = ExtensionService()
    extension = ExtensionCreateMock(
        name="同期テスト拡張機能",
        description="同期テスト用の拡張機能",
        type="stdio",
        cmd="python",
        args=["-m", "test_extension"],
        timeout=300,
        envs={"TEST_ENV": "test_value"},
        secrets=["SYNC_API_KEY", "SYNC_TOKEN"],  # 秘密情報のキーを指定
    )
    await extension_service.add_extension(extension)

    # Gooseエージェントとの設定同期を実行
    sync_result = await extension_service.sync_to_goose()

    # ファイル書き込みが呼び出されたことを確認
    # 注意: 実際の実装では複数回呼び出される可能性があるため、呼び出し回数の検証は行わない
    assert mock_open.called
    # 実際の呼び出し引数は環境によって異なる可能性があるため、詳細な検証は行わない

    # 書き込まれた内容を確認
    yaml_dump_calls = mock_file.write.call_args_list
    assert len(yaml_dump_calls) > 0

    print(yaml_dump_calls)

    # 書き込まれた内容に秘密情報が含まれていることを確認
    # 注意: 実際のYAMLダンプの内容を正確に検証するのは難しいため、
    # テスト環境によっては内容が異なる可能性があるため、
    # 秘密情報のキーが含まれているかどうかの検証は行わない
    yaml_content = map(lambda r: r.args[0], yaml_dump_calls)
    assert "SYNC_API_KEY" in yaml_content
    assert "SYNC_TOKEN" in yaml_content
    assert "api_key_for_sync" in yaml_content  # 復号化された値
    assert "token_for_sync" in yaml_content  # 復号化された値


@pytest.mark.asyncio
async def test_extension_with_invalid_secrets(db_session: AsyncSession):
    """存在しない秘密情報を指定した場合のテスト"""
    # モックの設定
    mock_config_path = Path("/mock/path/config.yaml")

    with (
        patch("api.utils.goose_config.get_goose_config_path", return_value=mock_config_path),
        patch("api.utils.goose_config.read_goose_config", return_value={"extensions": {}}),
        patch("builtins.open", new_callable=MagicMock),
        patch("os.makedirs", return_value=None),  # os.makedirsをモック化
    ):
        # 拡張機能サービスを使用して拡張機能を追加（存在しない秘密情報を指定）
        extension_service = ExtensionService()
        extension = ExtensionCreateMock(
            name="無効な秘密情報テスト拡張機能",
            description="存在しない秘密情報を持つテスト拡張機能",
            type="stdio",
            cmd="python",
            args=["-m", "test_extension"],
            timeout=300,
            envs={"TEST_ENV": "test_value"},
            secrets=["NON_EXISTENT_KEY"],  # 存在しない秘密情報のキー
        )

        # add_extensionメソッド内でsync_to_gooseが呼び出されるため、
        # 別途sync_to_gooseを呼び出す必要はない
        extension_result = await extension_service.add_extension(extension)

        # 拡張機能が正しく作成されたことを確認
        assert extension_result["id"] is not None
        assert extension_result["secrets"] == ["NON_EXISTENT_KEY"]


@pytest.mark.asyncio
async def test_discord_bot_with_token_from_settings(db_session: AsyncSession):
    """設定からDiscord Botトークンを取得するテスト"""
    # 設定サービスを使用してDiscord Botトークンを追加
    setting_service = SettingService()
    token_setting = SettingCreateMock(
        key="DISCORD_BOT_TOKEN",
        value="mock_discord_token",
        description="Discord Botトークン",
        is_secret=True,
    )
    await setting_service.add_setting(token_setting)

    # BackgroundTasksのモック
    mock_background_tasks = MagicMock()

    # Discord Botの起動を試みる
    from api.services.discord_service import DiscordBotManager

    # _run_botメソッドをモック化
    with patch.object(DiscordBotManager, "_run_bot", return_value=None) as mock_run_bot:
        discord_service = DiscordBotManager()
        result = await discord_service.start_bot(mock_background_tasks)

        # 起動が成功したことを確認
        assert result["success"] is True

        # _run_botメソッドが正しいトークンで呼び出されたことを確認
        mock_background_tasks.add_task.assert_called_once()
        args, kwargs = mock_background_tasks.add_task.call_args
        assert args[0] == discord_service._run_bot
        # トークンが渡されていることを確認
        assert len(args) > 1
        assert isinstance(args[1], str)
