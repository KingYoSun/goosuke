# Goosuke API リファレンス

このドキュメントは、Goosuke APIの詳細な仕様を提供します。

## 基本情報

- ベースURL: `http://localhost:8000`
- 認証: JWTベース（`Authorization: Bearer {token}`ヘッダーを使用）
- レスポンス形式: JSON

## 発火レイヤーと実行レイヤー

Goosuke は「発火レイヤー」と「実行レイヤー」の2つの主要コンポーネントで構成されています：

1. **発火レイヤー**: APIリクエスト、Webhook、Botなどの「アクション」を受け取り、コンテキストとプロンプトをセットにしたタスクを生成します。
2. **実行レイヤー**: 発火レイヤーから受け取ったタスクを実行し、結果を返します。

## アクションとタスク

Goosuke の中核となる概念は「アクション」と「タスク」です：

- **アクション**: システムへの入力点（APIリクエスト、Slack/Discord botのメッセージ、Webhookなど）
- **タスク**: アクションから得られた「コンテキスト」と、ユーザーが望む動作を記述した「プロンプト」のセット

この設計により、新しいアクションとタスクを定義するだけで、様々な作業を自動化できます。

## エンドポイント一覧

### 認証

#### ログイン

```
POST /api/v1/auth/login
```

リクエスト:
```json
{
  "username": "user",
  "password": "password"
}
```

レスポンス:
```json
{
  "access_token": "eyJ0eXAi...",
  "token_type": "bearer"
}
```

### タスク管理

#### タスク作成

```
POST /api/v1/tasks/
```

リクエスト:
```json
{
  "task_type": "general",
  "prompt": "ユーザーが望む動作を記述したプロンプト",
  "context": {
    "key": "value"
  },
  "name": "タスク名",
  "is_template": false,
  "parent_id": null,
  "extension_ids": [1, 2]
}
```

レスポンス:
```json
{
  "task_id": 1,
  "success": true,
  "output": "タスク実行結果",
  "extensions_output": {}
}
```

#### タスク詳細取得

```
GET /api/v1/tasks/{task_id}
```

レスポンス:
```json
{
  "id": 1,
  "user_id": 1,
  "name": "タスク名",
  "task_type": "general",
  "prompt": "プロンプト",
  "context": {
    "key": "value"
  },
  "result": "実行結果",
  "extensions_output": {},
  "status": "completed",
  "error": null,
  "is_template": false,
  "parent_id": null,
  "created_at": "2025-03-09T12:00:00+09:00",
  "completed_at": "2025-03-09T12:01:00+09:00"
}
```

#### タスク一覧取得

```
GET /api/v1/tasks/
```

クエリパラメータ:
- `user_id`: ユーザーID（オプション）
- `task_type`: タスクタイプ（オプション）
- `limit`: 取得件数（デフォルト: 10）
- `offset`: オフセット（デフォルト: 0）

レスポンス:
```json
[
  {
    "id": 1,
    "user_id": 1,
    "name": "タスク名",
    "task_type": "general",
    "status": "completed",
    "is_template": false,
    "parent_id": null,
    "created_at": "2025-03-09T12:00:00+09:00",
    "completed_at": "2025-03-09T12:01:00+09:00"
  },
  ...
]
```

### アクション管理

#### アクション作成

```
POST /api/v1/actions/
```

リクエスト:
```json
{
  "name": "アクション名",
  "action_type": "api",
  "config": {
    "endpoint": "/webhook"
  },
  "context_rules": {
    "key": {
      "source": "data",
      "transform": "string"
    }
  },
  "task_id": 1
}
```

レスポンス:
```json
{
  "id": 1,
  "name": "アクション名",
  "action_type": "api",
  "config": {
    "endpoint": "/webhook"
  },
  "context_rules": {
    "key": {
      "source": "data",
      "transform": "string"
    }
  },
  "task_id": 1,
  "is_enabled": true,
  "created_at": "2025-03-09T12:00:00+09:00"
}
```

#### アクション詳細取得

```
GET /api/v1/actions/{action_id}
```

レスポンス:
```json
{
  "id": 1,
  "name": "アクション名",
  "action_type": "api",
  "config": {
    "endpoint": "/webhook"
  },
  "context_rules": {
    "key": {
      "source": "data",
      "transform": "string"
    }
  },
  "task_id": 1,
  "is_enabled": true,
  "created_at": "2025-03-09T12:00:00+09:00",
  "updated_at": "2025-03-09T12:01:00+09:00",
  "last_triggered_at": "2025-03-09T12:02:00+09:00"
}
```

#### アクション一覧取得

```
GET /api/v1/actions/
```

クエリパラメータ:
- `action_type`: アクションタイプ（オプション）
- `is_enabled`: 有効かどうか（オプション）
- `limit`: 取得件数（デフォルト: 10）
- `offset`: オフセット（デフォルト: 0）

レスポンス:
```json
[
  {
    "id": 1,
    "name": "アクション名",
    "action_type": "api",
    "task_id": 1,
    "is_enabled": true,
    "created_at": "2025-03-09T12:00:00+09:00",
    "last_triggered_at": "2025-03-09T12:02:00+09:00"
  },
  ...
]
```

#### アクショントリガー

```
POST /api/v1/actions/{action_id}/trigger
```

リクエスト:
```json
{
  "data": "入力データ",
  "metadata": {
    "source": "api"
  }
}
```

レスポンス:
```json
{
  "task_id": 2,
  "success": true,
  "output": "タスク実行結果",
  "extensions_output": {}
}
```

#### アクション有効化

```
PUT /api/v1/actions/{action_id}/enable
```

レスポンス:
```json
{
  "message": "アクションを有効化しました"
}
```

#### アクション無効化

```
PUT /api/v1/actions/{action_id}/disable
```

レスポンス:
```json
{
  "message": "アクションを無効化しました"
}
```

### 拡張機能管理

#### 拡張機能一覧取得

```
GET /api/v1/extensions/
```

レスポンス:
```json
[
  {
    "id": 1,
    "name": "拡張機能名",
    "description": "拡張機能の説明",
    "version": "1.0.0",
    "enabled": true
  },
  ...
]
```

### Discord連携

#### Discordメッセージ要約

```
POST /api/v1/discord/summarize
```

リクエスト:
```json
{
  "channel_id": "123456789",
  "message_ids": ["111", "222", "333"]
}
```

レスポンス:
```json
{
  "task_id": 3,
  "success": true,
  "summary": "メッセージの要約結果"
}
```

### ヘルスチェック

```
GET /api/v1/health
```

レスポンス:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2025-03-09T12:00:00+09:00"
}
```

## エラーレスポンス

エラーが発生した場合、以下の形式でレスポンスが返されます：

```json
{
  "detail": "エラーメッセージ"
}
```

HTTPステータスコード：
- 400: Bad Request - リクエストが不正
- 401: Unauthorized - 認証が必要
- 403: Forbidden - 権限がない
- 404: Not Found - リソースが見つからない
- 500: Internal Server Error - サーバー内部エラー

## 認証と認可

APIの多くのエンドポイントは認証が必要です。認証には、JWTトークンを使用します。

1. `/api/v1/auth/login`エンドポイントでログインし、アクセストークンを取得
2. リクエストヘッダーに`Authorization: Bearer {token}`を設定

一部のエンドポイントは管理者権限が必要です：
- アクションの作成、一覧取得、詳細取得
- 拡張機能の管理

## 使用例

### アクションとタスクの連携

1. タスクテンプレートを作成：
```
POST /api/v1/tasks/
{
  "task_type": "template",
  "prompt": "以下の内容を要約してください: {content}",
  "name": "要約テンプレート",
  "is_template": true
}
```

2. アクションを作成（タスクテンプレートと連携）：
```
POST /api/v1/actions/
{
  "name": "Webhook要約",
  "action_type": "webhook",
  "context_rules": {
    "content": {
      "source": "text"
    }
  },
  "task_id": 1
}
```

3. アクションをトリガー：
```
POST /api/v1/actions/1/trigger
{
  "text": "要約したいテキスト..."
}
```

これにより、Webhookから受け取ったテキストが要約され、結果が返されます。