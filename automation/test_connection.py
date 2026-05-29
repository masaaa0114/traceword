"""
test_connection.py
Notion API と Claude API の接続確認スクリプト

使い方：
  cd automation
  python test_connection.py
"""
import os
from dotenv import load_dotenv

load_dotenv()

def test_notion():
    """Notion API 接続テスト"""
    print("\n=== Notion API テスト ===")
    try:
        from notion_client import Client
        notion = Client(auth=os.getenv("NOTION_API_KEY"))

        db_ids = {
            "日次ログ DB": os.getenv("NOTION_DAILY_LOG_DB_ID"),
            "週報 DB": os.getenv("NOTION_WEEKLY_REPORT_DB_ID"),
            "タスク DB": os.getenv("NOTION_TASK_DB_ID"),
            "意思決定ログ DB": os.getenv("NOTION_DECISION_LOG_DB_ID"),
        }

        for name, db_id in db_ids.items():
            if not db_id:
                print(f"  ⚠️  {name}: ID が未設定")
                continue
            try:
                result = notion.databases.retrieve(database_id=db_id)
                title = result.get("title", [{}])[0].get("text", {}).get("content", "無題")
                print(f"  ✅ {name}: 接続OK（{title}）")
            except Exception as e:
                print(f"  ❌ {name}: 接続失敗 → {e}")

    except ImportError:
        print("  ❌ notion-client がインストールされていません")
        print("     pip install notion-client を実行してください")
    except Exception as e:
        print(f"  ❌ Notion API キーエラー: {e}")


def test_claude():
    """Claude API 接続テスト"""
    print("\n=== Claude API テスト ===")
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=50,
            messages=[{"role": "user", "content": "「接続テスト成功」と返してください"}]
        )
        print(f"  ✅ Claude API: 接続OK")
        print(f"     レスポンス: {response.content[0].text}")
    except ImportError:
        print("  ❌ anthropic がインストールされていません")
        print("     pip install anthropic を実行してください")
    except Exception as e:
        print(f"  ❌ Claude API エラー: {e}")


def test_write_to_notion():
    """Notion への書き込みテスト"""
    print("\n=== Notion 書き込みテスト ===")
    try:
        from notion_client import Client
        from datetime import datetime

        notion = Client(auth=os.getenv("NOTION_API_KEY"))
        db_id = os.getenv("NOTION_DAILY_LOG_DB_ID")

        if not db_id:
            print("  ⚠️  NOTION_DAILY_LOG_DB_ID が未設定のためスキップ")
            return

        today = datetime.now().strftime("%Y-%m-%d")
        page = notion.pages.create(
            parent={"type": "data_source_id", "data_source_id": os.getenv("NOTION_DAILY_LOG_DS_ID", db_id)},
            properties={
                "日付": {"title": [{"text": {"content": f"[テスト] {today}"}}]},
                "実施日": {"date": {"start": today}},
                "自動生成": {"checkbox": True},
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {
                            "content": "✅ API 接続テスト成功。このページは削除してOKです。"
                        }}]
                    }
                }
            ]
        )
        print(f"  ✅ 書き込みテスト成功")
        print(f"     作成ページID: {page['id']}")
        print(f"     Notion で確認して削除してください")

    except Exception as e:
        print(f"  ❌ 書き込みテスト失敗: {e}")


def check_env():
    """環境変数の設定チェック"""
    print("\n=== 環境変数チェック ===")
    required = {
        "ANTHROPIC_API_KEY": "Claude API キー",
        "NOTION_API_KEY": "Notion API キー",
        "NOTION_DAILY_LOG_DB_ID": "日次ログ DB ID",
        "NOTION_WEEKLY_REPORT_DB_ID": "週報 DB ID",
        "NOTION_TASK_DB_ID": "タスク DB ID",
        "NOTION_DECISION_LOG_DB_ID": "意思決定ログ DB ID",
    }
    optional = {
        "GITHUB_TOKEN": "GitHub トークン（コードレビュー用）",
        "GITHUB_REPO": "GitHub リポジトリ名",
    }

    all_ok = True
    for key, label in required.items():
        val = os.getenv(key)
        if val:
            masked = val[:8] + "..." + val[-4:] if len(val) > 12 else "****"
            print(f"  ✅ {label}: {masked}")
        else:
            print(f"  ❌ {label}: 未設定")
            all_ok = False

    for key, label in optional.items():
        val = os.getenv(key)
        status = "✅ 設定済み" if val else "⚪ 未設定（任意）"
        print(f"  {status}: {label}")

    return all_ok


if __name__ == "__main__":
    print("=" * 50)
    print("  TraceWords 自動化システム 接続テスト")
    print("=" * 50)

    env_ok = check_env()

    if env_ok:
        test_notion()
        test_claude()
        test_write_to_notion()
    else:
        print("\n⚠️  必須の環境変数が未設定です。")
        print("   .env ファイルを確認してください。")
        print("   参考: .env.example")

    print("\n" + "=" * 50)
    print("  テスト完了")
    print("=" * 50)
