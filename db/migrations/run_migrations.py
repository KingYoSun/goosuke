#!/usr/bin/env python
"""
データベースマイグレーション実行スクリプト

このスクリプトは、Alembicを使用してデータベースマイグレーションを実行します。
マイグレーションの作成、アップグレード、ダウングレードをサポートします。
"""

import argparse
import subprocess
import sys
from pathlib import Path

# プロジェクトルートディレクトリを取得
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
# alembic.iniのパス
ALEMBIC_INI_PATH = PROJECT_ROOT / "alembic.ini"


def run_migrations(args):
    """マイグレーションを実行する

    Args:
        args: コマンドライン引数
    """
    # Alembicコマンドの作成
    alembic_cmd = ["alembic"]

    # 設定ファイルのパスを指定
    alembic_cmd.extend(["-c", str(ALEMBIC_INI_PATH)])

    # サブコマンドを追加
    if args.create:
        # マイグレーションスクリプトの作成
        alembic_cmd.extend(["revision", "--autogenerate", "-m", args.message])
    elif args.downgrade:
        # ダウングレード
        alembic_cmd.extend(["downgrade", args.revision])
    elif args.revision:
        # 特定のリビジョンへのアップグレード
        alembic_cmd.extend(["upgrade", args.revision])
    else:
        # 最新バージョンへのアップグレード
        alembic_cmd.extend(["upgrade", "head"])

    # コマンドを実行
    print(f"実行コマンド: {' '.join(alembic_cmd)}")
    result = subprocess.run(alembic_cmd, cwd=PROJECT_ROOT)

    if result.returncode != 0:
        print("マイグレーションの実行中にエラーが発生しました。")
        sys.exit(1)

    print("マイグレーションが正常に完了しました。")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="データベースマイグレーションを実行します。")
    parser.add_argument(
        "--revision",
        "-r",
        help="アップグレード/ダウングレードするリビジョン（デフォルト: head）",
        default="head",
    )
    parser.add_argument("--downgrade", "-d", help="ダウングレードを実行する", action="store_true")
    parser.add_argument(
        "--create",
        "-c",
        help="新しいマイグレーションスクリプトを作成する",
        action="store_true",
    )
    parser.add_argument(
        "--message",
        "-m",
        help="マイグレーションスクリプトの説明メッセージ",
        default="auto generated migration",
    )

    args = parser.parse_args()
    run_migrations(args)


if __name__ == "__main__":
    main()
