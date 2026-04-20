"""小红书通道 — 笔记收藏/探索内容

依赖: pip install ai-content-hub[xiaohongshu]

认证方式:
  - Cookie方式: 在浏览器登录小红书后，复制Cookie
  - 配置项: channels.xiaohongshu.cookie 或环境变量 XHS_COOKIE

技术方案参考: https://github.com/NanmiCoder/MediaCrawler
"""

from __future__ import annotations

import json
import re
from typing import AsyncIterator

from ..core.base import BaseChannel
from ..core.models import ContentItem, ContentType, Channel

try:
    import httpx
except ImportError:
    httpx = None


class XiaohongshuChannel(BaseChannel):
    """小红书笔记采集"""

    name = "xiaohongshu"
    display_name = "小红书"
    description = "采集小红书收藏笔记、探索内容"
    supported_content_types = [ContentType.ARTICLE, ContentType.POST]

    API_BASE = "https://edith.xiaohongshu.com/api/sns/web/v1"

    def __init__(self, config: dict):
        super().__init__(config)
        self.cookie = config.get("cookie", "")
        self.collection_ids = config.get("collection_ids", [])
        self.delay = config.get("delay", 2.0)

    def validate_config(self) -> list[str]:
        errors = []
        if not self.cookie:
            errors.append("小红书Cookie未配置（channels.xiaohongshu.cookie）")
        return errors

    def _get_headers(self) -> dict:
        return {
            "Cookie": self.cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.xiaohongshu.com/",
            "Origin": "https://www.xiaohongshu.com",
        }

    async def scan(self, full: bool = False) -> AsyncIterator[ContentItem]:
        if not httpx:
            raise ImportError("需要安装 httpx: pip install httpx")

        async with httpx.AsyncClient(
            headers=self._get_headers(), follow_redirects=True, timeout=30
        ) as client:
            if self.collection_ids:
                for coll_id in self.collection_ids:
                    async for item in self._scan_collection(client, coll_id, full):
                        yield item
            else:
                async for item in self._scan_favorites(client, full):
                    yield item

    async def _scan_favorites(self, client: httpx.AsyncClient, full: bool) -> AsyncIterator[ContentItem]:
        try:
            page = 1
            while True:
                r = await client.get(
                    f"{self.API_BASE}/collection/feed",
                    params={"page": page, "page_size": 20},
                )
                if r.status_code != 200:
                    break

                data = r.json()
                notes = data.get("data", {}).get("notes", [])
                if not notes:
                    break

                for note_data in notes:
                    item = self._parse_summary(note_data)
                    if item:
                        yield item

                if not data.get("data", {}).get("has_more", False):
                    break
                page += 1
                import asyncio
                await asyncio.sleep(self.delay)

        except Exception as e:
            self.logger.error(f"扫描小红书收藏失败: {e}")

    async def _scan_collection(self, client: httpx.AsyncClient, collection_id: str, full: bool) -> AsyncIterator[ContentItem]:
        try:
            page = 1
            while True:
                r = await client.get(
                    f"{self.API_BASE}/collection/note",
                    params={"collection_id": collection_id, "page": page, "page_size": 20},
                )
                if r.status_code != 200:
                    break

                data = r.json()
                notes = data.get("data", {}).get("notes", [])
                if not notes:
                    break

                for note_data in notes:
                    item = self._parse_summary(note_data)
                    if item:
                        yield item

                if not data.get("data", {}).get("has_more", False):
                    break
                page += 1
                import asyncio
                await asyncio.sleep(self.delay)

        except Exception as e:
            self.logger.error(f"扫描小红书收藏夹{collection_id}失败: {e}")

    def _parse_summary(self, note_data: dict) -> ContentItem | None:
        try:
            note = note_data.get("note_card", note_data)
            note_id = note.get("note_id", "")
            display_title = note.get("display_title", "")
            note_type = note.get("type", "")
            desc = note.get("desc", "")
            user = note.get("user", {})
            nickname = user.get("nickname", "")

            url = f"https://www.xiaohongshu.com/explore/{note_id}"

            tag_list = note.get("tag_list", [])
            tags = ["小红书"] + [t.get("name", "") for t in tag_list if t.get("name")]

            interact_info = note.get("interact_info", {})
            content_type = ContentType.VIDEO if note_type == "video" else ContentType.POST

            return ContentItem(
                id=f"xhs_{note_id}",
                title=display_title or desc[:50] or "小红书笔记",
                content=desc,
                channel=Channel.XIAOHONGSHU,
                content_type=content_type,
                url=url,
                author=nickname,
                created_at=note.get("time", ""),
                tags=tags,
                metadata={
                    "note_type": note_type,
                    "liked_count": interact_info.get("liked_count", "0"),
                },
            )
        except Exception as e:
            self.logger.warning(f"解析小红书笔记失败: {e}")
            return None

    async def parse(self, url: str) -> ContentItem | None:
        if "xiaohongshu.com" not in url:
            return None
        if not httpx:
            raise ImportError("需要安装 httpx")

        note_id = self._extract_note_id(url)
        if not note_id:
            return None

        async with httpx.AsyncClient(
            headers=self._get_headers(), follow_redirects=True, timeout=30
        ) as client:
            try:
                r = await client.get(f"https://www.xiaohongshu.com/explore/{note_id}")
                if r.status_code != 200:
                    return None

                note_data = self._extract_from_html(r.text)
                if not note_data:
                    return ContentItem(
                        id=f"xhs_{note_id}",
                        title="小红书笔记",
                        content="内容提取失败，请查看原文",
                        channel=Channel.XIAOHONGSHU,
                        content_type=ContentType.POST,
                        url=url,
                        tags=["小红书"],
                    )

                return self._parse_detail(note_data, url)
            except Exception as e:
                self.logger.error(f"解析小红书链接失败 {url}: {e}")
                return None

    def _extract_note_id(self, url: str) -> str:
        for pattern in [r"explore/([a-f0-9]+)", r"item/([a-f0-9]+)", r"note/([a-f0-9]+)"]:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return ""

    def _extract_from_html(self, html: str) -> dict | None:
        match = re.search(r'__INITIAL_STATE__\s*=\s*({.*?})\s*</script>', html, re.DOTALL)
        if not match:
            return None
        try:
            json_str = match.group(1).replace("undefined", "null")
            data = json.loads(json_str)
            note = data.get("note", {}).get("noteDetailMap", {})
            if note:
                first_key = list(note.keys())[0]
                return note[first_key].get("note", {})
        except (json.JSONDecodeError, KeyError, IndexError):
            pass
        return None

    def _parse_detail(self, note_data: dict, url: str) -> ContentItem:
        note_id = note_data.get("noteId", "")
        title = note_data.get("title", "")
        desc = note_data.get("desc", "")
        note_type = note_data.get("type", "")

        user = note_data.get("user", {})
        nickname = user.get("nickname", "")

        tag_list = note_data.get("tagList", [])
        tags = ["小红书"]
        for tag in tag_list:
            if isinstance(tag, dict):
                tags.append(tag.get("name", ""))
            elif isinstance(tag, str):
                tags.append(tag)

        image_list = note_data.get("imageList", [])
        image_urls = [img.get("urlDefault", img.get("url", "")) for img in image_list]

        interact_info = note_data.get("interactInfo", {})
        content_type = ContentType.VIDEO if note_type == "video" else ContentType.POST

        # 组装正文
        content_parts = [desc] if desc else []
        if image_urls:
            content_parts.append("\n## 图片")
            for i, img_url in enumerate(image_urls, 1):
                content_parts.append(f"![图片{i}]({img_url})")

        return ContentItem(
            id=f"xhs_{note_id}",
            title=title or desc[:50] or "小红书笔记",
            content="\n\n".join(content_parts),
            channel=Channel.XIAOHONGSHU,
            content_type=content_type,
            url=url,
            author=nickname,
            tags=tags,
            metadata={
                "note_type": note_type,
                "liked_count": interact_info.get("likedCount", "0"),
                "collected_count": interact_info.get("collectedCount", "0"),
                "comment_count": interact_info.get("commentCount", "0"),
                "image_count": len(image_urls),
            },
        )
