# Goosuke

小～中規模組織向けGoose AIエージェント連携プラットフォーム

## プロジェクト概要

Goosuke は小～中規模組織向けの業務効率化ツールで、オープンソースのAIエージェント「Goose」とFastAPIを組み合わせたプラットフォームです。Dockerコンテナ環境で動作し、Discordと連携して、会議の要約作成などを自動化します。

## 機能

- **Discord連携**: Discordチャンネルでの会話を要約
- **拡張機能管理**: Goose拡張機能のインストールと管理
- **API**: RESTful APIによる柔軟な連携
- **認証**: JWTベースの認証システム

## 技術スタック

- **AI エージェント**: Goose（オープンソース）
- **発火レイヤー**: FastAPI（APIリクエスト、Webhook、Botなどのアクションを処理）
- **実行レイヤー**: Goose CLI（タスクの実行を担当）
- **コンテナ化**: Docker & Docker Compose
- **データベース**: SQLite（最小構成）
- **認証**: JWTベースの簡易認証
- **クライアント連携**: Discord Bot API

## 必要条件

- Docker と Docker Compose
- Discord Bot トークン（Discord連携機能を使用する場合）

## インストール方法

1. リポジトリをクローン

```bash
git clone https://github.com/yourusername/goosuke.git
cd goosuke
```

2. 環境変数の設定

```bash
cp .env.example .env
```

`.env`ファイルを編集して、必要な環境変数を設定します。

3. Dockerコンテナのビルドと起動

```bash
docker-compose up -d
```

## 使い方

### アクションとタスクの定義

Goosuke は「アクション」と「タスク」の2つの概念を中心に設計されています：

1. **アクション**: APIリクエスト、Slack/Discord botのメッセージ、Webhookなど、システムへの入力点
2. **タスク**: アクションから得られた「コンテキスト」と、ユーザーが望む動作を記述した「プロンプト」のセット

この設計により、新しいアクションとタスクを定義するだけで、様々な作業を自動化できます。

### APIの利用

APIドキュメントは以下のURLで確認できます：

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### Discord Botの設定

1. [Discord Developer Portal](https://discord.com/developers/applications)でBotを作成
2. Botトークンを取得し、`.env`ファイルの`DISCORD_BOT_TOKEN`に設定
3. 必要な権限（メッセージの読み取り、送信、リアクションの追加など）を付与
4. Botを目的のサーバーに招待

### 会議要約機能の使用方法

1. Discordチャンネルで会話を行う
2. 要約したい会話の範囲のメッセージに ✏️（鉛筆）リアクションを付ける
3. Botが自動的に関連メッセージを収集し、要約を生成
4. 要約結果がチャンネルに投稿される

### Goose CLIの設定

**注意**: Goose CLIの`configure`コマンドは対話的に実行する必要があるため、APIからは実行できません。以下の設定は、ターミナルで直接実行してください。

#### LLM Providerの設定

Gooseを使用するには、LLM（大規模言語モデル）プロバイダーの設定が必要です。以下のコマンドをターミナルで実行してください：

```bash
goose configure
```

対話的なプロンプトに従って、使用するLLMプロバイダー（OpenAI、Anthropic、Mistral AIなど）とAPIキーを設定します。

詳細は[Goose公式ドキュメント - LLM Providers](https://block.github.io/goose/docs/getting-started/providers)を参照してください。

#### MCPベースのExtensionの追加

Gooseの機能を拡張するために、MCPベースの拡張機能を追加できます：

```bash
# 拡張機能の追加
goose configure

# プロンプトでExtensionsを選択し、拡張機能の追加・管理を行います
```

拡張機能の詳細については、[Goose公式ドキュメント - Using Extensions](https://block.github.io/goose/docs/getting-started/using-extensions)を参照してください。

## 開発

### ローカル開発環境のセットアップ

```bash
# 依存関係のインストール
pip install -r requirements.txt

# 開発サーバーの起動
uvicorn api.main:app --reload
```

### テストの実行

```bash
pytest
```

## ライセンス

[MITライセンス](LICENSE)

## 貢献

プロジェクトへの貢献は大歓迎です。Issue報告や機能提案、プルリクエストなどお気軽にどうぞ。