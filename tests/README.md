# Goosuke テスト

このディレクトリには、Goosuke プロジェクトのテストが含まれています。

## テスト構成

テストは以下のカテゴリに分類されています：

### 1. 基本機能テスト

- **test_health.py**: ヘルスチェック機能のテスト
- **test_auth.py**: 認証機能のテスト
- **test_action_model.py**: アクションモデルのテスト
- **test_action_service.py**: アクションサービスのテスト
- **test_task_model.py**: タスクモデルのテスト
- **test_task_executor.py**: タスク実行機能のテスト

### 2. 統合テスト

- **test_integration.py**: 発火レイヤーと実行レイヤーの連携テスト

### 3. Discord 連携テスト（新規追加）

- **test_discord_bot.py**: Discord Bot 機能のテスト
  - イベントハンドラのテスト
  - メッセージ処理のテスト
  - リアクション処理のテスト
  - エラー処理のテスト

- **test_discord_service.py**: Discord サービスのテスト
  - Bot サービスのテスト
  - Webhook サービスのテスト
  - エラー処理のテスト

- **test_discord_routes.py**: Discord API ルーターのテスト
  - エンドポイントのテスト
  - 認証のテスト
  - Webhook 処理のテスト
  - エラー処理のテスト

### 4. エラーハンドリングテスト（新規追加）

- **test_error_handling.py**: アプリケーション全体のエラーハンドリングテスト
  - データベースエラーのテスト
  - 認証エラーのテスト
  - バリデーションエラーのテスト
  - サービスレイヤーのエラー処理テスト
  - その他の異常系テスト

## テスト実行方法

### Docker を使用したテスト実行

プロジェクトルートディレクトリで以下のコマンドを実行します：

```bash
# すべてのテストを実行
docker-compose -f docker-compose.test.yml run --rm test

# 特定のテストファイルのみ実行
docker-compose -f docker-compose.test.yml run --rm test pytest tests/test_discord_bot.py

# 特定のテスト関数のみ実行
docker-compose -f docker-compose.test.yml run --rm test pytest tests/test_discord_bot.py::test_on_ready_handler
```

### ローカル環境でのテスト実行

プロジェクトルートディレクトリで以下のコマンドを実行します：

```bash
# 依存関係のインストール
pip install -r requirements.txt

# すべてのテストを実行
pytest

# 特定のテストファイルのみ実行
pytest tests/test_discord_bot.py

# 特定のテスト関数のみ実行
pytest tests/test_discord_bot.py::test_on_ready_handler

# カバレッジレポート付きでテスト実行
pytest --cov=. --cov-report=term --cov-report=html
```

## テストカバレッジ

テストカバレッジを確認するには、以下のコマンドを実行します：

```bash
# カバレッジレポートの生成
pytest --cov=. --cov-report=html

# HTMLレポートを開く
open htmlcov/index.html  # macOSの場合
```

## モックの使用

テストでは、外部依存関係（Discord API、データベース、Goose CLI など）をモックして、テストの再現性と信頼性を確保しています。主に以下のモックを使用しています：

- **unittest.mock**: Python 標準ライブラリのモック機能
- **AsyncMock**: 非同期関数のモック
- **MagicMock**: 柔軟なモック機能
- **patch**: 特定のモジュールや関数をモックに置き換える

## テスト作成のガイドライン

新しいテストを作成する際は、以下のガイドラインに従ってください：

1. テストファイル名は `test_` で始める
2. テスト関数名も `test_` で始める
3. 非同期テストには `@pytest.mark.asyncio` デコレータを使用する
4. テストには適切なドキュメント文字列を含める
5. モックを使用する場合は `unittest.mock` を使用する
6. 正常系と異常系の両方をテストする
7. エッジケースを考慮する
8. テストは独立して実行できるようにする