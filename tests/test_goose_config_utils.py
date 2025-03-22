"""
Goose設定ファイル操作ユーティリティのテスト

このモジュールは、Goose設定ファイル操作ユーティリティの機能をテストします。
"""

import os
import platform
import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

from api.utils.goose_config import get_goose_config_path, read_goose_config, read_goose_extensions


def test_get_goose_config_path():
    """Goose設定ファイルのパス取得機能をテスト"""
    # Dockerコンテナ内の場合
    with patch("os.path.exists", return_value=True):
        config_path = get_goose_config_path()
        assert str(config_path) == str(Path("/home/goosuke/.config/goose/config.yaml"))

    # Windowsの場合はスキップ（Linuxでは実行できないため）
    if platform.system() != "Windows":
        # macOS/Linuxの場合のみテスト
        with (
            patch("os.path.exists", return_value=False),
            patch("os.name", "posix"),
            patch("pathlib.Path.home", return_value=Path("/home/testuser")),
        ):
            config_path = get_goose_config_path()
            assert str(config_path) == str(Path("/home/testuser/.config/goose/config.yaml"))
    else:
        # Windowsの場合
        with (
            patch("os.path.exists", return_value=False),
            patch("os.name", "nt"),
            patch("os.environ.get", return_value="C:\\Users\\Test\\AppData\\Roaming"),
        ):
            config_path = get_goose_config_path()
            assert str(config_path) == str(Path("C:\\Users\\Test\\AppData\\Roaming\\Block\\goose\\config\\config.yaml"))


def test_read_goose_config_file_not_exists():
    """存在しない設定ファイルの読み取り機能をテスト"""
    # 存在しない設定ファイルの場合
    with (
        patch("api.utils.goose_config.get_goose_config_path") as mock_path,
        patch("pathlib.Path.exists", return_value=False),
    ):
        mock_path.return_value = Path("/nonexistent/path/config.yaml")
        config = read_goose_config()
        assert config == {}


def test_read_goose_config_file_exists():
    """存在する設定ファイルの読み取り機能をテスト"""
    # テスト用の設定ファイルを作成
    test_config = {
        "extensions": {
            "ext1": {
                "enabled": True,
                "type": "stdio",
                "cmd": "python",
                "args": ["-m", "ext1"],
                "timeout": 300,
                "envs": {"ENV1": "value1"},
                "name": "Extension 1",
            },
            "ext2": {
                "enabled": True,
                "type": "builtin",
                "name": "Extension 2",
            },
        },
        "other_setting": "value",
    }

    # 一時ファイルを使用してテスト
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as temp_file:
        temp_path = Path(temp_file.name)
        yaml.dump(test_config, temp_file)

    try:
        # 設定ファイルを読み取り
        with patch("api.utils.goose_config.get_goose_config_path", return_value=temp_path):
            config = read_goose_config()
            assert config == test_config
            assert "extensions" in config
            assert len(config["extensions"]) == 2
            assert config["other_setting"] == "value"
    finally:
        # テスト用ファイルを削除
        if temp_path.exists():
            os.remove(temp_path)


def test_read_goose_config_error():
    """設定ファイル読み取りエラーをテスト"""
    # 読み取りエラーの場合
    with (
        patch("api.utils.goose_config.get_goose_config_path") as mock_path,
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", side_effect=Exception("Test error")),
    ):
        mock_path.return_value = Path("/test/path/config.yaml")
        config = read_goose_config()
        assert config == {}


def test_read_goose_extensions():
    """拡張機能設定の読み取り機能をテスト"""
    # テスト用の設定
    test_config = {
        "extensions": {
            "ext1": {
                "enabled": True,
                "type": "stdio",
                "cmd": "python",
                "args": ["-m", "ext1"],
                "timeout": 300,
                "envs": {"ENV1": "value1"},
                "name": "Extension 1",
            },
            "ext2": {
                "enabled": True,
                "type": "builtin",
                "name": "Extension 2",
            },
        },
        "other_setting": "value",
    }

    # read_goose_configをモック化
    with patch("api.utils.goose_config.read_goose_config", return_value=test_config):
        extensions = read_goose_extensions()
        assert extensions == test_config["extensions"]
        assert len(extensions) == 2
        assert "ext1" in extensions
        assert "ext2" in extensions
        assert extensions["ext1"]["name"] == "Extension 1"
        assert extensions["ext2"]["name"] == "Extension 2"


def test_read_goose_extensions_empty():
    """空の拡張機能設定の読み取り機能をテスト"""
    # 拡張機能設定がない場合
    with patch("api.utils.goose_config.read_goose_config", return_value={}):
        extensions = read_goose_extensions()
        assert extensions == {}

    # 拡張機能設定が空の場合
    with patch("api.utils.goose_config.read_goose_config", return_value={"extensions": {}}):
        extensions = read_goose_extensions()
        assert extensions == {}
