# Goosuke テスト実行ガイド

このドキュメントでは、Goosuke プロジェクトのテスト実行方法について説明します。

## テスト環境

テストは Docker を使用して実行されます。これにより、ローカル環境と CI/CD 環境で一貫したテスト実行が可能になります。

## 前提条件

- Docker
- Docker Compose

## ローカルでのテスト実行

### テストの実行

```bash
# テストの実行
docker-compose -f docker-compose.test.yml run --rm test

# 特定のテストファイルのみ実行
docker-compose -f docker-compose.test.yml run --rm test pytest tests/test_health.py

# 特定のテスト関数のみ実行
docker-compose -f docker-compose.test.yml run --rm test pytest tests/test_health.py::test_health_check
```

### リントの実行

```bash
# リントの実行
docker-compose -f docker-compose.test.yml run --rm lint

# 個別のリントツールを実行
docker-compose -f docker-compose.test.yml run --rm test sh -c "flake8 ."
docker-compose -f docker-compose.test.yml run --rm test sh -c "mypy ."
docker-compose -f docker-compose.test.yml run --rm test sh -c "black --check ."
docker-compose -f docker-compose.test.yml run --rm test sh -c "isort --check-only --profile black ."
```

### コードフォーマットの実行

```bash
# すべてのコードを自動フォーマット
docker-compose -f docker-compose.test.yml run --rm format

# 個別のフォーマットツールを実行
docker-compose -f docker-compose.test.yml run --rm test sh -c "autoflake --remove-all-unused-imports --recursive --in-place --exclude=__init__.py ."
docker-compose -f docker-compose.test.yml run --rm test sh -c "black ."
docker-compose -f docker-compose.test.yml run --rm test sh -c "isort --profile black ."
```

### テストとリントの両方を実行

```bash
docker-compose -f docker-compose.test.yml up --build
```

## コード品質設定

プロジェクトには以下のコード品質設定ファイルが含まれています：

### `.flake8`

flake8 の設定ファイルです。主な設定：

- 行の長さの制限: 88文字（black と同じ）
- 無視するエラー: E203, W503（black のフォーマットスタイルと競合するため）
- `__init__.py` ファイルでの使用されていないインポート (F401) を無視

### `pyproject.toml`

black と isort の設定ファイルです。主な設定：

- black の行の長さ: 88文字
- isort の設定: black プロファイルを使用
- Python バージョン: 3.10

## テストカバレッジ

テスト実行時にカバレッジレポートが生成されます。レポートは以下の形式で出力されます：

- ターミナル出力: テスト実行時に表示
- XML 形式: `coverage.xml` ファイルに出力（CI/CD 環境での使用）

## CI/CD 環境でのテスト

GitHub Actions を使用して、プッシュやプルリクエスト時に自動的にテストとリントが実行されます。ワークフローの設定は `.github/workflows/test.yml` に定義されています。

CI/CD 環境では以下のテストが実行されます：

1. リント（flake8, mypy, black, isort）
2. Python 3.10 と 3.11 でのテスト実行
3. テストカバレッジの測定と Codecov へのアップロード

## テスト戦略

### 単体テスト

- モデルテスト: データベースモデルの機能テスト
- サービステスト: ビジネスロジックを実装するサービス層のテスト
- ユーティリティテスト: ヘルパー関数やユーティリティのテスト

### 統合テスト

- 発火レイヤーと実行レイヤーの連携テスト
- Discord 連携テスト（モック使用）

### API テスト

- エンドポイントテスト
- 認証テスト
- ヘルスチェックテスト

## テスト作成のガイドライン

新しいテストを作成する際は、以下のガイドラインに従ってください：

1. テストファイルは `tests/` ディレクトリに配置する
2. テストファイル名は `test_` で始める
3. テスト関数名も `test_` で始める
4. 非同期テストには `@pytest.mark.asyncio` デコレータを使用する
5. テストには適切なドキュメント文字列を含める
6. モックを使用する場合は `unittest.mock` を使用する

## トラブルシューティング

### テストが失敗する場合

1. エラーメッセージを確認する
2. 依存関係が最新であることを確認する
3. ローカルの変更が Docker イメージに反映されていることを確認する

### リントエラーが発生する場合

1. フォーマットを実行して自動修正可能な問題を修正する: `docker-compose -f docker-compose.test.yml run --rm format`
2. 自動修正できない問題は手動で修正する
3. `.flake8` や `pyproject.toml` の設定を確認する

### Docker 関連の問題

1. Docker デーモンが実行中であることを確認する
2. Docker イメージを再ビルドする: `docker-compose -f docker-compose.test.yml build --no-cache`
3. Docker ボリュームをクリーンアップする: `docker volume prune`