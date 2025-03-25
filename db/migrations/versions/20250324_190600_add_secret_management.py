"""
APIキー管理のセキュリティ強化のためのマイグレーション

このマイグレーションでは、以下の変更を行います：
1. Settingモデルに is_secret カラムを追加
2. Extensionモデルに secrets カラムを追加
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20250324_190600_add_secret_management"
down_revision = "10ed3b1e2663"  # 前のマイグレーションの実際のリビジョンID
branch_labels = None
depends_on = None


def upgrade():
    # Settingモデルに is_secret カラムを追加
    op.add_column("settings", sa.Column("is_secret", sa.Boolean(), nullable=False, server_default="0"))

    # Extensionモデルに secrets カラムを追加
    op.add_column("extensions", sa.Column("secrets", sa.JSON(), nullable=True))


def downgrade():
    # 追加したカラムを削除
    op.drop_column("extensions", "secrets")
    op.drop_column("settings", "is_secret")
