"""
Webリサーチモジュール

Tavily Search API と Claude API を組み合わせて、テーマに関する情報を
収集・要約・構造化する。
"""

import os
from dataclasses import dataclass

import anthropic
import requests
from tavily import TavilyClient


@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    score: float


class Researcher:
    """Tavily + Claude APIを使ってWebリサーチを行うクラス。"""

    MODEL = "claude-sonnet-4-6"

    def __init__(self) -> None:
        self.tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
        self.claude = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # ------------------------------------------------------------------
    # 内部メソッド
    # ------------------------------------------------------------------

    def _generate_queries(self, theme: str) -> list[str]:
        """Claudeを使ってテーマから最適な検索クエリを3つ生成する。"""
        message = self.claude.messages.create(
            model=self.MODEL,
            max_tokens=256,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"以下のテーマについてWebリサーチを行います。\n"
                        f"異なる角度をカバーする最適な検索クエリを3つ生成してください。\n"
                        f"出力形式：1行1クエリ（番号・記号なし）\n\n"
                        f"テーマ：{theme}"
                    ),
                }
            ],
        )
        lines = message.content[0].text.strip().splitlines()
        return [l.strip() for l in lines if l.strip()][:3]

    def _tavily_search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """Tavily APIで1クエリ分の検索を実行する。"""
        response = self.tavily.search(
            query=query,
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

    def _fetch_page(self, url: str, timeout: int = 10) -> str:
        """指定URLのページテキストをフェッチする。"""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; AIArticleAgent/1.0)"}
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            return f"[fetch error: {e}]"

    def _summarize(
        self, theme: str, all_results: list[SearchResult]
    ) -> tuple[str, list[str]]:
        """Claudeでリサーチ結果を要約し、重要ポイント5項目を抽出する。"""
        combined = "\n\n".join(
            f"【{r.title}】\n{r.content}" for r in all_results[:8]
        )
        message = self.claude.messages.create(
            model=self.MODEL,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"以下はテーマ「{theme}」に関するWebリサーチ結果です。\n"
                        f"分析して次の2つを出力してください。\n\n"
                        f"## リサーチ結果\n{combined}\n\n"
                        f"## 出力フォーマット（厳守）\n"
                        f"要約:\n<300字以内の要約>\n\n"
                        f"重要ポイント:\n"
                        f"- ポイント1\n- ポイント2\n- ポイント3\n"
                        f"- ポイント4\n- ポイント5"
                    ),
                }
            ],
        )
        raw = message.content[0].text.strip()
        summary = ""
        key_points: list[str] = []
        section = None

        for line in raw.splitlines():
            stripped = line.strip()
            if stripped.startswith("要約:"):
                section = "summary"
                rest = stripped.removeprefix("要約:").strip()
                if rest:
                    summary = rest
            elif stripped.startswith("重要ポイント:"):
                section = "points"
            elif section == "summary" and stripped:
                summary = (summary + " " + stripped).strip()
            elif section == "points" and stripped.startswith("-"):
                key_points.append(stripped.lstrip("- ").strip())

        return summary, key_points

    # ------------------------------------------------------------------
    # パブリックAPI
    # ------------------------------------------------------------------

    def research(self, theme: str) -> dict:
        """
        テーマについてWebリサーチを実行し、構造化された結果を返す。

        Args:
            theme: 調査テーマ（例：「HumanAds AIエージェント広告」）

        Returns:
            {
                "summary": 要約テキスト,
                "sources": [URL一覧],
                "key_points": [重要ポイントリスト],
                "raw": SearchResult のリスト（生データ）,
            }
        """
        print(f"[Researcher] クエリ生成中: {theme}")
        queries = self._generate_queries(theme)
        print(f"[Researcher] 生成クエリ: {queries}")

        seen_urls: set[str] = set()
        all_results: list[SearchResult] = []

        for query in queries:
            print(f"[Researcher] 検索中: {query}")
            for r in self._tavily_search(query):
                if r.url not in seen_urls:
                    seen_urls.add(r.url)
                    all_results.append(r)

        # スコア降順で整列
        all_results.sort(key=lambda r: r.score, reverse=True)

        print(f"[Researcher] {len(all_results)} 件取得。要約・ポイント抽出中...")
        summary, key_points = self._summarize(theme, all_results)

        return {
            "summary": summary,
            "sources": [r.url for r in all_results],
            "key_points": key_points,
            "raw": all_results,
        }
