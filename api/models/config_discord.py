"""
Discord設定モデルモジュール

このモジュールは、Discord固有の設定を管理するデータモデルを定義します。
"""

from sqlalchemy import Column, DateTime, Enum, Integer, String
from sqlalchemy.sql import func

from ..database import Base


class ConfigDiscord(Base):
    """Discord設定モデル
    Discord固有の設定を格納するテーブルモデル
    """

    __tablename__ = "config_discord"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)  # 設定名

    # 取得タイプ（'reaction', 'text', 'textWithMention'）
    catch_type: Column = Column(
        Enum("reaction", "text", "textWithMention", name="discord_catch_type"), nullable=False, default="reaction"
    )

    catch_value = Column(String, nullable=False)  # 取得対象（絵文字、キーワードなど）

    # メッセージ収集戦略
    message_type: Column = Column(
        Enum("single", "thread", "range", name="discord_message_type"), nullable=False, default="single"
    )

    # レスポンス形式
    response_format: Column = Column(
        Enum("reply", "dm", "channel", name="discord_response_format"), nullable=False, default="reply"
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        """文字列表現
        Returns:
            str: Discord設定の文字列表現
        """
        return (
            f"<ConfigDiscord(id={self.id}, name={self.name}, "
            f"catch_type={self.catch_type}, catch_value={self.catch_value})>"
        )
