"""
base/notion_client.py
Notion API との共通通信処理
"""
import os
from datetime import datetime
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

notion = Client(auth=os.getenv("NOTION_API_KEY"))

def create_page(database_id: str, title: str, content: str,
                properties: dict = None) -> dict:
    """
    Notion DB に新規ページを作成（新API対応）
    DB ごとに異なるタイトル列名（日付/週/決定事項など）を自動検出する
    """
    ds_id = _resolve_data_source_id(database_id)

    # タイトル列名を data_source から自動取得
    title_key = _get_title_property_name(ds_id) or "Name"

    # properties に既にタイトル列が含まれていれば、それを優先
    if properties and title_key in properties:
        props = dict(properties)
    else:
        props = {
            title_key: {"title": [{"text": {"content": title}}]},
            **(properties or {})
        }

    children = _markdown_to_blocks(content)
    return notion.pages.create(
        parent={"type": "data_source_id", "data_source_id": ds_id},
        properties=props,
        children=children
    )


def _get_title_property_name(data_source_id: str):
    """data_source からタイトル列のプロパティ名を取得"""
    try:
        ds = notion.data_sources.retrieve(data_source_id=data_source_id)
        for prop_name, prop_def in ds.get("properties", {}).items():
            if prop_def.get("type") == "title":
                return prop_name
    except Exception:
        pass
    return None


def _resolve_data_source_id(maybe_db_id: str) -> str:
    """
    渡された ID が DB の場合、対応する data_source_id を探して返す。
    .env に NOTION_*_DB_ID と NOTION_*_DS_ID が両方ある前提で、
    DB ID と一致するキーを探し、その DS_ID を返す。
    見つからなければ渡された ID をそのまま返す（フォールバック）。
    """
    db_id_clean = maybe_db_id.replace("-", "")

    db_to_ds_map = {
        os.getenv("NOTION_TASK_DB_ID", "").replace("-", ""):          os.getenv("NOTION_TASK_DS_ID", ""),
        os.getenv("NOTION_DAILY_LOG_DB_ID", "").replace("-", ""):     os.getenv("NOTION_DAILY_LOG_DS_ID", ""),
        os.getenv("NOTION_WEEKLY_REPORT_DB_ID", "").replace("-", ""): os.getenv("NOTION_WEEKLY_REPORT_DS_ID", ""),
        os.getenv("NOTION_DECISION_LOG_DB_ID", "").replace("-", ""): os.getenv("NOTION_DECISION_LOG_DS_ID", ""),
        os.getenv("NOTION_AUTO_LOG_DB_ID", "").replace("-", ""):     os.getenv("NOTION_AUTO_LOG_DS_ID", ""),
    }

    if db_id_clean in db_to_ds_map and db_to_ds_map[db_id_clean]:
        return db_to_ds_map[db_id_clean]
    return maybe_db_id

def append_to_page(page_id: str, content: str) -> None:
    """既存ページにブロックを追記（新API: 引数は block_id）"""
    blocks = _markdown_to_blocks(content)
    notion.blocks.children.append(block_id=page_id, children=blocks)

def find_today_page(database_id: str):
    """今日の日付のページIDを検索（新API: data_sources.query 使用）"""
    today = datetime.now().strftime("%Y-%m-%d")
    ds_id = _resolve_data_source_id(database_id)
    try:
        results = notion.data_sources.query(
            data_source_id=ds_id,
            filter={
                "property": "実施日",
                "date": {"equals": today}
            }
        )
        pages = results.get("results", [])
        return pages[0]["id"] if pages else None
    except Exception:
        return None

def update_property(page_id: str, properties: dict) -> None:
    """ページのプロパティを更新"""
    notion.pages.update(page_id=page_id, properties=properties)

def _markdown_to_blocks(markdown: str) -> list:
    """Markdown テキストを Notion ブロック形式に変換"""
    blocks = []
    for line in markdown.split("\n"):
        if not line.strip():
            continue
        if line.startswith("## "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text",
                                   "text": {"content": line[3:]}}]
                }
            })
        elif line.startswith("### "):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text",
                                   "text": {"content": line[4:]}}]
                }
            })
        elif line.startswith("- "):
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text",
                                   "text": {"content": line[2:]}}]
                }
            })
        elif line.startswith("□ ") or line.startswith("✅ "):
            blocks.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"type": "text",
                                   "text": {"content": line[2:]}}],
                    "checked": line.startswith("✅")
                }
            })
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text",
                                   "text": {"content": line}}]
                }
            })
    return blocks[:100]  # Notion の 1回あたり上限
