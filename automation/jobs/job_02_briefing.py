"""
jobs/job_02_briefing.py

JOB-02: 朝会アジェンダ自動生成
実行タイミング: 毎朝 8:30（JOB-01の30分後）
処理内容:
  1. Notion から直近の日次ログ・未完了タスクを取得
  2. Claude で朝会アジェンダを生成
  3. Notion の今日のページに追記
"""
import os
from notion_client import Client
from base.claude_client import ask_claude_structured
from base.notion_client import create_page, find_today_page, append_to_page
from base.utils import (setup_logger, log_job_start, log_job_end,
                        log_job_error, today_str, today_label)

logger = setup_logger("JOB-02 Briefing")
notion = Client(auth=os.getenv("NOTION_API_KEY"))

def get_pending_tasks() -> str:
    """未完了タスクを Notion から取得（新API: data_sources.query 使用）"""
    try:
        # data_source_id を優先、なければ db_id をフォールバックで使う
        ds_id = os.getenv("NOTION_TASK_DS_ID") or os.getenv("NOTION_TASK_DB_ID")
        results = notion.data_sources.query(
            data_source_id=ds_id,
            filter={
                "and": [
                    {"property": "ステータス",
                     "status": {"does_not_equal": "Done"}},
                    {"property": "CEO判断必要",
                     "checkbox": {"equals": True}}
                ]
            },
            sorts=[{"property": "優先度", "direction": "descending"}],
            page_size=10
        )
        tasks = []
        for page in results.get("results", []):
            props = page.get("properties", {})
            title_prop = props.get("タスク名", {}).get("title", [])
            title = title_prop[0]["text"]["content"] if title_prop else "（無題）"
            dept_prop = props.get("担当部署", {}).get("select", {})
            dept = dept_prop.get("name", "") if dept_prop else ""
            priority_prop = props.get("優先度", {}).get("select", {})
            priority = priority_prop.get("name", "") if priority_prop else ""
            tasks.append(f"- [{priority}] {title}（{dept}）")
        return "\n".join(tasks) if tasks else "CEO判断が必要な未完了タスクはありません。"
    except Exception as e:
        logger.warning(f"タスク取得失敗: {e}")
        return "タスク取得に失敗しました。"

def get_recent_decisions() -> str:
    """直近3件の意思決定ログを取得（新API: data_sources.query 使用）"""
    try:
        ds_id = os.getenv("NOTION_DECISION_LOG_DS_ID") or os.getenv("NOTION_DECISION_LOG_DB_ID")
        results = notion.data_sources.query(
            data_source_id=ds_id,
            sorts=[{"property": "決定日", "direction": "descending"}],
            page_size=3
        )
        decisions = []
        for page in results.get("results", []):
            props = page.get("properties", {})
            title_prop = props.get("決定事項", {}).get("title", [])
            title = title_prop[0]["text"]["content"] if title_prop else "（無題）"
            date_prop = props.get("決定日", {}).get("date", {})
            date = date_prop.get("start", "") if date_prop else ""
            decisions.append(f"- {date}: {title}")
        return "\n".join(decisions) if decisions else "直近の意思決定ログはありません。"
    except Exception as e:
        logger.warning(f"意思決定ログ取得失敗: {e}")
        return "取得に失敗しました。"

def generate_agenda(pending_tasks: str, recent_decisions: str) -> str:
    """Claude で朝会アジェンダを生成"""
    prompt = f"""
今日（{today_label()}）の朝会アジェンダを作成してください。

# CEO 判断が必要な未完了タスク
{pending_tasks}

# 直近の意思決定ログ（参考）
{recent_decisions}

# 出力形式

## 🌅 朝会アジェンダ — {today_label()}

### 今日の CEO 判断論点（優先度順）

**論点1: [タイトル]**
- 背景：
- 選択肢：A) ... / B) ...
- 推奨：
- Devil's 反論：

**論点2: [タイトル]**
（以下同様、最大5件まで）

---

### 📋 各部署への今日の指示

| 部署 | 今日のタスク | 期限 |
|------|------------|------|
| T00 CoS | ... | 本日中 |
| T01 Strategy | ... | 本日中 |
| T06 Product | ... | 本日中 |
（重要な部署のみ記載）

---

### ⚡ Devil's Advocate（T10）からの一言
今日の最も見落としやすいリスクを1つ指摘する。

---

### 📊 今週の進捗ステータス
事業計画との比較（3行以内）

論点は「今日本当に決める必要があるもの」に絞ること。
不要な情報で CEO の時間を奪わないこと。
"""
    return ask_claude_structured(prompt)

def run():
    """JOB-02 メイン実行"""
    log_job_start(logger, "JOB-02 朝会アジェンダ生成")
    try:
        logger.info("未完了タスクを取得中...")
        tasks = get_pending_tasks()

        logger.info("意思決定ログを取得中...")
        decisions = get_recent_decisions()

        logger.info("アジェンダを生成中...")
        agenda = generate_agenda(tasks, decisions)

        section = f"\n---\n## 🌅 T00 Chief of Staff — 朝会アジェンダ\n\n{agenda}"

        daily_log_db = os.getenv("NOTION_DAILY_LOG_DB_ID")
        page_id = find_today_page(daily_log_db)

        if page_id:
            append_to_page(page_id, section)
            logger.info("日次ログに朝会アジェンダを追記しました")
        else:
            create_page(
                database_id=daily_log_db,
                title=f"{today_str()} 朝会アジェンダ",
                content=section,
                properties={"実施日": {"date": {"start": today_str()}}}
            )
            logger.info("新規ページを作成しました")

        log_job_end(logger, "JOB-02 朝会アジェンダ生成")

    except Exception as e:
        log_job_error(logger, "JOB-02", e)
        raise

if __name__ == "__main__":
    run()
