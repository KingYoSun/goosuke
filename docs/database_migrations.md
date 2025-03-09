# データベースマイグレーション

このプロジェクトでは、SQLAlchemyとAlembicを使用してデータベースマイグレーションを管理しています。

## 設定ファイル

- `alembic.ini`: Alembicの設定ファイル
- `db/migrations/env.py`: マイグレーション環境の設定ファイル
- `db/migrations/script.py.mako`: マイグレーションスクリプトのテンプレート

## マイグレーションの実行方法

マイグレーションは `db/migrations/run_migrations.py` スクリプトを使用して実行します。

### 新しいマイグレーションの作成

モデルを変更した後、以下のコマンドを実行して新しいマイグレーションスクリプトを作成します：

```bash
python db/migrations/run_migrations.py --create --message "マイグレーションの説明"
```

このコマンドは、現在のモデル定義と既存のデータベーススキーマを比較し、必要な変更を含むマイグレーションスクリプトを自動生成します。

### マイグレーションの適用

データベースを最新のスキーマに更新するには、以下のコマンドを実行します：

```bash
python db/migrations/run_migrations.py
```

または、特定のリビジョンまでアップグレードする場合：

```bash
python db/migrations/run_migrations.py --revision リビジョンID
```

### マイグレーションのロールバック

以前のバージョンにロールバックするには、以下のコマンドを実行します：

```bash
python db/migrations/run_migrations.py --downgrade --revision リビジョンID
```

## マイグレーションの仕組み

1. `api/models/` ディレクトリ内のモデルクラスが `Base` クラスを継承し、テーブル定義を提供します。
2. Alembicは現在のモデル定義と既存のデータベーススキーマを比較し、差分を検出します。
3. 差分に基づいて、マイグレーションスクリプトが生成されます。
4. マイグレーションスクリプトは、`upgrade()` と `downgrade()` 関数を含み、スキーマの変更方法を定義します。

## 注意事項

- マイグレーションスクリプトは、`db/migrations/versions/` ディレクトリに保存されます。
- マイグレーションスクリプトは、タイムスタンプとメッセージに基づいて命名されます。
- データベースURLは環境変数 `DATABASE_URL` から取得されます。デフォルトは `sqlite:///db/sqlite.db` です。
- 非同期SQLite接続（`aiosqlite`）を使用しているため、マイグレーションも非同期モードで実行されます。