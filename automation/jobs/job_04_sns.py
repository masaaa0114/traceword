"""
jobs/job_04_sns.py

JOB-04: SNSコンテンツ案の自動生成
実行タイミング: 毎週月曜 9:00
処理内容:
  1. 今週のテーマを業界ニュース・事業フェーズから自動判断
  2. Claude で X (Twitter) と note の投稿案を生成
  3. Notion の週報ページに追記（CEO が選んで使う）
"""
import os
from base.claude_client import ask_claude_structured
from base.notion_client import find_today_page, append_to_page, create_page
from base.utils import (setup_logger, log_job_start, log_job_end,
                        log_job_error, today_str, today_label, week_label)

logger = setup_logger("JOB-04 SNS")

# コンテンツ発信の軸（T08 PR/Content の設定）
CONTENT_THEMES = [
    "陸上指導論 × データ活用",
    "選手の感覚言語化の実例",
    "コーチと選手のコミュニケーション",
    "業界トレンド解説（GPS・AI・計測技術）",
    "CEO個人の発信（コーチ経験談・独立ストーリー）",
    "TraceWords の開発裏話",
]

def generate_sns_content() -> str:
    """今週分の SNS コンテンツ案を生成"""
    prompt = f"""
今週（{week_label()}）の SNS 投稿コンテンツ案を作成してください。

# 発信テーマの軸
{chr(10).join(f'- {t}' for t in CONTENT_THEMES)}

# 発信先と特性
- X (Twitter)：140文字、陸上指導者・コーチ向け、技術的な洞察を短く
- note：800〜1500文字、深い考察記事、「保存・シェア」されるもの

# 出力形式

## 📱 X (Twitter) 投稿案（今週分 / 3〜5本）

### X案1：[テーマ名]
投稿文（140文字以内）：
...
ハッシュタグ：#陸上競技 #コーチング...
投稿推奨日時：月曜 or 火曜 朝7時

### X案2：[テーマ名]
...

---

## 📝 note 記事案（今週1本）

### タイトル：「...」
書き出し（300文字）：
...
構成案：
1. ...
2. ...
3. ...
想定読者：...
CTA（最後の一行）：...

---

## ⚡ Devil's Advocate の指摘
このコンテンツ案で「刺さらない」リスクを1つ。

---

## 📌 CEO へのメモ
このコンテンツを投稿する前に確認してほしいこと。

# 注意事項
- 「拡散重視のバズ狙い」はしない
- 横展開（他競技）のコンテンツは作らない
- 競合の悪口は書かない
- 専門性と親しみやすさのバランスを取る
"""
    return ask_claude_structured(prompt)

def run():
    """JOB-04 メイン実行"""
    log_job_start(logger, "JOB-04 SNSコンテンツ生成")
    try:
        logger.info("今週のSNSコンテンツ案を生成中...")
        content = generate_sns_content()

        section = f"\n---\n## 📱 T08 PR/Content — 今週の SNS コンテンツ案\n\n{content}"

        daily_log_db = os.getenv("NOTION_DAILY_LOG_DB_ID")
        page_id = find_today_page(daily_log_db)
        if page_id:
            append_to_page(page_id, section)
        else:
            create_page(
                database_id=daily_log_db,
                title=f"{today_str()} SNSコンテンツ案",
                content=section,
                properties={"実施日": {"date": {"start": today_str()}}}
            )

        logger.info("SNSコンテンツ案を Notion に保存しました")
        log_job_end(logger, "JOB-04 SNSコンテンツ生成")

    except Exception as e:
        log_job_error(logger, "JOB-04", e)
        raise

if __name__ == "__main__":
    run()
