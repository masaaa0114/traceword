"""
base/claude_client.py
Claude API との共通通信処理
"""
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

BUSINESS_CONTEXT = """
あなたは陸上競技特化の統合プラットフォーム「TraceWords」の
自動化エージェントです。

# 事業概要
- プロダクト：選手の感覚言語化アプリ（陸上競技特化）
- ターゲット：大学・高校・実業団のコーチ・選手
- 競合：Atleta（最大の脅威）、Runmetrix（カシオ）
- 差別化：陸上特化の深さ × シンプルさ × コーチ-選手間コミュニケーション
- フェーズ：MVP開発中（感覚言語化アプリが最初の機能）
- 創業者：ITエンジニア出身の陸上ボランティアコーチ、37歳

# 行動原則
1. 論理的・丁寧・具体的に
2. 結論を先に、根拠は後に
3. CEO の意思決定を助けることが最優先
4. 不確実なことは「不明」と記す
"""

def ask_claude(prompt: str, system: str = None, max_tokens: int = 2000) -> str:
    """Claude API にシンプルな質問を投げる"""
    system_prompt = (system or "") + "\n\n" + BUSINESS_CONTEXT
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

def ask_claude_structured(prompt: str, system: str = None, max_tokens: int = 3000) -> str:
    """構造化（Markdown）アウトプットを要求する"""
    system_prompt = (system or "") + "\n\n" + BUSINESS_CONTEXT
    full_prompt = prompt + "\n\n出力は Notion にそのまま貼れる Markdown 形式で。"
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": full_prompt}]
    )
    return response.content[0].text
