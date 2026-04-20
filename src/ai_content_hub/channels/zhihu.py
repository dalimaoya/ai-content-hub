"""知乎通道 — 收藏文章/回答/想法

依赖: pip install ai-content-hub[zhihu]

认证方式:
  - Cookie方式: 在浏览器登录知乎后，复制Cookie中的z_c0 token
  - 配置项: channels.zhihu.cookie 或环境变量 ZHIHU_COOKIE
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import AsyncIterator

from ..core.base import BaseChannel
from ..core.models import ContentItem, ContentType, Channel

try:
    import httpx
except ImportError:
    httpx = None


class ZhihuChannel(BaseChannel):
    """知乎收藏夹 & 关注内容采集"""

    name = "zhihu"
    display_name = "知乎"
    description = "采集知乎收藏文章、回答、想法"
    supported_content_types = [ContentType.ARTICLE, ContentType.ANSWER]

    API_BASE = "https://www.zhihu.com/api/v4"

    def __init__(self, config: dict):
        super().__init__(config)
        self.cookie = config.get("cookie", "")
        self.favlist_ids = config.get("favlist_ids", [])

    def validate_config(self) -> list[str]:
        errors = []
        if not self.cookie:
            errors.append("知乎Cookie未配置（channels.zhihu.cookie）")
        return errors

    def _get_headers(self) -> dict:
        return {
            "Cookie": self.cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://www.zhihu.com/",
        }

    async def scan(self, full: bool = False) -> AsyncIterator[ContentItem]:
        if not httpx:
            raise ImportError("需要安装 httpx: pip install httpx")

        async with httpx.AsyncClient(
            headers=self._get_headers(), follow_redirects=True, timeout=30
        ) as client:
            if self.favlist_ids:
                for fid in self.favlist_ids:
                    async for item in self._scan_favlist(client, fid, full):
                        yield item
            else:
                async for item in self._scan_default(client, full):
                    yield item

    async def _scan_default(self, client: httpx.AsyncClient, full: bool) -> AsyncIterator[ContentItem]:
        try:
            r = await client.get(f"{self.API_BASE}/me/favlists")
            if r.status_code != 200:
                return
            for favlist in r.json().get("data", []):
                fid = favlist.get("id")
                if fid:
                    async for item in self._scan_favlist(client, fid, full):
                        yield item
        except Exception as e:
            self.logger.error(f"扫描知乎收藏夹失败: {e}")

    async def _scan_favlist(self, client: httpx.AsyncClient, favlist_id: int, full: bool) -> AsyncIterator[ContentItem]:
        offset = 0
        while True:
            try:
                r = await client.get(
                    f"{self.API_BASE}/favlists/{favlist_id}/items",
                    params={"offset": offset, "limit": 20},
                )
                if r.status_code != 200:
                    break
                data = r.json()
                items = data.get("data", [])
                if not items:
                    break
                for item_data in items:
                    content_item = self._parse_item(item_data)
                    if content_item:
                        yield content_item
                if data.get("paging", {}).get("is_end", True):
                    break
                offset += 20
            except Exception as e:
                self.logger.error(f"获取收藏夹{favlist_id}失败: {e}")
                break

    def _parse_item(self, item_data: dict) -> ContentItem | None:
        try:
            content = item_data.get("content", {})
            item_type = content.get("type", "")

            if item_type == "answer":
                url = f"https://www.zhihu.com/question/{content.get('question', {}).get('id')}/answer/{content.get('id')}"
                title = content.get("question", {}).get("title", "知乎回答")
                content_type = ContentType.ANSWER
            elif item_type == "article":
                url = content.get("url", "")
                title = content.get("title", "知乎文章")
                content_type = ContentType.ARTICLE
            elif item_type == "pin":
                url = f"https://www.zhihu.com/pin/{content.get('id')}"
                title = content.get("excerpt", "")[:50] or "知乎想法"
                content_type = ContentType.PIN
            else:
                url = content.get("url", "")
                title = content.get("title", "知乎内容")
                content_type = ContentType.ARTICLE

            body = self._clean_html(content.get("content", content.get("excerpt", "")))
            author = content.get("author", {}).get("name", "")
            created_time = content.get("created_time", 0)

            return ContentItem(
                id=f"zhihu_{content.get('id', abs(hash(url)))}",
                title=title,
                content=body,
                channel=Channel.ZHIHU,
                content_type=content_type,
                url=url,
                author=author,
                created_at=datetime.fromtimestamp(created_time).isoformat() if created_time else "",
                tags=["知乎", item_type],
                metadata={
                    "voteup_count": content.get("voteup_count", 0),
                    "comment_count": content.get("comment_count", 0),
                },
            )
        except Exception as e:
            self.logger.warning(f"解析知乎内容失败: {e}")
            return None

    @staticmethod
    def _clean_html(html: str) -> str:
        if not html:
            return ""
        text = re.sub(r"<[^>]+>", "", html)
        return re.sub(r"\s+", " ", text).strip()

    async def parse(self, url: str) -> ContentItem | None:
        if "zhihu.com" not in url:
            return None
        if not httpx:
            raise ImportError("需要安装 httpx")

        async with httpx.AsyncClient(
            headers=self._get_headers(), follow_redirects=True, timeout=30
        ) as client:
            try:
                if "/question/" in url and "/answer/" in url:
                    return await self._parse_answer(client, url)
                elif "/p/" in url:
                    return await self._parse_article(client, url)
                else:
                    return await self._parse_generic(client, url)
            except Exception as e:
                self.logger.error(f"解析知乎链接失败 {url}: {e}")
                return None

    async def _parse_answer(self, client: httpx.AsyncClient, url: str) -> ContentItem | None:
        match = re.search(r"answer/(\d+)", url)
        if not match:
            return None
        a_id = match.group(1)

        r = await client.get(f"{self.API_BASE}/answers/{a_id}")
        if r.status_code != 200:
            return None

        data = r.json().get("data", {})
        question = data.get("question", {})

        return ContentItem(
            id=f"zhihu_answer_{a_id}",
            title=question.get("title", "知乎回答"),
            content=self._clean_html(data.get("content", "")),
            channel=Channel.ZHIHU,
            content_type=ContentType.ANSWER,
            url=url,
            author=data.get("author", {}).get("name", ""),
            created_at=datetime.fromtimestamp(data.get("created_time", 0)).isoformat() if data.get("created_time") else "",
            tags=["知乎", "回答"],
            metadata={
                "voteup_count": data.get("voteup_count", 0),
                "comment_count": data.get("comment_count", 0),
            },
        )

    async def _parse_article(self, client: httpx.AsyncClient, url: str) -> ContentItem | None:
        match = re.search(r"/p/(\d+)", url)
        if not match:
            return None
        article_id = match.group(1)

        r = await client.get(f"{self.API_BASE}/articles/{article_id}")
        if r.status_code != 200:
            return None

        data = r.json().get("data", {})

        return ContentItem(
            id=f"zhihu_article_{article_id}",
            title=data.get("title", "知乎文章"),
            content=self._clean_html(data.get("content", "")),
            channel=Channel.ZHIHU,
            content_type=ContentType.ARTICLE,
            url=url,
            author=data.get("author", {}).get("name", ""),
            created_at=data.get("created", ""),
            tags=["知乎", "文章"],
            metadata={
                "voteup_count": data.get("voteup_count", 0),
                "comment_count": data.get("comment_count", 0),
            },
        )

    async def _parse_generic(self, client: httpx.AsyncClient, url: str) -> ContentItem | None:
        r = await client.get(url)
        if r.status_code != 200:
            return None

        title_match = re.search(r"<title>(.*?)</title>", r.text)
        title = title_match.group(1).replace(" - 知乎", "").strip() if title_match else "知乎内容"

        content_match = re.search(r'"content":"(.*?)"', r.text)
        content = self._clean_html(content_match.group(1)) if content_match else "内容提取失败，请查看原文"

        return ContentItem(
            id=f"zhihu_url_{abs(hash(url))}",
            title=title,
            content=content[:5000],
            channel=Channel.ZHIHU,
            content_type=ContentType.ARTICLE,
            url=url,
            tags=["知乎"],
        )
