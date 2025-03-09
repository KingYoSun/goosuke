"""
パスワード管理モジュール

このモジュールは、パスワードのハッシュ化と検証を行う機能を提供します。
"""

from passlib.context import CryptContext

# パスワードハッシュ化のコンテキスト
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワードを検証する関数
    Args:
        plain_password (str): 平文パスワード
        hashed_password (str): ハッシュ化されたパスワード
    Returns:
        bool: パスワードが一致する場合はTrue、それ以外はFalse
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """パスワードをハッシュ化する関数
    Args:
        password (str): 平文パスワード
    Returns:
        str: ハッシュ化されたパスワード
    """
    return pwd_context.hash(password)
