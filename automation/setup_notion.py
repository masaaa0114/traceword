# -*- coding: utf-8 -*-
"""
setup_notion.py
Notion ワークスペースの全DBを自動作成するスクリプト（完全版）

使い方：
  python setup_notion.py        # DB作成 + プロパティ自動追加
  python setup_notion.py --reset # 既存DBを削除して作り直す
"""

import os
import re
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# 事前チェック
# ============================================================

def check_requirements():
    try:
        from notion_client import Client
        print("  OK notion-client")
    except ImportError:
        print("  ERROR: pip install notion-client")
        return False

    api_key = os.getenv("NOTION_API_KEY", "").strip()
    if not api_key:
        print("  ERROR: NOTION_API_KEY が未設定")
        return False
    print(f"  OK NOTION_API_KEY: {api_key[:8]}...")

    parent_id = os.getenv("NOTION_PARENT_PAGE_ID", "").strip()
    if not parent_id:
        print("  ERROR: NOTION_PARENT_PAGE_ID が未設定")
        return False
    print(f"  OK NOTION_PARENT_PAGE_ID: {parent_id[:8]}...")
    return True


# ============================================================
# 親ページにコンテンツ追加
# ============================================================

def setup_parent_page(notion, parent_page_id):
    """親ページの中身を確認・追加"""
    print("\nChecking parent page content...")

    try:
        # 既存のブロックを取得
        children = notion.blocks.children.list(block_id=parent_page_id)
        existing_blocks = children.get("results", [])

        # すでに見出しがあるかチェック
        has_heading = any(
            b.get("type", "").startswith("heading") or
            (b.get("type") == "paragraph" and "TraceWords" in str(b))
            for b in existing_blocks
        )

        if has_heading:
            print("  Parent page already has content. Skipping.")
            return

        # コンテンツを追加
        blocks = [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {
                        "content": "🏃 TraceWords 組織ダッシュボード"
                    }}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {
                        "content": "陸上×IT 統合プラットフォーム事業の組織管理スペースです。"
                    }}]
                }
            },
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {
                        "content": "📁 データベース一覧"
                    }}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {
                        "content": "下記の5つのデータベースで組織を運営しています。"
                    }}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "📋 全部署タスク管理 — タスク一元管理"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "📅 日次ログ — 毎日の朝会と部署アウトプット"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "📈 週報アーカイブ — 週次レポート"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "🎲 意思決定ログ — 重要な意思決定の記録"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "⚙️ 自動化ログ — 自動化ジョブの実行履歴"}}]
                }
            },
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "🎯 組織の北極星指標"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {
                        "content": "陸上競技に「データと感覚をつなぐ言語」を取り戻す。"
                    }}]
                }
            },
        ]

        notion.blocks.children.append(
            block_id=parent_page_id,
            children=blocks
        )
        print(f"  Added {len(blocks)} blocks to parent page")

    except Exception as e:
        print(f"  WARN: {e}")


# ============================================================
# DB プロパティ定義（日本語名で直接作る）
# ============================================================

def get_db_definitions():
    """すべて日本語名で定義。Notion API は日本語名のプロパティを受け入れる"""
    return {
        "task": {
            "emoji": "📋",
            "name": "全部署タスク管理",
            "env_key": "NOTION_TASK_DB_ID",
            "title_key": "タスク名",
            "properties": {
                "タスク名": {"title": {}},
                "担当部署": {
                    "select": {
                        "options": [
                            {"name": "T00 CoS", "color": "gray"},
                            {"name": "T01 Strategy", "color": "blue"},
                            {"name": "T02 Legal", "color": "purple"},
                            {"name": "T03 Finance", "color": "green"},
                            {"name": "T04 Marketing", "color": "orange"},
                            {"name": "T05 Sales", "color": "yellow"},
                            {"name": "T06 Product", "color": "red"},
                            {"name": "T07 Design", "color": "pink"},
                            {"name": "T08 PR", "color": "brown"},
                            {"name": "T09 Research", "color": "default"},
                            {"name": "T10 Devil", "color": "blue"},
                        ]
                    }
                },
                "ステータス": {"status": {}},
                "優先度": {
                    "select": {
                        "options": [
                            {"name": "🔴 高", "color": "red"},
                            {"name": "🟡 中", "color": "yellow"},
                            {"name": "🟢 低", "color": "green"},
                        ]
                    }
                },
                "期限": {"date": {}},
                "実施日": {"date": {}},
                "CEO判断必要": {"checkbox": {}},
                "Devil反論済み": {"checkbox": {}},
                "種類": {
                    "select": {
                        "options": [
                            {"name": "日次タスク", "color": "blue"},
                            {"name": "週次タスク", "color": "green"},
                            {"name": "プロジェクト", "color": "orange"},
                            {"name": "単発", "color": "gray"},
                        ]
                    }
                },
                "詳細": {"rich_text": {}},
                "成果物リンク": {"url": {}},
            }
        },

        "daily": {
            "emoji": "📅",
            "name": "日次ログ",
            "env_key": "NOTION_DAILY_LOG_DB_ID",
            "title_key": "日付",
            "properties": {
                "日付": {"title": {}},
                "実施日": {"date": {}},
                "朝会実施": {"checkbox": {}},
                "主な議題": {"rich_text": {}},
                "CEO判断事項": {"rich_text": {}},
                "一日のサマリ": {"rich_text": {}},
                "関連部署": {
                    "multi_select": {
                        "options": [
                            {"name": "T00", "color": "gray"},
                            {"name": "T01", "color": "blue"},
                            {"name": "T02", "color": "purple"},
                            {"name": "T03", "color": "green"},
                            {"name": "T04", "color": "orange"},
                            {"name": "T05", "color": "yellow"},
                            {"name": "T06", "color": "red"},
                            {"name": "T07", "color": "pink"},
                            {"name": "T08", "color": "brown"},
                            {"name": "T09", "color": "default"},
                            {"name": "T10", "color": "blue"},
                        ]
                    }
                },
                "自動生成": {"checkbox": {}},
            }
        },

        "weekly": {
            "emoji": "📈",
            "name": "週報アーカイブ",
            "env_key": "NOTION_WEEKLY_REPORT_DB_ID",
            "title_key": "週",
            "properties": {
                "週": {"title": {}},
                "開始日": {"date": {}},
                "終了日": {"date": {}},
                "全体評価": {
                    "select": {
                        "options": [
                            {"name": "🌟 優秀", "color": "yellow"},
                            {"name": "🟢 良好", "color": "green"},
                            {"name": "🟡 課題あり", "color": "orange"},
                            {"name": "🔴 要改善", "color": "red"},
                        ]
                    }
                },
                "主要成果": {"rich_text": {}},
                "主要課題": {"rich_text": {}},
                "来週の方針": {"rich_text": {}},
                "CEO振り返り": {"rich_text": {}},
                "自動生成": {"checkbox": {}},
            }
        },

        "decision": {
            "emoji": "🎲",
            "name": "意思決定ログ",
            "env_key": "NOTION_DECISION_LOG_DB_ID",
            "title_key": "決定事項",
            "properties": {
                "決定事項": {"title": {}},
                "決定日": {"date": {}},
                "カテゴリ": {
                    "select": {
                        "options": [
                            {"name": "戦略", "color": "blue"},
                            {"name": "開発", "color": "orange"},
                            {"name": "法務", "color": "purple"},
                            {"name": "財務", "color": "green"},
                            {"name": "組織", "color": "gray"},
                            {"name": "マーケ", "color": "yellow"},
                            {"name": "その他", "color": "default"},
                        ]
                    }
                },
                "重要度": {
                    "select": {
                        "options": [
                            {"name": "🔴 高", "color": "red"},
                            {"name": "🟡 中", "color": "yellow"},
                            {"name": "🟢 低", "color": "green"},
                        ]
                    }
                },
                "状態": {
                    "select": {
                        "options": [
                            {"name": "決定済み", "color": "green"},
                            {"name": "実行中", "color": "blue"},
                            {"name": "効果検証中", "color": "yellow"},
                            {"name": "完了", "color": "gray"},
                            {"name": "撤回", "color": "red"},
                        ]
                    }
                },
                "再評価日": {"date": {}},
                "Devil反論あり": {"checkbox": {}},
                "背景": {"rich_text": {}},
                "採用理由": {"rich_text": {}},
            }
        },

        "automation": {
            "emoji": "⚙️",
            "name": "自動化ログ",
            "env_key": "NOTION_AUTO_LOG_DB_ID",
            "title_key": "ジョブ名",
            "properties": {
                "ジョブ名": {"title": {}},
                "実行日時": {"date": {}},
                "ジョブID": {
                    "select": {
                        "options": [
                            {"name": "JOB-01 情報収集", "color": "blue"},
                            {"name": "JOB-02 朝会アジェンダ", "color": "green"},
                            {"name": "JOB-03 週報生成", "color": "orange"},
                            {"name": "JOB-04 SNSコンテンツ", "color": "pink"},
                            {"name": "JOB-05 コードレビュー", "color": "red"},
                            {"name": "JOB-06 KPIアラート", "color": "yellow"},
                            {"name": "JOB-07 月次レポート", "color": "purple"},
                        ]
                    }
                },
                "結果": {
                    "select": {
                        "options": [
                            {"name": "✅ 成功", "color": "green"},
                            {"name": "⚠️ 警告", "color": "yellow"},
                            {"name": "❌ 失敗", "color": "red"},
                        ]
                    }
                },
                "出力サマリ": {"rich_text": {}},
                "実行時間（秒）": {"number": {"format": "number"}},
                "エラー詳細": {"rich_text": {}},
            }
        },
    }


# ============================================================
# DB 作成（プロパティを後から1つずつ追加）
# ============================================================

def create_db_with_properties(notion, parent_page_id, db_def):
    """
    notion-client 3.x の新API形式でDBを作成する。
    プロパティは initial_data_source.properties に入れる。
    戻り値: (database_id, data_source_id) のタプル
    """
    name  = db_def["name"]
    props = db_def["properties"]

    print(f"\n[{db_def['emoji']}] {name}")

    try:
        db = notion.databases.create(
            parent={"type": "page_id", "page_id": parent_page_id},
            icon={"type": "emoji", "emoji": db_def["emoji"]},
            title=[{"type": "text", "text": {"content": name}}],
            initial_data_source={"properties": props}
        )
        db_id = db["id"]

        # data_source_id を取得（ページ作成時に必要）
        data_sources = db.get("data_sources", [])
        ds_id = data_sources[0]["id"] if data_sources else None

        print(f"  Created DB: {db_id.replace('-','')[:8]}...")
        if ds_id:
            print(f"  Data source: {ds_id.replace('-','')[:8]}...")

        # 作成されたプロパティを確認（data_source から取得）
        if ds_id:
            try:
                ds = notion.data_sources.retrieve(data_source_id=ds_id)
                created_props = list(ds.get("properties", {}).keys())
                print(f"  Properties: {len(created_props)} / {len(props)}")
                if len(created_props) >= len(props):
                    print(f"  All properties OK")
                else:
                    missing = set(props.keys()) - set(created_props)
                    print(f"  WARN missing: {missing}")
            except Exception as e:
                print(f"  (could not verify properties: {e})")

        return (db_id.replace("-", ""), ds_id.replace("-", "") if ds_id else None)
    except Exception as e:
        print(f"  ERROR creating DB: {e}")
        return (None, None)


# ============================================================
# 既存DBアーカイブ
# ============================================================

def archive_existing_dbs(notion, db_ids):
    """既存DBを削除"""
    print("\n[RESET] Archiving existing DBs...")
    failed = []
    for key, db_id in db_ids.items():
        if not db_id:
            continue
        try:
            notion.pages.update(page_id=db_id, archived=True)
            print(f"  Archived: {key}")
        except Exception:
            failed.append((key, db_id))
            print(f"  Skip: {key} (will create new)")

    if failed:
        print()
        print("  *** Manual cleanup needed in Notion ***")
        for key, db_id in failed:
            print(f"    {key}: {db_id[:8]}...")
        print("  Open each DB → Right click → Delete")
        print()


# ============================================================
# .env 更新
# ============================================================

def update_env_file(db_ids):
    """取得した DB ID を .env に書き込む"""
    print("\nUpdating .env ...")
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

    if not os.path.exists(env_path):
        example = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env.example")
        if os.path.exists(example):
            with open(example, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = "# TraceWords\n"
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(content)

    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()

    for env_key, db_id in db_ids.items():
        if not db_id:
            continue
        pattern  = rf"^{re.escape(env_key)}=.*$"
        new_line = f"{env_key}={db_id}"
        if re.search(pattern, content, re.MULTILINE):
            content = re.sub(pattern, new_line, content, flags=re.MULTILINE)
            print(f"  Updated: {env_key}")
        else:
            content += f"\n{new_line}"
            print(f"  Added:   {env_key}")

    with open(env_path, "w", encoding="utf-8") as f:
        f.write(content)


# ============================================================
# サンプルデータ
# ============================================================

def add_sample_data(notion, task_ds_id, daily_ds_id):
    """サンプルタスクと初日ログを追加（新APIはdata_source_id指定）"""
    print("\nAdding sample data...")
    today = datetime.now().strftime("%Y-%m-%d")

    tasks = [
        {
            "タスク名":    {"title": [{"text": {"content": "MVP 要件定義書の最終確認"}}]},
            "担当部署":    {"select": {"name": "T06 Product"}},
            "優先度":      {"select": {"name": "🔴 高"}},
            "期限":        {"date": {"start": today}},
            "種類":        {"select": {"name": "プロジェクト"}},
            "CEO判断必要": {"checkbox": True},
        },
        {
            "タスク名":   {"title": [{"text": {"content": "利用規約・プラポリのドラフト作成"}}]},
            "担当部署":   {"select": {"name": "T02 Legal"}},
            "優先度":     {"select": {"name": "🟡 中"}},
            "種類":       {"select": {"name": "プロジェクト"}},
        },
        {
            "タスク名":   {"title": [{"text": {"content": "競合 Atleta の最新動向調査"}}]},
            "担当部署":   {"select": {"name": "T01 Strategy"}},
            "優先度":     {"select": {"name": "🟢 低"}},
            "種類":       {"select": {"name": "週次タスク"}},
        },
    ]

    ok = 0
    for t in tasks:
        try:
            notion.pages.create(parent={"type": "data_source_id", "data_source_id": task_ds_id}, properties=t)
            ok += 1
        except Exception as e:
            print(f"  WARN task skip: {e}")
    print(f"  Sample tasks: {ok}/{len(tasks)}")

    # 日次ログ
    try:
        notion.pages.create(
            parent={"type": "data_source_id", "data_source_id": daily_ds_id},
            properties={
                "日付":     {"title": [{"text": {"content": f"{today} セットアップ完了"}}]},
                "実施日":   {"date": {"start": today}},
                "主な議題": {"rich_text": [{"text": {"content": "Notion HQ の自動セットアップが完了しました。"}}]},
                "自動生成": {"checkbox": True},
            },
            children=[
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "🎉 セットアップ完了"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {
                            "content": "TraceWords HQ の Notion スペースが自動セットアップされました。"
                        }}]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": "次のステップ"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": "Claude Projects にナレッジをアップロード"}}],
                        "checked": False
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": ".env に ANTHROPIC_API_KEY を設定"}}],
                        "checked": False
                    }
                },
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": "python test_connection.py で接続テスト"}}],
                        "checked": False
                    }
                },
            ]
        )
        print("  Daily log: OK")
    except Exception as e:
        print(f"  WARN daily log: {e}")


# ============================================================
# メイン
# ============================================================

def main():
    print("=" * 55)
    print("  TraceWords HQ - Notion Auto Setup")
    print("=" * 55)

    print("\n[1/6] Checking requirements...")
    if not check_requirements():
        return

    from notion_client import Client
    # notion-client 3.x は新API(initial_data_source形式)を使う
    notion = Client(auth=os.getenv("NOTION_API_KEY"))

    parent_page_id = os.getenv("NOTION_PARENT_PAGE_ID", "").replace("-", "").strip()

    # --reset
    if "--reset" in sys.argv:
        existing = {
            "NOTION_TASK_DB_ID":          os.getenv("NOTION_TASK_DB_ID", ""),
            "NOTION_DAILY_LOG_DB_ID":     os.getenv("NOTION_DAILY_LOG_DB_ID", ""),
            "NOTION_WEEKLY_REPORT_DB_ID": os.getenv("NOTION_WEEKLY_REPORT_DB_ID", ""),
            "NOTION_DECISION_LOG_DB_ID":  os.getenv("NOTION_DECISION_LOG_DB_ID", ""),
            "NOTION_AUTO_LOG_DB_ID":      os.getenv("NOTION_AUTO_LOG_DB_ID", ""),
        }
        archive_existing_dbs(notion, existing)

    print("\n[2/6] Setting up parent page content...")
    setup_parent_page(notion, parent_page_id)

    print("\n[3/6] Creating databases with all properties...")
    defs = get_db_definitions()
    created = {}        # env_key -> database_id
    data_sources = {}   # env_key -> data_source_id
    for key, db_def in defs.items():
        db_id, ds_id = create_db_with_properties(notion, parent_page_id, db_def)
        if db_id:
            created[db_def["env_key"]] = db_id
            data_sources[db_def["env_key"]] = ds_id

    print(f"\n  Result: {len(created)} / {len(defs)} DBs created")

    print("\n[4/6] Updating .env ...")
    if created:
        # DB ID と data_source ID の両方を保存
        env_data = dict(created)
        for env_key, ds_id in data_sources.items():
            if ds_id:
                # NOTION_TASK_DB_ID -> NOTION_TASK_DS_ID
                ds_key = env_key.replace("_DB_ID", "_DS_ID")
                env_data[ds_key] = ds_id
        update_env_file(env_data)

    print("\n[5/6] Adding sample data...")
    task_ds  = data_sources.get("NOTION_TASK_DB_ID")
    daily_ds = data_sources.get("NOTION_DAILY_LOG_DB_ID")
    if task_ds and daily_ds:
        add_sample_data(notion, task_ds, daily_ds)
    else:
        print("  Skipped (data source not available)")

    print("\n[6/6] Done!")
    print("=" * 55)
    print(f"  Created: {len(created)} DBs")
    for k, v in created.items():
        print(f"  {k}: {v[:8]}...")
    print()
    print("Next steps:")
    print("  1. Open Notion and check TraceWords HQ")
    print("  2. Set ANTHROPIC_API_KEY in .env")
    print("  3. Run: python test_connection.py")
    print("=" * 55)


if __name__ == "__main__":
    main()
