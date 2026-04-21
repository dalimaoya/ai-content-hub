# 飞书文档解析通道

from __future__ import annotations

import logging
import re
from typing import AsyncIterator

from ..core.base import BaseChannel
from ..core.models import Channel, ContentItem, ContentType

logger = logging.getLogger(__name__)


class FeishuDocChannel(BaseChannel):
    """飞书文档解析通道

    功能：通过Playwright无头浏览器渲染飞书文档页面，提取正文内容
    支持：链接分享模式的飞书文档（任何人可查看）
    依赖：pip install playwright && playwright install chromium
    配置项：
        urls: list - 要解析的飞书文档URL列表
    """

    name = "feishu"
    display_name = "飞书文档"

    CONTENT_SELECTORS = [
        ".doc-content",
        ".render-unit-wrapper",
        ".doc-body",
        "[data-block-id]",
        "article",
    ]

    TITLE_SELECTORS = [
        ".doc-title .title-text",
        ".doc-title",
        "h1",
    ]

    def validate_config(self) -> bool:
        return bool(self.config.get("urls"))

    async def scan(self, incremental: bool = True) -> AsyncIterator[ContentItem]:
        """解析飞书文档URL列表"""
        urls = self.config.get("urls", [])
        processed = set(self.config.get("_processed_ids", []))

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("需要安装 playwright: pip install playwright && playwright install chromium")
            return

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            for url in urls:
                item_id = f"feishu_{hash(url) % 1000000}"

                if incremental and item_id in processed:
                    continue

                result = await self._parse_with_browser(browser, url)

                if result:
                    yield ContentItem(
                        id=item_id,
                        title=result["title"],
                        content=result["content"],
                        channel=Channel.CUSTOM,
                        content_type=ContentType.ARTICLE,
                        url=url,
                        metadata={
                            "source_url": url,
                            "parser": "feishu_doc_channel",
                        },
                    )
                    processed.add(item_id)

            await browser.close()

    async def parse(self, url_or_id: str) -> ContentItem | None:
        """解析单个飞书文档URL"""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("需要安装 playwright")
            return None

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
            result = await self._parse_with_browser(browser, url_or_id)
            await browser.close()

        if result:
            return ContentItem(
                id=f"feishu_{hash(url_or_id) % 1000000}",
                title=result["title"],
                content=result["content"],
                channel=Channel.CUSTOM,
                content_type=ContentType.ARTICLE,
                url=url_or_id,
                metadata={"source_url": url_or_id},
            )
        return None

    async def _parse_with_browser(self, browser, url: str) -> dict | None:
        """用Playwright浏览器解析飞书文档"""
        page = None
        try:
            page = await browser.new_page()
            page.set_default_timeout(30000)

            response = await page.goto(url, wait_until="networkidle")

            if response and response.status in (403, 404):
                logger.warning(f"飞书文档无法访问 ({response.status}): {url}")
                return None

            # 等待内容渲染
            for selector in self.CONTENT_SELECTORS:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    break
                except Exception:
                    continue
            else:
                await page.wait_for_timeout(3000)

            # 提取标题
            title = ""
            for selector in self.TITLE_SELECTORS:
                try:
                    title_el = await page.query_selector(selector)
                    if title_el:
                        title = await title_el.inner_text()
                        if title:
                            break
                except Exception:
                    continue

            if not title:
                title = await page.title()
                title = re.sub(r'\s*[-–—]\s*飞书云文档$', '', title)
                title = re.sub(r'\s*[-–—]\s*Lark$', '', title)

            # 提取正文
            markdown_parts = []
            blocks = await page.query_selector_all("[data-block-id]")

            if blocks:
                for block in blocks:
                    text = (await block.inner_text()).strip()
                    if not text:
                        continue
                    block_type = await block.get_attribute("data-block-type") or ""
                    if "heading1" in block_type:
                        markdown_parts.append(f"# {text}\n")
                    elif "heading2" in block_type:
                        markdown_parts.append(f"## {text}\n")
                    elif "heading3" in block_type:
                        markdown_parts.append(f"### {text}\n")
                    elif "bullet" in block_type or "unordered" in block_type:
                        markdown_parts.append(f"- {text}\n")
                    elif "ordered" in block_type:
                        markdown_parts.append(f"1. {text}\n")
                    elif "quote" in block_type:
                        markdown_parts.append(f"> {text}\n")
                    elif "code" in block_type:
                        markdown_parts.append(f"```\n{text}\n```\n")
                    else:
                        markdown_parts.append(f"{text}\n\n")
            else:
                content_el = None
                for selector in self.CONTENT_SELECTORS:
                    content_el = await page.query_selector(selector)
                    if content_el:
                        break
                if content_el:
                    markdown_parts.append(await content_el.inner_text())

            markdown = re.sub(r'\n{3,}', '\n\n', '\n'.join(markdown_parts)).strip()

            return {"title": title.strip(), "content": markdown}

        except Exception as e:
            logger.error(f"解析飞书文档失败: {e}")
            return None
        finally:
            if page:
                await page.close()

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "config_valid": self.validate_config(),
            "urls_count": len(self.config.get("urls", [])),
        }
