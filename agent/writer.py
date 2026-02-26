"""
記事執筆モジュール

Anthropic Claude (claude-sonnet-4-6) を使用して、
リサーチ結果をもとにペルソナの文体でMarkdown記事を生成する。
"""

import os
from dataclasses import dataclass, field

import anthropic

from persona import PERSONA_SYSTEM_PROMPT

# ---------------------------------------------------------------------------
# プロンプトテンプレート
# ---------------------------------------------------------------------------

USER_PROMPT_TEMPLATE = """
テーマ：{theme}

調査結果：
{research_summary}

重要ポイント：
{key_points}

体験ログ：
{experience_log}

上記をもとに記事を執筆してください。
"""


# ---------------------------------------------------------------------------
# データクラス
# ---------------------------------------------------------------------------


@dataclass
class Article:
    title: str
    body: str
    word_count: int = field(init=False)

    def __post_init__(self) -> None:
        self.word_count = len(self.body)


# ---------------------------------------------------------------------------
# Writer クラス
# ---------------------------------------------------------------------------


class Writer:
    """Claude APIを使って記事を生成するクラス。"""

    MODEL = "claude-sonnet-4-6"

    def __init__(self, system_prompt: str = PERSONA_SYSTEM_PROMPT) -> None:
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.system_prompt = system_prompt

    # ------------------------------------------------------------------
    # パブリックAPI
    # ------------------------------------------------------------------

    def write_article(
        self,
        theme: str,
        research: dict,
        experience_log: str = "",
        screenshots: list = [],
    ) -> str:
        """
        テーマとリサーチ結果をもとにMarkdown形式の記事を執筆する。

        Args:
            theme: 記事テーマ
            research: Researcher.research() が返す dict
                      （summary / sources / key_points / raw）
            experience_log: 体験ログのテキスト（任意）
            screenshots: スクリーンショットのパスまたはBase64リスト（任意、現在は未使用）

        Returns:
            Markdown形式の記事文字列（2000〜3000字）
        """
        key_points_text = "\n".join(
            f"- {p}" for p in research.get("key_points", [])
        )
        sources_text = "\n".join(research.get("sources", []))

        user_prompt = USER_PROMPT_TEMPLATE.format(
            theme=theme,
            research_summary=research.get("summary", "（要約なし）"),
            key_points=key_points_text or "（ポイントなし）",
            experience_log=experience_log or "（体験ログなし）",
        )

        user_prompt += f"""
## 参考URL
{sources_text}

## 執筆要件
- 文字数：2000〜3000字
- 出力形式：Markdown
- 構成：
  - タイトル（H1）：SEOを意識したキーワードを含む
  - リード文：150字程度で記事全体の要約
  - H2セクション×3〜4：体験ベースの具体的な内容
  - まとめ：読者へのアクションを促す締め
- 記事末尾に「本記事はAIエージェントが執筆しました」と明記すること
"""

        message = self.client.messages.create(
            model=self.MODEL,
            max_tokens=4096,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        return message.content[0].text.strip()

    def write(self, theme: str, research: dict | list) -> Article:
        """
        研究結果（dictまたはSearchResultリスト）から Article を生成する。

        research が list の場合は dict 形式に変換してから write_article を呼ぶ。
        """
        if isinstance(research, list):
            research = {
                "summary": "\n".join(r.content for r in research),
                "sources": [r.url for r in research],
                "key_points": [],
                "raw": research,
            }

        body = self.write_article(theme=theme, research=research)
        title = self._extract_title(body)
        return Article(title=title, body=body)

    # ------------------------------------------------------------------
    # 内部ヘルパー
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_title(markdown: str) -> str:
        """Markdown本文からH1タイトルを抽出する。"""
        for line in markdown.splitlines():
            if line.startswith("# "):
                return line.lstrip("# ").strip()
        return "無題"
