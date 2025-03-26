"""
暗号化ユーティリティのテスト

このモジュールは、秘密情報の暗号化・復号化を行うユーティリティ関数をテストします。
"""

from api.utils.crypto_utils import (
    decrypt_value,
    encrypt_value,
    maybe_decrypt_value,
    maybe_encrypt_value,
)


def test_encrypt_decrypt_string():
    """文字列の暗号化・復号化をテスト"""
    # 文字列を暗号化
    original_value = "test_secret_value"
    encrypted_value = encrypt_value(original_value)

    # 暗号化された値が元の値と異なることを確認
    assert encrypted_value != original_value
    assert isinstance(encrypted_value, str)

    # 暗号化された値を復号化
    decrypted_value = decrypt_value(encrypted_value)

    # 復号化された値が元の値と一致することを確認
    assert decrypted_value == original_value


def test_encrypt_decrypt_dict():
    """辞書の暗号化・復号化をテスト"""
    # 辞書を暗号化
    original_value = {"key1": "value1", "key2": 123, "key3": True}
    encrypted_value = encrypt_value(original_value)

    # 暗号化された値が元の値と異なることを確認
    assert encrypted_value != original_value
    assert isinstance(encrypted_value, str)

    # 暗号化された値を復号化
    decrypted_value = decrypt_value(encrypted_value)

    # 復号化された値が元の値と一致することを確認
    assert decrypted_value == original_value


def test_encrypt_decrypt_list():
    """リストの暗号化・復号化をテスト"""
    # リストを暗号化
    original_value = ["item1", "item2", 123, True]
    encrypted_value = encrypt_value(original_value)

    # 暗号化された値が元の値と異なることを確認
    assert encrypted_value != original_value
    assert isinstance(encrypted_value, str)

    # 暗号化された値を復号化
    decrypted_value = decrypt_value(encrypted_value)

    # 復号化された値が元の値と一致することを確認
    assert decrypted_value == original_value


def test_encrypt_decrypt_none():
    """None値の暗号化・復号化をテスト"""
    # None値を暗号化
    original_value = None
    encrypted_value = encrypt_value(original_value)

    # None値は暗号化されずにNoneのままであることを確認
    assert encrypted_value is None

    # 復号化も同様にNoneを返すことを確認
    decrypted_value = decrypt_value(encrypted_value)
    assert decrypted_value is None


def test_maybe_encrypt_value():
    """条件付き暗号化をテスト"""
    # 秘密情報の場合は暗号化される
    original_value = "secret_value"
    encrypted_value = maybe_encrypt_value(original_value, True)
    assert encrypted_value != original_value
    assert isinstance(encrypted_value, str)

    # 秘密情報でない場合は暗号化されない
    non_secret_value = "non_secret_value"
    non_encrypted_value = maybe_encrypt_value(non_secret_value, False)
    assert non_encrypted_value == non_secret_value

    # None値は暗号化されない
    none_value = None
    none_encrypted_value = maybe_encrypt_value(none_value, True)
    assert none_encrypted_value is None


def test_maybe_decrypt_value():
    """条件付き復号化をテスト"""
    # 秘密情報を暗号化
    original_value = "secret_value"
    encrypted_value = encrypt_value(original_value)

    # 秘密情報の場合は復号化される
    decrypted_value = maybe_decrypt_value(encrypted_value, True)
    assert decrypted_value == original_value

    # 秘密情報でない場合は復号化されない
    non_secret_value = "non_secret_value"
    non_decrypted_value = maybe_decrypt_value(non_secret_value, False)
    assert non_decrypted_value == non_secret_value

    # None値は復号化されない
    none_value = None
    none_decrypted_value = maybe_decrypt_value(none_value, True)
    assert none_decrypted_value is None


def test_encrypt_decrypt_complex_structure():
    """複雑なデータ構造の暗号化・復号化をテスト"""
    # 複雑なデータ構造を暗号化
    original_value = {
        "string": "test_string",
        "number": 123,
        "boolean": True,
        "list": [1, 2, 3, "four", {"five": 5}],
        "nested": {
            "key1": "value1",
            "key2": [True, False],
            "key3": {"subkey": "subvalue"},
        },
    }
    encrypted_value = encrypt_value(original_value)

    # 暗号化された値が元の値と異なることを確認
    assert encrypted_value != original_value
    assert isinstance(encrypted_value, str)

    # 暗号化された値を復号化
    decrypted_value = decrypt_value(encrypted_value)

    # 復号化された値が元の値と一致することを確認
    assert decrypted_value == original_value
