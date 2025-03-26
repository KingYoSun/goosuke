"""
設定サービスのテスト

このモジュールは、設定サービスの機能をテストします。
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.setting_service import SettingService
from api.utils.crypto_utils import decrypt_value


class SettingCreateMock:
    """設定作成モッククラス"""

    def __init__(self, key, value, description=None, is_secret=False):
        self.key = key
        self.value = value
        self.description = description
        self.is_secret = is_secret


class SettingUpdateMock:
    """設定更新モッククラス"""

    def __init__(self, key=None, value=None, description=None, is_secret=None):
        self.key = key
        self.value = value
        self.description = description
        self.is_secret = is_secret


@pytest.mark.asyncio
async def test_add_setting(db_session: AsyncSession):
    """設定の追加をテスト"""
    service = SettingService()

    # 通常の設定を追加
    normal_setting = SettingCreateMock(
        key="NORMAL_SETTING",
        value="normal_value",
        description="通常の設定",
        is_secret=False,
    )
    result = await service.add_setting(normal_setting)

    # 結果を検証
    assert result["id"] is not None
    assert result["key"] == "NORMAL_SETTING"
    assert result["value"] == "normal_value"
    assert result["description"] == "通常の設定"
    assert result["is_secret"] is False

    # 秘密情報を追加
    secret_setting = SettingCreateMock(
        key="SECRET_SETTING",
        value="secret_value",
        description="秘密の設定",
        is_secret=True,
    )
    result = await service.add_setting(secret_setting)

    # 結果を検証（秘密情報は表示されない）
    assert result["id"] is not None
    assert result["key"] == "SECRET_SETTING"
    assert result["value"] == "********"  # マスクされている
    assert result["description"] == "秘密の設定"
    assert result["is_secret"] is True

    # データベースから直接取得して検証
    setting = await service.get_setting_by_key("SECRET_SETTING")
    assert setting is not None
    assert setting["key"] == "SECRET_SETTING"
    assert setting["value"] == "secret_value"  # 復号化されている
    assert setting["description"] == "秘密の設定"
    assert setting["is_secret"] is True


@pytest.mark.asyncio
async def test_get_setting(db_session: AsyncSession):
    """設定の取得をテスト"""
    service = SettingService()

    # 通常の設定を追加
    normal_setting = SettingCreateMock(
        key="GET_NORMAL",
        value="normal_value",
        description="通常の設定",
        is_secret=False,
    )
    normal_result = await service.add_setting(normal_setting)

    # 秘密情報を追加
    secret_setting = SettingCreateMock(
        key="GET_SECRET",
        value="secret_value",
        description="秘密の設定",
        is_secret=True,
    )
    secret_result = await service.add_setting(secret_setting)

    # IDで設定を取得
    normal_setting = await service.get_setting(normal_result["id"])
    assert normal_setting is not None
    assert normal_setting["key"] == "GET_NORMAL"
    assert normal_setting["value"] == "normal_value"
    assert normal_setting["is_secret"] is False

    # IDで秘密情報を取得（復号化されている）
    secret_setting = await service.get_setting(secret_result["id"])
    assert secret_setting is not None
    assert secret_setting["key"] == "GET_SECRET"
    assert secret_setting["value"] == "secret_value"  # 復号化されている
    assert secret_setting["is_secret"] is True

    # キーで設定を取得
    normal_setting = await service.get_setting_by_key("GET_NORMAL")
    assert normal_setting is not None
    assert normal_setting["key"] == "GET_NORMAL"
    assert normal_setting["value"] == "normal_value"

    # キーで秘密情報を取得（復号化されている）
    secret_setting = await service.get_setting_by_key("GET_SECRET")
    assert secret_setting is not None
    assert secret_setting["key"] == "GET_SECRET"
    assert secret_setting["value"] == "secret_value"  # 復号化されている


@pytest.mark.asyncio
async def test_list_settings(db_session: AsyncSession):
    """設定一覧の取得をテスト"""
    service = SettingService()

    # 複数の設定を追加
    settings = [
        SettingCreateMock(key="LIST_NORMAL_1", value="value1", is_secret=False),
        SettingCreateMock(key="LIST_SECRET_1", value="secret1", is_secret=True),
        SettingCreateMock(key="LIST_NORMAL_2", value="value2", is_secret=False),
        SettingCreateMock(key="LIST_SECRET_2", value="secret2", is_secret=True),
    ]

    for setting in settings:
        await service.add_setting(setting)

    # 設定一覧を取得
    settings_list = await service.list_settings()

    # 結果を検証
    assert len(settings_list) >= 4  # 他のテストで作成された設定も含まれる可能性がある

    # 秘密情報がマスクされていることを確認
    for setting in settings_list:
        if setting["is_secret"]:
            assert setting["value"] == "********"  # マスクされている
        elif setting["key"] in ["LIST_NORMAL_1", "LIST_NORMAL_2"]:
            assert setting["value"] in ["value1", "value2"]  # マスクされていない


@pytest.mark.asyncio
async def test_update_setting(db_session: AsyncSession):
    """設定の更新をテスト"""
    service = SettingService()

    # 通常の設定を追加
    normal_setting = SettingCreateMock(
        key="UPDATE_NORMAL",
        value="initial_value",
        description="更新前の説明",
        is_secret=False,
    )
    normal_result = await service.add_setting(normal_setting)

    # 秘密情報を追加
    secret_setting = SettingCreateMock(
        key="UPDATE_SECRET",
        value="initial_secret",
        description="更新前の秘密",
        is_secret=True,
    )
    secret_result = await service.add_setting(secret_setting)

    # 通常の設定を更新
    update_data = SettingUpdateMock(
        value="updated_value",
        description="更新後の説明",
    )
    updated_normal = await service.update_setting(normal_result["id"], update_data)
    assert updated_normal["value"] == "updated_value"
    assert updated_normal["description"] == "更新後の説明"
    assert updated_normal["is_secret"] is False

    # 秘密情報を更新
    update_data = SettingUpdateMock(
        value="updated_secret",
        description="更新後の秘密",
    )
    updated_secret = await service.update_setting(secret_result["id"], update_data)
    assert updated_secret["value"] == "********"  # マスクされている
    assert updated_secret["description"] == "更新後の秘密"
    assert updated_secret["is_secret"] is True

    # 更新された秘密情報を取得して検証
    secret_setting = await service.get_setting(secret_result["id"])
    assert secret_setting["value"] == "updated_secret"  # 復号化されている

    # 通常の設定を秘密情報に変更
    update_data = SettingUpdateMock(is_secret=True)
    updated_to_secret = await service.update_setting(normal_result["id"], update_data)
    assert updated_to_secret["is_secret"] is True
    assert updated_to_secret["value"] == "********"  # マスクされている

    # 秘密情報を通常の設定に変更
    update_data = SettingUpdateMock(is_secret=False)
    updated_to_normal = await service.update_setting(secret_result["id"], update_data)
    assert updated_to_normal["is_secret"] is False
    assert updated_to_normal["value"] == "updated_secret"  # マスクされていない


@pytest.mark.asyncio
async def test_remove_setting(db_session: AsyncSession):
    """設定の削除をテスト"""
    service = SettingService()

    # 設定を追加
    setting = SettingCreateMock(
        key="REMOVE_TEST",
        value="test_value",
        description="削除テスト用の設定",
        is_secret=False,
    )
    result = await service.add_setting(setting)

    # 設定が存在することを確認
    setting = await service.get_setting(result["id"])
    assert setting is not None

    # 設定を削除
    delete_result = await service.remove_setting(result["id"])
    assert delete_result is True

    # 設定が削除されたことを確認
    setting = await service.get_setting(result["id"])
    assert setting is None

    # 存在しない設定の削除を試みる
    delete_result = await service.remove_setting(9999)
    assert delete_result is False


@pytest.mark.asyncio
async def test_encryption_in_database(db_session: AsyncSession):
    """データベース内での暗号化をテスト"""
    service = SettingService()

    # 秘密情報を追加
    secret_setting = SettingCreateMock(
        key="ENCRYPTION_TEST",
        value="secret_value_for_encryption_test",
        description="暗号化テスト用の設定",
        is_secret=True,
    )
    result = await service.add_setting(secret_setting)

    # データベースから直接クエリを実行して暗号化された値を取得
    from sqlalchemy import text

    query = text("SELECT value FROM settings WHERE key = 'ENCRYPTION_TEST'")
    db_result = await db_session.execute(query)
    encrypted_value = db_result.scalar()

    # 暗号化された値が元の値と異なることを確認
    assert encrypted_value != "secret_value_for_encryption_test"

    # 暗号化された値を復号化して元の値と一致することを確認
    decrypted_value = decrypt_value(encrypted_value)
    assert decrypted_value == "secret_value_for_encryption_test"
