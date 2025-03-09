"""
設定モデルモジュール

このモジュールは、アプリケーション設定を管理するデータモデルを定義します。
"""

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from ..database import Base


class Setting(Base):
    """設定モデル
    アプリケーション設定を格納するテーブルモデル
    """

    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        """文字列表現
        Returns:
            str: 設定の文字列表現
        """
        return f"<Setting(key={self.key})>"
