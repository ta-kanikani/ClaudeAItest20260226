"""
記事執筆モジュール

Anthropic Claude (claude-sonnet-4-6) を使用して、
リサーチ結果をもとにペルソナの文体で記事を生成する。
"""

import os
from dataclasses import dataclass

import anthropic

from researcher import SearchResult


@dataclass
class Article:
    title: str
    body: str


class Writer:
    """Claude APIを使って記事を生成するクラス。"""

    MODEL = "claude-sonnet-4-6"

    def __init__(self, system_prompt: str) -> None:
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.system_prompt = system_prompt

    def write(self, theme: str, research: list[SearchResult]) -> Article:
        """
        テーマとリサーチ結果をもとに記事を執筆する。

        Args:
            theme: 記事テーマ
            research: Researcher が収集した SearchResult のリスト

        Returns:
            Article（タイトルと本文）
        """
        research_text = "\n\n".join(
            f"【{r.title}】\n{r.content}\nURL: {r.url}" for r in research
        )

        user_message = f"""
以下のリサーチ結果をもとに、テーマ「{theme}」について記事を執筆してください。

## リサーチ結果
{research_text}

## 出力フォーマット
タイトル: <記事タイトル>

<記事本文（Markdown形式）>
"""

        message = self.client.messages.create(
            model=self.MODEL,
            max_tokens=4096,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        raw = message.content[0].text
        title, body = self._parse(raw)
        return Article(title=title, body=body)

    @staticmethod
    def _parse(raw: str) -> tuple[str, str]:
        """LLM出力からタイトルと本文を分離する。"""
        lines = raw.strip().splitlines()
        title = ""
        body_lines = []

        for i, line in enumerate(lines):
            if line.startswith("タイトル:"):
                title = line.removeprefix("タイトル:").strip()
            else:
                body_lines = lines[i + 1 :] if title else lines[i:]
                break

        body = "\n".join(body_lines).strip()
        return title or "無題", body
