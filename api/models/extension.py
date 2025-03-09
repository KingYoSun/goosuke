"""
拡張機能モデルモジュール

このモジュールは、Goose拡張機能を管理するデータモデルを定義します。
"""

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from ..database import Base


class Extension(Base):
    """拡張機能モデル
    Goose拡張機能の情報を格納するテーブルモデル
    """

    __tablename__ = "extensions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String, nullable=True)
    enabled = Column(Boolean, default=True)
    config = Column(JSON, nullable=True, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        """文字列表現
        Returns:
            str: 拡張機能の文字列表現
        """
        return f"<Extension(id={self.id}, name={self.name}, enabled={self.enabled})>"
