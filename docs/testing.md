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

## テスト設計原則

### 1. テスト間の独立性確保

各テストは独立して実行できるように設計されています。テスト間でのデータベース状態の共有による問題を防ぐため、以下の方法を採用しています：

- **トランザクションベースのテスト分離**: 各テストはトランザクション内で実行され、テスト終了時に自動的にロールバックされます。
- **テスト前のデータベースリセット**: 各テスト実行前にテーブルをクリアし、クリーンな状態から開始します。
- **フィクスチャの適切なスコープ設定**: テスト関数ごとに独立したデータベースセッションを提供します。

### 2. モックの最小化

テストの信頼性を高めるため、モックの使用を最小限にしています：

- **goose CLIとテスト用モックDB以外のモックは最小限に**: 実際のサービスロジックとデータベース操作をテストします。
- **外部APIや外部サービスのみをモック化**: 外部依存性のあるコンポーネントのみをモック化します。

### 3. データベース接続の統一

データベース接続のパターンを統一し、エラーハンドリングを強化しています：

```python
@asynccontextmanager
async def test_get_db_context():
    async with TestAsyncSessionLocal() as session:
        async with session.begin():
            yield session
            # トランザクションは自動的にロールバックされる
```

### 4. テストコードの保守性向上

テストコードの保守性を高めるため、以下の方法を採用しています：

- **共通のセットアップコードを集約**: `conftest.py`に共通のセットアップコードを集約しています。
- **テストヘルパー関数の導入**: 繰り返し行われる操作を関数化しています。
- **テストケースの目的と検証内容を明確化**: ドキュメント文字列を充実させています。

## テスト作成のガイドライン

新しいテストを作成する際は、以下のガイドラインに従ってください：

1. テストファイルは `tests/` ディレクトリに配置する
2. テストファイル名は `test_` で始める
3. テスト関数名も `test_` で始める
4. 非同期テストには `@pytest.mark.asyncio` デコレータを使用する
5. テストには適切なドキュメント文字列を含める
6. モックを使用する場合は `unittest.mock` を使用する
7. `commit()`の代わりに`flush()`を使用する（トランザクション内での操作のため）
8. データベースから直接取得して検証する処理を追加する
9. モックの使用を最小限にする（外部連携のみモック化）

## マイグレーションとテスト

テスト実行時のマイグレーション管理について説明します。

### マイグレーションの自動適用

テスト実行時には、最新のマイグレーションが自動的に適用されます。これにより、テスト環境のデータベーススキーマが常に最新の状態に保たれます。

テスト実行時の動作：

1. テストセッション開始時に、現在適用されているマイグレーションのバージョンと最新のマイグレーションのバージョンが比較されます。
2. 最新のマイグレーションが適用されていない場合は、自動的に適用されます。
3. マイグレーション適用後、SQLAlchemyのモデル定義に基づいてテーブルが作成されます。

### マイグレーション管理のベストプラクティス

1. **新しいマイグレーションを追加した場合**:
   - ローカル開発環境で `python db/migrations/run_migrations.py` を実行してマイグレーションを適用します。
   - テスト実行時には自動的に最新のマイグレーションが適用されるため、追加の操作は不要です。

2. **CI/CD環境でのマイグレーション**:
   - CI/CD環境でも同様に、テスト実行時に自動的に最新のマイグレーションが適用されます。

3. **マイグレーションの競合を避ける**:
   - 複数の開発者が同時にマイグレーションを作成する場合は、マイグレーションファイルの命名規則に注意してください。
   - タイムスタンプベースの命名を使用して、競合を避けます。

## トラブルシューティング

### テストが失敗する場合

1. エラーメッセージを確認する
2. 依存関係が最新であることを確認する
3. ローカルの変更が Docker イメージに反映されていることを確認する
4. トランザクションの問題がないか確認する（`commit()`ではなく`flush()`を使用しているか）

### リントエラーが発生する場合

1. フォーマットを実行して自動修正可能な問題を修正する: `docker-compose -f docker-compose.test.yml run --rm format`
2. 自動修正できない問題は手動で修正する
3. `.flake8` や `pyproject.toml` の設定を確認する

### Docker 関連の問題

1. Docker デーモンが実行中であることを確認する
2. Docker イメージを再ビルドする: `docker-compose -f docker-compose.test.yml build --no-cache`
3. Docker ボリュームをクリーンアップする: `docker volume prune`

### データベース関連の問題

1. テスト間でのデータベース状態の共有による問題がないか確認する
2. トランザクションが正しく開始・終了されているか確認する
3. テスト前にテーブルが正しくクリアされているか確認する