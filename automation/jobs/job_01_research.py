"""
jobs/job_01_research.py

JOB-01: 競合・業界情報の定期収集
実行タイミング: 毎朝 8:00
処理内容:
  1. 陸上界・スポーツテック関連の RSS / ニュースを取得
  2. Claude で要約・自社への示唆を生成
  3. Notion の日次ログに追記
"""
import os
import feedparser
import requests
from bs4 import BeautifulSoup
from base.claude_client import ask_claude_structured
from base.notion_client import create_page, find_today_page, append_to_page
from base.utils import setup_logger, log_job_start, log_job_end, log_job_error, today_str, today_label

logger = setup_logger("JOB-01 Research")

# 監視する情報ソース
RSS_FEEDS = [
    {
        "name": "陸上マガジン",
        "url": "https://www.rikujomag.com/feed",
        "category": "陸上界"
    },
    {
        "name": "月刊陸上競技",
        "url": "https://www.rikujyo.co.jp/feed",
        "category": "陸上界"
    },
    {
        "name": "SportsTech情報（Athlexer等）",
        "url": "https://sportstechworld.com/feed",
        "category": "スポーツテック"
    },
]

SEARCH_KEYWORDS = [
    "Atleta 陸上",
    "部活 コンディション管理 アプリ",
    "陸上競技 データ分析",
    "スポーツ SaaS 日本",
    "TraceWords 競合",
]

def fetch_rss_items(feed_url: str, max_items: int = 5) -> list[dict]:
    """RSSフィードから最新記事を取得"""
    try:
        feed = feedparser.parse(feed_url)
        items = []
        for entry in feed.entries[:max_items]:
            items.append({
                "title": entry.get("title", ""),
                "summary": entry.get("summary", "")[:300],
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
            })
        return items
    except Exception as e:
        logger.warning(f"RSS取得失敗 {feed_url}: {e}")
        return []

def fetch_google_news(keyword: str, max_items: int = 3) -> list[dict]:
    """Google News RSS から特定キーワードの記事を取得"""
    try:
        url = f"https://news.google.com/rss/search?q={requests.utils.quote(keyword)}&hl=ja&gl=JP&ceid=JP:ja"
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:max_items]:
            items.append({
                "title": entry.get("title", ""),
                "summary": entry.get("summary", "")[:200],
                "link": entry.get("link", ""),
            })
        return items
    except Exception as e:
        logger.warning(f"Google News取得失敗 {keyword}: {e}")
        return []

def collect_all_news() -> str:
    """全情報ソースからニュースを収集してテキストにまとめる"""
    all_news = []

    for feed in RSS_FEEDS:
        items = fetch_rss_items(feed["url"])
        if items:
            all_news.append(f"\n【{feed['name']} ({feed['category']})】")
            for item in items:
                all_news.append(f"- {item['title']}: {item['summary'][:150]}")

    for keyword in SEARCH_KEYWORDS:
        items = fetch_google_news(keyword)
        if items:
            all_news.append(f"\n【検索: {keyword}】")
            for item in items:
                all_news.append(f"- {item['title']}")

    return "\n".join(all_news) if all_news else "今日は収集できた記事がありませんでした。"

def analyze_with_claude(raw_news: str) -> str:
    """収集したニュースを Claude で分析・要約"""
    prompt = f"""
以下は今日収集した陸上界・スポーツテック関連のニュースです。

{raw_news}

# あなたの仕事（T09 Research + T01 Strategy の役割）

以下の観点で分析・整理してください：

## 1. 今日のトップニュース（3件以内）
事業に最も関連性が高いニュースを選び、1〜2行で要約。

## 2. 競合動向
Atleta、Runmetrix、その他競合の動きがあれば抽出。
なければ「特になし」と記載。

## 3. 自社 TraceWords への示唆
今日の情報から見えてくる：
- チャンス（追い風になる情報）
- リスク（脅威になる情報）
- 開発・マーケへの具体的なアクション提案（1〜2件）

## 4. Devil's Advocate の反論
上記の示唆に対して、「本当にそれは正しいか？」という反論を1件。

## 5. CEO へのアクション提案
今日の情報を受けて、CEO が今週中にやるべきことがあれば1件。
なければ「今週は特になし」と記載。
"""
    return ask_claude_structured(prompt)

def run():
    """JOB-01 メイン実行"""
    log_job_start(logger, "JOB-01 競合・業界情報収集")
    try:
        logger.info("ニュース収集中...")
        raw_news = collect_all_news()

        logger.info("Claude で分析中...")
        analysis = analyze_with_claude(raw_news)

        section = f"\n---\n## 🔍 T09 Research — 今日の業界情報（{today_label()}）\n\n{analysis}"

        daily_log_db = os.getenv("NOTION_DAILY_LOG_DB_ID")
        page_id = find_today_page(daily_log_db)

        if page_id:
            append_to_page(page_id, section)
            logger.info("既存の日次ログページに追記しました")
        else:
            create_page(
                database_id=daily_log_db,
                title=f"{today_str()} — 自動生成",
                content=section,
                properties={
                    "実施日": {"date": {"start": today_str()}},
                    "朝会実施": {"checkbox": False},
                }
            )
            logger.info("新規ページを作成して保存しました")

        log_job_end(logger, "JOB-01 競合・業界情報収集")

    except Exception as e:
        log_job_error(logger, "JOB-01", e)
        raise

if __name__ == "__main__":
    run()
