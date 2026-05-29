"""
jobs/job_03_weekly.py

JOB-03: 週報の自動生成
実行タイミング: 毎週金曜 17:00
"""
import os
from base.claude_client import ask_claude_structured
from base.notion_client import create_page
from base.utils import (setup_logger, log_job_start, log_job_end,
                        log_job_error, today_str, week_label)

logger = setup_logger("JOB-03 Weekly")

def generate_weekly_report() -> str:
    prompt = f"""
{week_label()}の週次レポートを作成してください。

# 出力形式

## 📊 今週の総評
3行以内で今週全体の評価。

## ✅ 今週の主要成果
箇条書き5件以内。

## ⚠️ 今週の課題・遅延
遅れているものと理由。

## 🎯 来週の優先タスク（部署別）
- T00 CoS:
- T01 Strategy:
- T06 Product:
- T04 Marketing:

## ⚡ Devil's Advocate の一言
今週の決定で最も後悔するリスクがある判断を1つ。

## 📈 KPI 進捗（自己評価）
| KPI | 目標 | 評価 |
|-----|------|------|
| 朝会実施率 | 95% | -- |
| 開発進捗 | +10% | -- |
| SNS投稿 | 3本 | -- |

## 💡 CEO の振り返り欄（記入してください）
- 今週の気づき：
- 来週の自分の集中領域：
"""
    return ask_claude_structured(prompt)

def run():
    log_job_start(logger, "JOB-03 週報生成")
    try:
        report = generate_weekly_report()
        create_page(
            database_id=os.getenv("NOTION_WEEKLY_REPORT_DB_ID"),
            title=week_label(),
            content=report,
            properties={
                "開始日": {"date": {"start": today_str()}},
                "全体評価": {"select": {"name": "🟢 良好"}},
            }
        )
        logger.info(f"週報を Notion に保存しました: {week_label()}")
        log_job_end(logger, "JOB-03 週報生成")
    except Exception as e:
        log_job_error(logger, "JOB-03", e)
        raise

if __name__ == "__main__":
    run()


# ============================================================

"""
jobs/job_06_kpi.py

JOB-06: KPIアラート監視
実行タイミング: 毎日 20:00
"""

def run_kpi_alert():
    _logger = setup_logger("JOB-06 KPI")
    log_job_start(_logger, "JOB-06 KPIアラート")
    try:
        from notion_client import Client
        notion_c = Client(auth=os.getenv("NOTION_API_KEY"))

        # タスクの未完了件数を確認（新API: data_sources.query）
        results = notion_c.data_sources.query(
            data_source_id=os.getenv("NOTION_TASK_DS_ID") or os.getenv("NOTION_TASK_DB_ID"),
            filter={
                "and": [
                    {"property": "ステータス",
                     "status": {"does_not_equal": "Done"}},
                    {"property": "優先度",
                     "select": {"equals": "🔴 高"}}
                ]
            }
        )
        high_priority_count = len(results.get("results", []))

        alerts = []
        if high_priority_count >= 5:
            alerts.append(f"🚨 高優先度の未完了タスクが {high_priority_count} 件あります")

        if alerts:
            from base.claude_client import ask_claude_structured
            alert_text = "\n".join(alerts)
            suggestion = ask_claude_structured(f"""
以下のアラートが検知されました：
{alert_text}

CEO へのアドバイスを2〜3行で。
何を優先して、何を後回しにすべきか。
""")
            section = f"## 🚨 KPI アラート — 本日検知\n\n{alert_text}\n\n{suggestion}"
            from base.notion_client import find_today_page, append_to_page
            page_id = find_today_page(os.getenv("NOTION_DAILY_LOG_DB_ID"))
            if page_id:
                append_to_page(page_id, section)
            _logger.info(f"アラート {len(alerts)} 件を Notion に記録")
        else:
            _logger.info("本日のアラートはありません")

        log_job_end(_logger, "JOB-06 KPIアラート")
    except Exception as e:
        log_job_error(_logger, "JOB-06", e)
        raise


# ============================================================

"""
jobs/job_07_monthly.py

JOB-07: 月次レポート自動生成
実行タイミング: 毎月最終日 21:00
"""

def run_monthly_report():
    from datetime import datetime
    _logger = setup_logger("JOB-07 Monthly")
    log_job_start(_logger, "JOB-07 月次レポート")
    try:
        now = __import__("base.utils", fromlist=["now_jst"]).now_jst()
        month_label = f"{now.year}年{now.month}月"
        prompt = f"""
{month_label} の月次レポートを作成してください。

## 月次レポート — {month_label}

### 1. 今月の総評
今月のテーマと達成度を3行で。

### 2. 事業KPI達成状況
| KPI | 月初目標 | 実績 | 達成率 |
|-----|---------|------|--------|
| 開発進捗率 | -- | -- | -- |
| ヒアリング件数 | -- | -- | -- |
| SNSフォロワー | -- | -- | -- |

### 3. 今月の主要意思決定
今月行った重要な決定のサマリ。

### 4. 来月のテーマと目標
来月（{now.year}年{now.month + 1 if now.month < 12 else 1}月）の重点課題3つ。

### 5. Devil's Advocate の月次反論
今月の経営判断で最もリスクが高かったものを指摘。

### 6. CEO の振り返り欄
（記入してください）
- 今月最も成長した点：
- 来月改善したいこと：
- 独立計画の進捗：
"""
        report = ask_claude_structured(prompt)
        create_page(
            database_id=os.getenv("NOTION_DAILY_LOG_DB_ID"),
            title=f"{month_label} 月次レポート",
            content=report,
            properties={"実施日": {"date": {"start": today_str()}}}
        )
        _logger.info(f"月次レポートを保存しました: {month_label}")
        log_job_end(_logger, "JOB-07 月次レポート")
    except Exception as e:
        log_job_error(_logger, "JOB-07", e)
        raise
