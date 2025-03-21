# Goosuke システムパターン

## システムアーキテクチャ

Goosuke は以下の主要コンポーネントで構成されています：

```
                      ┌────────────────────────────────────┐
                      │            コンテナ                 │
  ┌─────────┐        │  ┌────────┐      ┌──────────────┐  │       ┌─────────────┐
  │ Slack   │◄───────┼──┤ 発火    │◄────┤ 実行レイヤー  │   │      │ Notion      │
  │ Teams   │        │  │ レイヤー│      │ (Goose CLI)  │  │      │ Google Drive│
  │ Email   │────────┼─►│        │─────►│ Extensions   │──┼─────►│ JIRA        │
  └─────────┘        │  └────────┘      └──────────────┘  │      │ その他      │
                     │            ▲          ▲            │      └─────────────┘
                     └────────────┼──────────┼────────────┘
                                  │          │
                         ┌────────┘          └────────┐
                         │                            │
                 ┌───────┴────────┐         ┌─────────┴─────────┐
                 │   認証サービス  │         │ ストレージサービス  │
                 └────────────────┘         └───────────────────┘
```

### 主要コンポーネント

#### 1. 発火レイヤー

発火レイヤーは、システムへの入力点を受け取り、タスクを生成するコンポーネントです。

**主な役割**:
- 「アクション」の受け取り（APIリクエスト、Webhook、Botなど）
- コンテキストの抽出
- タスクの生成
- 認証・認可処理
- リクエスト検証とエラーハンドリング

**技術実装**:
- FastAPI（RESTful API）
- Pydantic（データ検証）
- SQLAlchemy（データベースアクセス）
- JWT（認証）

#### 2. 実行レイヤー

実行レイヤーは、発火レイヤーから受け取ったタスクを実行するコンポーネントです。

**主な役割**:
- タスクの実行
- Goose CLIの呼び出し
- 拡張機能の管理
- 実行結果の処理

**技術実装**:
- Goose CLI
- Python サブプロセス
- 拡張機能システム

#### 3. 認証サービス

認証サービスは、ユーザー認証と認可を担当するコンポーネントです。

**主な役割**:
- ユーザー認証
- トークン管理
- アクセス制御

**技術実装**:
- JWT（JSON Web Token）
- Passlib（パスワードハッシュ）
- Python-jose（JWT実装）

#### 4. ストレージサービス

ストレージサービスは、データの永続化を担当するコンポーネントです。

**主な役割**:
- データの永続化
- マイグレーション管理
- データアクセス

**技術実装**:
- SQLite（小規模用）
- SQLAlchemy（ORM）
- Alembic（マイグレーション）

## 設計パターン

### 1. アクションとタスクのパターン

Goosuke の中核となる概念は「アクション」と「タスク」です：

- **アクション**: システムへの入力点（APIリクエスト、Slack/Discord botのメッセージ、Webhookなど）
- **タスクテンプレート**: ユーザーが望む動作を記述した「プロンプト」と実行タイプを定義したもの
- **タスク実行**: タスクテンプレートと「コンテキスト」を組み合わせた実際の実行インスタンス

このパターンにより、新しいアクションとタスクテンプレートを定義するだけで、様々な作業を自動化できます。

### 2. レイヤードアーキテクチャ

Goosuke は以下のレイヤーで構成されています：

1. **プレゼンテーションレイヤー**: API、Webhook、Botなどのインターフェース
2. **アプリケーションレイヤー**: ビジネスロジック、サービス
3. **ドメインレイヤー**: モデル、エンティティ
4. **インフラストラクチャレイヤー**: データベース、外部サービス連携

### 3. サービスパターン

各機能は独立したサービスとして実装されています：

- **UserService**: ユーザー管理
- **ActionService**: アクション管理
- **ActionConfigService**: アクション設定関連管理
- **TaskService**: タスク管理
- **ExtensionService**: 拡張機能管理
- **DiscordService**: Discord連携
- **DiscordConfigService**: Discord設定管理

### 4. 依存性注入パターン

FastAPIの依存性注入システムを活用して、コンポーネント間の結合度を低減しています。

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/")
def read_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users
```

### 5. リポジトリパターン

データアクセスはリポジトリパターンを使用して抽象化されています。

```python
class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self):
        return self.db.query(User).all()
    
    def get_by_id(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()
```

### 6. 設定分離パターン

サービス固有の設定を専用のモデルで管理し、アクションと関連付けることで、柔軟な設定管理を実現しています。

```python
# Discord設定モデル
class ConfigDiscord(Base):
    __tablename__ = "config_discord"
    id = Column(Integer, primary_key=True)
    catch_type = Column(Enum("reaction", "text", "textWithMention"))
    catch_value = Column(String)
    message_type = Column(Enum("single", "thread", "range"))
    response_format = Column(Enum("reply", "dm", "channel"))
    # ...

# アクション設定関連モデル
class ActionConfig(Base):
    __tablename__ = "action_config"
    id = Column(Integer, primary_key=True)
    action_id = Column(Integer, ForeignKey("actions.id"))
    config_type = Column(Enum("discord", "slack"))
    config_id = Column(Integer)
    # ...
```

### 7. 非同期コンテキスト管理パターン

データベース接続などのリソースを非同期コンテキスト管理で効率的に扱います。

```python
@asynccontextmanager
async def _get_db_context():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### 8. 拡張機能管理パターン

拡張機能を管理するための構造化されたモデルとサービスを提供しています。

```python
# 拡張機能モデル
class Extension(Base):
    __tablename__ = "extensions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True, unique=True)
    description = Column(Text, nullable=True)
    version = Column(String, nullable=True)
    enabled = Column(Boolean, default=True)
    
    # Goose拡張機能の設定フィールド
    type = Column(String, nullable=True)  # builtin, stdio, sse
    cmd = Column(String, nullable=True)  # stdio タイプの場合のコマンド
    args = Column(JSON, nullable=True)  # stdio タイプの場合の引数
    timeout = Column(Integer, nullable=True)  # タイムアウト（秒）
    envs = Column(JSON, nullable=True)  # 環境変数
```

## コンポーネント間の関係

### 1. アクションとタスクの関係

アクションとタスクの関係は以下のようになります：

1. アクションが発生（APIリクエスト、Botメッセージなど）
2. 発火レイヤーがアクションを受け取る
3. アクション設定に基づいてコンテキストを抽出
4. 関連するタスクテンプレートを取得
5. タスクテンプレートとコンテキストからタスク実行を生成
6. タスク実行を実行レイヤーに渡す
7. 実行レイヤーがタスクを実行
8. 結果を発火レイヤーに返す
9. 発火レイヤーが結果をレスポンスとして返す

### 2. 発火レイヤーと実行レイヤーの関係

発火レイヤーと実行レイヤーは以下のように連携します：

1. 発火レイヤーがタスク実行を生成
2. タスク実行を実行レイヤーに渡す
3. 実行レイヤーがタスクを実行
4. 実行結果を発火レイヤーに返す

### 3. アクションと設定の関係

アクションと設定の関係は以下のようになります：

1. アクションが特定のサービス（Discord、Slackなど）の設定と関連付けられる
2. アクション設定関連テーブルがアクションIDと設定ID、設定タイプを関連付ける
3. アクションが発生すると、関連する設定に基づいてコンテキストを抽出
4. 抽出されたコンテキストとタスクテンプレートからタスク実行を生成

### 4. タスクテンプレートとタスク実行の関係

タスクテンプレートとタスク実行の関係は以下のようになります：

1. タスクテンプレートは再利用可能なタスクの定義（プロンプト、タイプなど）を保持
2. タスク実行はテンプレートを元に生成され、特定のコンテキストと実行結果を保持
3. 一つのテンプレートから複数の実行インスタンスが生成される
4. タスク実行はテンプレートへの参照を保持し、テンプレートは複数の実行を持つ

### 5. 拡張機能システム

拡張機能システムは以下のカテゴリに分類されます：

- **コネクタ拡張**: 外部サービスとの接続（Slack, Notion, Google Workspace など）
- **処理拡張**: データ変換、フォーマット変更
- **ユーティリティ拡張**: 日付処理、テキスト操作、データ検証など
- **カスタム拡張**: 組織固有のビジネスロジック実装

拡張機能は以下のタイプに分類されます：

- **builtin**: Gooseに組み込まれた拡張機能
- **stdio**: 標準入出力を使用する外部プロセスとして実行される拡張機能
- **sse**: Server-Sent Events（SSE）を使用するHTTPベースの拡張機能

### 6. GoosukeとGoose間の設定同期

GoosukeとGoose間の設定同期は以下のように行われます：

1. **Gooseからの同期（sync_from_goose）**: 
   - Gooseの設定ファイルから拡張機能設定を読み取る
   - 読み取った設定をGoosukeのデータベースに反映する

2. **Gooseへの同期（sync_to_goose）**:
   - Goosukeのデータベースから拡張機能設定を読み取る
   - 読み取った設定をGooseの設定ファイルに反映する

3. **起動時の自動同期**:
   - アプリケーション起動時に両方向の同期を実行
   - 同期エラーはログに記録され、アプリケーションの起動は継続

## データフロー

### 基本フロー

1. ユーザーがDiscordで鉛筆リアクションを付ける（アクション）
2. Discord Botがリアクションを検出
3. DiscordConfigServiceが設定を取得
4. ActionConfigServiceが関連するアクションを取得
5. メッセージの内容からコンテキストを抽出
6. アクションに関連するタスクテンプレートを取得
7. タスクテンプレートとコンテキストからタスク実行を生成
8. 生成されたタスク実行を実行レイヤーに渡す
9. 実行レイヤーがGoose CLIを使用してタスクを実行
10. 結果をDiscord Botを通じてチャンネルに返送

### 非同期処理フロー

長時間実行タスク用：

1. アクションを受信
2. タスク実行IDを生成して即時応答
3. タスク実行をバックグラウンドワーカーにキューイング
4. 処理完了時にコールバックURLに通知
5. ユーザーが結果を取得（プッシュまたはプル）

### Discord設定に基づく処理フロー

1. Discord Botがイベント（リアクション、メッセージなど）を受信
2. イベントタイプと値に基づいてDiscord設定を検索
3. 設定が見つかった場合、関連するアクションを検索
4. 設定のメッセージ収集戦略に基づいてメッセージを収集
5. 収集したメッセージからコンテキストを生成
6. アクションに関連するタスクテンプレートを使用してタスクを実行
7. 設定のレスポンス形式に基づいて結果を返送（返信、DM、チャンネル）

### 拡張機能設定同期フロー

1. アプリケーション起動時に`ExtensionService`のインスタンスを作成
2. `sync_from_goose`メソッドを呼び出し、Gooseの設定ファイルから拡張機能設定を読み取る
3. 読み取った設定をGoosukeのデータベースに反映する
4. `sync_to_goose`メソッドを呼び出し、Goosukeのデータベースから拡張機能設定を読み取る
5. 読み取った設定をGooseの設定ファイルに反映する
6. 同期結果をログに記録する