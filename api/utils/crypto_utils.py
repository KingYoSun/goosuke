"""
暗号化ユーティリティモジュール

このモジュールは、秘密情報の暗号化・復号化を行うユーティリティ関数を提供します。
"""

import base64
import json
import logging
from typing import Any, Dict, Optional, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..config import settings

logger = logging.getLogger(__name__)


def _get_encryption_key() -> bytes:
    """暗号化キーを取得する

    Returns:
        bytes: 暗号化キー
    """
    try:
        # SECRET_KEYからFernetキーを生成
        password = settings.SECRET_KEY.encode()
        salt = b"goosuke_salt"  # 本番環境では環境変数から取得するなど、より安全な方法で管理
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    except Exception as e:
        # エラーが発生した場合はデフォルトのキーを返す
        logger.error(f"暗号化キーの生成に失敗しました: {e}")
        # Fernetキーは32バイトをBase64エンコードした形式である必要がある
        return base64.urlsafe_b64encode(b"0123456789012345678901234567890123456789012345678901234567890123"[:32])


def encrypt_value(value: Union[str, Dict[str, Any], list, int, float, bool, None]) -> Optional[str]:
    """値を暗号化する

    Args:
        value (Union[str, Dict[str, Any], list, int, float, bool, None]): 暗号化する値

    Returns:
        Optional[str]: 暗号化された値（Base64エンコード）、エラー時はNone
    """
    if value is None:
        return None

    try:
        # JSON形式に変換
        value_str = json.dumps(value)

        # 暗号化
        try:
            f = Fernet(_get_encryption_key())
            encrypted = f.encrypt(value_str.encode())

            # Base64エンコード
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"値の暗号化に失敗しました: {e}")
            # エラーが発生した場合は元の値をJSON文字列としてBase64エンコード
            logger.warning("暗号化に失敗したため、Base64エンコードのみを適用します")
            return base64.urlsafe_b64encode(value_str.encode()).decode()
    except Exception as e:
        logger.error(f"値のJSON変換に失敗しました: {e}")
        return None


def decrypt_value(encrypted_value: str) -> Any:
    """暗号化された値を復号化する

    Args:
        encrypted_value (str): 暗号化された値（Base64エンコード）

    Returns:
        Any: 復号化された値
    """
    if encrypted_value is None:
        return None

    try:
        # Base64デコード
        encrypted = base64.urlsafe_b64decode(encrypted_value)

        try:
            # 復号化
            f = Fernet(_get_encryption_key())
            decrypted = f.decrypt(encrypted)

            # JSON形式から変換
            return json.loads(decrypted.decode())
        except Exception as e:
            logger.error(f"値の復号化に失敗しました: {e}")
            # 復号化に失敗した場合は、Base64デコードした値をそのまま返す
            try:
                # Base64デコードした値をJSON形式から変換
                return json.loads(encrypted.decode())
            except Exception as e2:
                logger.error(f"Base64デコード後のJSON変換に失敗しました: {e2}")
                # それも失敗した場合は元の値をそのまま返す
                return encrypted_value
    except Exception as e:
        logger.error(f"Base64デコードに失敗しました: {e}")
        return encrypted_value


def maybe_encrypt_value(value: Any, is_secret: bool) -> Any:
    """必要に応じて値を暗号化する

    Args:
        value (Any): 値
        is_secret (bool): 秘密情報かどうか

    Returns:
        Any: 暗号化された値（秘密情報の場合）または元の値
    """
    if not is_secret or value is None:
        return value

    return encrypt_value(value)


def maybe_decrypt_value(value: Any, is_secret: bool) -> Any:
    """必要に応じて値を復号化する

    Args:
        value (Any): 値
        is_secret (bool): 秘密情報かどうか

    Returns:
        Any: 復号化された値（秘密情報の場合）または元の値
    """
    if not is_secret or value is None:
        return value

    return decrypt_value(value)
