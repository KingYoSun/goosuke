"""
設定管理モジュール

このモジュールは、アプリケーションの設定を管理します。
環境変数から設定を読み込み、アプリケーション全体で使用される設定値を提供します。
"""

from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """アプリケーション設定クラス"""

    # 基本設定
    APP_NAME: str = "Goosuke"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "小～中規模組織向けGoose AIエージェント連携プラットフォーム"
    GOOSUKE_ENV: str = "development"

    # データベース設定
    DATABASE_URL: str = "sqlite:///db/sqlite.db"

    # 認証設定
    SECRET_KEY: str = "goosuke_default_secret_key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    # Discord設定
    DISCORD_BOT_TOKEN: Optional[str] = None
    DISCORD_WEBHOOK_SECRET: Optional[str] = None

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


# グローバル設定インスタンス
settings = Settings()


def get_settings() -> Settings:
    """設定インスタンスを取得する関数

    Returns:
        Settings: 設定インスタンス
    """
    return settings
