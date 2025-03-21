"""
アクション設定関連モデルモジュール

このモジュールは、アクションと設定の関連付けを管理するデータモデルを定義します。
"""

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class ActionConfig(Base):
    """アクション設定関連モデル
    アクションと設定の関連付けを管理するテーブルモデル
    """

    __tablename__ = "action_config"

    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("actions.id"), nullable=False)

    # 設定タイプ（"discord", "slack"など）
    config_type: Column = Column(Enum("discord", "slack", name="config_type"), nullable=False)

    config_id = Column(Integer, nullable=False)  # 関連する設定のID

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーションシップ
    action = relationship("Action", backref="config_relations")

    def __repr__(self) -> str:
        """文字列表現
        Returns:
            str: アクション設定関連の文字列表現
        """
        return (
            f"<ActionConfig(id={self.id}, action_id={self.action_id}, "
            f"config_type={self.config_type}, config_id={self.config_id})>"
        )
