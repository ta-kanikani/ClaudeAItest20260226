"""
AI記事執筆エージェント - エントリーポイント

ペルソナを持つAIエージェントが、指定テーマについて
自律的にWebリサーチ→記事執筆→WordPress入稿を行う。
"""

import os
from dotenv import load_dotenv

from persona import PERSONA_SYSTEM_PROMPT
from researcher import Researcher
from writer import Writer
from cms import CMSClient


def main(theme: str) -> None:
    load_dotenv()

    print(f"[Agent] テーマ「{theme}」の記事作成を開始します")

    # Step 1: Webリサーチ（クエリ自動生成→検索→要約）
    researcher = Researcher()
    research = researcher.research(theme)
    print(f"[Agent] リサーチ完了: {len(research['sources'])} 件のソースを取得")
    print(f"[Agent] 重要ポイント: {len(research['key_points'])} 項目")

    # Step 2: 記事執筆
    writer = Writer(system_prompt=PERSONA_SYSTEM_PROMPT)
    article = writer.write(theme=theme, research=research)
    print(f"[Agent] 記事執筆完了: {article.word_count} 字")

    # Step 3: WordPress入稿
    cms = CMSClient()
    post_url = cms.publish(article)
    print(f"[Agent] 入稿完了: {post_url}")


if __name__ == "__main__":
    import sys

    theme = sys.argv[1] if len(sys.argv) > 1 else "最新AIサービスの活用法"
    main(theme)
