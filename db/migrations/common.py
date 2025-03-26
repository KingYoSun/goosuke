"""
マイグレーション管理の共通ユーティリティ

このモジュールは、マイグレーションの実行と状態確認のための共通関数を提供します。
"""

from pathlib import Path

from alembic import command
from alembic.config import Config


def get_alembic_config(database_url=None):
    """Alembic設定を取得する

    Args:
        database_url (str, optional): データベースURL。指定された場合は設定を上書きします。

    Returns:
        Config: Alembic設定オブジェクト
    """
    # プロジェクトルートディレクトリを取得
    project_root = Path(__file__).parent.parent.parent.absolute()
    # alembic.iniのパス
    alembic_ini_path = project_root / "alembic.ini"

    # Alembic設定オブジェクトの作成
    alembic_cfg = Config(str(alembic_ini_path))

    # データベースURLが指定されている場合は上書き
    if database_url:
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    return alembic_cfg


def run_migrations(database_url=None, revision="head"):
    """マイグレーションを実行する

    Args:
        database_url (str, optional): データベースURL。指定された場合は設定を上書きします。
        revision (str, optional): 適用するリビジョン。デフォルトは "head"。

    Returns:
        bool: マイグレーションが成功した場合はTrue
    """
    alembic_cfg = get_alembic_config(database_url)
    command.upgrade(alembic_cfg, revision)
    return True


def get_current_migration_version(database_url=None):
    """現在適用されているマイグレーションのバージョンを取得する

    Args:
        database_url (str, optional): データベースURL。指定された場合は設定を上書きします。

    Returns:
        str: 現在適用されているマイグレーションのバージョン
    """
    alembic_cfg = get_alembic_config(database_url)
    return command.current(alembic_cfg)


def get_latest_migration_version():
    """最新のマイグレーションのバージョンを取得する

    Returns:
        str: 最新のマイグレーションのバージョン
    """
    # プロジェクトルートディレクトリを取得
    project_root = Path(__file__).parent.parent.parent.absolute()
    # マイグレーションディレクトリのパス
    migrations_dir = project_root / "db" / "migrations" / "versions"

    # マイグレーションファイルの一覧を取得
    migration_files = list(migrations_dir.glob("*.py"))
    if not migration_files:
        return None

    # ファイル名からバージョン部分を抽出
    versions = []
    for f in migration_files:
        # ファイル名の形式: 20250324_190600_add_secret_management.py
        parts = f.stem.split("_")
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            versions.append(f"{parts[0]}_{parts[1]}")

    if not versions:
        return None

    # 最新のバージョンを返す
    return max(versions)


def check_migrations_status(database_url=None):
    """マイグレーションの状態を確認する

    Args:
        database_url (str, optional): データベースURL。指定された場合は設定を上書きします。

    Returns:
        dict: マイグレーションの状態を表す辞書
            - current: 現在適用されているマイグレーションのバージョン
            - latest: 最新のマイグレーションのバージョン
            - is_latest: 最新のマイグレーションが適用されているかどうか
    """
    current = get_current_migration_version(database_url)
    latest = get_latest_migration_version()

    # currentがNoneの場合（データベースが初期化されていない場合）
    if current is None:
        return {
            "current": None,
            "latest": latest,
            "is_latest": False,
        }

    # latestがNoneの場合（マイグレーションファイルが存在しない場合）
    if latest is None:
        return {
            "current": current,
            "latest": None,
            "is_latest": True,  # マイグレーションファイルがない場合は最新とみなす
        }

    return {
        "current": current,
        "latest": latest,
        "is_latest": current == latest,
    }
