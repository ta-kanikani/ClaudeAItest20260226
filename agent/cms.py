"""
WordPress入稿モジュール

WordPress REST API を使って記事を下書き投稿する。
"""

import os

import requests

from writer import Article


class CMSClient:
    """WordPress REST API クライアント。"""

    def __init__(self) -> None:
        self.base_url = os.environ["WP_BASE_URL"].rstrip("/")
        self.username = os.environ["WP_USERNAME"]
        self.password = os.environ["WP_APP_PASSWORD"]

    def publish(self, article: Article, status: str = "draft") -> str:
        """
        記事をWordPressに投稿する。

        Args:
            article: 投稿する Article オブジェクト
            status: 投稿ステータス（"draft" | "publish"）

        Returns:
            投稿されたページのURL
        """
        endpoint = f"{self.base_url}/wp-json/wp/v2/posts"

        payload = {
            "title": article.title,
            "content": article.body,
            "status": status,
        }

        response = requests.post(
            endpoint,
            json=payload,
            auth=(self.username, self.password),
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        return data.get("link", "")
