"""
Goose設定ファイル操作ユーティリティ

このモジュールは、Gooseの設定ファイルを読み取るための機能を提供します。
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)


def get_goose_config_path() -> Path:
    """Goose の設定ファイルのパスを取得する

    Returns:
        Path: 設定ファイルのパス
    """
    # Docker コンテナ内かどうかを確認
    if os.path.exists("/home/goosuke"):
        # Docker コンテナ内の場合は、goosuke ユーザーのホームディレクトリを使用
        config_dir = Path("/home/goosuke/.config/goose")
    elif os.name == "nt":  # Windows
        config_dir = Path(os.environ.get("APPDATA", "")) / "Block" / "goose" / "config"
    else:  # macOS/Linux
        config_dir = Path.home() / ".config" / "goose"

    return config_dir / "config.yaml"


def read_goose_config() -> Dict[str, Any]:
    """Goose の設定ファイルを読み取る

    Returns:
        Dict[str, Any]: 設定内容
    """
    config_path = get_goose_config_path()
    if not config_path.exists():
        logger.warning(f"Goose設定ファイルが見つかりません: {config_path}")
        return {}

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}
        return config
    except Exception as e:
        logger.error(f"Goose設定ファイルの読み取りに失敗しました: {e}")
        return {}


def read_goose_extensions() -> Dict[str, Any]:
    """Goose の設定ファイルから拡張機能の設定を読み取る

    Returns:
        Dict[str, Any]: 拡張機能の設定
    """
    config = read_goose_config()
    extensions: Dict[str, Any] = config.get("extensions", {})
    return extensions
