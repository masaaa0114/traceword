# TraceWords 自動化システム — セットアップガイド

## 概要

このシステムは、Claude API + Notion API + GitHub Actions を使って、
AI 組織のジョブを自動的に実行します。

## ジョブ一覧

| ID | ジョブ名 | タイミング | 処理内容 |
|----|---------|----------|---------|
| JOB-01 | 情報収集 | 毎朝 8:00 | 競合・業界ニュース収集 → Notion |
| JOB-02 | 朝会アジェンダ | 毎朝 8:30 | 未完了タスク確認 → アジェンダ生成 → Notion |
| JOB-03 | 週報生成 | 毎週金曜 17:00 | 週次サマリ → Notion |
| JOB-04 | SNS案生成 | 毎週月曜 9:00 | 今週のSNS投稿案 → Notion |
| JOB-05 | コードレビュー | 毎週日曜 22:00 | GitHub差分 → 品質チェック → Notion |
| JOB-06 | KPIアラート | 毎日 20:00 | 高優先未完了タスク監視 → アラート |
| JOB-07 | 月次レポート | 毎月最終日 21:00 | 月次サマリ → Notion |

## セットアップ手順

### Step 1: リポジトリの準備

```bash
# automation/ ディレクトリをプロジェクトに配置
# 構造:
# your-project/
# ├── automation/
# │   ├── base/
# │   ├── jobs/
# │   ├── run_job.py
# │   ├── requirements.txt
# │   └── .env.example
# └── .github/
#     └── workflows/
#         └── daily_automation.yml  ← github_actions_workflow.yml をリネーム
```

### Step 2: 依存ライブラリのインストール

```bash
cd automation
pip install -r requirements.txt
```

### Step 3: 環境変数の設定

```bash
cp .env.example .env
# .env を編集して各 API キーを入力
```

必要な API キー:
- `ANTHROPIC_API_KEY`: https://console.anthropic.com
- `NOTION_API_KEY`: https://www.notion.so/my-integrations

Notion データベース ID の取得方法:
1. 対象の Notion ページを開く
2. URL の `https://www.notion.so/xxxxxxxx` の `xxxxxxxx` 部分をコピー

### Step 4: Notion インテグレーションの権限設定

各データベースを開いて:
「・・・」→「+ Add connections」→ あなたのインテグレーションを選択

対象:
- 日次ログ DB
- 週報アーカイブ DB
- 全部署タスク管理 DB
- 意思決定ログ DB

### Step 5: 動作確認（手動実行）

```bash
cd automation

# 情報収集テスト
python run_job.py job01

# 朝会アジェンダテスト
python run_job.py job02

# 全日次ジョブ
python run_job.py all_daily
```

### Step 6: 自動実行の設定

**方法A: GitHub Actions（推奨 / PC不要）**

1. GitHub リポジトリの Settings > Secrets > Actions に全 API キーを追加
2. `github_actions_workflow.yml` を `.github/workflows/daily_automation.yml` にコピー
3. コミット・プッシュ → 自動的に毎日実行される

**方法B: cron（Mac/Linux のみ）**

```bash
# ログ保存先を作成
mkdir -p automation/logs

# crontab に設定
crontab -e
# crontab.txt の内容を貼り付け（パスを変更してから）
```

## 月額コスト試算

| サービス | 費用 | 備考 |
|---------|------|------|
| Claude API | 約500〜1,500円/月 | ジョブ実行回数による |
| GitHub Actions | 0円 | 無料枠内（月2,000分）で十分 |
| Notion | 0円 | 無料プラン |
| **合計** | **500〜1,500円/月** | |

## カスタマイズ方法

### 情報収集先を追加する（JOB-01）

`jobs/job_01_research.py` の `RSS_FEEDS` に追加:

```python
RSS_FEEDS = [
    # 既存の設定...
    {
        "name": "追加したいメディア名",
        "url": "https://example.com/feed",
        "category": "カテゴリ"
    },
]
```

### 新しいジョブを追加する

1. `jobs/job_XX_name.py` を作成
2. `run_job.py` に登録
3. `crontab.txt` または `github_actions_workflow.yml` にスケジュール追加

## トラブルシューティング

### Notion への書き込みが失敗する
- インテグレーションの接続権限を確認
- DB の ID が正しいか確認（ハイフンなしの32文字）

### Claude API でエラーになる
- API キーが有効か確認
- 残高・利用制限を確認（console.anthropic.com）

### GitHub Actions が動かない
- リポジトリの Actions が有効になっているか確認
- Secrets が正しく設定されているか確認

## 重要な注意事項

このシステムは「半自律」設計です。
- ジョブは「提案・草案・情報収集」を自動化
- 最終的な意思決定・投稿・コミットは必ず CEO が判断
- 自動で SNS 投稿・コード push などは行わない設計

これは意図的な設計です。AIが全部自動でやるより、
CEOが確認した上で実行する方が、事業の品質と安全性が保たれます。
