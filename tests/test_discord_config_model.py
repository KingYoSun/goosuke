"""
Discord設定モデルのテスト

このモジュールは、Discord設定モデルの機能をテストします。
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.config_discord import ConfigDiscord


@pytest.mark.asyncio
async def test_create_discord_config(db_session: AsyncSession):
    """Discord設定の作成をテスト"""
    # Discord設定を作成
    discord_config = ConfigDiscord(
        name="テスト設定",
        catch_type="reaction",
        catch_value="✅",
        message_type="single",
        response_format="reply",
    )
    db_session.add(discord_config)
    await db_session.commit()
    await db_session.refresh(discord_config)

    # 作成されたDiscord設定を検証
    assert discord_config.id is not None
    assert discord_config.name == "テスト設定"
    assert discord_config.catch_type == "reaction"
    assert discord_config.catch_value == "✅"
    assert discord_config.message_type == "single"
    assert discord_config.response_format == "reply"
    assert discord_config.created_at is not None


@pytest.mark.asyncio
async def test_discord_config_enum_values(db_session: AsyncSession):
    """Discord設定の列挙型フィールドをテスト"""
    # 異なる列挙型の値でDiscord設定を作成
    configs = [
        ConfigDiscord(
            name="リアクション設定",
            catch_type="reaction",
            catch_value="👍",
            message_type="single",
            response_format="reply",
        ),
        ConfigDiscord(
            name="テキスト設定",
            catch_type="text",
            catch_value="!summary",
            message_type="thread",
            response_format="dm",
        ),
        ConfigDiscord(
            name="メンション設定",
            catch_type="textWithMention",
            catch_value="summarize",
            message_type="range",
            response_format="channel",
        ),
    ]

    # 設定を保存
    for config in configs:
        db_session.add(config)
    await db_session.commit()

    # 各設定を検証
    for i, config in enumerate(configs):
        await db_session.refresh(config)
        assert config.id is not None

    # 列挙型の値を検証
    assert configs[0].catch_type == "reaction"
    assert configs[0].message_type == "single"
    assert configs[0].response_format == "reply"

    assert configs[1].catch_type == "text"
    assert configs[1].message_type == "thread"
    assert configs[1].response_format == "dm"

    assert configs[2].catch_type == "textWithMention"
    assert configs[2].message_type == "range"
    assert configs[2].response_format == "channel"


@pytest.mark.asyncio
async def test_update_discord_config(db_session: AsyncSession):
    """Discord設定の更新をテスト"""
    # Discord設定を作成
    discord_config = ConfigDiscord(
        name="更新テスト",
        catch_type="reaction",
        catch_value="🔄",
        message_type="single",
        response_format="reply",
    )
    db_session.add(discord_config)
    await db_session.commit()
    await db_session.refresh(discord_config)

    # 初期状態を検証
    assert discord_config.name == "更新テスト"
    assert discord_config.catch_type == "reaction"
    assert discord_config.catch_value == "🔄"

    # 設定を更新
    discord_config.name = "更新後の設定"
    discord_config.catch_type = "text"
    discord_config.catch_value = "!updated"
    discord_config.message_type = "thread"
    discord_config.response_format = "channel"

    await db_session.commit()
    await db_session.refresh(discord_config)

    # 更新後の状態を検証
    assert discord_config.name == "更新後の設定"
    assert discord_config.catch_type == "text"
    assert discord_config.catch_value == "!updated"
    assert discord_config.message_type == "thread"
    assert discord_config.response_format == "channel"
    assert discord_config.updated_at is not None
