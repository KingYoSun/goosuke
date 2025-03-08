# Goosuke デザインドキュメント - 小～中規模組織向け

## 1. 概要

Goosuke は、オープンソースの AI エージェント Goose と FastAPI を組み合わせた、小～中規模組織向けの業務効率化プラットフォームです。コンテナ環境で動作し、Slack などのコラボレーションツールと連携して、会議の要約作成、ナレッジベースの検索・更新、マルチモーダルコンテンツの処理などを手軽に自動化します。

### 1.1 目的

- チームメンバーの反復的な業務を自動化し、限られたリソースを効率的に活用する
- 小～中規模組織が日常的に使用するサービスと簡単に連携して情報活用を促進する
- 手軽にセットアップできるセルフホスト型ソリューションを提供し、データのプライバシーを確保する
- 軽量かつ拡張可能なアーキテクチャにより、組織固有のニーズに低コストで対応する

### 1.2 ターゲットユーザー

- 小～中規模組織のメンバー（技術的専門知識を問わない）
- スタートアップや中小企業のナレッジワーカー
- 限られたIT人材で運用する必要がある組織
- 非営利団体、教育機関、小規模チームなど

## 2. システムアーキテクチャ

Goosuke は以下の主要コンポーネントで構成されます：

```
                   ┌────────────────────────────────────┐
                   │            コンテナ                │
┌─────────┐        │  ┌────────┐      ┌──────────────┐  │      ┌─────────────┐
│ Slack   │◄───────┼──┤ FastAPI │◄────┤ Goose CLI    │  │      │ Notion      │
│ Teams   │        │  │ 層      │      │              │  │      │ Google Drive│
│ Email   │────────┼─►│        │─────►│ Extensions   │──┼─────►│ JIRA        │
└─────────┘        │  └────────┘      └──────────────┘  │      │ その他      │
                   │            ▲          ▲            │      └─────────────┘
                   └────────────┼──────────┼────────────┘
                                │          │
                       ┌────────┘          └────────┐
                       │                             │
               ┌───────┴────────┐         ┌─────────┴─────────┐
               │   認証サービス  │         │ ストレージサービス  │
               └────────────────┘         └───────────────────┘
```

### 2.1 コア技術スタック

- **AI エージェント**: Goose（オープンソース AI エージェント）
- **API 層**: FastAPI（Python ベースの高性能 Web フレームワーク）
- **コンテナ化**: Docker および Docker Compose（シンプルな環境用）
- **データベース**: SQLite（小規模用）/ PostgreSQL（中規模用、オプション）
- **キャッシュ**: Redis（オプション、規模に応じて）
- **認証**: JWT ベースの軽量認証
- **ストレージ**: ローカルファイルシステムまたは S3 互換ストレージ（オプション）

## 3. コンポーネント設計

### 3.1 FastAPI レイヤー

FastAPI は以下の機能を提供します：

- RESTful API エンドポイント
- WebSocket サポート（リアルタイム通信用）
- 自動ドキュメント生成（OpenAPI）
- 認証・認可処理
- リクエスト検証とエラーハンドリング
- 非同期処理サポート
- サービス統合のためのルーター

**主要エンドポイント**:

```
/api/v1/tasks - タスク管理 (POST, GET, DELETE)
/api/v1/agents - エージェント設定 (GET, PUT)
/api/v1/connections - サービス接続管理
/api/v1/auth - 認証関連
/api/v1/webhooks - 外部サービスからのイベント受信
```

### 3.2 Goose 統合

Goose CLI を内部的に活用し、以下の機能を提供：

- エージェントの設定と管理
- プロンプトのカスタマイズとテンプレート
- エクステンション管理
- 実行ロギングとモニタリング

### 3.3 拡張システム

Goose エクステンションを管理し、以下のカテゴリに分類：

- **コネクタ拡張**: 外部サービスとの接続（Slack, Notion, Google Workspace など）
- **処理拡張**: データ変換、フォーマット変更
- **ユーティリティ拡張**: 日付処理、テキスト操作、データ検証など
- **カスタム拡張**: 組織固有のビジネスロジック実装（シンプルなスクリプトで拡張可能）

## 4. データフロー

### 4.1 基本フロー

1. ユーザーがSlackでGoosuke宛にメッセージを送信
2. Slackからのwebhookがコンテナのエンドポイントを呼び出し
3. FastAPIレイヤーがリクエストを処理し、認証を行う
4. リクエストをGooseに適したフォーマットに変換
5. Goose CLIがタスクを実行し、必要に応じて拡張機能を使用
6. 結果をFastAPIを通じてSlackに返送

### 4.2 非同期処理フロー

長時間実行タスク用：

1. リクエストを受信
2. タスクIDを生成して即時応答
3. タスクをバックグラウンドワーカーにキューイング
4. 処理完了時にコールバックURLに通知
5. ユーザーが結果を取得（プッシュまたはプル）

## 5. セキュリティ設計

### 5.1 認証・認可

- シンプルなJWT ベースの認証
- 基本的なロールベースのアクセス制御
- 環境変数によるAPI認証情報の管理
- 簡易セッション管理

### 5.2 データセキュリティ

- 設定ファイルでの機密情報管理
- 転送中の暗号化（TLS/SSL）
- シンプルなアクセス制御
- 基本的なログ記録

### 5.3 サービス統合のセキュリティ

- API キーの安全な管理（環境変数または設定ファイル）
- 必要最小限の権限設定ガイド
- 定期的な認証情報の確認推奨

## 6. スケーラビリティとリソース設計

### 6.1 リソース効率

- 軽量なコンテナ設計（最小リソース要件）
- シングルホストでの動作に最適化
- 必要に応じた段階的なスケールアップ対応
- 低コストでの運用を優先

### 6.2 パフォーマンス最適化

- タスクのキュー処理による負荷分散
- アイドル時のリソース解放
- バッチ処理によるリソース効率化
- 同時実行数の設定によるリソース調整

## 7. 外部サービス統合

Goosuke は小～中規模組織が頻繁に利用する以下の外部サービスとの統合を優先的にサポートします：

### 7.1 コミュニケーションプラットフォーム
- Slack
- Discord
- Mattermost（オープンソース選択肢）

### 7.2 ドキュメント管理
- Notion
- Google Workspace
- Microsoft Office 365（基本機能）
- Markdown ファイル（ローカル/Git）

### 7.3 プロジェクト管理
- Trello
- Asana
- GitHub Projects
- ClickUp

### 7.4 その他の一般的なツール
- Airtable
- Google Forms/Sheets
- Calendly
- Zoom

### 7.5 簡易カスタム統合
- シンプルな REST API 連携
- Webhook イベント処理
- CSV/JSON データ処理

## 8. デプロイメント

### 8.1 コンテナ構成

```
goosuke/
├── api/                # FastAPI アプリケーション
├── goose/              # Goose CLI とカスタマイズ
├── extensions/         # 拡張機能
├── config/             # 設定ファイル
├── scripts/            # デプロイ・管理スクリプト
├── docs/               # ドキュメント
└── docker-compose.yml  # ローカル環境用
```

### 8.2 デプロイメントオプション

- Docker Compose（主要デプロイメント方法）
- シングルコンテナ軽量版（最小構成）
- クラウドプロバイダー向け簡易セットアップスクリプト
- ワンクリックデプロイメントオプション（Digital Ocean, Heroku等）

## 9. モニタリングと運用

### 9.1 シンプルなロギング

- 基本的なログ記録
- 簡易ログローテーション
- 重要イベントの記録
- エラーログの保存

### 9.2 基本メトリクス

- 利用統計（日次/週次）
- タスク成功率のシンプルな集計
- メモリ/CPU使用量の基本モニタリング
- ストレージ使用量の追跡

### 9.3 管理者通知

- 重大エラーの基本的な通知機能
- 定期的な利用状況レポート（オプション）
- メンテナンス通知

## 10. 開発ロードマップ

### フェーズ 1（MVP）
- シンプルな Docker Compose 設定
- FastAPI と Goose の基本統合
- Slack/Discord 連携による会議要約機能
- 簡易認証

### フェーズ 2
- 主要サービス統合（Notion, Google Workspace）
- 基本的な拡張機能システム
- シンプル管理ページ
- インストール・設定ウィザード

### フェーズ 3
- コミュニティ向け拡張機能の充実
- 追加ツール連携（Trello, Airtable等）
- リソース使用量の最適化
- テンプレート機能

## 11. 技術的課題と対策

### 11.1 小～中規模組織向け課題

- 技術リソースが限られた組織での簡単な導入・運用
- 低コストでの運用維持
- Goose のバージョン更新に伴う互換性問題
- 限られたリソース内での効率的な実行

### 11.2 対策

- ワンクリック導入とセットアップウィザード
- 最小限のメンテナンス要件設計
- バージョン互換性の明確な文書化
- リソース使用の自動調整機能

## 12. レファレンス実装

### 12.1 基本的なFastAPIルーターの例

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from .models import TaskRequest, TaskResponse
from .auth import get_current_user
from .goose_service import GooseExecutor

router = APIRouter(prefix="/api/v1/tasks")

@router.post("/", response_model=TaskResponse)
async def create_task(
    task: TaskRequest, 
    current_user = Depends(get_current_user)
):
    """タスクを作成して実行"""
    executor = GooseExecutor()
    result = await executor.execute(
        task.prompt,
        extensions=task.extensions,
        context=task.context
    )
    
    return TaskResponse(
        id=result.id,
        status="completed" if result.success else "failed",
        result=result.output,
        created_at=result.timestamp
    )

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, current_user = Depends(get_current_user)):
    """タスクの情報を取得"""
    # 実装内容
```

### 12.2 Goose実行サービスの例

```python
import subprocess
import json
import asyncio
from uuid import uuid4
from datetime import datetime

class GooseExecutor:
    def __init__(self, goose_path="/app/goose/bin/goose"):
        self.goose_path = goose_path
        
    async def execute(self, prompt, extensions=None, context=None):
        """Goose CLIを実行して結果を返す"""
        task_id = str(uuid4())
        
        cmd = [self.goose_path, "execute", "--prompt", prompt]
        
        if extensions:
            for ext in extensions:
                cmd.extend(["--extension", ext])
                
        if context:
            context_file = f"/tmp/context_{task_id}.json"
            with open(context_file, "w") as f:
                json.dump(context, f)
            cmd.extend(["--context-file", context_file])
            
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return {
                    "id": task_id,
                    "success": False,
                    "output": stderr.decode(),
                    "timestamp": datetime.now()
                }
                
            return {
                "id": task_id,
                "success": True,
                "output": stdout.decode(),
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            return {
                "id": task_id,
                "success": False,
                "output": str(e),
                "timestamp": datetime.now()
            }
```

## 13. リスクと対策

### 13.1 小～中規模組織向けリスク

- APIコスト管理（予算を超えるリスク）
- シンプルな運用管理の実現
- 技術的理解が限られたユーザーへのサポート
- データ保護とプライバシー管理の簡易化

### 13.2 対策

- 使用量の可視化と予算管理ツール
- 運用自動化とシンプルな管理インターフェース
- コミュニティサポートとドキュメント充実
- プライバシー設定テンプレートの提供

### 13.3 コミュニティ活用

- オープンソースコミュニティでの拡張機能共有
- ユースケーステンプレートのコミュニティライブラリ
- 小規模組織間でのベストプラクティス共有
- プラグイン開発のコミュニティコントリビューション

---

© 2025 Goosuke Project