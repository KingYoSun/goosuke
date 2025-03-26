"""
設定モデルのテスト

このモジュールは、設定モデルの機能をテストします。
"""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.models.setting import Setting


@pytest.mark.asyncio
async def test_create_setting(db_session: AsyncSession):
    """設定の作成をテスト"""
    # 設定を作成
    setting = Setting(
        key="TEST_API_KEY",
        value="test_api_key_value",
        description="テスト用のAPI Key",
        is_secret=True,
    )
    db_session.add(setting)
    await db_session.commit()

    # 作成された設定を検証
    assert setting.id is not None
    assert setting.key == "TEST_API_KEY"
    assert setting.value == "test_api_key_value"
    assert setting.description == "テスト用のAPI Key"
    assert setting.is_secret is True
    assert setting.created_at is not None
    assert setting.updated_at is None  # 新規作成時はupdated_atはNone

    # データベースから直接取得して検証
    result = await db_session.execute(select(Setting).where(Setting.id == setting.id))
    db_setting = result.scalars().first()
    assert db_setting is not None
    assert db_setting.key == "TEST_API_KEY"
    assert db_setting.value == "test_api_key_value"
    assert db_setting.is_secret is True


@pytest.mark.asyncio
async def test_update_setting(db_session: AsyncSession):
    """設定の更新をテスト"""
    # 設定を作成
    setting = Setting(
        key="UPDATE_TEST_KEY",
        value="initial_value",
        description="更新前の説明",
        is_secret=False,
    )
    db_session.add(setting)
    await db_session.commit()

    # 初期状態を検証
    assert setting.key == "UPDATE_TEST_KEY"
    assert setting.value == "initial_value"
    assert setting.description == "更新前の説明"
    assert setting.is_secret is False

    # 設定を更新
    setting.value = "updated_value"
    setting.description = "更新後の説明"
    setting.is_secret = True

    await db_session.commit()

    # 更新された設定を検証
    assert setting.key == "UPDATE_TEST_KEY"  # 変更なし
    assert setting.value == "updated_value"
    assert setting.description == "更新後の説明"
    assert setting.is_secret is True

    # データベースから直接取得して検証
    result = await db_session.execute(select(Setting).where(Setting.id == setting.id))
    db_setting = result.scalars().first()
    assert db_setting is not None
    assert db_setting.value == "updated_value"
    assert db_setting.description == "更新後の説明"
    assert db_setting.is_secret is True


@pytest.mark.asyncio
async def test_query_settings(db_session: AsyncSession):
    """設定のクエリをテスト"""
    # 複数の設定を作成
    settings = [
        Setting(
            key="QUERY_TEST_1",
            value="value1",
            description="通常の設定",
            is_secret=False,
        ),
        Setting(
            key="QUERY_TEST_2",
            value="value2",
            description="秘密の設定",
            is_secret=True,
        ),
        Setting(
            key="QUERY_TEST_3",
            value="value3",
            description="別の通常の設定",
            is_secret=False,
        ),
    ]

    for setting in settings:
        db_session.add(setting)

    await db_session.commit()

    # すべての設定を取得
    result = await db_session.execute(select(Setting))
    all_settings = result.scalars().all()
    assert len(all_settings) >= 3  # 他のテストで作成された設定も含まれる可能性がある

    # 秘密情報でフィルタリング
    result = await db_session.execute(select(Setting).where(Setting.is_secret == True))
    secret_settings = result.scalars().all()
    assert len(secret_settings) >= 1
    for setting in secret_settings:
        assert setting.is_secret is True

    # キーで検索
    result = await db_session.execute(select(Setting).where(Setting.key == "QUERY_TEST_2"))
    found_setting = result.scalars().first()
    assert found_setting is not None
    assert found_setting.key == "QUERY_TEST_2"
    assert found_setting.is_secret is True


@pytest.mark.asyncio
async def test_setting_string_representation(db_session: AsyncSession):
    """設定の文字列表現をテスト"""
    # 設定を作成
    setting = Setting(
        key="STRING_REPR_TEST",
        value="test_value",
        description="文字列表現をテストする設定",
        is_secret=False,
    )
    db_session.add(setting)
    await db_session.commit()

    # 文字列表現を検証
    string_repr = str(setting)
    assert "<Setting(key=STRING_REPR_TEST)>" == string_repr


@pytest.mark.asyncio
async def test_setting_unique_key_constraint(db_session: AsyncSession):
    """設定キーの一意性制約をテスト"""
    # 1つ目の設定を作成
    setting1 = Setting(
        key="UNIQUE_TEST",
        value="value1",
        description="一意性テスト用の設定1",
        is_secret=False,
    )
    db_session.add(setting1)
    await db_session.commit()

    # 同じキーで2つ目の設定を作成
    setting2 = Setting(
        key="UNIQUE_TEST",
        value="value2",
        description="一意性テスト用の設定2",
        is_secret=True,
    )
    db_session.add(setting2)

    # 一意性制約違反のエラーが発生することを確認
    with pytest.raises(IntegrityError):
        await db_session.commit()
