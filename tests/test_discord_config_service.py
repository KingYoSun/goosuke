"""
Discord設定サービスのテスト

このモジュールは、Discord設定サービスの機能をテストします。
"""

from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest

from api.models.config_discord import ConfigDiscord
from api.services.discord_config_service import DiscordConfigService


@pytest.mark.asyncio
async def test_create_discord_config(db_session):
    """Discord設定作成機能をテスト"""

    # get_db関数をオーバーライドして、テスト用のdb_sessionを返すようにする
    @asynccontextmanager
    async def override_get_db():
        yield db_session

    # Discord設定サービスのインスタンスを作成
    discord_config_service = DiscordConfigService()

    # get_db関数をパッチして、テスト用のdb_sessionを使用する
    with patch("api.services.discord_config_service._get_db_context", override_get_db):
        # Discord設定を作成
        result = await discord_config_service.create_discord_config(
            name="テスト設定",
            catch_type="reaction",
            catch_value="✅",
            message_type="single",
            response_format="reply",
        )

    # 結果を検証
    assert result["id"] is not None
    assert result["name"] == "テスト設定"
    assert result["catch_type"] == "reaction"
    assert result["catch_value"] == "✅"
    assert result["message_type"] == "single"
    assert result["response_format"] == "reply"
    assert "created_at" in result


@pytest.mark.asyncio
async def test_get_discord_config(db_session):
    """Discord設定取得機能をテスト"""
    # テスト用のDiscord設定を作成
    discord_config = ConfigDiscord(
        name="取得テスト",
        catch_type="text",
        catch_value="!test",
        message_type="thread",
        response_format="dm",
    )
    db_session.add(discord_config)
    await db_session.commit()
    await db_session.refresh(discord_config)

    # get_db関数をオーバーライドして、テスト用のdb_sessionを返すようにする
    @asynccontextmanager
    async def override_get_db():
        yield db_session

    # Discord設定サービスのインスタンスを作成
    discord_config_service = DiscordConfigService()

    # get_db関数をパッチして、テスト用のdb_sessionを使用する
    with patch("api.services.discord_config_service._get_db_context", override_get_db):
        # Discord設定を取得
        result = await discord_config_service.get_discord_config(discord_config.id)

    # 結果を検証
    assert result["id"] == discord_config.id
    assert result["name"] == "取得テスト"
    assert result["catch_type"] == "text"
    assert result["catch_value"] == "!test"
    assert result["message_type"] == "thread"
    assert result["response_format"] == "dm"
    assert "created_at" in result


@pytest.mark.asyncio
async def test_get_discord_config_by_reaction(db_session):
    """リアクションによるDiscord設定取得機能をテスト"""
    # テスト用のDiscord設定を作成
    discord_config = ConfigDiscord(
        name="リアクション取得テスト",
        catch_type="reaction",
        catch_value="🔍",
        message_type="single",
        response_format="reply",
    )
    db_session.add(discord_config)
    await db_session.commit()
    await db_session.refresh(discord_config)

    # get_db関数をオーバーライドして、テスト用のdb_sessionを返すようにする
    @asynccontextmanager
    async def override_get_db():
        yield db_session

    # Discord設定サービスのインスタンスを作成
    discord_config_service = DiscordConfigService()

    # get_db関数をパッチして、テスト用のdb_sessionを使用する
    with patch("api.services.discord_config_service._get_db_context", override_get_db):
        # リアクション値でDiscord設定を取得
        result = await discord_config_service.get_discord_config_by_reaction("🔍")

    # 結果を検証
    assert result is not None
    assert result["id"] == discord_config.id
    assert result["name"] == "リアクション取得テスト"
    assert result["catch_type"] == "reaction"
    assert result["catch_value"] == "🔍"

    # 存在しないリアクション値でテスト
    with patch("api.services.discord_config_service._get_db_context", override_get_db):
        result = await discord_config_service.get_discord_config_by_reaction("🔄")

    # 結果を検証
    assert result is None


@pytest.mark.asyncio
async def test_list_discord_configs(db_session):
    """Discord設定一覧取得機能をテスト"""
    # テスト用のDiscord設定を複数作成
    configs = [
        ConfigDiscord(
            name=f"一覧テスト{i+1}",
            catch_type="reaction" if i % 2 == 0 else "text",
            catch_value=f"テスト値{i+1}",
            message_type="single",
            response_format="reply",
        )
        for i in range(3)
    ]

    for config in configs:
        db_session.add(config)
    await db_session.commit()

    # get_db関数をオーバーライドして、テスト用のdb_sessionを返すようにする
    @asynccontextmanager
    async def override_get_db():
        yield db_session

    # Discord設定サービスのインスタンスを作成
    discord_config_service = DiscordConfigService()

    # get_db関数をパッチして、テスト用のdb_sessionを使用する
    with patch("api.services.discord_config_service._get_db_context", override_get_db):
        # すべてのDiscord設定を取得
        all_results = await discord_config_service.list_discord_configs()
        assert len(all_results) >= 3  # 他のテストで作成されたものも含まれる可能性がある

        # タイプでフィルタリング
        reaction_results = await discord_config_service.list_discord_configs(catch_type="reaction")
        assert len(reaction_results) >= 2  # 少なくとも2つのreactionタイプがある
        for result in reaction_results:
            assert result["catch_type"] == "reaction"

        # 制限とオフセットをテスト
        limited_results = await discord_config_service.list_discord_configs(limit=2)
        assert len(limited_results) == 2


@pytest.mark.asyncio
async def test_update_discord_config(db_session):
    """Discord設定更新機能をテスト"""
    # テスト用のDiscord設定を作成
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

    # get_db関数をオーバーライドして、テスト用のdb_sessionを返すようにする
    @asynccontextmanager
    async def override_get_db():
        yield db_session

    # Discord設定サービスのインスタンスを作成
    discord_config_service = DiscordConfigService()

    # get_db関数をパッチして、テスト用のdb_sessionを使用する
    with patch("api.services.discord_config_service._get_db_context", override_get_db):
        # Discord設定を更新
        result = await discord_config_service.update_discord_config(
            config_id=discord_config.id,
            name="更新後の設定",
            catch_type="text",
            catch_value="!updated",
            message_type="thread",
            response_format="channel",
        )

    # 結果を検証
    assert result["id"] == discord_config.id
    assert result["name"] == "更新後の設定"
    assert result["catch_type"] == "text"
    assert result["catch_value"] == "!updated"
    assert result["message_type"] == "thread"
    assert result["response_format"] == "channel"
    assert "updated_at" in result

    # 存在しないIDで更新をテスト
    with patch("api.services.discord_config_service._get_db_context", override_get_db):
        result = await discord_config_service.update_discord_config(
            config_id=9999,
            name="存在しない設定",
        )

    # 結果を検証
    assert result is None


@pytest.mark.asyncio
async def test_delete_discord_config(db_session):
    """Discord設定削除機能をテスト"""
    # テスト用のDiscord設定を作成
    discord_config = ConfigDiscord(
        name="削除テスト",
        catch_type="reaction",
        catch_value="❌",
        message_type="single",
        response_format="reply",
    )
    db_session.add(discord_config)
    await db_session.commit()
    await db_session.refresh(discord_config)

    # get_db関数をオーバーライドして、テスト用のdb_sessionを返すようにする
    @asynccontextmanager
    async def override_get_db():
        yield db_session

    # Discord設定サービスのインスタンスを作成
    discord_config_service = DiscordConfigService()

    # get_db関数をパッチして、テスト用のdb_sessionを使用する
    with patch("api.services.discord_config_service._get_db_context", override_get_db):
        # Discord設定を削除
        success = await discord_config_service.delete_discord_config(discord_config.id)

    # 結果を検証
    assert success is True

    # 削除されたことを確認
    with patch("api.services.discord_config_service._get_db_context", override_get_db):
        result = await discord_config_service.get_discord_config(discord_config.id)
        assert result is None

    # 存在しないIDで削除をテスト
    with patch("api.services.discord_config_service._get_db_context", override_get_db):
        success = await discord_config_service.delete_discord_config(9999)
        assert success is False
