"""
タスクモデルモジュール

このモジュールは、コンテキストとプロンプトをセットにした実行可能なタスクを管理するデータモデルを定義します。
"""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Task(Base):
    """タスクモデル
    コンテキストとプロンプトをセットにした実行可能なタスク
    """

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String, index=True, nullable=True)  # タスク名（再利用のため）
    task_type = Column(String, index=True, nullable=False)  # 'discord_summary', 'api_request', etc.

    # コンテキストとプロンプトを明確に分離
    context = Column(JSON, nullable=True)  # アクションから得られたコンテキスト
    prompt = Column(Text, nullable=False)  # ユーザーが望む動作を記述したプロンプト

    result = Column(Text, nullable=True)
    extensions_output = Column(JSON, nullable=True)
    status = Column(
        String, index=True, nullable=False, default="pending"
    )  # 'pending', 'processing', 'completed', 'failed'
    error = Column(Text, nullable=True)

    # 再利用関連
    is_template = Column(Boolean, default=False)  # テンプレートとして使用可能か
    parent_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)  # 親タスク（テンプレート）

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # リレーションシップ
    user = relationship("User", backref="tasks")
    parent = relationship("Task", remote_side=[id], backref="derived_tasks")

    def __repr__(self) -> str:
        """文字列表現
        Returns:
            str: タスクの文字列表現
        """
        return f"<Task(id={self.id}, name={self.name}, type={self.task_type}, status={self.status})>"
