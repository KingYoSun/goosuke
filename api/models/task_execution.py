"""
タスク実行ログモデルモジュール

このモジュールは、実行されたタスクのログを記録するデータモデルを定義します。
"""

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class TaskExecution(Base):
    """タスク実行ログモデル
    実行されたタスクのログを記録
    """

    __tablename__ = "task_executions"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("task_templates.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 実行時のコンテキスト
    context = Column(JSON, nullable=True)  # アクションから得られたコンテキスト

    # 実行結果
    result = Column(Text, nullable=True)
    extensions_output = Column(JSON, nullable=True)
    status = Column(
        String, index=True, nullable=False, default="pending"
    )  # 'pending', 'processing', 'completed', 'failed'
    error = Column(Text, nullable=True)

    # 実行時間情報
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # リレーションシップ
    template = relationship("TaskTemplate", back_populates="executions")
    user = relationship("User", backref="task_executions")

    def __repr__(self) -> str:
        """文字列表現
        Returns:
            str: タスク実行ログの文字列表現
        """
        return f"<TaskExecution(id={self.id}, template_id={self.template_id}, status={self.status})>"
