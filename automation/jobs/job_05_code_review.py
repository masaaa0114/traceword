"""
jobs/job_05_code_review.py

JOB-05: コードのスリム化・品質チェック
実行タイミング: 毎週日曜 22:00
処理内容:
  1. GitHub から直近1週間のコミット差分を取得
  2. Claude でコードレビュー（品質・スリム化・セキュリティ）
  3. Notion に改善提案レポートを保存
  4. 重大な問題があれば GitHub Issue を自動作成
"""
import os
import requests
from base.claude_client import ask_claude_structured
from base.notion_client import create_page
from base.utils import (setup_logger, log_job_start, log_job_end,
                        log_job_error, today_str, today_label)

logger = setup_logger("JOB-05 CodeReview")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO  = os.getenv("GITHUB_REPO", "")
GH_HEADERS   = {"Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json"}

def get_recent_commits(days: int = 7) -> list[dict]:
    """直近 N 日のコミット一覧を取得"""
    from datetime import datetime, timedelta
    since = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
    url = f"https://api.github.com/repos/{GITHUB_REPO}/commits?since={since}&per_page=20"
    resp = requests.get(url, headers=GH_HEADERS, timeout=10)
    if resp.status_code != 200:
        logger.warning(f"GitHub API エラー: {resp.status_code}")
        return []
    return resp.json()

def get_commit_diff(sha: str) -> str:
    """特定コミットの差分を取得（最大2000文字）"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/commits/{sha}"
    resp = requests.get(url, headers=GH_HEADERS, timeout=10)
    if resp.status_code != 200:
        return ""
    data = resp.json()
    files = data.get("files", [])
    diffs = []
    for f in files[:5]:  # 最大5ファイル
        filename = f.get("filename", "")
        patch = f.get("patch", "")[:500]
        if patch:
            diffs.append(f"### {filename}\n```\n{patch}\n```")
    return "\n".join(diffs)[:2000]

def create_github_issue(title: str, body: str) -> None:
    """GitHub に Issue を自動作成"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
    payload = {
        "title": f"[自動検知] {title}",
        "body": body,
        "labels": ["auto-review", "bug"]
    }
    resp = requests.post(url, json=payload, headers=GH_HEADERS, timeout=10)
    if resp.status_code == 201:
        logger.info(f"GitHub Issue 作成: {title}")
    else:
        logger.warning(f"Issue 作成失敗: {resp.status_code}")

def review_code(commits_summary: str, diff_sample: str) -> str:
    """Claude でコードをレビュー"""
    prompt = f"""
今週の TraceWords プロジェクトのコードをレビューしてください。

## 今週のコミット概要
{commits_summary}

## 差分サンプル（代表的なもの）
{diff_sample}

# レビュー観点

## 1. スリム化の提案
- 不要なコード・重複処理の指摘
- よりシンプルに書ける箇所
- 依存ライブラリの整理

## 2. 品質チェック
- バグの可能性（重大度：高/中/低）
- テストが必要な箇所
- エラーハンドリングの漏れ

## 3. セキュリティチェック
- APIキーの扱い
- 個人情報の取り扱い
- 認証・認可の問題

## 4. パフォーマンスチェック
- 不要な API 呼び出し
- N+1 問題
- 重い処理の最適化余地

## 5. MVP 観点での過剰実装チェック
「今やらなくていいこと」をやっていないか。
YAGNI 原則に違反していないか。

## 6. 今週のアクション提案（優先度順）
重大な問題があれば「🚨 即対応必要」と明記。

## 7. Devil's Advocate
このレビュー自体への反論（見落とし・偏りはないか）。

# 注意
- MVP フェーズなので完璧主義にならない
- 「動くこと」優先、ただし安全性は妥協しない
- コードが取得できない場合は、その旨を書いて一般的な
  MVP 開発の注意点をまとめること
"""
    return ask_claude_structured(prompt)

def run():
    """JOB-05 メイン実行"""
    log_job_start(logger, "JOB-05 コードレビュー")
    try:
        commits = []
        diff_sample = "（GitHubトークン未設定のため差分取得をスキップ）"

        if GITHUB_TOKEN and GITHUB_REPO:
            logger.info("GitHub からコミット情報を取得中...")
            commits = get_recent_commits(days=7)
            commits_summary = "\n".join([
                f"- {c['sha'][:7]}: {c['commit']['message'][:80]}"
                for c in commits[:10]
            ]) or "今週のコミットはありません。"

            if commits:
                latest_sha = commits[0]["sha"]
                diff_sample = get_commit_diff(latest_sha)
        else:
            commits_summary = "GitHubトークン未設定のため、コミット情報を取得できませんでした。"
            logger.warning("GITHUB_TOKEN または GITHUB_REPO が未設定です")

        logger.info("Claude でコードレビュー中...")
        review = review_code(commits_summary, diff_sample)

        # 重大な問題があれば GitHub Issue を作成
        if "🚨 即対応必要" in review and GITHUB_TOKEN and GITHUB_REPO:
            create_github_issue(
                title=f"{today_str()} 週次コードレビューで重大な問題を検知",
                body=review[:3000]
            )

        section = f"# 🔧 T06 Product/Engineering — 週次コードレビュー\n\n日付: {today_label()}\n\n{review}"

        create_page(
            database_id=os.getenv("NOTION_DAILY_LOG_DB_ID"),
            title=f"{today_str()} コードレビューレポート",
            content=section,
            properties={"実施日": {"date": {"start": today_str()}}}
        )

        logger.info("コードレビューレポートを Notion に保存しました")
        log_job_end(logger, "JOB-05 コードレビュー")

    except Exception as e:
        log_job_error(logger, "JOB-05", e)
        raise

if __name__ == "__main__":
    run()
