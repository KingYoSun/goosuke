"""
タスクテンプレートモデルモジュール

このモジュールは、再利用可能なタスクテンプレートを管理するデータモデルを定義します。
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class TaskTemplate(Base):
    """タスクテンプレートモデル
    再利用可能なタスクテンプレート
    """

    __tablename__ = "task_templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String, index=True, nullable=False)  # テンプレート名
    task_type = Column(String, index=True, nullable=False)  # 'discord_summary', 'api_request', etc.
    prompt = Column(Text, nullable=False)  # ユーザーが望む動作を記述したプロンプト
    description = Column(Text, nullable=True)  # テンプレートの説明

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーションシップ
    user = relationship("User", backref="task_templates")
    executions = relationship("TaskExecution", back_populates="template")

    def __repr__(self) -> str:
        """文字列表現
        Returns:
            str: タスクテンプレートの文字列表現
        """
        return f"<TaskTemplate(id={self.id}, name={self.name}, type={self.task_type})>"
