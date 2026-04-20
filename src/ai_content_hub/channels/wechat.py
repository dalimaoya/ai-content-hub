# 微信公众号文章通道

from __future__ import annotations

import logging
import re
from typing import AsyncIterator

from ..core.base import BaseChannel
from ..core.models import Channel, ContentItem, ContentType

logger = logging.getLogger(__name__)


class WechatChannel(BaseChannel):
    """微信公众号文章解析通道

    功能：解析微信公众号文章URL，提取标题/作者/正文/图片
    配置项：无需额外配置，发链接即触发
    """

    name = "wechat"
    display_name = "微信文章"

    # 微信文章URL模式
    WECHAT_URL_PATTERN = re.compile(r"mp\.weixin\.qq\.com/s/")

    def validate_config(self) -> bool:
        """微信文章不需要额外配置"""
        return True

    async def scan(self, incremental: bool = True) -> AsyncIterator[ContentItem]:
        """微信文章通道不支持定时扫描，只能通过parse()解析链接"""
        # 微信文章是被动解析模式，没有主动扫描能力
        return
        yield  # make it an async generator

    async def parse(self, url_or_id: str) -> ContentItem | None:
        """解析微信公众号文章URL"""
        if not self.WECHAT_URL_PATTERN.search(url_or_id):
            logger.error(f"不是微信文章URL: {url_or_id}")
            return None

        try:
            import httpx
            from readability import Document
            from lxml import html as lxml_html
        except ImportError:
            raise ImportError("请安装依赖: pip install ai-content-hub[wechat]")

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
                resp = await client.get(url_or_id, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                resp.raise_for_status()
                html_content = resp.text

            # 提取标题：优先 var msg_title → og:title → readability
            title = self._extract_title(html_content)

            # 提取作者/公众号
            author = self._extract_author(html_content)

            # 提取发布时间
            pub_time = self._extract_pub_time(html_content)

            # 提取正文
            doc = Document(html_content)
            content_html = doc.summary()
            content_text = self._html_to_text(content_html)

            # 生成ID
            from hashlib import md5
            item_id = f"wechat_{md5(url_or_id.encode()).hexdigest()[:12]}"

            return ContentItem(
                id=item_id,
                title=title,
                content=content_text,
                channel=Channel.WECHAT,
                content_type=ContentType.ARTICLE,
                url=url_or_id,
                author=author,
                created_at=pub_time,
                metadata={"source": "wechat_article"},
            )

        except Exception as e:
            logger.error(f"解析微信文章失败: {e}")
            return None

    @staticmethod
    def _extract_title(html_content: str) -> str:
        """从HTML中提取标题"""
        # 1. var msg_title
        m = re.search(r'var\s+msg_title\s*=\s*["\']([^"\']+)["\']', html_content)
        if m:
            return m.group(1).strip()

        # 2. og:title
        m = re.search(r'<meta\s+property="og:title"\s+content="([^"]*)"', html_content)
        if m:
            return m.group(1).strip()

        # 3. readability fallback
        try:
            from readability import Document
            doc = Document(html_content)
            return doc.title() or "无标题"
        except Exception:
            return "无标题"

    @staticmethod
    def _extract_author(html_content: str) -> str:
        """从HTML中提取作者/公众号名"""
        # var nickname
        m = re.search(r'var\s+nickname\s*=\s*["\']([^"\']+)["\']', html_content)
        if m:
            return m.group(1).strip()

        # profile_biz -> nickname
        m = re.search(r'class="profile_nickname">([^<]+)<', html_content)
        if m:
            return m.group(1).strip()

        return ""

    @staticmethod
    def _extract_pub_time(html_content: str) -> str:
        """从HTML中提取发布时间"""
        # var ct (时间戳)
        m = re.search(r'var\s+ct\s*=\s*["\'](\d+)["\']', html_content)
        if m:
            try:
                from datetime import datetime
                ts = int(m.group(1))
                return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, OSError):
                pass

        # publish_time
        m = re.search(r'var\s+publish_time\s*=\s*["\']([^"\']+)["\']', html_content)
        if m:
            return m.group(1).strip()

        return ""

    @staticmethod
    def _html_to_text(html_content: str) -> str:
        """将HTML转为纯文本"""
        try:
            from lxml import html as lxml_html
            tree = lxml_html.fromstring(html_content)
            # 移除script和style
            for tag in tree.xpath("//script | //style"):
                tag.getparent().remove(tag)
            return tree.text_content().strip()
        except Exception:
            # fallback: 简单标签去除
            text = re.sub(r"<[^>]+>", "", html_content)
            return text.strip()
