"""
ヘルスチェック機能のテストモジュール

このモジュールは、ヘルスチェック機能のテストを提供します。
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_health_check(client: AsyncClient):
    """ヘルスチェックエンドポイントのテスト"""
    # ヘルスチェックリクエスト
    response = await client.get("/api/health/")

    # レスポンスの検証
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "app_name" in data
    assert "app_version" in data
    assert "environment" in data
    assert "system_info" in data
    assert "database" in data
    # テスト環境ではデータベース接続が失敗する可能性があるため、
    # ステータスの検証は行わず、キーが存在することだけを確認する
    assert "status" in data["database"]


async def test_ping(client: AsyncClient):
    """Pingエンドポイントのテスト"""
    # Pingリクエスト
    response = await client.get("/api/health/ping")

    # レスポンスの検証
    assert response.status_code == 200
    data = response.json()
    assert data["ping"] == "pong"


async def test_root(client: AsyncClient):
    """ルートエンドポイントのテスト"""
    # ルートリクエスト
    response = await client.get("/")

    # レスポンスの検証
    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data
    assert "version" in data
    assert "description" in data
