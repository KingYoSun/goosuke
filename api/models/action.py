"""
アクションモデルモジュール

このモジュールは、システムへの入力点（APIリクエスト、Botメッセージ、Webhookなど）を管理するデータモデルを定義します。
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Action(Base):
    """アクションモデル
    システムへの入力点（APIリクエスト、Botメッセージ、Webhookなど）
    """

    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)  # アクション名
    action_type = Column(String, index=True, nullable=False)  # 'api', 'discord', 'slack', 'webhook'

    # アクション設定とコンテキスト抽出ルールは別テーブルで管理するため削除

    # 関連するタスクテンプレート
    task_template_id = Column(Integer, ForeignKey("task_templates.id"), nullable=True)

    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)

    # リレーションシップ
    task_template = relationship("TaskTemplate", backref="actions")

    def __repr__(self) -> str:
        """文字列表現
        Returns:
            str: アクションの文字列表現
        """
        return f"<Action(id={self.id}, name={self.name}, type={self.action_type})>"
