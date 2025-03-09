"""
ユーザーモデルモジュール

このモジュールは、ユーザー認証に関連するデータモデルを定義します。
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from ..database import Base


class User(Base):
    """ユーザーモデル
    ユーザー認証情報を格納するテーブルモデル
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self) -> str:
        """文字列表現
        Returns:
            str: ユーザーの文字列表現
        """
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
