"""
Webリサーチモジュール

Tavily Search APIを使用してテーマに関する情報を収集する。
"""

import os
from dataclasses import dataclass

from tavily import TavilyClient


@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    score: float


class Researcher:
    """Tavily APIを使ってWebリサーチを行うクラス。"""

    def __init__(self) -> None:
        api_key = os.environ["TAVILY_API_KEY"]
        self.client = TavilyClient(api_key=api_key)

    def search(self, theme: str, max_results: int = 5) -> list[SearchResult]:
        """
        テーマに関するWeb検索を実行し、結果を返す。

        Args:
            theme: 検索テーマ
            max_results: 取得する最大件数

        Returns:
            SearchResult のリスト
        """
        response = self.client.search(
            query=theme,
            search_depth="advanced",
            max_results=max_results,
        )

        results = []
        for item in response.get("results", []):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    score=item.get("score", 0.0),
                )
            )
        return results
